# Phase 0 Research: Cross-Platform Backends

**Feature**: 005-cross-platform-backends | **Date**: 2026-07-05

All Technical Context unknowns resolved. Each decision below is grounded in the
codebase patterns read during planning (`capabilities.py`, `engines/local_media.py`,
`engines/embeddings.py`, `engines/models.py`, `seedance.py`, `pyproject.toml`).

## D1 — Image portable backend: stable-diffusion.cpp subprocess

**Decision**: Add a `backend="sdcpp"` image backend: the stable-diffusion.cpp `sd`
CLI binary driven via `subprocess.run` with an explicit timeout, writing a PNG to
the requested `out_path`. New `ImageModel` registry row; new (probe, load, run)
triple in the existing `_IMAGE_BACKENDS` dispatch table — `ModelManager` and the
routes stay untouched (the table's documented extension contract). Weights: a
sha256-pinned GGUF checkpoint declared as a `ModelFile` manifest; the user places it
per the install hint; probe/load verify with the existing `verify_sha256`.

**Rationale**: MIT license, single static binary with official releases for all
three OSes, CPU-friendly, zero Python dependencies — the closest possible analog of
the `openmontage-remotion` pattern (binary presence gates the probe, subprocess-only
crossing). The image dispatch table was explicitly built for this ("Adding a backend
is a new triple here + rows in the registry").

**Alternatives considered**: LocalAI gateway (MIT) — rejected as the *image* path:
requires the user to run and manage a server for a capability a plain binary
delivers; kept as the pattern for embeddings where a server is the natural shape.
PyTorch/diffusers — rejected: multi-GB dependency tree, violates the lean-extras
ethos, slow CPU path anyway.

## D2 — STT portable backend: whisper.cpp subprocess

**Decision**: Add a portable STT backend: the whisper.cpp `whisper-cli` binary via
`subprocess.run` (+ timeout), with a sha256-pinned ggml/GGUF Whisper model file.
`STT_MODELS` gains a second row with a `backend` discriminator; `local_media.py`
gains an `_STT_BACKENDS` dispatch table mirroring `_IMAGE_BACKENDS` (the current
`mlx_whisper` functions become the `"mlx"` triple, byte-identical; the seam-arity
shims already tolerate entry-aware seams).

**Rationale**: MIT, official cross-platform releases, the de-facto portable Whisper.
Binary + pinned model file matches D1, so both ride the same `portable.py` helpers.

**Alternatives considered**: faster-whisper (MIT, pip-installable) — rejected for
v1: pulls CTranslate2 (a heavy native wheel) into an extra, and a second *Python*
STT runtime duplicates what the binary already gives; it remains a clean future
registry addition if demand appears. Audio decoding: whisper.cpp consumes WAV/16 kHz
natively; the studio's existing STT input path already normalizes uploads, and the
same ffmpeg system-dependency note as mlx-whisper applies for exotic formats.

## D3 — TTS portable backend: validate the existing kokoro-onnx

**Decision**: No new TTS component. Kokoro-82M via `kokoro-onnx` (ONNX Runtime,
CPU) is already the registry's only TTS entry, is already runtime-portable
(`_runtime_supported` does not gate it on MLX), and already has sha256-pinned model
files (`KOKORO_MODEL` / `KOKORO_VOICES` + `verify_sha256`). Brick 5's TTS work is:
(a) make `pip install 'agency-studio[media]'` succeed off-Mac (D5), (b) assert
non-Mac availability truth in tests, (c) confirm in the Linux/Windows live run.

**Rationale**: The spec (clarified assumption) requires confirming portability, not
adding a redundant engine. Piper would add a second component, a second voice
model, and a second license entry for zero user-visible gain.

**Alternatives considered**: Piper (MIT) — rejected for v1: redundant with an
already-portable engine; noted as a future registry addition.

## D4 — Embeddings portable backend: llama.cpp loopback gateway

**Decision**: Add a `backend="llamacpp-gateway"` embedding backend that POSTs to a
user-run llama.cpp server's `/v1/embeddings` endpoint on a **loopback** address
(default `http://127.0.0.1:8080`, overridable via `AGENCY_STUDIO_EMBED_GATEWAY_URL`),
using stdlib `urllib`. The URL is validated host-is-loopback (127.0.0.1 / ::1 /
localhost) *before any request*; non-loopback → hard error (spec FR-010). Probe: one
GET `/health` with a short timeout — `gateway_down` (with a start hint) is
distinguished from `missing_binary`/not-configured (install hint). New `EmbedModel`
row declares the served model's dimensions and carries the existing "switching
affects new stores; re-ingest" note. `embeddings.py` gains a two-triple dispatch
(`"mlx"` — the current functions, byte-identical — and `"llamacpp-gateway"`).

**Rationale**: The roadmap names llama.cpp's embedding endpoint explicitly; a
gateway needs zero Python dependencies (stdlib urllib), works identically on all
three OSes, and llama.cpp is MIT with official binaries. The clarified
loopback-only-HTTP decision makes it constitution-clean.

**Alternatives considered**: llama-cpp-python — rejected: native build/wheel
friction across 3 OSes, a heavy extra for what one running binary provides.
sentence-transformers/torch — rejected: dependency weight. Driving llama.cpp as a
per-call subprocess — rejected: model reload per embed call (an ingest makes
hundreds of calls); the server holds the model warm, which is what `ModelManager`
does for MLX.

## D5 — Packaging: platform environment markers, no new extras

**Decision**: Add `sys_platform == "darwin"` environment markers to the MLX-only
packages inside existing extras (`mflux`, `mlx-whisper` in `[media]`;
`mlx-embedding-models`, `einops` in `[studio]`) so the same
`pip install 'agency-studio[media]'` succeeds on Linux/Windows and delivers the
portable subset (kokoro-onnx + soundfile). The binary-based backends (sd,
whisper-cli, llama.cpp) need no pip extra at all — their hints point at pinned
upstream releases.

**Rationale**: One install command per capability on every OS (end-user
simplicity); no new extra names to document; on macOS the resolved set is
byte-identical to today.

**Alternatives considered**: New parallel extras (`[media-portable]`, …) — rejected:
doubles the install-hint matrix and leaks platform reasoning onto the user.

## D6 — Platform-aware default resolution

**Decision**: Change `capabilities._default(entries)` to: the `default=True` entry
if it is AVAILABLE; else the first AVAILABLE entry in registry order; else the
`default=True` entry (today's value — preserves the honest 501-with-hint when
nothing is available). `resolve()` and `inventory()` pick this up unchanged.

**Rationale**: Implements the clarified spec decision with a three-line change at
the single defaulting chokepoint. On a Mac with MLX installed the default entry is
available → byte-identical. The only behavioral delta is the case that today
guarantees a 501.

**Alternatives considered**: Per-platform default flags in the registry — rejected:
duplicates what availability already knows. Silent selection-store writes —
rejected: a default is not a user choice and must not masquerade as one.

## D7 — Mission preflight (FR-012)

**Decision**: New `capabilities.preflight(families: Iterable[str]) -> list[Blocker]`
— for each requested family, resolve the active entry and collect a blocker
(family, entry id, reason, enablement) when it is unavailable. The server's
mission-start handler derives the needed families from the mission request's asset
options (assets on → image + tts; video opt-in → video; attached docs/RAG → embedding;
audio input → stt) and returns **409 + blockers JSON** before launching anything.
The GUI renders the blockers list from the error payload (no new component — the
mission form already surfaces launch errors).

**Rationale**: The chokepoint is the mission-start handler (assets markers don't
exist until the brain produces them, so "families the mission needs" =
families its request enables). 409 mirrors the existing unavailable-selection
status. Pure function in `capabilities.py` keeps it offline-testable.

**Alternatives considered**: Preflight at marker-render time — rejected: violates
the clarified fail-before-launch decision (mission would already have burned a
run). Blocking in `parse_markers` — rejected: it is deliberately pure.

## D8 — CI: 3-OS offline-suite matrix

**Decision**: `.github/workflows/offline-suite.yml`: matrix
{ubuntu-latest, windows-latest, macos-latest} × Python 3.12; steps: checkout,
setup-python, `pip install -e . -e ./agencykit pytest`, `python -m pytest`. No
extras installed — the suite must pass with zero optional backends (SC-004), which
is exactly what it asserts.

**Rationale**: Clarified decision. The suite is stdlib + monkeypatched boundaries,
so runners need nothing but Python; installing no extras makes the "green with
nothing installed" claim the thing CI actually proves.

**Alternatives considered**: Linux-only CI — rejected by clarification. Adding a
with-extras matrix leg — deferred: extras on Mac runners re-introduce MLX
hardware assumptions; live-binary validation stays a deferred live run (Wave 2
practice).

## D9 — Windows-safe subprocess discipline

**Decision**: All new subprocess calls go through a `portable.py` runner:
`subprocess.run([...], timeout=..., capture_output=True, text=True)` — no `killpg`,
no POSIX-only process groups, no shell=True. Timeouts are per-operation constants
(probe ≤ 1 s; generation/transcription generous, minutes-scale) surfaced as clean
errors, honoring the no-hangs edge case.

**Rationale**: The existing openmontage backend's `killpg` tree-kill is POSIX-bound;
the new backends must run on native Windows, and `subprocess.run(timeout=)` is the
portable core of the same guarantee for single-process binaries.

## D10 — Integrity (FR-013): pinned manifests, no silent downloads

**Decision**: New-backend model files are declared as `ModelFile` manifests
(filename + pinned upstream URL in the hint + sha256) but are **user-acquired**:
the install hint names the exact release/file and the destination directory (the
existing studio models dir); probe reports `missing_model_files` (with the hint)
when absent and `model_files_mismatch` when the sha256 check fails; load re-verifies
before first use. The studio itself never downloads for the new backends. Binaries
are pinned by version in the hint (`sd --version` / `whisper-cli` release tag);
mismatched binaries are not blocked (no reliable cross-OS binary fingerprint), the
pinned hint is the contract. Existing backends (HF-pinned snapshot downloads,
kokoro `ensure_file`) keep their current behavior — byte-identical (Principle X).

**Rationale**: Implements the clarified pinned+verified decision with the
repository's existing checksum machinery (`verify_sha256`), and keeps FR-010's
"never a silent download" honest for everything this brick adds.

**Alternatives considered**: Auto-download pinned weights at first load (the
existing MLX/kokoro pattern) — rejected for new backends: FR-010 as clarified makes
acquisition an explicit user step; revisiting belongs to the Brick 7 one-click
installer, not here.
