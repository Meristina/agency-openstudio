# Implementation Plan: Cross-Platform Backends ("any machine")

**Branch**: `005-cross-platform-backends` | **Date**: 2026-07-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-cross-platform-backends/spec.md`

## Summary

Give every Apple-Silicon-bound capability family a portable sibling behind the
existing registries, exactly the way `openmontage-remotion` landed behind
`VIDEO_MODELS`: new registry rows + new (probe → load → run) triples, zero new
surfaces. Image gains a `stable-diffusion.cpp` subprocess backend, speech-to-text
gains a `whisper.cpp` subprocess backend, embeddings gain a llama.cpp
loopback-gateway backend, and text-to-speech (already ONNX/CPU via kokoro-onnx) is
validated and packaged for non-Mac installs. `capabilities.resolve()` becomes
platform-aware in its default step, a mission preflight blocks launches that would
die on an absent family, and a 3-OS CI matrix keeps the offline suite provably green
everywhere.

## Technical Context

**Language/Version**: Python ≥ 3.10, stdlib-only core (per constitution); frontend
React + Vite under `app/studio/` (no new GUI surface this brick — new entries render
through the existing Brick 4 capabilities panel).

**Primary Dependencies**: None added to core. New optional components are
user-installed external binaries (`sd` from stable-diffusion.cpp, `whisper-cli` from
whisper.cpp, a user-run llama.cpp server) driven over subprocess/loopback-HTTP
boundaries with stdlib `subprocess`/`urllib`. `pyproject.toml` optional extras gain
platform environment markers so `[media]`/`[studio]` install cleanly off-Mac.

**Storage**: Existing `selections.json` (Brick 4, unchanged schema). Model weights
for new backends live in the existing studio models directory used by
`ModelFile`/`ensure_file`, pinned by sha256.

**Testing**: `pytest` at repo root, fully offline — every subprocess boundary
(`subprocess.run`, `shutil.which`) and loopback-HTTP boundary (`urllib`) is
monkeypatched; no binaries, no network, no GPU, no Node. Live runs with real
binaries deferred (Wave 2 practice).

**Target Platform**: macOS (Apple Silicon + Intel), Linux, native Windows — server
and all four portable backends CPU-only.

**Project Type**: Local-first web service (stdlib HTTP/SSE server) + web GUI.

**Performance Goals**: Correct completion, not parity: CPU image generation and
transcription are expected to be minutes-scale. Every subprocess call carries an
explicit timeout (no hangs — spec edge case); probes stay < 1 s (import check /
`which` / one loopback HEAD with short timeout).

**Constraints**: 501-with-hint on every absent backend (never a crash); byte-identical
behavior on an unchanged Mac; no network during asset production except plain HTTP
to loopback for the gateway backend (clarified exception); HTTPS-only everywhere
else; model files verified by sha256 before use; AGPL-compatible components only.

**Scale/Scope**: 4 capability families, 3 new backend implementations + 1 validated
existing one, ~6 studio modules touched, 1 new engines module, 1 CI workflow,
~8 test files extended.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — no reasoning path changes; all
  new backends are multimodal production, not reasoning; no token-billed API anywhere.
- [x] **II. Engine neutrality**: PASS — no Engine-contract surface touched.
- [x] **III. No invented information**: PASS — research/citation/inspector paths
  untouched; the preflight runs before mission launch and never edits deliverables.
- [x] **IV. Local-first & offline-by-default**: PASS — this brick *implements* the
  principle's cross-platform mandate. All new backends free/local/CPU. The llama.cpp
  gateway is loopback-only (the user's own machine); no new cloud path.
- [x] **V. Subprocess boundaries**: PASS — sd/whisper-cli/llama.cpp are driven only
  via subprocess or loopback HTTP; `openmontage/` and `agencykit/` subtrees untouched.
- [x] **VI. Security**: PASS with one documented refinement — server bind, CORS,
  `path_inside()` untouched; API keys untouched. The gateway backend speaks plain
  HTTP strictly to validated loopback addresses (127.0.0.1 / ::1 / localhost — a
  clarified spec decision, FR-010); any non-loopback URL is rejected before any
  request is made. HTTPS-only remains absolute for non-loopback traffic.
- [x] **VII. Offline tests**: PASS — all new behavior covered by monkeypatched
  offline tests; the new CI matrix enforces this on 3 OSes per PR.
- [x] **VIII. End-user simplicity**: PASS — selection stays in the Brick 4 panel;
  install hints are copy-paste concrete; no terminal needed to *select* (installing
  a binary is a guided setup step, consistent with the existing extras practice).
- [x] **IX. License**: PASS — stable-diffusion.cpp (MIT), whisper.cpp (MIT),
  llama.cpp (MIT), kokoro-onnx (MIT, already recorded); each recorded in
  `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — new registry rows + new dispatch triples;
  existing entries and seams byte-identical. The one shared-path change —
  platform-aware `_default()` — only alters the case where the built-in default is
  UNAVAILABLE (today: guaranteed 501), and is a spec-clarified requirement; on a Mac
  with MLX present nothing changes. Inspector veto loop untouched.
