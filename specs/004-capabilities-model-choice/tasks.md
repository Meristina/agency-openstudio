# Tasks: Capabilities & Model Choice (the end of env-only)

**Input**: Design documents from `/specs/004-capabilities-model-choice/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/capabilities-api.md, quickstart.md

**Tests**: MANDATORY — Constitution Principle VII / FR-014: every code change ships
offline tests (no network, no CLI, no Node, no GPU; registries, subprocess catalog
probe, env, and data dir all monkeypatched). Write each story's tests first and see
them fail before implementing.

**Organization**: Tasks grouped by user story (US1 inventory · US2 selection ·
US3 resolution) so each story is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 (spec.md priorities P1 / P2 / P3)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The shared types every story builds on — no project init needed
(existing web app: `agency_studio/` stdlib server + `app/studio/` React GUI).

- [X] T001 Create `agency_studio/capabilities.py` with the shared vocabulary from
      data-model.md: `Family` (9 values + `SELECTABLE_FAMILIES`), `CostClass`
      (`free|paid|free_paid`), `Availability`, `UnavailableReason` (5 codes), and
      the frozen `CapabilityEntry` dataclass (id, label, family, cost,
      availability, reason, enablement, tier, note, default, key_env) — stdlib
      only, module docstring stating the passive-check contract (FR-005).
- [X] T002 [P] Mirror the same vocabulary in TypeScript in `app/studio/src/types.ts`:
      `Family`, `CostClass`, `CapabilityEntry`, `CapabilityFamilyView`,
      `CapabilityInventory` (shapes from contracts/capabilities-api.md).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: STT/TTS registry promotion (FR-004) and the passive probe kit — US1
enumerates registries that must exist first, US2/US3 select/resolve against them.

**⚠️ CRITICAL**: No user story work until this phase completes.

- [X] T003 [P] Add `SttModel`/`TtsModel` frozen dataclasses and insertion-ordered
      `STT_MODELS`/`TTS_MODELS` registries to `agency_studio/engines/models.py`
      following the `ImageModel`/`EmbedModel` pattern (id, label, note, repo,
      revision, probe_module, default) — initial entries wrap today's constants
      exactly: `whisper-large-v3-turbo` (`STT_HF_REPO`/`STT_HF_REVISION`, probe
      `mlx_whisper`) and `kokoro-v1.0` (probe `kokoro_onnx`); add
      `stt_models_payload()`/`tts_models_payload()` helpers (research.md R6).
- [X] T004 Switch the STT/TTS paths in `agency_studio/engines/local_media.py` to
      read the default registry entry (repo + revision via `_pinned_repo`) instead
      of module constants — same values through the same code, byte-identical
      behavior (Constitution X).
- [X] T005 [P] Offline tests for the promotion in `tests/test_local_media.py`:
      registry entries carry the exact pinned repo/revision the constants had;
      STT/TTS load paths receive identical arguments as before (monkeypatched
      backends); defaults flagged.
- [X] T006 Implement the passive probe kit in `agency_studio/capabilities.py`
      (research.md R1): `_extra_available(module)` via `importlib.util.find_spec`,
      `_key_present(env_name)` presence-only boolean, `_runtime_supported(entry)`
      platform predicate (MLX ⇒ arm64 darwin) — each returning
      (Availability, reason, enablement) triples; install hints reuse the extras'
      existing `pip install 'agency-studio[...]'` wording.
- [X] T007 Offline tests for the probe kit in `tests/test_capabilities.py`
      (new file): find_spec hit/miss, key set/unset (value never in the result),
      runtime predicate true/false — all via monkeypatch, no real imports.

**Checkpoint**: Registries complete, probes proven — user stories can begin.

---

## Phase 3: User Story 1 - See the honest capability inventory (Priority: P1) 🎯 MVP

**Goal**: One aggregated inventory of all 9 families with cost class, availability,
reason + enablement step — visible in the GUI, zero terminal (FR-001/002/003/005,
FR-012, FR-017).

**Independent Test**: On a machine with a known mix of extras/keys (all stubbed in
tests), open the capabilities view / `GET /api/capabilities` and verify every family
appears with correct cost class, availability, and unavailability reasons — no env
vars touched (spec US1 Independent Test; SC-001/002/005).

### Tests for User Story 1 (write first, watch them fail) ⚠️

- [X] T008 [P] [US1] Offline tests in `tests/test_capabilities.py`: entry builders
      for the 7 model families — image/video/visual/embedding (from
      `IMAGE_MODELS`/`VIDEO_MODELS`/`VISUAL_MODELS`/`EMBED_MODELS`),
      kg-extraction (claude|gliner2), stt/tts (new registries) — assert cost class
      per entry (local ⇒ free, keyed cloud ⇒ paid + correct `key_env` name),
      availability + reason/enablement under stubbed probes, embedding entries
      carry the ndim-coupling note (R7).
- [X] T009 [P] [US1] Offline tests in `tests/test_capabilities.py`: OpenMontage
      catalog probe — stubbed `_spawn_catalog` JSON ⇒ normalized entries with
      `ToolRuntime` tier and tier-derived cost (`local|local_gpu ⇒ free`,
      `api ⇒ paid`, `hybrid ⇒ free_paid`); probe failure/timeout/bad JSON ⇒ family
      renders one `catalog_error` state, other families unaffected; result cached,
      `refresh=True` re-probes (R4, spec edge case 2).
- [X] T010 [P] [US1] Offline tests in `tests/test_capabilities.py`: MCP family from
      a tmp `mcp.json` (command server available iff `shutil.which` hit + [mcp]
      extra present; url server; missing/empty/unreadable config ⇒ empty family
      with reason; all entries cost `free`) (R5, FR-017).
- [X] T011 [P] [US1] Contract test in `tests/test_server_capabilities.py` (new
      file): `GET /api/capabilities` — all 9 families always present, every
      unavailable entry carries non-null reason + enablement (SC-002), no response
      byte contains a stubbed key value (SC-007), `?refresh=1` triggers exactly one
      re-probe, broken store/catalog degrade into the payload with zero 5xx
      (SC-005).

### Implementation for User Story 1

- [X] T012 [US1] Implement the 5 existing-model-family entry builders in
      `agency_studio/capabilities.py` (image, video, visual, embedding,
      kg-extraction) mapping each registry entry → `CapabilityEntry` via the T006
      probes; paid entries carry `key_env` (`AGENCY_STUDIO_VIDEO_API_KEY`,
      `AGENCY_STUDIO_VISUAL_API_KEY`), embedding note per R7.
- [X] T013 [US1] Implement the stt/tts family builders in
      `agency_studio/capabilities.py` from `STT_MODELS`/`TTS_MODELS`.
- [X] T014 [US1] Implement the OpenMontage catalog probe in
      `agency_studio/capabilities.py`: `_spawn_catalog()` subprocess seam
      (`[sys.executable, "-c", <ToolRegistry discover/support_envelope script>]`,
      `cwd=openmontage/`, ~20 s timeout — mirror
      `openmontage_backend._spawn_render`; NEVER an in-process import,
      Constitution V), JSON normalization to entries with tier + tier-derived
      cost, per-process cache with `refresh` bypass (R4).
- [X] T015 [US1] Implement the MCP family builder in
      `agency_studio/capabilities.py` via `mcp_client.list_servers()` +
      `_extra_available("mcp")` + `shutil.which(command)`; tolerant of
      missing/unreadable `mcp.json` (R5, FR-017).
- [X] T016 [US1] Implement `inventory()` in `agency_studio/capabilities.py`:
      aggregate all 9 builders → ordered `CapabilityFamilyView` list
      (`selectable` false for production-tools/mcp; selection fields None/false
      until US2; `active` = built-in default until US3) + `generated_at`.
- [X] T017 [US1] Add `GET /api/capabilities` (+ `?refresh=1`) to
      `agency_studio/server.py` `do_GET` — `_send_json` house style, no new
      static/CORS surface (FR-015); wire T011 green.
- [X] T018 [P] [US1] Add `fetchCapabilities(refresh?)` to `app/studio/src/api.ts`
      and vitest coverage in `app/studio/src/capabilities-api.test.ts` (typed by
      T002 mirrors).
- [X] T019 [US1] Create `app/studio/src/components/Capabilities.tsx` — read-only
      view: family sections, FREE/PAID/dual badges, AVAILABLE/UNAVAILABLE with
      inline reason + enablement hint, tier badge on production tools — and mount
      it in `app/studio/src/App.tsx` navigation.

**Checkpoint**: US1 fully functional — honest inventory visible end-to-end (MVP).

---

## Phase 4: User Story 2 - Pick a default model per capability, and have it stick (Priority: P2)

**Goal**: Per-model-family persisted selection from the interface — no restart, no
terminal; unavailable entries refused with reason; stale selections flagged
(FR-006/007/008/011).

**Independent Test**: Select an available model for one family via
`PUT /api/capabilities/selection`, restart the (test) server against the same data
dir, confirm the selection is still reported; attempt an unavailable entry and
confirm the 409 reason + enablement step (spec US2 Independent Test; SC-003).

### Tests for User Story 2 (write first, watch them fail) ⚠️

- [X] T020 [P] [US2] Offline tests in `tests/test_capabilities.py`:
      `SelectionStore` — round-trip under a tmp `AGENCY_STUDIO_DATA_DIR`; atomic
      write (tmp + `os.replace`, no torn file on simulated crash between steps);
      tolerant load: missing file / invalid JSON / wrong shape / unknown version
      ⇒ `{}` never raises (R2, spec edge case 3).
- [X] T021 [P] [US2] Contract tests in `tests/test_server_capabilities.py`:
      `PUT /api/capabilities/selection` 200 (view reflects new default
      immediately), 400 unknown family / unknown id / inventory-only family
      (production-tools, mcp), 409 unavailable with reason + enablement in the
      body (FR-008); `DELETE /api/capabilities/selection/{family}` 204 idempotent,
      400 unknown family; selection survives handler re-instantiation against the
      same data dir (SC-003).
- [X] T022 [US2] Implement `SelectionStore` in `agency_studio/capabilities.py`:
      `selections.json` v1 schema in `rag.data_dir()`, atomic write, tolerant
      load, last-write-wins (R2).
- [X] T023 [US2] Add `PUT /api/capabilities/selection` and
      `DELETE /api/capabilities/selection/{family}` to `agency_studio/server.py`
      (`do_POST`-adjacent `do_PUT`/`do_DELETE` routing per house style):
      validate family ∈ SELECTABLE_FAMILIES → id ∈ registry → entry available →
      write; refusal bodies per contracts/capabilities-api.md.
- [X] T024 [US2] Compute selection state in `inventory()`: `selected` from the
      store, `selected_stale` when the id is unknown (`unknown_entry`) or
      unavailable — flagged, never an error (FR-011, spec edge case 4).
- [X] T025 [P] [US2] Add `selectCapability(family, id)` / `clearCapability(family)`
      to `app/studio/src/api.ts` + vitest cases in
      `app/studio/src/capabilities-api.test.ts` (incl. surfacing the 409 payload).
- [X] T026 [US2] Extend `app/studio/src/components/Capabilities.tsx`: default
      picker on selectable families only, immediate refresh on change, stale
      badge with reason, 409 refusal rendered inline with the enablement step
      (US2 acceptance scenarios 1/3/4).

**Checkpoint**: US1 + US2 work independently — selections persist and self-heal.

---

## Phase 5: User Story 3 - Missions honor the persisted choice; env vars still win (Priority: P3)

**Goal**: Every consumer resolves env → persisted selection → built-in default;
byte-identical with neither; override visibly flagged (FR-009/010).

**Independent Test**: With a persisted selection and no env, a consuming operation
(stubbed backend) receives the selected id; set the family's env var and it wins;
with neither, arguments are byte-identical to pre-brick behavior (spec US3
Independent Test; SC-004).

### Tests for User Story 3 (write first, watch them fail) ⚠️

- [X] T027 [P] [US3] Offline tests in `tests/test_capabilities.py`: `resolve()`
      precedence — env wins over selection wins over default; env naming an
      unknown id raises (fail-loud, R3); stale/unknown selection skipped silently
      to default (FR-011); no env + no selection ⇒ exactly the family's built-in
      default constant (FR-009 scenario 3).
- [X] T028 [P] [US3] Offline consumer-wiring tests in
      `tests/test_server_capabilities.py`: with a persisted image selection the
      `/api/image` handler passes the selected id to the (monkeypatched) media
      manager; same pattern for video (`default_video_model`), visual, embedding
      (`Retriever` init), kg (`make_extractor`), stt/tts (registry entry lookup);
      then with the env var set, the env id wins (SC-004).
- [X] T029 [US3] Implement `resolve(family)` + the per-family env table in
      `agency_studio/capabilities.py` (R3): existing
      `AGENCY_STUDIO_VIDEO_BACKEND` / `AGENCY_STUDIO_KG_BACKEND` reused unchanged;
      new `AGENCY_STUDIO_IMAGE_MODEL`, `AGENCY_STUDIO_VISUAL_BACKEND`,
      `AGENCY_STUDIO_EMBED_MODEL`, `AGENCY_STUDIO_STT_MODEL`,
      `AGENCY_STUDIO_TTS_MODEL`; env read at call time.
- [X] T030 [US3] Wire the consumers through `resolve()`: image default in
      `agency_studio/server.py` (`payload.get("model") or resolve("image")`,
      today's line ~1884), `default_video_model()` in `agency_studio/seedance.py`
      (selection inserted between env and `DEFAULT_VIDEO_MODEL`), visual default
      in `agency_studio/visual.py`, embed default at `Retriever` construction in
      `agency_studio/rag.py`/server, extractor default in
      `agency_studio/knowledge.py` `make_extractor`, STT/TTS entry lookup in
      `agency_studio/engines/local_media.py` — each preserving its existing
      fail-loud env semantics and byte-identical no-config path (Constitution X).
- [X] T031 [US3] Populate `env_override` (var name when set) and `active`
      (resolved id) per family in `inventory()` / the `GET /api/capabilities`
      payload (FR-010).
- [X] T032 [US3] Show the env-override banner on affected families in
      `app/studio/src/components/Capabilities.tsx` ("selection currently
      overridden by $VAR") per US3 acceptance scenario 2.

**Checkpoint**: All three stories independently functional — the brick is complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T033 [P] SC-007 hardening test in `tests/test_server_capabilities.py`: with
      stub key values set, assert no capabilities/selection response body, no
      `selections.json` content, and no captured server log line contains any key
      value (FR-013).
- [X] T034 [P] Document the resolution order and the seven per-family env vars in
      `README.md` (configuration section) — env demoted to power-user override,
      GUI is the primary path (Constitution VIII).
- [X] T035 Validate `specs/004-capabilities-model-choice/quickstart.md` end to end;
      run `pytest -q` (full offline suite green — SC-006) and
      `cd app/studio && npx vitest run && npm run build`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none — start immediately; T001 ∥ T002.
- **Foundational (Phase 2)**: needs T001. Blocks all stories. T003 ∥ T006 (different
  files); T004 after T003; T005 after T004; T007 after T006.
- **US1 (Phase 3)**: needs Phase 2. Tests T008–T011 first (all ∥). Then T012–T013
  (same file, sequential), T014, T015, T016 after T012–T015, T017 after T016;
  GUI: T018 ∥ backend work (needs only T002), T019 after T017 + T018.
- **US2 (Phase 4)**: needs Phase 2 (+T016/T017 for the selection-state and endpoint
  integration points). T020 ∥ T021 first. T022 → T023 → T024; T025 ∥ backend,
  T026 after T023 + T025.
- **US3 (Phase 5)**: needs Phase 2; integrates with US2's store (T022) for the
  selection leg — env and default legs testable without it. T027 ∥ T028 first.
  T029 → T030 → T031; T032 after T031.
- **Polish (Phase 6)**: after desired stories; T033 ∥ T034, T035 last.

### Story independence notes

- US1 delivers value alone (read-only inventory) — the MVP.
- US2 layers the store + endpoints on US1's inventory but its store/endpoint tests
  run against Phase 2 primitives alone.
- US3's `resolve()` is independently testable (env/default legs) even before US2;
  the full three-leg chain needs T022.

### Parallel Opportunities

- T001 ∥ T002 · T003 ∥ T006 · T005 ∥ T007.
- All of a story's test tasks run in parallel (T008–T011; T020–T021; T027–T028).
- Frontend (T018, T025) parallels backend within each story.
- After Phase 2, US1/US2/US3 backend work can proceed on parallel branches if
  staffed — merge order P1 → P2 → P3.

## Parallel Example: User Story 1

```bash
# All US1 tests together (must fail before implementation):
Task: "T008 model-family entry builders tests in tests/test_capabilities.py"
Task: "T009 OpenMontage probe tests in tests/test_capabilities.py"
Task: "T010 MCP family tests in tests/test_capabilities.py"
Task: "T011 GET /api/capabilities contract test in tests/test_server_capabilities.py"

# Then frontend in parallel with backend:
Task: "T018 fetchCapabilities in app/studio/src/api.ts + vitest"
```

## Implementation Strategy

**MVP first**: Phases 1–3 only ⇒ the honest inventory ships alone (US1 = the
spec's stated standalone value). Stop, validate against SC-001/002/005, demo.

**Incremental**: add Phase 4 (selection persists — SC-003), then Phase 5
(resolution + override visibility — SC-004), then Polish (SC-006/007). Each phase
ends at a checkpoint with the full offline suite green; commit per task or logical
group (Conventional Commits, squash-merge PR to main per house rules).
