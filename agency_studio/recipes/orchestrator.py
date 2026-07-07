"""Sequential recipe runner over the existing mission stream.

Drives a recipe's declared stages in order, streaming the **mission SSE vocabulary** so the
existing timeline renders the whole chain. Every stage does real work (see ``stages.py``);
the mission stage runs the veto-gated mission unchanged. A stage that cannot run raises
``RecipeStageUnavailable`` (surfaced by the endpoint as an honest error frame); the mission
stage stopping (cancel/error/veto) ends the run with its outputs already preserved.

Per-stage resume (issue #21 · T043): when a **post-mission** stage fails, the run snapshots a
recipe checkpoint (``completed_stages`` + replayable ``outputs``) and returns an error result
carrying the checkpoint id, so the existing resume affordance can restart at the failed stage
without re-running the veto-gated mission. The mission stage itself is never checkpointed here —
it owns the existing mission checkpoint machinery.
"""

from __future__ import annotations

import threading

from . import checkpoint
from .models import Recipe
from .stages import ensure_cloud_allowed, run_compose, run_export

# The recipe mission stage runs on the v1 validated engine (Art. II). Kept here as the single
# source of truth so the server's pre-flight validation gate uses the same id.
ENGINE = "claude-code"


def _replay(handler, stage, outputs: dict) -> None:
    """Replay an already-completed stage on resume: emit its start/done frames and, for a media
    stage, re-emit the asset frame from the saved output — so the resumed timeline renders identically
    to a fresh run, without re-doing the work."""
    handler._write_sse({"phase": "stage", "stage": stage.kind, "status": "start"})
    entry = outputs.get(stage.kind)
    if stage.kind in ("compose", "pipeline") and isinstance(entry, dict):
        handler._write_sse({"phase": "asset", "stage": stage.kind, "kind": "video",
                            "status": entry.get("status"), "url": entry.get("url")})
    handler._write_sse({"phase": "stage", "stage": stage.kind, "status": "done", "replayed": True})


def _restore_mission(resume_envelope: dict) -> "dict | None":
    """Reconstruct the mission ``result_box`` from a resume envelope by RELOADING the saved dossier
    (never re-running the veto-gated mission). Returns ``None`` when the dossier can't be reloaded —
    the caller then re-runs the mission stage normally rather than resuming on a missing base."""
    mission_out = (resume_envelope.get("outputs") or {}).get("mission") or {}
    mid = mission_out.get("mission_id")
    if not mid:
        return None
    from agency_cli.runner_bridge import MissionResult
    from agency_kit import store
    try:
        dossier = store.load(mid)
    except (OSError, ValueError):
        return None
    return {"result": MissionResult(path=store.missions_dir() / mid / "dossier.json", dossier=dossier)}


def run(handler, recipe: Recipe, *, run_id: str, subject: str, cloud_optins: set[str],
        cancel_event: threading.Event, explicit_cancel: threading.Event,
        resume_envelope: "dict | None" = None) -> dict:
    result_box: dict = {}
    outputs: dict = {}
    completed: set[str] = set()
    if resume_envelope is not None:
        outputs = dict(resume_envelope.get("outputs") or {})
        completed = set(resume_envelope.get("completed_stages") or [])
        if "mission" in completed:
            restored = _restore_mission(resume_envelope)
            if restored is None:  # base dossier gone — fall back to a clean re-run of the mission
                completed.discard("mission")
                outputs.pop("mission", None)
            else:
                result_box = restored
    handler._write_sse({"phase": "run", "run_id": run_id})
    for stage in recipe.stages:
        ensure_cloud_allowed(stage.kind, stage.tier, cloud_optins)
        if cancel_event.is_set():
            return {"cancelled": True}
        if stage.kind in completed:
            _replay(handler, stage, outputs)
            continue
        handler._write_sse({"phase": "stage", "stage": stage.kind, "status": "start"})
        try:
            if stage.kind == "mission":
                # Images render locally within the mission (asset_clause); video is a dedicated
                # LOCAL compose stage below, so use_video stays off (the default video backend may
                # be cloud — never a silent paid render here).
                result_box = handler._stream_mission(
                    subject, ENGINE, cancel_event,
                    web_search=True, use_video=False,
                    run_id=run_id, explicit_cancel=explicit_cancel,
                    verification={"min_sources": 3, "resolve": False},
                ) or {"cancelled": True}
                if "result" not in result_box:
                    return result_box  # cancelled / error / veto — mission owns its own checkpoint
                outputs["mission"] = {"mission_id": str(result_box["result"].dossier.get("mission_id"))}
            elif stage.kind == "pipeline":
                from .stages import run_pipeline_stage
                result_box, entry = run_pipeline_stage(handler, recipe, subject, cancel_event)
                outputs["pipeline"] = entry
                if entry is not None:
                    handler._write_sse({"phase": "asset", "stage": "pipeline", "kind": "video",
                                        "status": entry.get("status"), "url": entry.get("url")})
            elif stage.kind == "compose":
                entry = run_compose(handler, result_box, cancel_event)
                outputs["compose"] = entry
                if entry is not None:
                    handler._write_sse({"phase": "asset", "stage": "compose", "kind": "video",
                                        "status": entry.get("status"), "url": entry.get("url")})
            elif stage.kind == "export":
                outputs["export"] = run_export(handler, result_box)
        except Exception as exc:
            # A cancel surfaces as a raised error from a stage's subprocess drive; report it as a
            # clean cancelled run, like the mission stage does.
            if cancel_event.is_set():
                return {"cancelled": True}
            # A fatal POST-mission stage is resumable: snapshot the completed work so the operator
            # can restart at this stage without re-running the veto-gated mission. Only checkpoint
            # when the mission is done (else there is nothing worth skipping — e.g. a lone pipeline
            # recipe, or a probe failure before any stage completed).
            if "mission" in completed:
                checkpoint.write(handler.server.docs_root, checkpoint.envelope(
                    run_id=run_id, recipe_id=recipe.id, subject=subject, cloud_optins=cloud_optins,
                    completed_stages=sorted(completed), outputs=outputs))
                return {"error": str(exc), "checkpoint": run_id}
            return {"error": str(exc)}
        completed.add(stage.kind)
        handler._write_sse({"phase": "stage", "stage": stage.kind, "status": "done"})
    # Clean success ⇒ discard any prior checkpoint for this run so a completed run is never resumable.
    checkpoint.delete(handler.server.docs_root, run_id)
    if outputs:
        result_box.setdefault("outputs", {}).update(outputs)
    return result_box
