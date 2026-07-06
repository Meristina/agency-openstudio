---

description: "Task list for S6 Export implementation"
---

# Tasks: Export — Turn Finished Work into Shareable Bundles (Brick 7 · Screen S6)

**Input**: Design documents from `/specs/012-s6-export/`

**Prerequisites**: plan.md, spec.md (clarified 2026-07-06), research.md, data-model.md, contracts/

**Tests**: MANDATORY per Constitution Principle VII — every code change ships offline tests (no
network, no CLI, no Node, no GPU; boundaries monkeypatched). `export_pdf` is monkeypatched in
bundler tests so WeasyPrint is not required.

**Organization**: Grouped by the two v1 user stories. Bulk per-client/campaign export (former US3)
is **deferred** (spec Clarifications) and generates no tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 (setup, foundational, polish carry no story label)

## Path Conventions

- Server (Python, stdlib core): `agency_studio/`, tests in `tests/` (root pytest)
- Frontend (React + Vite): `app/studio/src/`, co-located `*.test.ts(x)` (Vitest)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new module scaffolding and the base catalog namespace.

- [X] T001 Create the `screens/export/` module with empty files `Export.tsx`, `ExportPanel.tsx`, `FormatCard.tsx`, `exportModel.ts`, `download.ts` in `app/studio/src/screens/export/`
- [X] T002 [P] Add the base `export.*` catalog keys (screen title + shared loading/empty/empty-for-context/connection-lost state keys) as typed `CatalogKey`s in `app/studio/src/i18n/catalog.ts`, with EN entries in `app/studio/src/i18n/en.ts` and FR entries in `app/studio/src/i18n/fr.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Screen must render as a shipped route, and the shared pure model + download helper both
stories depend on must exist and be green.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [X] T003 Flip the `export` route in `app/studio/src/shell/router.ts`: `status` `"placeholder" → "shipped"` and `taxonomyScoped` `false → true`
- [X] T004 Mount `<Export />` for route id `"export"` in the `Outlet` of `app/studio/src/shell/Shell.tsx`, remove the `export` entry from `app/studio/src/screens/placeholders.tsx`, and update `app/studio/src/screens/placeholders.test.tsx` to expect only `settings`
- [X] T005 [P] Write offline tests (tests-first) in `app/studio/src/screens/export/exportModel.test.ts`: `availableFormats` derivation, `hasMedia` gating (assets present/absent → `no-media-to-pack`), `contentsDescription` keys, `friendlyFilename`, single-deliverable scope
- [X] T006 [P] Write offline tests (tests-first) in `app/studio/src/screens/export/download.test.ts`: Blob → download filename from `Content-Disposition`, and 501/404/500 surfaced as catchable errors
- [X] T007 [P] Implement the pure model `app/studio/src/screens/export/exportModel.ts` (`availableFormats`, `hasMedia` gating from the dossier `assets` manifest, `contentsDescription`, `friendlyFilename`) — no I/O, deterministic (makes T005 pass)
- [X] T008 [P] Implement `app/studio/src/screens/export/download.ts` (`downloadBlob(blob, filename)`; prefers server `Content-Disposition` filename, falls back to `friendlyFilename`; browser APIs only, no new dependency) (makes T006 pass)

**Checkpoint**: Export renders as a shipped screen; shared model + download helper green.

---

## Phase 3: User Story 1 - Turn a finished deliverable into a shareable file (Priority: P1) 🎯 MVP

**Goal**: From Export, pick a **finished** deliverable, choose a format — **document (PDF)** or
**media pack (zip)** — see plain progress/confirmation, and download it; with capability-absent
(501), no-media disabling, only-finished offering, and friendly empty states. (The full dossier
bundle is US2.)

**Independent Test**: With finished deliverables (one with media, one without), export the document
and the media pack and confirm each downloads and opens off the studio; confirm a media-less
deliverable disables the media pack with "no media to pack"; confirm a `[pdf]`-absent env shows
"not available — how to enable" for the document while the media pack still works; confirm a
running/failed mission is not offered; confirm the friendly empty state.

### Tests for User Story 1 (offline, tests-first) ⚠️

- [X] T009 [P] [US1] Write `tests/test_bundler.py` for `build_media_zip(mission_id, assets_root)`: correct entries, sanitized relative arcnames, `path_inside` confinement (a planted out-of-tree/symlinked file is excluded), and empty/absent media root → "no media" signal
- [X] T010 [P] [US1] Extend `tests/test_server.py` for `GET /api/mission/{id}/media.zip`: route dispatch, scope confinement (foreign/corrupt mission → 404), `application/zip` + `Content-Disposition`, and no-media → 404
- [X] T011 [P] [US1] Write `app/studio/src/screens/export/Export.test.tsx`: lists finished deliverables scoped by client context, only-finished offered, empty (first-run) / empty-for-context / connection-lost states, a11y/keyboard
- [X] T012 [P] [US1] Write `app/studio/src/screens/export/ExportPanel.test.tsx` (document + media pack): choose format, produce + download (mocked `fetchMissionPdf` / `fetchMissionMediaZip`), progress + ready confirmation; media pack disabled when no media; 501 → capability-absent (that format only); 500 → plain retry

### Implementation for User Story 1

- [X] T013 [US1] Add `fetchMissionMediaZip(id, signal?)` to `app/studio/src/api.ts` — `fetch → Blob`, throws on non-`ok` (mirrors the existing `fetchMissionPdf`) (makes T012's media-pack path pass)
- [X] T014 [P] [US1] Implement `build_media_zip(mission_id, assets_root)` in `agency_studio/bundler.py` (new, stdlib `zipfile`): walk `assets_root/missions/<id>/`, add each file only after `path_inside(assets_root, …)`, sanitized relative arcname, stream into a temp file, signal "no media" when empty; read-only, no dossier mutation (makes T009 pass)
- [X] T015 [US1] Add `_handle_mission_media_zip(mission_id)` + its `_route_get` dispatch line in `agency_studio/server.py`, mirroring `_handle_mission_pdf`: `_safe_mission_id`, `_load_scoped_dossier` (404 on foreign/corrupt), `bundler.build_media_zip`, stream via `_send_bytes(body, "application/zip", extra_headers={"Content-Disposition": …})`, no-media → 404, packaging failure → generic 500 (makes T010 pass)
- [X] T016 [US1] Implement `app/studio/src/screens/export/Export.tsx`: list finished deliverables via the existing `listMissions` (scoped by `useClientContext()`), only-finished, empty/empty-for-context/connection-lost states, keyboard + screen-reader labels (makes T011 pass)
- [X] T017 [US1] Implement `app/studio/src/screens/export/ExportPanel.tsx` + `FormatCard.tsx` for the **document** and **media pack** formats: format chooser, produce → progress → download via `download.ts`, ready confirmation, capability-absent (501) state for that format, media-pack disabled when `hasMedia` is false, render/packaging-failure retry (makes T012 pass)
- [X] T018 [P] [US1] Add US1 `export.*` strings (document + media-pack format names, produce/download/progress/ready, capability-absent, no-media-to-pack, only-finished reason) to `app/studio/src/i18n/en.ts` and `app/studio/src/i18n/fr.ts`

**Checkpoint**: US1 MVP — a finished deliverable exports as a document or media pack and downloads.

---

## Phase 4: User Story 2 - Choose what goes in the bundle (Priority: P2)

**Goal**: Add the **full dossier bundle** (document + media + a human-readable sources list,
self-contained) and the plain-language **contents descriptions** for every format, so the operator
knows what they are handing over; handle media pruned since production gracefully.

**Independent Test**: With a finished deliverable that has content and media, review the
plain-language contents of each format, produce the full bundle, **stop the studio**, and confirm
the `.zip` is self-contained (readable deliverable + `media/` + `sources.md`, no raw dossier JSON);
confirm the deliverable is byte-for-byte unchanged in S4 afterward; confirm a media-pruned
deliverable still bundles gracefully with a plain note.

### Tests for User Story 2 (offline, tests-first) ⚠️

- [X] T019 [P] [US2] Extend `tests/test_bundler.py` for `build_bundle(mission_id, assets_root)` and `sources_markdown(dossier)`: bundle contains `deliverable.pdf` (via **monkeypatched** `export_pdf`), `media/…`, and `sources.md`; media-less mission → bundle without `media/`; `[pdf]` absent (monkeypatched `export_pdf` raising `ImportError`) propagates; `sources_markdown` from `dossier["sources"]`, empty sources → graceful line; input dossier unchanged (read-only); no raw `dossier.json` entry
- [X] T020 [P] [US2] Extend `tests/test_server.py` for `GET /api/mission/{id}/bundle.zip`: route dispatch, scope confinement (404), `application/zip` + `Content-Disposition`, `[pdf]` absent → 501 (install hint), no-deliverable → 404
- [X] T021 [P] [US2] Extend `app/studio/src/screens/export/ExportPanel.test.tsx` (bundle path): full-bundle produce + download (mocked `fetchMissionBundle`); plain-language contents description rendered for each of the three formats (FR-005); media-pruned graceful note

### Implementation for User Story 2

- [X] T022 [US2] Add `fetchMissionBundle(id, signal?)` to `app/studio/src/api.ts` — `fetch → Blob`, throws on non-`ok` (mirrors `fetchMissionPdf`) (makes T021 pass)
- [X] T023 [US2] Implement `sources_markdown(dossier)` and `build_bundle(mission_id, assets_root)` in `agency_studio/bundler.py`: `deliverable.pdf` via `agency_cli.exporter.export_pdf` (propagate `ImportError`/`OSError`), `media/…` via the confined walk from T014, `sources.md` from `dossier["sources"]` (verbatim, no URL resolution), no raw dossier snapshot (makes T019 pass)
- [X] T024 [US2] Add `_handle_mission_bundle(mission_id)` + its `_route_get` dispatch line in `agency_studio/server.py`, mirroring `_handle_mission_pdf`: scope via `_load_scoped_dossier`, `[pdf]` absent (`ImportError`) → 501 with install hint, no-deliverable → 404, failure → generic 500, stream `application/zip` + `Content-Disposition` (makes T020 pass)
- [X] T025 [US2] Extend `app/studio/src/screens/export/ExportPanel.tsx` + `FormatCard.tsx`: add the **full dossier bundle** format and render the plain-language contents description for all three formats (FR-005); add the media-pruned graceful note (makes T021 pass)
- [X] T026 [P] [US2] Add US2 `export.*` strings (full-bundle format name, per-format contents descriptions, media-pruned note) to `app/studio/src/i18n/en.ts` and `app/studio/src/i18n/fr.ts`

**Checkpoint**: US2 — full bundle + contents transparency; US1 (document + media pack) still works.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Verify the completeness, accessibility, security, and non-regression invariants.

- [X] T027 [P] Verify EN/FR completeness for all `export.*` keys (every key present in both catalogs, zero raw-key leaks) via the umbrella i18n completeness check (SC-004)
- [X] T028 [P] Accessibility pass across Export — choose-deliverable / choose-format / download fully keyboard-operable, screen-reader-labeled, AA contrast, visible focus (SC-005, FR-017)
- [X] T029 Run the full offline suite: root `pytest tests/` (bundler + server, `export_pdf` monkeypatched) and `npm run test -- src/screens/export` — all green with no network/CLI/Node-in-Python/GPU (Constitution VII, SC-006); confirm existing `/pdf` tests stay green (byte-identical)
- [X] T030 Run `npm run build` in `app/studio` — production build succeeds with the new module
- [ ] T031 Run the `quickstart.md` manual verification (SC-001…SC-009): read-only intact in S4 after export (FR-016), no outbound network on any export (FR-008/SC-007), foreign/bogus id → clean 404 and no out-of-tree file in any zip (FR-018), EN⇄FR chrome switch, and `[pdf]`-absent capability state (SC-008)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: depends on Setup — **BLOCKS both user stories** (screen must render; shared model + download helper must exist).
- **US1 (Phase 3)**: depends on Foundational. Delivers the MVP.
- **US2 (Phase 4)**: depends on Foundational; layers the full bundle onto US1's screen. `bundler.py` and `ExportPanel.tsx` are extended (US2 edits the same files US1 created — see Within-story order).
- **Polish (Phase 5)**: depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: independent — a working Export screen (document + media pack) with standalone value.
- **US2 (P2)**: builds on the same screen + `bundler.py`, but is independently testable (its own bundle endpoint, sources list, and contents descriptions). US1 remains functional without US2.

### Within Each User Story

- Tests (T009–T012, T019–T021) are written FIRST and must FAIL before implementation.
- Server: `bundler.py` function (T014 / T023) before its handler wiring (T015 / T024).
- Frontend: `api.ts` wrapper (T013 / T022) before the panel wiring that calls it (T017 / T025).
- i18n strings (T018 / T026) can land in parallel with their story's UI.

### File-contention notes (do NOT mark [P] across these)

- `agency_studio/bundler.py`: T014 (US1) creates it; T023 (US2) extends it → sequential.
- `agency_studio/server.py`: T015 (US1) and T024 (US2) both add a handler + route line → sequential.
- `app/studio/src/screens/export/ExportPanel.tsx`: T017 (US1) then T025 (US2) → sequential.
- `app/studio/src/api.ts`: T013 (US1) then T022 (US2) → sequential.
- `en.ts` / `fr.ts`: T002, T018, T026 all touch them → sequential within each file.

### Parallel Opportunities

- Setup: T002 [P] alongside T001.
- Foundational: T005 [P] + T006 [P] (tests) then T007 [P] + T008 [P] (impl, different files).
- US1 tests: T009 [P] + T010 [P] + T011 [P] + T012 [P] (different files).
- US1 impl: T014 [P] (bundler) and T018 [P] (i18n) run alongside the frontend/server wiring.
- US2 tests: T019 [P] + T020 [P] + T021 [P].
- Polish: T027 [P] + T028 [P].

---

## Parallel Example: User Story 1

```bash
# Tests first (all different files):
Task: "build_media_zip tests in tests/test_bundler.py"           # T009
Task: "media.zip endpoint tests in tests/test_server.py"          # T010
Task: "Export.test.tsx list/states/a11y"                          # T011
Task: "ExportPanel.test.tsx document + media pack"                # T012

