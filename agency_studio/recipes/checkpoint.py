"""Recipe-run checkpoint envelope — reuses the mission checkpoint seam.

A composed recipe chains an expensive, veto-gated mission stage into cheaper downstream stages
(compose/export) and, now, a fatal ``pipeline`` stage. When a **post-mission** stage fails, this
snapshots the run (``completed_stages`` + replayable ``outputs``) under ``docs_root`` so a resume
skips the mission and restarts at the failed stage instead of re-spending the mission's minutes and
tokens. It rides the mission checkpoint primitives verbatim (id-validated path, atomic write, the
never-web-served checkpoints dir), and is distinguished from a mission checkpoint by ``kind`` — so
the recipe resume path only ever loads a recipe envelope, and the mission resume path only a
mission one.
"""

from __future__ import annotations

KIND = "recipe"


def envelope(*, run_id: str, recipe_id: str, subject: str, cloud_optins, completed_stages,
             outputs: dict) -> dict:
    """The persisted snapshot. ``id`` is the run's stable id (uuid4 hex, or the id resumed from —
    stable across a fail→resume→fail chain, matching the mission checkpoint), so it satisfies the
    strict checkpoint-id shape the path guard enforces."""
    return {
        "id": run_id,
        "kind": KIND,
        "recipe_id": recipe_id,
        "subject": subject,
        "cloud_optins": sorted(cloud_optins),
        "completed_stages": list(completed_stages),
        "outputs": outputs,
    }


def write(docs_root, env: dict) -> None:
    from agency_studio.server import _write_checkpoint
    _write_checkpoint(docs_root, env)


def load(docs_root, cid: str) -> "dict | None":
    """Load a **recipe** checkpoint by id, or ``None`` for an unsafe id / missing / corrupt file /
    a checkpoint that isn't a recipe one (so a mission id can never be resumed as a recipe)."""
    from agency_studio.server import _load_checkpoint
    env = _load_checkpoint(docs_root, cid)
    return env if isinstance(env, dict) and env.get("kind") == KIND else None


def delete(docs_root, cid: str) -> None:
    from agency_studio.server import _delete_checkpoint
    _delete_checkpoint(docs_root, cid)
