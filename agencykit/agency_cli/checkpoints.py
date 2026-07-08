"""Durable CLI crash-recovery checkpoints.

The mission loop (`cli_engine.run_mission_cli`) emits a JSON snapshot after routing,
after every department, and after every synth→inspect cycle — but only when a caller
wires an ``on_checkpoint`` sink. The Studio server wires one for SSE crash-recovery;
this module is the equivalent sink for the plain ``agency run`` CLI, so a mission
killed mid-flight (e.g. after three departments, during synthesis) can resume without
re-paying the completed phases instead of losing everything.

A checkpoint is transient crash-recovery, NOT the durable dossier: it is written per
boundary, superseded by the saved dossier, and deleted on successful completion. It is
keyed by (project_root, engine, goal) so re-running the same goal in the same directory
finds and continues its interrupted run; a different goal is a different checkpoint.

Art. IX is preserved by construction — the engine only snapshots ALREADY-INSPECTED
state (never a half-done synthesis), and `_validate_resume_state` rejects a snapshot
whose invariants don't hold, so a stale or corrupt checkpoint can never smuggle an
un-inspected result into a resumed mission.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

from agency_kit import store


def _dir() -> Path:
    """`~/.agency/checkpoints`, created on demand. A function (not a constant) so tests
    can redirect it by monkeypatching `store.agency_dir`."""
    d = store.agency_dir() / "checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _key(goal: str, engine: str, project_root) -> str:
    """Stable filename stem for a run. NUL-joined so no field can bleed into the next."""
    root = store.canonical_project_root(project_root)
    raw = f"{root}\x00{engine}\x00{goal}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def path_for(goal: str, engine: str, project_root) -> Path:
    return _dir() / f"{_key(goal, engine, project_root)}.json"


def read(goal: str, engine: str, project_root) -> Optional[dict]:
    """The saved snapshot for this run, or None if absent/unreadable/corrupt.

    Tolerant by design: a truncated write (killed mid-flight) or hand-corrupted file
    must degrade to a clean fresh run, never raise."""
    path = path_for(goal, engine, project_root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write(goal: str, engine: str, project_root, snapshot: dict) -> None:
    """Persist the latest snapshot atomically (temp file in the same dir + `os.replace`)
    so a kill during the write can't leave a torn checkpoint. Best-effort: a persistence
    error must never abort the live mission (the engine already swallows sink errors)."""
    path = path_for(goal, engine, project_root)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def clear(goal: str, engine: str, project_root) -> None:
    """Delete the checkpoint (best-effort) — called once the durable dossier is saved,
    so a completed mission never leaves a resumable envelope behind."""
    path = path_for(goal, engine, project_root)
    try:
        path.unlink()
    except OSError:
        pass


def describe(snapshot: dict) -> str:
    """One-line human summary for the resume notice, e.g.
    '2/3 departments done, 1 inspection cycle' — best-effort, never raises."""
    route = snapshot.get("route") or []
    done = len(snapshot.get("dept_outputs") or {})
    iters = snapshot.get("iteration") or 0
    parts = [f"{done}/{len(route)} departments done"]
    if iters:
        parts.append(f"{iters} inspection cycle{'s' if iters != 1 else ''}")
    return ", ".join(parts)
