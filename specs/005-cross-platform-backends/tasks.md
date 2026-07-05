# Tasks: Cross-Platform Backends ("any machine")

**Input**: Design documents from `/specs/005-cross-platform-backends/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: MANDATORY (Constitution VII) — every code change ships offline tests; all
subprocess (`subprocess.run`, `shutil.which`), loopback-HTTP (`urllib`), import
(`find_spec`) and platform (`sys.platform` / `platform.machine`) boundaries are
monkeypatched. Tests are written FIRST within each phase and must fail before the
implementation task lands.

**Organization**: Grouped by user story; US1 (mission runs off-Mac) is the MVP.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3 (user-story phases only)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Packaging and CI groundwork that everything else rides on.

- [X] T001 Add `sys_platform == "darwin"` environment markers to MLX-only packages in `pyproject.toml` (`mflux`, `mlx-whisper` in `[media]`; `mlx-embedding-models`, `einops` in `[studio]`) so both extras install their portable subset on Linux/Windows; macOS resolution stays byte-identical (research D5)
- [X] T002 [P] Create `.github/workflows/offline-suite.yml` — matrix {ubuntu-latest, windows-latest, macos-latest} × Python 3.12: checkout, setup-python, `pip install -e . -e ./agencykit pytest`, `python -m pytest`; NO extras installed (research D8, SC-004)
- [X] T003 [P] Record stable-diffusion.cpp (MIT), whisper.cpp (MIT), and llama.cpp (MIT) with pinned release versions in `docs/LICENSES.md` (FR-011)

**Checkpoint**: CI runs (and passes — no code changed yet) on all three OSes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared portable-backend plumbing, registry rows, and
availability/defaulting logic every story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Write offline tests for the portable helpers in `tests/test_portable.py` (new file): `require_loopback` accepts `http://127.0.0.1:*`/`[::1]`/`localhost` and rejects non-loopback hosts and non-http(s) schemes; `run_subprocess` maps `TimeoutExpired` to a clean error (no hang, no raw traceback); `verify_model_file` returns reason-coded failures (`missing_model_files` / `model_files_mismatch`); `find_binary` is a single stub point — must FAIL before T006
- [X] T005 [P] Write offline tests for registry + capabilities deltas in `tests/test_capabilities.py`: new rows (`stable-diffusion-cpp`, `whisper-cpp`, `nomic-embed-gguf`) present with `default=False`; existing rows byte-identical (ids, defaults, fields); new reason codes surface with enablement hints; `_default()` platform-aware behavior (default available → unchanged; default unavailable + sibling available → first available; nothing available → built-in default) — must FAIL before T007/T008
- [X] T006 Implement `agency_studio/engines/portable.py`: `find_binary`, `require_loopback`, `get_json`/`post_json` (stdlib urllib, timeouts, no off-loopback redirects), `run_subprocess` (no shell, no killpg, text, captured output, explicit timeout), `verify_model_file` (exists → `verify_sha256` → path) per `contracts/backend-seams.md`
- [X] T007 Add registry rows and discriminators in `agency_studio/engines/models.py`: `SttModel.backend: str = "mlx"` and `EmbedModel.backend: str = "mlx"` (existing literals untouched); new `ImageModel` row `stable-diffusion-cpp` (backend `sdcpp`, binary `sd`), new `SttModel` row `whisper-cpp` (backend `whispercpp`, binary `whisper-cli`), new `EmbedModel` row `nomic-embed-gguf` (backend `llamacpp-gateway`, `AGENCY_STUDIO_EMBED_GATEWAY_URL`, correct `ndim`); `ModelFile` manifests (filename + pinned source URL in hint + sha256) for the sd GGUF checkpoint and the whisper.cpp model file (data-model.md)
- [X] T008 Extend `agency_studio/capabilities.py`: new reason codes (`missing_binary`, `missing_model_files`, `model_files_mismatch`, `gateway_down`); entry-builder wiring so the three new rows probe correctly per platform (binary + model-file checks for sdcpp/whispercpp; loopback health check for the gateway — passive, short-timeout, stubbed in tests); platform-aware `_default()` (research D6); make T005 pass

**Checkpoint**: Foundation ready — inventory shows the new entries with honest
platform-aware availability; user stories can start.

---

## Phase 3: User Story 1 — A mission with assets runs on a machine without Apple Silicon (Priority: P1) 🎯 MVP

**Goal**: The portable backends actually produce assets: sdcpp image generation,
whisper.cpp transcription, gateway embeddings, portable kokoro TTS — so the same
mission with assets completes on Linux/Windows without MLX.

**Independent Test**: On a simulated non-Mac platform (monkeypatched), with stubbed
binaries/gateway, an asset render for each family succeeds through the portable
backend; the acceptance live run (real Linux/Windows box) is the deferred Wave-2
style validation in quickstart.md.

### Tests for User Story 1 (MANDATORY — offline) ⚠️

