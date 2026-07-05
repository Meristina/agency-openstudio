# Tasks: Clients & Projects (Brick 6)

**Input**: Design documents from `/specs/006-clients-projects/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/taxonomy-api.md, quickstart.md

**Tests**: MANDATORY (Constitution VII + FR-011) — every code change ships offline tests (no network, no CLI agent, no GPU; store redirected to a tmp dir; Node only for the frontend Vitest suite, per existing convention). Tests are written FIRST and must fail before the implementation task makes them pass.

**Organization**: Grouped by user story; US1 (tagging) is the MVP increment, US2 (browsing) the visible payoff, US3 (migration + re-assign) makes the taxonomy total.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (user story phases only)

## Path Conventions

Web app per plan.md: backend `agency_studio/`, frontend `app/studio/src/`, offline suite `tests/` at repo root.

---

## Phase 1: Setup

**Purpose**: Confirm a green baseline so every later red test is attributable to this brick.

- [X] T001 Run the offline gates on a clean tree and record both green: `pytest` at repo root and `cd app/studio && npm test` (no file changes; abort and fix the environment if either is red)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The taxonomy core every story consumes — normalization, resolution order, registry IO, and the workspace-scoped store scan. No user story work before this phase is done.

**⚠️ CRITICAL**: US1–US3 all resolve attribution through this module.

- [X] T002 [P] Write failing unit tests for name normalization & validation in tests/test_taxonomy.py: trim + casefold keys; hierarchy-namespaced project/campaign keys (same-named projects under two clients stay distinct); display form preserves first-typed casing; empty-after-trim ⇒ absent; >120 chars and control chars rejected (data-model.md "Validation rules", research D5)
- [X] T003 [P] Write failing unit tests for attribution resolution in tests/test_taxonomy.py: order override > dossier fields > derived default; defaults client "Studio", project = final path component of the canonical `project_root` stamp, stamp-less ⇒ project "Unassigned"; per-level fallback (campaign kept when client/project absent); resolution total over any readable dossier (data-model.md "MissionAttribution")
- [X] T004 [P] Write failing unit tests for the registry in tests/test_taxonomy.py: load of missing/corrupt `taxonomy.json` ⇒ empty registry; save is atomic (tmp + `os.replace` in same dir); override set/replace/clear round-trip; `names` first-typed persistence (research D2)
- [X] T005 Implement agency_studio/taxonomy.py — normalization/display helpers, field validation, `resolve(dossier, registry)`, registry load/save (path from `agency_kit.store.agency_dir()` / "taxonomy.json") — making T002–T004 pass
- [X] T006 Write failing unit tests for the store scan in tests/test_taxonomy.py: iterate a tmp store via `store.missions_path()`, workspace scoping via `store.mission_in_project`, corrupt/unreadable dossier skipped (same tolerance as `list_missions`), read-only (no file mtime/content changes)
- [X] T007 Implement the workspace-scoped dossier scan iterator in agency_studio/taxonomy.py, making T006 pass

**Checkpoint**: `pytest tests/test_taxonomy.py` green — user stories can begin.

---

## Phase 3: User Story 1 — Tag a mission with its client, project, and campaign (Priority: P1) 🎯 MVP

**Goal**: Missions (and thus their deliverables) carry client/project/campaign; untagged missions behave byte-identically and resolve to the workspace default.

**Independent Test**: Start one tagged and one untagged mission (runner monkeypatched); the first's saved dossier carries the exact tags and the `done` frame reports the attribution; the second's request/dossier handling is unchanged from pre-brick behavior.

### Tests for User Story 1 (write first, must fail) ⚠️

- [X] T008 [P] [US1] Write failing server tests in tests/test_server_taxonomy.py for POST /api/mission payload handling: optional `client`/`project`/`campaign` accepted; non-string ⇒ absent; empty-after-trim ⇒ absent; >120 chars or control chars ⇒ HTTP 400 before any mission starts; payload without tags parses exactly as today (contracts/taxonomy-api.md §1)
- [X] T009 [P] [US1] Write failing server tests in tests/test_server_taxonomy.py for the completion path (runner_bridge monkeypatched, tmp store): tags merged into the new mission's own dossier and re-saved via `store.save`; `done` SSE frame carries `attribution`; checkpoint envelope includes the tags and a resume re-supplies them; a mission run with no tags produces a dossier byte-identical to the monkeypatched runner's output

### Implementation for User Story 1

- [X] T010 [US1] Parse and validate the three optional payload fields in `_parse_mission_params` (agency_studio/server.py), returning 400 on invalid values, absent-tolerant otherwise — makes T008 pass
- [X] T011 [US1] Thread tags through the mission worker in agency_studio/server.py: include in the checkpoint envelope beside goal/engine/flags; restore from a resume envelope; after `result.dossier` is available, merge fields and re-save via `agency_kit.store.save`; add `attribution` to the `done` SSE frame — makes T009 pass
- [X] T012 [P] [US1] Add taxonomy fields to the mission-start payload types and request builder in app/studio/src/types.ts and app/studio/src/api.ts
- [X] T013 [US1] Add three optional inputs (Client / Project / Campaign) to the mission-start form in app/studio/src/App.tsx (plain text inputs for now; datalist suggestions arrive with US2), wired into the api.ts payload
- [X] T014 [US1] Add/extend Vitest coverage in app/studio/src/App.test.tsx and app/studio/src/api.test.ts: fields render, values reach the POST payload, empty fields are omitted

**Checkpoint**: US1 fully functional — tagged missions persist their taxonomy; untagged path untouched.

---

## Phase 4: User Story 2 — Browse history by client and by campaign (Priority: P2)

**Goal**: Workspace-scoped grouped views — taxonomy tree with counts, filterable history — in API and GUI; the flat feed stays byte-identical.

**Independent Test**: Seed a tmp store with missions tagged for two clients (one with a campaign) plus one untagged; `GET /api/taxonomy` groups them correctly with counts; filtered `GET /api/missions` returns exactly each slice; paramless listing is unchanged; unknown names ⇒ empty result.

### Tests for User Story 2 (write first, must fail) ⚠️

- [X] T015 [P] [US2] Write failing unit tests for the tree builder in tests/test_taxonomy.py: clients → projects → campaigns with mission counts (client count = sum of its projects), display names preferred from registry `names`, every readable mission in exactly one project, empty store ⇒ empty tree (data-model.md aggregates)
- [X] T016 [US2] Implement tree builder and attribution-filter helpers in agency_studio/taxonomy.py, making T015 pass
- [X] T017 [P] [US2] Write failing server tests in tests/test_server_taxonomy.py for GET /api/taxonomy: contract shape (contracts/taxonomy-api.md §2), workspace scoping (other-project missions invisible), empty store ⇒ `{"clients": []}`, serving the endpoint writes nothing (store + registry files byte-unchanged)
- [X] T018 [P] [US2] Write failing server tests in tests/test_server_taxonomy.py for GET /api/missions filters: case-insensitive name matching, filters compose (AND), rows gain resolved attribution columns, unknown names ⇒ `{"missions": []}` with 200, invalid values ⇒ 400, and **paramless response identical to the pre-brick handler output** (contracts/taxonomy-api.md §3)
- [X] T019 [US2] Implement the routes in agency_studio/server.py: `GET /api/taxonomy` and optional query filters on `GET /api/missions` (paramless path delegates to the existing `store.list_missions` call untouched); update the endpoint inventory in the server.py module docstring — makes T017–T018 pass

### GUI for User Story 2

- [X] T020 [P] [US2] Add taxonomy types and fetchers in app/studio/src/types.ts and app/studio/src/api.ts: `fetchTaxonomy()`, filtered mission listing; Vitest in app/studio/src/api.test.ts
- [X] T021 [US2] Create app/studio/src/components/TaxonomyBrowser.tsx — grouped history (group-by-client default, group-by-campaign toggle, drill-down to the existing mission list/detail) — and mount it in the history area of app/studio/src/App.tsx; wire `<datalist>` suggestions from the taxonomy tree into the US1 start-form inputs
- [X] T022 [US2] Write Vitest coverage in app/studio/src/components/TaxonomyBrowser.test.tsx: grouping renders both modes, drill-down filters, empty taxonomy renders an empty state

**Checkpoint**: US1 + US2 — history browsable by client and by campaign; flat feed untouched.

---

## Phase 5: User Story 3 — Existing history folds in untouched (Priority: P3)

**Goal**: Every pre-Brick-6 mission appears under its derived default project with historical files byte-identical; the override registry re-assigns any mission without touching its record.

**Independent Test**: Fixture tmp store of pre-Brick-6 dossiers (stamped, stamp-less, corrupt); SHA-256 snapshot; browse tree + filters + assign round-trip; every hash unchanged, every readable mission appears exactly once, stamp-less under "Unassigned".

### Tests for User Story 3 (write first, must fail) ⚠️

- [X] T023 [P] [US3] Write the failing migration fixture test in tests/test_server_taxonomy.py: build pre-Brick-6 dossiers in the tmp store (with `project_root` stamp, without stamp, one corrupt file), snapshot SHA-256 of every store file, exercise `GET /api/taxonomy` + filtered and paramless `GET /api/missions` + `GET /api/mission/{id}`, then assert all hashes unchanged (SC-003), every readable mission in exactly one project (SC-002), stamped ⇒ workspace-named default project under "Studio", stamp-less ⇒ "Unassigned"
- [X] T024 [P] [US3] Write failing server tests in tests/test_server_taxonomy.py for POST /api/mission/{id}/assign: set (subset of levels) and `{"clear": true}` round-trip with post-change attribution in the response; 404 for unknown/corrupt/out-of-workspace mission (opaque, like GET-by-id); 400 for invalid values or a body that is neither set nor clear; the ONLY file written is `taxonomy.json` (dossier hashes unchanged through re-assignment) (contracts/taxonomy-api.md §4)

### Implementation for User Story 3

- [X] T025 [US3] Implement `POST /api/mission/{id}/assign` in agency_studio/server.py (same workspace confinement as `_load_scoped_dossier`; registry-only write via taxonomy module) — makes T023–T024 pass
- [X] T026 [P] [US3] Add `assignMission(id, attribution | clear)` to app/studio/src/api.ts with Vitest in app/studio/src/api.test.ts
- [X] T027 [US3] Add a re-assign action (move mission to client/project/campaign, and clear-override) to app/studio/src/components/TaxonomyBrowser.tsx, with coverage in TaxonomyBrowser.test.tsx

**Checkpoint**: All three stories functional — taxonomy total over old and new missions, history files untouched.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T028 [P] Documentation: describe the taxonomy (fields, endpoints, registry file, resolution order) wherever the studio's API/user docs live (README.md section; confirm no other endpoint inventory besides the server.py docstring already updated in T019); English-only per Constitution XI
- [X] T029 Full offline gates on the finished brick: `pytest` at repo root, then `cd app/studio && npm test && npm run build` — all green with no network/CLI/GPU
- [X] T030 Execute the quickstart.md manual walkthrough end-to-end (real mission optional/deferrable per the Brick 5 precedent — record what was exercised in the PR description)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: none — start immediately
- **Phase 2 (Foundational)**: after T001 — BLOCKS all user stories
- **Phase 3 (US1)**: after Phase 2
- **Phase 4 (US2)**: after Phase 2; independent of US1 for the API/tree (only the datalist wiring in T021 touches the US1 form — if US1 is skipped, ship T021 without that wiring)
- **Phase 5 (US3)**: after Phase 2; T023 additionally needs US2's endpoints (T019); T027 needs US2's browser (T021)
- **Phase 6 (Polish)**: after all desired stories

### Within phases

- Tests before implementation, failing first: T002–T004 → T005; T006 → T007; T008–T009 → T010–T011; T015 → T016; T017–T018 → T019; T023–T024 → T025
- Backend before GUI within each story (the GUI consumes the endpoints)
- server.py tasks are sequential across stories (same file): T010/T011 → T019 → T025

### Parallel Opportunities

- Phase 2: T002, T003, T004 together (same new test file but independent test classes — split among agents only if coordinating appends; otherwise sequential is fine), then T005
- US1: T008 ∥ T009; then T010 → T011 while T012 runs in parallel (frontend files)
- US2: T017 ∥ T018 ∥ T015; T020 ∥ T019
- US3: T023 ∥ T024; T026 ∥ T025
- Frontend and backend tracks parallelize throughout (different file sets)

## Parallel Example: User Story 2

```bash
# After Phase 2 — launch the failing-test tasks together:
Task: "T015 unit tests for tree builder in tests/test_taxonomy.py"
Task: "T017 server tests for GET /api/taxonomy in tests/test_server_taxonomy.py"
Task: "T018 server tests for GET /api/missions filters in tests/test_server_taxonomy.py"

# Then implementation in two parallel tracks:
Task: "T016 + T019 backend (taxonomy.py tree builder, server routes)"
Task: "T020 frontend api/types + tests"
```

## Implementation Strategy

**MVP first (US1)**: Phases 1–3, stop, validate independently (tagged dossier + unchanged untagged path), demo. **Incremental**: add US2 (browsable history — the done-when's visible half), then US3 (migration proof + re-assign). Each story lands additive and revertible (Constitution X); commit after each task or logical group; suite green at every checkpoint.

## Notes

- Offline discipline: all server tests monkeypatch `runner_bridge.run` and redirect the store to a tmp path (existing `tests/test_server*.py` patterns); no test touches `~/.agency`
- Byte-identity is asserted with SHA-256 snapshots, not mtimes
- No task edits `agencykit/` or `openmontage/` (Constitution V); `agency_kit.store` is consumed via its public API only
