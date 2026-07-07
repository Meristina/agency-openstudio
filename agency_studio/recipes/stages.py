"""Stage drivers for the recipe orchestrator.

Each driver does real work by reusing existing, proven studio machinery — never a
fabricated result (Principle III):

* ``mission``  → the runner bridge (wired in the orchestrator via ``_stream_mission``);
                 the inspector veto and source-verification gate are byte-identical.
* ``compose``  → a guaranteed-**local** composition video via ``openmontage_backend``
                 (subprocess Remotion), attached to the mission dossier. Degrades honestly
                 (skips the video, never fabricates one) when the local backend is absent.
* ``export``   → one downloadable bundle via the existing ``bundler`` (which auto-collects
                 every rendered asset under the mission's media dir).
* ``pipeline`` → one OpenMontage pipeline across the subprocess boundary (``om_bridge``).
"""

from __future__ import annotations

from pathlib import Path

_COMPOSITION_PROMPT_CHARS = 2000


class RecipeStageUnavailable(RuntimeError):
    """A stage cannot run on this machine (missing prerequisite) or a recipe used a paid
    stage without opt-in. Carries ``status = 501`` so the endpoint maps it like every other
    'capability absent' path."""

    status = 501


def ensure_cloud_allowed(stage_kind: str, tier: str, cloud_optins: set[str]) -> None:
    """A cloud-tier stage runs only when the user explicitly opted it in (FR-008)."""
    if tier == "cloud" and stage_kind not in cloud_optins:
        raise RecipeStageUnavailable(f"{stage_kind} needs explicit cloud opt-in")


def _dossier(result_box: dict) -> "dict | None":
    result = result_box.get("result")
    return getattr(result, "dossier", None) if result is not None else None


def _composition_prompt(dossier: dict) -> str:
    """The text the local composition video is built from: the mission's own deliverable,
    trimmed to a renderer-safe length (the marker never chooses compute — the same discipline
    openmontage_backend enforces on cut count/duration)."""
    text = (dossier.get("delivered") or dossier.get("goal") or "").strip()
    return text[:_COMPOSITION_PROMPT_CHARS] or "Campaign"


def run_compose(handler, result_box: dict, cancel_event) -> "dict | None":
    """Render a local campaign composition video from the mission dossier and attach it.

    Returns an honest asset manifest entry: ``status='ok'`` with the rendered video's media URL
    on success, or ``status='skipped'`` (with a reason) when the local backend is unavailable —
    the dossier and its images are preserved either way, and no video is ever fabricated.
    """
    dossier = _dossier(result_box)
    if dossier is None:
        return None
    from agency_studio import openmontage_backend as omb
    from agency_studio.server import _media_url
    from agency_kit import store

    assets_root = Path(handler.server.assets_root).resolve()
    mission_id = str(dossier.get("mission_id"))
    out_path = assets_root / "missions" / mission_id / "recipe-composition.mp4"
    try:
        omb.render_composition(_composition_prompt(dossier), out_path,
                               should_cancel=cancel_event.is_set)
    except omb.OpenMontageUnavailable as exc:
        # Local video is unavailable on this machine — deliver the dossier + images anyway and
        # say so honestly (never claim a video was produced).
        return {"type": "video", "status": "skipped", "reason": str(exc)}
    entry = {"type": "video", "status": "ok", "url": _media_url(assets_root, out_path)}
    dossier.setdefault("assets", []).append(entry)
    store.save(dossier)  # persist so the video is in the deliverable + every export path
    return entry


def run_export(handler, result_box: dict) -> "dict | None":
    """Assemble one downloadable bundle (dossier + every rendered asset) via the existing
    bundler — the same artifact the mission's ``/api/mission/{id}/bundle.zip`` route serves."""
    dossier = _dossier(result_box)
    if dossier is None:
        return None
    from agency_studio import bundler

    mission_id = str(dossier.get("mission_id"))
    try:
        path = bundler.build_bundle(mission_id, handler.server.assets_root)
    except Exception as exc:
        # Bundling is a convenience over the already-delivered dossier (also reachable via
        # /api/mission/{id}/bundle.zip). A failure here — missing [pdf] extra, no deliverable
        # yet — is honest and NON-fatal: the run still delivers the dossier + assets.
        return {"status": "skipped", "reason": str(exc)}
    return {"status": "ok", "bundle": str(path)}