- [x] **XI. English everywhere**: PASS.

**Post-Phase-1 re-check**: PASS — the design artifacts introduce no new violations;
the loopback-HTTP refinement under VI is carried into `contracts/backend-seams.md`
as a mandatory URL validation step.

## Project Structure

### Documentation (this feature)

```text
specs/005-cross-platform-backends/
├── plan.md              # This file
├── research.md          # Phase 0 output — backend & packaging decisions
├── data-model.md        # Phase 1 output — registry rows, probe reasons, blockers
├── quickstart.md        # Phase 1 output — Linux/Windows walkthrough
├── contracts/
│   ├── capabilities-api.md   # inventory/selection deltas + new reason codes
│   ├── preflight-api.md      # mission preflight block contract
│   └── backend-seams.md      # probe/load/run contracts per family
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
agency_studio/
├── engines/
│   ├── models.py         # + ImageModel row (sdcpp), SttModel row (whispercpp),
│   │                     #   EmbedModel row (llama.cpp gateway), ModelFile manifests
│   │                     #   (GGUF weights, sha256-pinned)
│   ├── local_media.py    # + sdcpp triple in _IMAGE_BACKENDS; STT backend dispatch
│   │                     #   (_STT_BACKENDS mirroring _IMAGE_BACKENDS) + whispercpp triple
│   ├── embeddings.py     # + backend dispatch (mlx | gateway) keyed on the entry
│   └── portable.py       # NEW — shared portable-backend helpers: binary probe
│                         #   (shutil.which + version pin), loopback URL validation,
│                         #   stdlib urllib JSON client, subprocess runner w/ timeout
├── capabilities.py       # platform-aware _default(); new reason codes
│                         #   (missing_binary / missing_model_files /
│                         #    model_files_mismatch / gateway_down); preflight()
└── server.py             # mission-start preflight integration (409 + blockers)

app/studio/               # no new surface; mission-start blocker message rendering only

pyproject.toml            # platform environment markers on MLX-only packages
.github/workflows/
└── offline-suite.yml     # NEW — 3-OS matrix (ubuntu/windows/macos) running pytest

docs/LICENSES.md          # + stable-diffusion.cpp, whisper.cpp, llama.cpp
README.md                 # cross-platform setup section

tests/
├── test_capabilities.py          # platform-aware default, new reasons, preflight
├── test_local_media.py           # sdcpp + whispercpp triples (stubbed subprocess)
├── test_rag.py / test_knowledge.py  # gateway embed path (stubbed urllib)
├── test_server.py / test_server_capabilities.py  # preflight 409, inventory deltas
└── test_portable.py              # NEW — loopback validation, binary probe, timeouts
```

**Structure Decision**: Single existing project; everything lands inside
`agency_studio/` behind the registries. The only new module is
`engines/portable.py` (shared helpers so the three portable backends don't
triplicate subprocess/loopback plumbing). No new top-level directories except
`.github/workflows/`.

## Complexity Tracking

No constitution violations to justify. The one nuance (plain HTTP to loopback for
the gateway backend) is a spec-clarified decision recorded under Constitution
Check VI, not a violation: the HTTPS-only rule targets outbound network traffic,
and the gateway never leaves the machine — enforcement is a hard loopback-host
check *before* any request.