# Then implementation (bundler + i18n parallel to wiring):
Task: "build_media_zip in agency_studio/bundler.py"               # T014 [P]
Task: "US1 export.* strings in en.ts + fr.ts"                     # T018 [P]
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational (screen renders) → 3. Phase 3 US1 → **STOP & VALIDATE**:
export a document and a media pack, confirm capability-absent / no-media / only-finished / empty
states. Ship the MVP.

### Incremental Delivery

1. Setup + Foundational → Export screen renders shipped.
2. US1 → document + media pack export → validate → demo (MVP).
3. US2 → full dossier bundle + contents transparency → validate → demo.
4. Polish → i18n/a11y/security/build/quickstart green.

### Constitution guardrails (apply to every server task)

- Bind `127.0.0.1` only, no CORS `*` (server unchanged on these).
- `path_inside()` on every packaged media file; sanitized zip arcnames (no `..`, no absolute).
- Scope every export via `_load_scoped_dossier` (foreign/corrupt → 404).
- Stdlib `zipfile` only — zero new runtime dependency; `agencykit/` subtree untouched (call `export_pdf`, never edit it).
- No secret read, packaged, logged, or surfaced; no outbound network; no mission-loop / store / saved-dossier change.

---

## Notes

- [P] = different files, no dependencies. Sequential where the File-contention notes say so.
- Tests are mandatory (Constitution VII) and written before implementation within each story.
- Bulk per-client/campaign export is **deferred** (spec Clarifications) — intentionally no tasks.
- Commit after each task or logical group; run the guard gate before presenting the change set.
