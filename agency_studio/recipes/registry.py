"""Default recipe registry plus inert OpenMontage manifest readers."""

from __future__ import annotations

import re
from pathlib import Path

from .models import InputSpec, Recipe, Stage

_ROOT = Path(__file__).resolve().parents[2]
_PIPELINE_DIR = _ROOT / "openmontage" / "pipeline_defs"
_SUBJECT = [InputSpec("subject", "recipes.input.subject")]


def _composed() -> dict[str, Recipe]:
    base = [
        Stage("mission", "recipes.stage.mission"),
        Stage("compose", "recipes.stage.compose"),
        Stage("export", "recipes.stage.export"),
    ]
    short = [Stage("mission", "recipes.stage.mission"), Stage("export", "recipes.stage.export")]
    return {
        "full-campaign": Recipe("full-campaign", "composed", "recipes.full_campaign.name", "recipes.full_campaign.desc", _SUBJECT, base),
        "client-pitch": Recipe("client-pitch", "composed", "recipes.client_pitch.name", "recipes.client_pitch.desc", _SUBJECT, base),
        "turnkey-event": Recipe("turnkey-event", "composed", "recipes.turnkey_event.name", "recipes.turnkey_event.desc", _SUBJECT, base),
        "social-content-pack": Recipe("social-content-pack", "composed", "recipes.social_content_pack.name", "recipes.social_content_pack.desc", _SUBJECT, short),
    }


def _field(text: str, name: str) -> str:
    # Manifest fields may be nested (e.g. orchestration.budget_default_usd is indented),
    # so tolerate leading whitespace; re.search returns the first match, and the fields we
    # read (name/category top-level, budget_default_usd only ever nested) stay unambiguous.
    match = re.search(rf"^[ \t]*{re.escape(name)}:\s*(.+)$", text, re.M)
    return match.group(1).strip().strip('"') if match else ""


def _desc(text: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("description:"):
            if ">" not in line:
                return line.partition(":")[2].strip()
            out: list[str] = []
            for item in lines[i + 1:]:
                if item.startswith((" ", "\t")):
                    out.append(item.strip())
                elif item.strip():
                    break
            return " ".join(out)
    return ""


def read_pipeline_metadata(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    budget = _field(text, "budget_default_usd")
    return {
        "name": _field(text, "name") or path.stem,
        "description": _desc(text),
        "category": _field(text, "category"),
        "tier": "cloud" if budget and budget not in {"0", "0.0", "0.00"} else "local",
    }


def read_orchestration(path: Path) -> dict[str, str]:
    """Read a pipeline's ``orchestration`` block as **inert data** (never an in-process import of
    ``openmontage/``): the executive-producer skill the agentic runner drives, its default budget,
    and the wall-time cap. Scoped to the ``orchestration:`` block so a stage's own ``skill:`` (each
    stage under ``stages:`` carries one) can never leak in as the orchestration skill. Returns empty
    strings for a manifest with no orchestration block (e.g. the framework-smoke contract fixture),
    so the runner probe fails honestly rather than driving a non-existent skill."""
    block: list[str] = []
    inside = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("orchestration:"):
            inside = True
            continue
        if inside:
            if line and not line[0].isspace():  # a dedent to a new top-level key ends the block
                break
            block.append(line)
    text = "\n".join(block)
    return {
        "skill": _field(text, "skill"),
        "budget": _field(text, "budget_default_usd"),
        "wall_minutes": _field(text, "max_wall_time_minutes"),
    }


def _production() -> dict[str, Recipe]:
    recipes: dict[str, Recipe] = {}
    if not _PIPELINE_DIR.exists():
        return recipes
    for path in sorted(_PIPELINE_DIR.glob("*.yaml")):
        meta = read_pipeline_metadata(path)
        rid = str(meta["name"])
        key = rid.replace("-", "_")
        tier = "cloud" if meta["tier"] == "cloud" else "local"
        recipes[rid] = Recipe(
            rid, "production", f"recipes.pipeline.{key}.name", f"recipes.pipeline.{key}.desc",
            _SUBJECT, [Stage("pipeline", "recipes.stage.pipeline", tier, {"pipeline": rid})],
            pipeline=rid,
        )
    return recipes


RECIPES: dict[str, Recipe] = {**_composed(), **_production()}


def serialize_recipe(recipe: Recipe) -> dict:
    return {
        "id": recipe.id,
        "kind": recipe.kind,
        "name_key": recipe.name_key,
        "desc_key": recipe.desc_key,
        "required_inputs": [spec.__dict__ for spec in recipe.required_inputs],
        "stages": [{"kind": s.kind, "tier": s.tier, "label_key": s.label_key} for s in recipe.stages],
        **({"pipeline": recipe.pipeline} if recipe.pipeline else {}),
    }
