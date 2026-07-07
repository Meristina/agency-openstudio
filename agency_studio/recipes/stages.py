"""Stage driver placeholders used by the recipe orchestrator."""

from __future__ import annotations


class RecipeStageUnavailable(RuntimeError):
    status = 501


def ensure_cloud_allowed(stage_kind: str, tier: str, cloud_optins: set[str]) -> None:
    if tier == "cloud" and stage_kind not in cloud_optins:
        raise RecipeStageUnavailable(f"{stage_kind} needs explicit cloud opt-in")


def compose_output(result_box: dict) -> dict:
    result = result_box.get("result")
    dossier = getattr(result, "dossier", {}) if result is not None else {}
    return {"mission_id": dossier.get("mission_id"), "assets": dossier.get("assets") or []}


def export_output(result_box: dict) -> dict:
    result = result_box.get("result")
    dossier = getattr(result, "dossier", {}) if result is not None else {}
    return {"mission_id": dossier.get("mission_id")}