- [X] T009 [P] [US1] Write sdcpp backend tests in `tests/test_local_media.py`: probe raises reason-coded `MediaUnavailable` for missing binary / missing model file / checksum mismatch (stubbed `find_binary`, `verify_model_file`); run invokes the documented argv contract via stubbed `run_subprocess` and writes to `out_path`; timeout → clean error — must FAIL before T013
- [X] T010 [US1] Write STT dispatch tests in `tests/test_local_media.py` (same file as T009 — sequential): `_STT_BACKENDS["mlx"]` preserves existing behavior byte-identically (existing monkeypatched fakes still pass via `_seam_arity` shims); `whispercpp` triple probes/runs through stubs; `transcribe()` dispatches on the resolved entry's backend — must FAIL before T014
- [X] T011 [P] [US1] Write gateway embedding tests in `tests/test_embeddings_gateway.py` (new file): URL resolution (env override, default), non-loopback URL hard-rejected before any request, probe → `gateway_down` with start hint on stubbed connection failure, run POSTs `{"input": [...]}` to `/v1/embeddings` and returns plain float lists, vector-length validated against `entry.ndim` — must FAIL before T015
- [X] T012 [P] [US1] Write TTS off-Mac availability test in `tests/test_capabilities.py`: with platform monkeypatched to Linux/Windows and `kokoro_onnx`+`soundfile` present (stubbed `find_spec`), the `kokoro-v1.0` entry reports AVAILABLE (spec assumption: confirm portability)

### Implementation for User Story 1

- [X] T013 [US1] Implement the `sdcpp` (probe, load, run) triple in `agency_studio/engines/local_media.py` and register it in `_IMAGE_BACKENDS`; probe/load/run per `contracts/backend-seams.md` (probe before eviction, load re-verifies sha256, run via `portable.run_subprocess`)
- [X] T014 [US1] Introduce `_STT_BACKENDS` dispatch in `agency_studio/engines/local_media.py` — move the existing mlx functions in as the `"mlx"` triple unchanged; add the `whispercpp` triple (binary + pinned model file, transcript parsed from output); route `transcribe()` through the resolved entry's backend
- [X] T015 [US1] Add backend dispatch to `agency_studio/engines/embeddings.py` — `"mlx"` = existing functions byte-identical; `"llamacpp-gateway"` = loopback client per `contracts/backend-seams.md`; `ModelManager.embed` keys stay `embed:<id>` (gateway has zero residency cost, mirrors video backends)
- [X] T016 [US1] Verify (and wire if missing) that every asset-production call site resolves its family through `capabilities.resolve()` — image render path in `agency_studio/assets.py` / `agency_studio/server.py` passes the resolved image id to `generate_image` the way stt/tts already resolve; add a regression test in `tests/test_assets_render.py`

**Checkpoint**: Each family produces an asset through its portable backend under
stubs; MVP demonstrable (live-run checklist deferred per quickstart.md §5).

---

## Phase 4: User Story 2 — Pick a portable backend without touching a terminal (Priority: P2)

**Goal**: The new entries are first-class in the Brick 4 panel: honest
availability + reasons on every platform, selectable when available, persisted,
env-overridable.

**Independent Test**: Inventory and selection endpoints exercised offline with
stubbed platforms/probes: new entries appear with correct reason codes; selecting
an available portable entry persists and drives resolution; env var still wins.

### Tests for User Story 2 (MANDATORY — offline) ⚠️

- [X] T017 [P] [US2] Write server inventory/selection tests in `tests/test_server_capabilities.py`: GET inventory lists the three new entries with platform-correct availability/reason/enablement (MLX entries report `unsupported_runtime` on stubbed Linux — FR-005); PUT selection of an available portable entry → 200 + persisted; PUT of an unavailable one → 409 carrying the new reason codes
- [X] T018 [P] [US2] Write precedence/persistence tests in `tests/test_capabilities.py`: env override beats a persisted portable selection (FR-006); selection survives a fresh `SelectionStore` (restart simulation); a persisted selection whose backend is absent on this machine surfaces `selected_stale` + reason (spec edge case)

### Implementation for User Story 2

- [X] T019 [US2] Surface the new reason codes in the capabilities panel in `app/studio/` — map `missing_binary` / `missing_model_files` / `model_files_mismatch` / `gateway_down` to human labels with the enablement hint rendered verbatim (copy-paste-able); no new component, extend the existing entry badge/hint rendering; update front-end test/snapshot if present

**Checkpoint**: US1 + US2 both work; a user on any (stubbed) platform sees and
selects portable backends entirely through the interface.

---

## Phase 5: User Story 3 — Absent backends fail cleanly everywhere (Priority: P3)

**Goal**: Every absence is a guidance moment: preflight blocks doomed missions
with the full blocker list; direct requests 501 with hints; nothing crashes or
hangs.

**Independent Test**: Offline server tests: mission launch with a blocked family →
409 + complete blockers list, nothing spawned; asset requests against absent
backends → 501 + hint for every family; process keeps serving.

