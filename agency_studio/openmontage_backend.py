"""openmontage — LOCAL video as a department deliverable (the OpenMontage fusion, brick A1).

The seedance brick (Wave 6) made ``video`` an asset type but was cloud-only by necessity:
text-to-video does not fit a 16 GB Mac. The OpenMontage fusion changes the premise — the
vendored ``openmontage/`` tree ships a genuinely headless, zero-key *composition* renderer
(Remotion: React scenes → h264 mp4, the same engine behind every OpenMontage demo). This
module wires it in as the studio's first LOCAL video backend: a ``local`` triple in
``seedance._VIDEO_BACKENDS``, selected per-install via ``$AGENCY_STUDIO_VIDEO_BACKEND``,
riding the SAME marker → ``parse_markers`` → ``assets.render`` → gallery/PDF pipeline with
zero server/GUI functional change (mirrors how GLiNER2 slotted in behind ``make_extractor``).

What it renders (and what it deliberately does not)
---------------------------------------------------
This is *composition* video — animated text/stat/callout scenes (the Explainer composition's
data-driven components), not text-to-*footage* generation. A department describes the clip in
its marker ``prompt`` (and may optionally structure it as ``cuts`` — validated in
``assets._build_video``); the render is `npx remotion render` in
``openmontage/remotion-composer/``, across a **subprocess boundary** (the charter forbids
importing openmontage in-process — its ``tools/base_tool.py`` autoloads ``.env`` at import).
The full agentic OpenMontage pipeline (research → assets → edit, driven through the claude
CLI) is the explicitly deferred A2 brick — see ``docs/OPENMONTAGE-FUSION.md``.

The security model, restated for a *local* render
-------------------------------------------------
The marker is still MODEL OUTPUT — untrusted. Three properties hold:

  1. **No network, ever.** The probe requires ``remotion-composer/node_modules`` to already
     exist — the studio never runs ``npm install`` itself, so a render can never make ``npx``
     fall through to a registry fetch. A missing install is a clean 501 + hint.
  2. **The marker never chooses compute.** Cut timings are NOT marker fields: every cut gets a
     fixed ``FIXED_CUT_SECONDS`` slot and the cut count is capped (``MAX_CUTS``), so total
     duration — the render's cost dimension — is renderer-fixed, exactly like seedance's
     fixed duration/resolution caps.
  3. **The marker never references the filesystem.** ``assets._clean_cuts`` whitelists only
     text/number content fields per scene type; ``source`` / ``backgroundVideo`` /
     ``backgroundImage`` / ``images`` / ``audio`` are dropped wholesale, so an injected marker
     can never pull an arbitrary local file into a rendered (and later exported) video.

Cancellation mirrors the agency-kit in-flight kill: the child runs in its own session
(``start_new_session``) and a "Stop mission" ``killpg``\\ s the whole render tree (Remotion
spawns a headless Chromium — the grandchildren must die too). The output is atomic:
Remotion writes to a ``.part`` name and the mp4 is renamed into place only on success —
complete or absent, never truncated (the ``seedance._http_download`` contract).
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional, Sequence

from .engines.local_media import MediaUnavailable

# The vendored OpenMontage tree, resolved relative to the repo root (the parent of the
# agency_studio package). In a site-packages install the subtree is absent → a clean 501.
REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSER_DIR = REPO_ROOT / "openmontage" / "remotion-composer"

# Fixed, safe render parameters — the marker NEVER chooses compute (see module docstring).
# 12 × 5 s = a 60 s ceiling per clip; the Explainer composition derives its duration from the
# cuts' out_seconds, so fixing the timings here fixes the render cost.
FIXED_CUT_SECONDS = 5.0
MAX_CUTS = 12
THEME = "clean-professional"    # one fixed theme — not the marker's to choose

# The Remotion entry + composition (the same pair openmontage's own render_demo.py drives).
_ENTRY = "src/index.tsx"
_COMPOSITION = "Explainer"

# A composition render is minutes, not hours — a wedged Chromium can't hang a mission forever.
_RENDER_TIMEOUT = 900          # seconds
_CANCEL_POLL = 0.5             # seconds between should_cancel checks while the child runs
_STDERR_TAIL = 800             # bytes of child stderr surfaced in a failure message


class OpenMontageUnavailable(MediaUnavailable):
    """Raised when the local video render path is unavailable — Node/npx missing, the
    ``openmontage/`` subtree absent, or ``remotion-composer`` not yet ``npm install``\\ ed.
    An ``ImportError`` subclass (via ``MediaUnavailable``) so the server's optional-extra
    handler maps it to a 501 + hint, exactly like ``SeedanceUnavailable``."""


# ── the (probe, load, run) triple — the contract seedance._backend dispatches on ──
def _probe_local(entry) -> None:
    """Availability gate for the local backend. Cheap (PATH + stat checks only — never heavy
    work, it runs before eviction). Each missing prerequisite raises ``OpenMontageUnavailable``
    with its own install hint. Requiring ``node_modules`` up front is a *local-first* guard:
    the studio never runs ``npm install`` itself, so ``npx remotion`` can never fall through
    to a network fetch mid-mission."""
    if shutil.which("node") is None or shutil.which("npx") is None:
        raise OpenMontageUnavailable(
            "local video needs Node.js 18+ (node + npx on PATH) — https://nodejs.org"
        )
    if not (COMPOSER_DIR / "package.json").exists():
        raise OpenMontageUnavailable(
            f"openmontage/remotion-composer not found at {COMPOSER_DIR} — the vendored "
            "openmontage/ subtree is required for the local video backend"
        )
    if not (COMPOSER_DIR / "node_modules").exists():
        raise OpenMontageUnavailable(
            "remotion-composer dependencies are not installed — run `npm install` in "
            "openmontage/remotion-composer once (the studio never runs npm itself)"
        )


def _load_local(entry):
    """A lightweight descriptor bound to the composer checkout. No weights, no residency cost —
    but it still flows through the manager's residency seam so eviction/warm-chip logic needs
    no special case (the exact ``seedance._load_cloud`` shape)."""
    return {"composer_dir": str(COMPOSER_DIR), "npx": shutil.which("npx")}


# ── the raw subprocess primitive (isolated so the offline suite monkeypatches it) ──
def _spawn_render(cmd: "list[str]", cwd: str,
                  should_cancel: "Optional[Callable[[], bool]]" = None) -> None:
    """Run one Remotion render to completion. The child gets its own session
    (``start_new_session``) so a cancel/timeout ``killpg``\\ s the WHOLE tree — Remotion's
    headless Chromium included — mirroring agency-kit's in-flight mission kill. Polls
    ``should_cancel`` while the child runs; cancel/timeout/nonzero-exit all raise
    ``RuntimeError`` (→ the render bridge records ``status='failed'`` and writes the
    ``_[video unavailable]_`` placeholder — the mission itself is never lost)."""
    proc = subprocess.Popen(
        cmd, cwd=cwd, start_new_session=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + _RENDER_TIMEOUT
        while True:
            try:
                _, err = proc.communicate(timeout=_CANCEL_POLL)
                if proc.returncode != 0:
                    tail = (err or b"")[-_STDERR_TAIL:].decode("utf-8", "replace").strip()
                    raise RuntimeError(f"openmontage: remotion render failed — {tail or 'no stderr'}")
                return
            except subprocess.TimeoutExpired:
                if should_cancel is not None and should_cancel():
                    raise RuntimeError("openmontage: render cancelled")
                if time.monotonic() > deadline:
                    raise RuntimeError(
                        f"openmontage: render exceeded {_RENDER_TIMEOUT}s and was killed"
                    )
    except BaseException:
        if proc.poll() is None:  # cancel/timeout/interrupt → kill the whole render tree
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        raise


def _build_props(prompt: str, cuts: "Optional[Sequence[dict]]") -> dict:
    """The Explainer props for one render. ``cuts`` (already whitelisted by
    ``assets._clean_cuts``) get FIXED sequential ``FIXED_CUT_SECONDS`` slots — timings are
    the renderer's, never the marker's (compute = cost). No cuts ⇒ the prompt-only fallback:
    a single ``text_card`` carrying the prompt text, so the plain Wave-6 marker contract
    (``type`` + ``prompt`` only) renders unchanged on the local backend."""
    chosen = list(cuts or [])[:MAX_CUTS]
    if not chosen:
        chosen = [{"type": "text_card", "text": prompt}]
    timed = []
    for i, cut in enumerate(chosen):
        timed.append({
            **cut,
            "id": f"cut-{i}",
            "source": "",  # composition cuts carry no media source — ever (see docstring §3)
            "in_seconds": round(i * FIXED_CUT_SECONDS, 3),
            "out_seconds": round((i + 1) * FIXED_CUT_SECONDS, 3),
        })
    return {"theme": THEME, "cuts": timed, "overlays": [], "captions": [], "audio": {}}


def _run_local(backend, entry, *, prompt: str, out_path: Path,
               should_cancel: "Optional[Callable[[], bool]]" = None,
               cuts: "Optional[Sequence[dict]]" = None) -> None:
    """Render one composition video into ``out_path`` via ``npx remotion render`` (subprocess
    boundary — never an in-process import). Renders to a sibling ``.part.mp4`` and renames on
    success, so ``out_path`` is complete or absent, never truncated. The props JSON lives in a
    temp file that is always removed."""
    if should_cancel is not None and should_cancel():
        raise RuntimeError("openmontage: render cancelled")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    props = _build_props(prompt, cuts)
    fd, props_name = tempfile.mkstemp(suffix=".json", prefix="om-props-")
    part = out_path.with_name(out_path.name + ".part.mp4")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(props, fh)
        _spawn_render(
            [backend["npx"], "remotion", "render", _ENTRY, _COMPOSITION, str(part),
             "--props", props_name, "--codec", "h264", "--overwrite"],
            cwd=backend["composer_dir"], should_cancel=should_cancel,
        )
        if not part.exists():
            raise RuntimeError("openmontage: render finished without producing an mp4")
        part.replace(out_path)  # atomic: complete or absent
    finally:
        Path(props_name).unlink(missing_ok=True)
        if part.exists():
            part.unlink()  # a failed render leaves no partial behind
