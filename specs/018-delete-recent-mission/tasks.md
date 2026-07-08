---
description: "Task list for: Delete a recent mission from the home list"
---

# Tasks: Delete a recent mission from the home list

**Input**: Design documents from `specs/018-delete-recent-mission/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/delete-mission.md

**Tests**: MANDATORY (Constitution VII) — every code change ships offline tests (store dir
monkeypatched, `fetch` mocked; no network/CLI/Node beyond vitest/GPU).

**Organization**: grouped by user story (US1 P1, US2 P2, US3 P3) for independent delivery.

## Format: `[ID] [P?] [Story] Description`

- **[P]** = parallelizable (different file, no incomplete dependency)
- Paths are repo-relative and exact.

---

## Phase 1: Setup

- [X] T001 Add shared i18n keys for the delete flow in `app/studio/src/i18n/en.ts` and `app/studio/src/i18n/fr.ts`: `home.recent.delete` (button label), `home.recent.deleteConfirm` (confirm prompt), `home.recent.deleteConfirmYes`, `home.recent.deleteConfirmCancel`, `home.recent.deleteError`. Keep the two catalogs key-parallel (the catalog parity test must stay green).

---

## Phase 2: Foundational (blocking prerequisites for all stories)

The backend delete capability + API client every story builds on. MUST complete before Phase 3.

- [X] T002 [P] Add `delete(mission_id: str) -> bool` to `agencykit/agency_kit/store.py`: resolve `path_inside(missions_dir(), mission_id)`; if the guard fails return `False` (never touch the filesystem); `shutil.rmtree` the directory if present; return `True` when a directory was removed, `False` when already absent (idempotent). Mirror the safety of the checkpoint delete.
- [X] T003 [P] Add `store.delete` unit tests in `agencykit/tests/test_store.py` (create if absent): deletes an existing mission dir (monkeypatch `store.missions_dir` → `tmp_path`); idempotent for a missing id; a traversal id (`../x`, absolute) is refused and touches nothing.
- [X] T004 Add `_handle_delete_mission` + a `path.startswith("/api/mission/")` branch in `do_DELETE` in `agency_studio/server.py`, mirroring `_handle_delete_checkpoint`: validate/normalize the id, call `store.delete`, respond `204` on removal and `404` on unknown/unsafe id; document the route in the module header. (Depends on T002.)
- [X] T005 Add delete-mission endpoint tests in `tests/test_server.py`, mirroring `test_list_and_delete_checkpoints_endpoints` + the `_delete` helper: `204` on delete, `404` on unknown/traversal id, idempotent second delete, store dir monkeypatched to `tmp_path`. (Depends on T004.)
- [X] T006 [P] Add `deleteMission(id: string): Promise<void>` to `app/studio/src/api.ts`: `fetch(\`/api/mission/${encodeURIComponent(id)}\`, { method: "DELETE" })`; resolve on `res.ok || res.status === 404` (both mean "gone"); throw `errorText` otherwise. Mirror `deleteDocument`/`deleteVisual`.

**Checkpoint**: backend + client can delete a mission (verify via the `quickstart.md` curl calls).

---

## Phase 3: User Story 1 — Remove an unwanted item from Recent work (Priority: P1) 🎯 MVP

**Goal**: From the Recent work list the user removes a saved mission and it disappears.

**Independent test**: Render `ResumeSection` with several delivered items, delete one, assert it
is removed from the list and the others remain; a failed delete leaves the item and shows an error.

- [X] T007 [US1] In `app/studio/src/screens/home/ResumeSection.tsx`, add a delete control per recent item, visually/semantically distinct from the open button, with an accessible label (`home.recent.delete`). Show it only for saved (terminal) items — not the live-followed item (FR-008), using the live/saved distinction already in `recentMissionsView`.
- [X] T008 [US1] Wire the delete control to call `deleteMission(item.key)`; on success remove the item from local state so the list updates without a reload (FR-004); on failure keep the item and render `home.recent.deleteError` (FR-006). If the followed/resume pointer references the deleted id, clear it via the follow-pointer `clear()` (FR-007).
- [X] T009 [US1] Extend `app/studio/src/screens/home/ResumeSection.test.tsx`: mock `deleteMission`; deleting an item removes it from the rendered list and leaves the others; a rejected `deleteMission` keeps the item and shows the error; the delete control is absent for a live item. Labels asserted in EN and FR.

**Checkpoint**: US1 delivers the core decluttering value on its own.

---

## Phase 4: User Story 2 — Guard against accidental deletion (Priority: P2)

**Goal**: No mission is removed without an explicit confirmation the user can cancel.

**Independent test**: Activate delete → cancel → item untouched and `deleteMission` never called;
activate delete → confirm → `deleteMission` called once and the item removed.

- [X] T010 [US2] In `ResumeSection.tsx`, gate the delete request behind an inline confirmation (confirm/cancel) using `home.recent.deleteConfirm` / `...Yes` / `...Cancel`; only "confirm" calls `deleteMission`. Keyboard/AT accessible (focusable controls, Escape cancels) per Art. VIII.
- [X] T011 [US2] Extend `ResumeSection.test.tsx`: activating delete then cancelling leaves the item and asserts `deleteMission` was NOT called; activating then confirming calls `deleteMission` exactly once and removes the item; confirmation strings present in EN and FR.

**Checkpoint**: deletion is safe — single misclicks cannot destroy work.

---

## Phase 5: User Story 3 — Deletion is consistent everywhere (Priority: P3)

**Goal**: A mission deleted from Recent work is also absent from the Library and any saved-missions listing.

**Independent test**: After a delete, the missions listing consumed by the Library no longer
includes the deleted mission.

- [X] T012 [US3] Add a consistency test in `tests/test_server.py`: create two saved missions, `DELETE /api/mission/{id}` one, then `GET /api/missions` returns only the remaining mission (the same listing the Library reads) — proving removal propagates to every surface (FR-005) with no separate index.
- [X] T013 [P] [US3] Consistency into the Library: covered by design + T012 rather than a new test. `DeliverableLibrary` consumes the same `listMissions()` → `GET /api/missions` that T012 proves excludes a deleted mission, so a dedicated frontend test ("a mission absent from the input list is absent from the output of a pure mapping function") would be tautological bloat. US3's acceptance is fully met by the real-server T012 + the shared endpoint. No frontend test added — intentionally.

**Checkpoint**: no confusing "deleted here but still there" state.

---

## Phase 6: Polish & cross-cutting

- [X] T014 Run the full offline suites and gates: `pytest tests/ -q` (studio) + `cd agencykit && pytest -q` + `cd app/studio && npm run test && npm run typecheck`. All green.
- [X] T015 [P] End-to-end coverage: the backend path is exercised by a **real HTTP server** test (`_start` + real `DELETE` → 204 → `GET /api/missions` delisted) and the GUI flow by real-component tests (ResumeSection render + confirm/cancel/error/FR-EN labels + `expectNamedInteractives` a11y). The manual browser walk in `quickstart.md` remains available to run against a live `agency-studio` (not executed headlessly here).

---

## Dependencies & execution order

- **Setup (T001)** → no code dependency; can run first or alongside foundational.
- **Foundational (T002–T006)** blocks all stories. Order: T002 → (T003, T004); T004 → T005; T006 independent.
- **US1 (T007–T009)** depends on Foundational (needs `deleteMission` + endpoint). MVP.
- **US2 (T010–T011)** depends on US1 (wraps the delete control with confirmation).
- **US3 (T012–T013)** depends on Foundational (T012 needs the endpoint); independent of US1/US2 UI.
- **Polish (T014–T015)** last.

Story order: **US1 → US2 → US3** (P1 → P2 → P3).

## Parallel opportunities

- Foundational: **T002** (store) ∥ **T006** (api client) — different files, no shared dep. **T003** (store test) starts once T002 lands.
- Across stories once Foundational is done: **US3/T012** (backend consistency test) can proceed in parallel with **US1** UI work (different files).
- **T013** [P] and **T015** [P] are independent of other same-phase tasks.

## Independent test criteria (per story)

- **US1**: delete one item from a rendered Recent work list → it's gone, others remain; failure path keeps it + error.
- **US2**: cancel → no delete/no request; confirm → exactly one delete + removal.
- **US3**: `GET /api/missions` (Library's source) excludes a deleted mission.

## Suggested MVP

**US1 only** (T001–T009): a working, tested delete from the home Recent work list — the whole
user request in its smallest safe form. US2 (confirmation hardening) and US3 (consistency proof)
layer on next.

## Format validation

All 15 tasks use `- [ ] Txxx [P?] [Story?] description + file path`; Setup/Foundational/Polish
carry no story label; US phases carry `[US1]`/`[US2]`/`[US3]`; every task names an exact file.