### Tests for User Story 3 (MANDATORY — offline) ⚠️

- [X] T020 [P] [US3] Write preflight unit tests in `tests/test_capabilities.py`: `preflight(families)` → `[]` when all available; single and multiple `Blocker`s with family/entry/reason/enablement; resolution respects env > selection > platform-aware default
- [X] T021 [P] [US3] Write mission preflight server tests in `tests/test_server.py`: mission POST with assets enabled + one family blocked → 409 with the exact `contracts/preflight-api.md` payload (ALL blockers listed) and no engine subprocess spawned (stub asserts not called); text-only mission → preflight not invoked, launch path byte-identical
- [X] T022 [US3] Write 501-mapping tests in `tests/test_server_media.py` (sequential with existing media tests): direct `/api/image`, `/api/stt`, embed-consuming request against an absent portable backend → HTTP 501, body contains the reason-coded hint, server keeps answering subsequent requests (FR-004)

### Implementation for User Story 3

- [X] T023 [US3] Implement `capabilities.preflight(families) -> list[Blocker]` in `agency_studio/capabilities.py` per data-model.md (pure, offline-testable; resolves the active entry per family and collects reason-coded blockers)
- [X] T024 [US3] Integrate preflight into the mission-start handler in `agency_studio/server.py`: derive needed families from the mission request's asset options (assets → image+tts; video opt-in → video; docs/RAG → embedding; audio input → stt per `contracts/preflight-api.md`); any blocker → 409 + blockers JSON before anything is spawned
- [X] T025 [US3] Render the 409 `blockers[]` payload in the mission form's existing launch-error surface in `app/studio/` (family + hint per line, link to capabilities panel); no new component

**Checkpoint**: All three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T026 [P] Add the cross-platform setup section to `README.md` (per-OS install paths, portable backend enablement, gateway loopback rule, env → selection → platform-aware default precedence)
- [X] T027 [P] Document the loopback-only plain-HTTP gateway exception in `docs/SECURITY.md` (clarified FR-010 decision; HTTPS-only remains absolute off-loopback)
- [X] T028 Execute the offline portions of `specs/005-cross-platform-backends/quickstart.md` and record the deferred live-run checklist (real Linux/Windows box with real binaries — Wave-2 practice) as the brick's acceptance follow-up in quickstart.md §5
- [X] T029 Byte-identical audit + full suite: run `python -m pytest` (all platforms via T002's CI); verify existing tests pass unmodified except where a task explicitly extended them, and that on a stubbed darwin/arm64 platform the inventory, defaults, and asset paths are identical to pre-brick behavior (Principle X, SC-006)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: none — start immediately; T001/T002/T003 independent.
- **Phase 2 (Foundational)**: needs T001 (markers) only conceptually; blocks ALL stories. Within: T004, T005 (tests) first and in parallel; T006 ← T004; T007 independent of T006; T008 ← T006 + T007.
- **Phase 3 (US1)**: needs Phase 2. Within: T009/T011/T012 parallel (different files), T010 after T009 (same file); T013 ← T009; T014 ← T010; T015 ← T011; T016 last (touches call sites).
- **Phase 4 (US2)**: needs Phase 2 (only T017's platform assertions touch US1 outputs indirectly through T008 — no US1 dependency).
- **Phase 5 (US3)**: needs Phase 2; T023 is cleanest after US1's backends exist but is testable against stubs independently.
- **Phase 6 (Polish)**: after desired stories complete; T026/T027 parallel.

### User Story Dependencies

- US1: Foundational only.
- US2: Foundational only (independent of US1 — inventory/selection operate on stubbed probes).
- US3: Foundational only (preflight resolves via capabilities regardless of which backends exist).

### Parallel Example: after Phase 2 completes

```bash
# Three developers (or three sequential blocks, priority order):
Dev A (US1): T009, T011, T012 in parallel → T010 → T013, T014, T015 → T016
Dev B (US2): T017 ∥ T018 → T019
Dev C (US3): T020 ∥ T021 → T022 → T023 → T024 → T025
```

---

## Implementation Strategy

**MVP first (US1)**: Phase 1 → Phase 2 → Phase 3, then STOP and validate: stubbed
asset production through every portable backend, plus the deferred live-run
checklist on a real non-Mac box. That alone delivers the brick's "done when"
kernel.

**Incremental delivery**: each story lands as its own reviewable increment
(commit after each task or logical group; suite green at every checkpoint). US2
then makes the backends user-selectable; US3 hardens absence into guidance;
Polish closes docs, security notes, and the byte-identical audit.

**Constitution notes for the implementer**: existing registry literals and MLX
seams are never edited in place — new rows, new triples, dispatch keyed on
`backend` (Principle X). All new subprocess/network code is Windows-safe and
timeout-bounded (research D9). No task introduces a runtime dependency into the
core (Principle: stdlib-only).
