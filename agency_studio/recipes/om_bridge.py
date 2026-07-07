"""Subprocess-only OpenMontage pipeline bridge.

A production recipe drives one agentic OpenMontage pipeline. The pipeline's own
``executive-producer`` skill is run by a CLI-agent **subprocess** inside ``openmontage/``
(never an in-process import — the charter and Principle V). That runner is not wired in
this build yet (Brick 8 · US2 · task T025), so ``run_pipeline`` fails **honestly** after
probing rather than fabricating a completed dossier or an inspector verdict (Principle III:
no invented information, the veto is never bypassed).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .stages import RecipeStageUnavailable

ROOT = Path(__file__).resolve().parents[2]
PIPELINES = ROOT / "openmontage" / "pipeline_defs"


def probe(pipeline: str) -> None:
    if shutil.which("node") is None or shutil.which("npx") is None:
        raise RecipeStageUnavailable("production recipes need Node.js and npx on PATH")
    if not (PIPELINES / f"{pipeline}.yaml").exists():
        raise RecipeStageUnavailable(f"unknown OpenMontage pipeline: {pipeline}")


def run_pipeline(pipeline: str, subject: str, project_root: str, should_cancel):
    """Drive one OpenMontage pipeline across the subprocess boundary.

    Not yet wired: rather than invent a dossier or a PASS verdict (Principle III), fail
    honestly once the machine-level prerequisites are confirmed present. When the CLI-agent
    runner lands (T025), this raises only for genuine unavailability and otherwise returns the
    real, inspector-gated result.
    """
    probe(pipeline)
    if should_cancel():
        raise RuntimeError("recipe cancelled")
    raise RecipeStageUnavailable(
        f"production recipe '{pipeline}' is not available in this build yet — the "
        "OpenMontage pipeline runner (a CLI-agent subprocess) is not wired in"
    )
