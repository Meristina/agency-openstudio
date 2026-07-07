"""Sequential recipe runner over the existing mission stream."""

from __future__ import annotations

import threading

from .models import Recipe
from .stages import RecipeStageUnavailable, compose_output, ensure_cloud_allowed, export_output

# The recipe mission stage runs on the v1 validated engine (Art. II). Kept here as the single
# source of truth so the server's pre-flight validation gate uses the same id.
ENGINE = "claude-code"


def run(handler, recipe: Recipe, *, run_id: str, subject: str, cloud_optins: set[str],
        cancel_event: threading.Event, explicit_cancel: threading.Event) -> dict:
    handler._write_sse({"phase": "run", "run_id": run_id})
    result_box: dict = {}
    for stage in recipe.stages:
        ensure_cloud_allowed(stage.kind, stage.tier, cloud_optins)
        handler._write_sse({"phase": "stage", "stage": stage.kind, "status": "start"})
        if stage.kind == "mission":
            result_box = handler._stream_mission(
                subject, ENGINE, cancel_event,
                web_search=True, use_video=True,
                run_id=run_id, explicit_cancel=explicit_cancel,
                verification={"min_sources": 3, "resolve": False},
            ) or {"cancelled": True}
            if "result" not in result_box:
                return result_box
        elif stage.kind == "pipeline":
            from .om_bridge import run_pipeline
            result_box = {"result": run_pipeline(recipe.pipeline or recipe.id, subject, handler.server.project_root, cancel_event.is_set)}
        elif stage.kind == "compose":
            # The real composition driver (openmontage_backend, subprocess) is task T013 —
            # not wired yet. Carry the mission's outputs forward without claiming a video was
            # rendered (never a false "asset done" — Principle III / FR-010).
            result_box.setdefault("outputs", {})["compose"] = compose_output(result_box)
        elif stage.kind == "export":
            # The real export/bundle driver is task T014 — not wired yet. Same honesty rule.
            result_box.setdefault("outputs", {})["export"] = export_output(result_box)
        handler._write_sse({"phase": "stage", "stage": stage.kind, "status": "done"})
    return result_box
