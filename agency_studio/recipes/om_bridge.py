"""Subprocess-only OpenMontage pipeline runner (Brick 8 · US2 · the "A2" work).

A production recipe drives one agentic OpenMontage pipeline end-to-end. The pipeline's own
``executive-producer`` skill is run by a **CLI-agent subprocess** inside ``openmontage/`` — never
an in-process import (the charter and Principle V: ``openmontage/tools/base_tool.py`` autoloads
``.env`` at import). This module owns that subprocess boundary.

What it does, and the invariants it holds
------------------------------------------
* **Probe first, fail honestly.** ``probe`` checks the machine-level prerequisites — Node/npx, a
  CLI engine, the pipeline manifest, and the executive-producer skill on disk. Any missing one
  raises :class:`RecipeStageUnavailable` (status 501 + an install hint); the endpoint surfaces it
  as an honest error frame, never a fabricated dossier (Principle III).
* **Subprocess boundary, cwd = openmontage/.** The agent runs *in* the vendored subtree so it
  picks up OpenMontage's own ``CLAUDE.md``, skills, and tools — exactly how OpenMontage is meant
  to be driven ("read the manifest, read the stage skill, use the tools").
* **Kill-tree cancel + hard timeout.** The child gets its own session (``start_new_session``); a
  cancel or timeout ``killpg``\\ s the WHOLE tree — the CLI agent's Node/tool grandchildren
  included — mirroring ``openmontage_backend._spawn_render`` and ``cli_engine._call``.
* **Atomic output.** The agent renders into a private work dir; the finished file is moved into
  ``out_path`` only after it is discovered and validated, so ``out_path`` is complete or absent,
  never a truncated render (the ``_run_local`` contract).
* **The subject never chooses compute or the filesystem.** The subject is the creative brief; the
  render target, the allowed tools, and the writable dir are renderer-fixed here — the agent is
  told to write only into the work dir, and a returned artifact (resolved through any symlink) that
  escapes it is rejected.

Trust boundary (why the prompt is not the security boundary)
------------------------------------------------------------
The child inherits the server's environment and is granted broad tools (Bash/Write/…), so the
in-prompt "write only into this directory" line is guidance, not a sandbox — a hostile ``subject``
could in principle steer it. This is **deliberately trusted-operator-only**, and the enclosing
model makes that safe: the studio binds ``127.0.0.1`` (never ``0.0.0.0``, no CORS ``*``) and is a
single-operator, local-first tool, so the ``subject`` is entered by the same operator whose machine
and credentials the agent already runs as — there is no remote attacker on this surface. Keys stay
**env-only** (the endpoint rejects any secret in the request body), so the child reads a cloud key
from the environment only when the operator opted that stage into ``cloud`` — never from untrusted
input. Confinement is defence-in-depth, not the trust root: the agent's cwd is the vendored subtree
and its writable target is a per-run work dir (``--add-dir``), and the artifact we accept is bounded
to that dir. A hard OS/container sandbox (curated env + mount scope) is the correct next step if this
ever runs untrusted input — see issue #21.

Not validatable offline (it needs the OpenMontage runtime — Node + skills + tools + a CLI engine),
so the one impure surface — the subprocess spawn (:func:`_spawn_agent`) — is isolated for the
offline suite to monkeypatch, exactly like ``openmontage_backend._spawn_render``.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from .registry import read_orchestration
from .stages import RecipeStageUnavailable

ROOT = Path(__file__).resolve().parents[2]
OM_ROOT = ROOT / "openmontage"
PIPELINES = OM_ROOT / "pipeline_defs"
SKILLS = OM_ROOT / "skills"

# The validated production engine binary (Art. II). Only the binary is engine-specific; a site
# can point it at another validated coding-agent CLI via the env var. Defaults to Claude Code.
_ENGINE_ENV = "AGENCY_STUDIO_OM_ENGINE"
_DEFAULT_ENGINE = "claude"
# An autonomous production run shells out to OpenMontage's Python tools, reads its skills, and
# writes intermediate assets — so it needs broader tools than the text-only mission engine
# (WebSearch alone). Least-privilege by default, widenable per-site for a pipeline that needs more.
_TOOLS_ENV = "AGENCY_STUDIO_OM_ALLOWED_TOOLS"
_DEFAULT_TOOLS = "Bash Read Write Edit Glob Grep WebSearch"

# A full pipeline (research → assets → edit → compose) is long-running but must never hang a run
# forever. The manifest's max_wall_time_minutes is the agent's own soft budget; this is the hard
# kill, set generously above it (soft cap × margin) so a wedged child still dies.
_DEFAULT_WALL_MINUTES = 20
_TIMEOUT_MARGIN = 600          # seconds of head-room over the agent's own wall-time budget
_CANCEL_POLL = 0.5             # seconds between should_cancel checks while the child runs
_OUTPUT_TAIL = 2000            # chars of agent output surfaced in a failure / summary

_ARTIFACT_RE = re.compile(r"^\s*OM_ARTIFACT=(.+?)\s*$", re.M)
_ERROR_RE = re.compile(r"^\s*OM_ERROR=(.+?)\s*$", re.M)
_VIDEO_SUFFIXES = (".mp4", ".mov", ".webm", ".mkv", ".gif")


def _engine_binary() -> str:
    return (os.environ.get(_ENGINE_ENV) or _DEFAULT_ENGINE).strip() or _DEFAULT_ENGINE


def _skill_path(orchestration: dict) -> "Optional[Path]":
    skill = (orchestration.get("skill") or "").strip()
    return (SKILLS / f"{skill}.md") if skill else None


def probe(pipeline: str) -> None:
    """Availability gate — cheap (PATH + stat checks only). Each missing prerequisite raises
    :class:`RecipeStageUnavailable` with its own install hint, so an absent capability degrades to
    an honest 501 and never a fabricated result."""
    binary = _engine_binary()
    if shutil.which("node") is None or shutil.which("npx") is None:
        raise RecipeStageUnavailable(
            "production recipes need Node.js 18+ (node + npx on PATH) — https://nodejs.org"
        )
    if shutil.which(binary) is None:
        raise RecipeStageUnavailable(
            f"production recipes drive the '{binary}' CLI agent — install it and authenticate "
            "(e.g. Claude Code), or set "
            f"{_ENGINE_ENV} to another validated coding-agent CLI on PATH"
        )
    manifest = PIPELINES / f"{pipeline}.yaml"
    if not manifest.exists():
        raise RecipeStageUnavailable(f"unknown OpenMontage pipeline: {pipeline}")
    skill = _skill_path(read_orchestration(manifest))
    if skill is None or not skill.exists():
        raise RecipeStageUnavailable(
            f"OpenMontage pipeline '{pipeline}' has no executive-producer skill to drive "
            "(not a producible production pipeline in this build)"
        )


def _kill_tree(proc: "subprocess.Popen") -> None:
    """SIGTERM the child's whole process group, then SIGKILL if it lingers. ``start_new_session``
    made ``proc`` the group leader, so ``proc.pid`` is the pgid and one signal reaches the Node/tool
    grandchildren too."""
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _spawn_agent(cmd: "list[str]", cwd: str, timeout: int,
                 should_cancel: "Optional[Callable[[], bool]]" = None) -> str:
    """Run one CLI-agent production pass to completion in ``cwd``; return its stdout.

    The single impure surface — isolated so the offline suite monkeypatches it (no CLI, no Node).
    The child runs under a reader thread (``communicate`` drains both pipes so a large log can't
    deadlock on a full pipe) while this thread polls ``should_cancel``; a cancel, a timeout, or a
    non-zero exit ``killpg``\\ s the whole tree and raises ``RuntimeError``."""
    proc = subprocess.Popen(
        cmd, cwd=cwd, start_new_session=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    streams: dict = {}

    def _drain() -> None:
        streams["out"], streams["err"] = proc.communicate()

    reader = threading.Thread(target=_drain, daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout
    try:
        while True:
            reader.join(_CANCEL_POLL)
            if not reader.is_alive():
                break
            if should_cancel is not None and should_cancel():
                raise RuntimeError("openmontage: pipeline cancelled")
            if time.monotonic() > deadline:
                raise RuntimeError(f"openmontage: pipeline exceeded {timeout}s and was killed")
    except BaseException:
        _kill_tree(proc)
        reader.join(5)
        raise
    out = (streams.get("out") or "").strip()
    err = (streams.get("err") or "").strip()
    if proc.returncode != 0:
        detail = (err or out)[-_OUTPUT_TAIL:]
        raise RuntimeError(
            f"openmontage: pipeline agent exited {proc.returncode}"
            + (f" — {detail}" if detail else " (no output)")
        )
    return out


def _within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def _resolve_artifact(stdout: str, work_dir: Path) -> Path:
    """The finished video the agent produced, as a **resolved real path inside ``work_dir``**.
    Prefer the explicit ``OM_ARTIFACT=`` sentinel; fall back to the newest video file in the work
    dir. SECURITY: the artifact is resolved (symlinks followed) and MUST stay inside ``work_dir`` —
    a sentinel or a symlink escaping it (an attempt to pull an arbitrary local file into the
    deliverable/export, since ``.is_file()`` follows links) is rejected. No artifact ⇒ an honest
    failure, never a fabricated one."""
    work_real = work_dir.resolve()
    match = _ARTIFACT_RE.search(stdout)
    if match:
        candidate = Path(match.group(1).strip())
        if not candidate.is_absolute():
            candidate = work_dir / candidate
        try:
            resolved = candidate.resolve(strict=True)  # follow the link, then bound the target
        except OSError:
            raise RuntimeError("openmontage: pipeline reported a missing artifact") from None
        if not _within(resolved, work_real):
            raise RuntimeError(
                "openmontage: pipeline reported an artifact outside its work dir — rejected"
            )
        if not resolved.is_file():
            raise RuntimeError("openmontage: pipeline reported an artifact that is not a file")
        return resolved
    # Fallback: the newest real video whose resolved path stays inside the work dir. Skip symlinks
    # outright — a genuine render is a real file, and a link is the escape vector we must not follow.
    videos = [
        p for p in work_dir.rglob("*")
        if not p.is_symlink() and p.is_file() and p.suffix.lower() in _VIDEO_SUFFIXES
        and _within(p, work_real)
    ]
    videos.sort(key=lambda p: p.stat().st_mtime)
    if videos:
        return videos[-1].resolve()
    raise RuntimeError("openmontage: pipeline finished without producing a video")


def _build_prompt(pipeline: str, subject: str, orchestration: dict, work_dir: Path) -> str:
    skill = orchestration.get("skill") or ""
    budget = (orchestration.get("budget") or "").strip()
    budget_line = f" Stay within a budget of about ${budget} USD." if budget else ""
    return (
        "You are running OpenMontage headlessly to produce ONE finished video, fully unattended.\n\n"
        f"Pipeline: {pipeline}\n"
        f"Creative brief / subject: {subject}\n\n"
        "Do this:\n"
        f"1. Read the manifest pipeline_defs/{pipeline}.yaml.\n"
        f"2. Read and follow skills/{skill}.md — you are the Executive Producer, the stateful brain "
        "that spawns each stage director and reviews its output before passing forward.\n"
        "3. Run the FULL pipeline AUTONOMOUSLY. This is an unattended run: do NOT pause for human "
        "approval at any checkpoint — apply your own best judgment at every gate and keep going to "
        f"a finished render.{budget_line}\n"
        f"4. Write the finished video file into this directory (and only this directory): {work_dir}\n"
        "5. Local-first: use only local/free tools and providers. Do NOT use a paid cloud provider "
        "unless its API key is ALREADY present in the environment.\n\n"
        "When you are done, print EXACTLY ONE line, on its own, with the absolute path to the "
        "finished video:\n"
        "OM_ARTIFACT=/absolute/path/to/video.mp4\n\n"
        "If you genuinely cannot produce the video, do NOT fabricate one — print exactly one line "
        "explaining why:\n"
        "OM_ERROR=<short reason>\n"
    )


def _timeout_seconds(orchestration: dict) -> int:
    raw = (orchestration.get("wall_minutes") or "").strip()
    try:
        minutes = int(float(raw)) if raw else _DEFAULT_WALL_MINUTES
    except ValueError:
        minutes = _DEFAULT_WALL_MINUTES
    return max(minutes, 1) * 60 + _TIMEOUT_MARGIN


def run_pipeline(pipeline: str, subject: str, *,
                 work_dir: Path, out_path: Path,
                 should_cancel: "Callable[[], bool]") -> dict:
    """Drive one OpenMontage pipeline across the subprocess boundary and return the finished
    artifact. Probes (→ :class:`RecipeStageUnavailable` / 501 when a prerequisite is absent), then
    spawns a CLI-agent production pass in ``openmontage/`` running the pipeline's executive-producer
    skill on ``subject`` UNATTENDED. The finished video is produced into ``work_dir`` and atomically
    placed at ``out_path`` (complete or absent). Principle III: an honest failure raises — a
    fabricated video or verdict is never returned."""
    probe(pipeline)
    if should_cancel():
        raise RuntimeError("openmontage: pipeline cancelled")
    orchestration = read_orchestration(PIPELINES / f"{pipeline}.yaml")
    work_dir.mkdir(parents=True, exist_ok=True)
    prompt = _build_prompt(pipeline, subject, orchestration, work_dir)
    # Trusted-operator-only: a broad-tool agent driven by an operator-supplied subject on a
    # 127.0.0.1 single-operator studio (see the module "Trust boundary" note). Confinement below —
    # cwd = vendored subtree, writable scope = the per-run work dir — is defence-in-depth.
    cmd = [
        _engine_binary(),
        "--allowedTools", (os.environ.get(_TOOLS_ENV) or _DEFAULT_TOOLS),
        "--add-dir", str(work_dir),  # the agent's cwd is openmontage/; the render target is outside it
        "-p", prompt,
    ]
    stdout = _spawn_agent(cmd, str(OM_ROOT), _timeout_seconds(orchestration), should_cancel)
    err = _ERROR_RE.search(stdout)
    if err:
        raise RuntimeError(f"openmontage: pipeline reported failure — {err.group(1).strip()}")
    artifact = _resolve_artifact(stdout, work_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        artifact.replace(out_path)          # atomic within one filesystem (work dir under assets root)
    except OSError:
        shutil.move(str(artifact), str(out_path))  # cross-device fallback (copy + unlink)
    return {"pipeline": pipeline, "subject": subject, "artifact": str(out_path),
            "summary": stdout[-_OUTPUT_TAIL:]}
