"""Sequential recipe runner over the existing mission stream.

Drives a recipe's declared stages in order, streaming the **mission SSE vocabulary** so the
existing timeline renders the whole chain. Every stage does real work (see ``stages.py``);
the mission stage runs the veto-gated mission unchanged. A stage that cannot run raises
``RecipeStageUnavailable`` (surfaced by the endpoint as an honest error frame); the mission
stage stopping (cancel/error/veto) ends the run with its outputs already preserved.
"""

from __future__ import annotations

import threading

from .models import Recipe
from .stages import ensure_cloud_allowed, run_compose, run_export

# The recipe mission stage runs on the v1 validated engine (Art. II). Kept here as the single
# source of truth so the server's pre-flight validation gate uses the same id.
ENGINE = "claude-code"


def run(handler, recipe: Recipe, *, run_id: str, subject: str, cloud_optins: set[str],
        cancel_event: threading.Event, explicit_cancel: threading.Event) -> dict:
    handler._write_sse({"phase": "run", "run_id": run_id})
    result_box: dict = {}
    outputs: dict = {}
    for stage in recipe.stages:
        ensure_cloud_allowed(stage.kind, stage.tier, cloud_optins)
        if cancel_event.is_set():
            result_box.setdefault("cancelled", True)
            return result_box
        handler._write_sse({"phase": "stage", "stage": stage.kind, "status": "start"})
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
                return result_box  # cancelled / error / veto — mission already persisted state
        elif stage.kind == "pipeline":
            from .om_bridge import run_pipeline
            result_box = {"result": run_pipeline(
                recipe.pipeline or recipe.id, subject,
                handler.server.project_root, cancel_event.is_set)}
        elif stage.kind == "compose":
            entry = run_compose(handler, result_box, cancel_event)
            outputs["compose"] = entry
            if entry is not None:
                handler._write_sse({"phase": "asset", "stage": "compose", "kind": "video",
                                    "status": entry.get("status"), "url": entry.get("url")})
        elif stage.kind == "export":
            outputs["export"] = run_export(handler, result_box)
        handler._write_sse({"phase": "stage", "stage": stage.kind, "status": "done"})
    if outputs:
        result_box.setdefault("outputs", {}).update(outputs)
    return result_box
