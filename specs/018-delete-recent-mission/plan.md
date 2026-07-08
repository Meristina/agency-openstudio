# Implementation Plan: Delete a recent mission from the home list

**Branch**: `018-delete-recent-mission` | **Date**: 2026-07-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/018-delete-recent-mission/spec.md`

## Summary

Add a per-item **delete** control to the studio home's Recent work list so a user can
permanently remove a saved mission they no longer want, behind an explicit confirmation. The
delete is a thin, additive slice over the existing saved-mission store: a new
`DELETE /api/mission/{id}` endpoint backed by a new `store.delete(mission_id)`, plus a delete
button + confirmation in `ResumeSection`. Because Recent work and the Library both read
`GET /api/missions`, removal from the one store makes the mission disappear everywhere on next
load. The whole surface mirrors the already-shipped `DELETE /api/checkpoints/{id}` pattern
(id validation → `path_inside` guard → 204/404, idempotent).

## Technical Context

**Language/Version**: Python 3.12 (studio server, stdlib-only) · TypeScript / React 19 + Vite (GUI)

**Primary Dependencies**: none new — Python stdlib `http.server`; `agency_kit.store` (the
vendored agency-kit fork, editable-installed) for the mission store; existing frontend `api.ts`
fetch layer.

**Storage**: filesystem mission store at `~/.agency/missions/<mission_id>/` (written by
`store.save`, read by `store.list_missions` → `GET /api/missions`). Deletion removes that
per-mission directory via `path_inside(store.missions_dir(), mission_id)`.

**Testing**: `pytest` (studio `tests/test_server.py` + agencykit `tests/` for `store.delete`),
fully offline (store dir monkeypatched to `tmp_path`, no network); `vitest` for the GUI.

**Target Platform**: local-first desktop studio, server bound to `127.0.0.1:8765`, cross-platform.

**Project Type**: web application (Python stdlib backend + React/Vite frontend) wrapping the
agency-kit brain.

**Performance Goals**: interactive — a delete completes and the item disappears within one
list-refresh cycle; no measurable impact on the mission loop (delete never touches it).

**Constraints**: no `Access-Control-Allow-Origin: *`, `127.0.0.1` only, `path_inside()` on the
deleted path (traversal defense), zero new runtime dependencies, offline-testable.

**Scale/Scope**: small — one endpoint, one store function, one GUI control + confirmation,
EN/FR strings, and their tests. Bulk "clear all" is out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md`. This is a studio GUI + local-storage
feature; it never touches the mission loop, engines, or research/inspection.

- [x] **I. Brain = subscription CLI agents**: N/A — no reasoning path; deletion is a local file
  operation, no engine call.
- [x] **II. Engine neutrality**: N/A — no engine involvement.
- [x] **III. No invented information**: N/A — not mission-facing content; deletion does not touch
  research, citations, or the inspector veto.
- [x] **IV. Local-first & offline-by-default**: PASS — pure local filesystem deletion; no network.
- [x] **V. Subprocess boundaries**: PASS — no `openmontage/` import; `store.delete` is added to
  `agency_kit.store`, the one imported library (edited normally, editable install).
- [x] **VI. Security**: PASS — DELETE keyed by mission id, guarded by `path_inside(missions_dir,
  id)` (mirrors the checkpoint-delete traversal defense); `127.0.0.1` only, no CORS `*`, no keys
  touched.
- [x] **VII. Offline tests**: PASS — endpoint + store tests monkeypatch the store dir to
  `tmp_path`; GUI tests are vitest; no network/CLI/Node/GPU.
- [x] **VIII. End-user simplicity**: PASS — one obvious delete control + a plain-language
  confirmation, bilingual EN/FR, keyboard/AT accessible.
- [x] **IX. License**: PASS — no new components/dependencies; nothing to record in
  `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — new endpoint + new store function + new GUI control;
  existing `GET`/`POST` mission routes and the veto loop are byte-identical.
- [x] **XI. English everywhere**: PASS — code/docs/commits in English; user-facing UI strings are
  product i18n (EN + FR), not source language.

**Result**: all gates PASS / N/A — no Complexity Tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/018-delete-recent-mission/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (store target, idempotency, confirmation UX)
├── data-model.md        # Phase 1 — entities (saved mission, follow pointer)
├── quickstart.md        # Phase 1 — how to exercise the delete end-to-end
├── contracts/
│   └── delete-mission.md  # DELETE /api/mission/{id} contract
├── checklists/
│   └── requirements.md  # spec quality checklist (done)
└── tasks.md             # Phase 2 — /speckit-tasks (NOT created here)
```

### Source Code (repository root)

```text
agencykit/agency_kit/
└── store.py                         # + delete(mission_id): path_inside guard, idempotent rmtree

agencykit/tests/
└── test_store.py                    # + store.delete unit tests (idempotent, path-safe)   [new or extend]

agency_studio/
└── server.py                        # + DELETE /api/mission/{id} branch in do_DELETE
                                     #   + _handle_delete_mission (mirrors _handle_delete_checkpoint)

tests/
└── test_server.py                   # + delete-mission endpoint tests (204/404/idempotent/traversal)

app/studio/src/
├── api.ts                           # + deleteMission(id): DELETE /api/mission/{id}
├── screens/home/ResumeSection.tsx   # + delete control + confirmation + local list removal
├── screens/home/homeModel.ts        # (RecentMissionItem already carries mission_id as `key`)
├── i18n/en.ts, i18n/fr.ts           # + home.recent.delete / .confirm strings
└── screens/home/ResumeSection.test.tsx  # + delete button + confirm + removal tests
```

**Structure Decision**: Web application — the existing split of Python stdlib backend
(`agency_studio/`), the vendored brain (`agencykit/agency_kit/store.py`), and the React GUI
(`app/studio/`). The feature adds one endpoint, one store function, and one GUI control across
those three, with no new module or layer.

## Complexity Tracking

> No Constitution violations — this section intentionally empty.
