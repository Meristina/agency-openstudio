# Implementation Plan: Clients & Projects (Brick 6)

**Branch**: `006-clients-projects` | **Date**: 2026-07-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-clients-projects/spec.md`

## Summary

Layer a client → project → campaign taxonomy ABOVE the existing mission store
without touching it: a new stdlib-only studio module (`agency_studio/taxonomy.py`)
resolves every mission's attribution in a fixed order — side-band override >
taxonomy fields carried by the mission's own dossier > default derived from the
existing `project_root` stamp (project = workspace directory name, client
"Studio", stamp-less → "Unassigned"). New missions get their tags merged into
their own dossier by the server after completion (a new write — historical
dossiers are never rewritten); re-assignment lives in a side-band override
registry (`~/.agency/taxonomy.json`). The server gains `GET /api/taxonomy`
(workspace-scoped tree with counts), optional `client`/`project`/`campaign`
filters on `GET /api/missions`, and `POST /api/mission/{id}/assign`; the GUI
gains three optional inputs on the mission-start form and grouped browsing in
history. Zero agencykit changes; `agency_kit.store` is used read-only plus its
public `save()` for the mission's own record.

## Technical Context

**Language/Version**: Python 3.11+ (stdlib-only server core); TypeScript / React 18 + Vite (GUI)

**Primary Dependencies**: None new. Backend: Python stdlib + `agency_kit.store` (the one permitted imported library, used via its existing public API only). Frontend: existing React/Vite toolchain.

**Storage**: JSON files. Existing: `~/.agency/missions/<id>/dossier.json` (untouched for historical missions; new missions gain three optional fields via a post-completion re-save of their own record). New: `~/.agency/taxonomy.json` — side-band registry holding per-mission overrides and display-name canonicalization, written atomically (tmp + rename).

**Testing**: `pytest` (repo-root `tests/`, fully offline — store faked onto a tmp path, no network/CLI/Node/GPU); Vitest for `app/studio/src` component/api tests.

**Target Platform**: Local single-user server on `127.0.0.1` — macOS, Linux, Windows.

**Project Type**: Web application (stdlib HTTP/SSE backend + React frontend) — extends the existing `agency_studio/` + `app/studio/` pair.

**Performance Goals**: Taxonomy tree and filtered listings scan the local store in memory (same pattern as `store.list_missions`); instant (<100 ms) for the realistic local scale of hundreds-to-low-thousands of missions.

**Constraints**: Offline-by-default (no network paths added); zero new runtime dependencies; additive-only — with no taxonomy input and no query params, every existing surface behaves byte-identically; historical dossier files byte-identical forever (verified by the migration test); no edits under `agencykit/` or `openmontage/`.

**Scale/Scope**: 1 new backend module, 1 modified backend module (server routes/payload), ~3 GUI files touched + 1 new component, 2 new offline test modules + 1 pre-Brick-6 fixture set, 2 new endpoints + 1 extended endpoint.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — taxonomy is pure metadata
  organization; no reasoning path is added or altered, no API calls of any kind.
- [x] **II. Engine neutrality**: N/A — no engine-facing behavior; the mission
  loop and Engine contract are untouched.
- [x] **III. No invented information**: PASS — research, citation, and the
  inspector veto loop are untouched (FR-009); taxonomy never alters deliverable
  content.
- [x] **IV. Local-first & offline-by-default**: PASS — everything is local JSON;
  no network access is introduced anywhere.
- [x] **V. Subprocess boundaries**: PASS — zero edits under `agencykit/` /
  `openmontage/`; the studio consumes `agency_kit.store`'s existing public API
  (`missions_path`, `load`, `save`, `mission_in_project`, `canonical_project_root`),
  which is the permitted import.
- [x] **VI. Security**: PASS — new routes ride the existing loopback-bound
  server; no static file serving added (no new `path_inside` surface), no CORS
  change, no outbound requests, no keys. Assign/read endpoints enforce the same
  workspace scoping as existing history routes.
- [x] **VII. Offline tests**: PASS — all new behavior covered in `tests/` with
  the store redirected to a tmp dir; migration fixture test asserts byte-identity
  of pre-Brick-6 dossiers (FR-011); Vitest covers the GUI additions.
- [x] **VIII. End-user simplicity**: PASS — three optional, suggestion-assisted
  fields on the existing start form; grouped history browsing in the GUI
  (FR-012); no terminal required; defaults need zero input.
- [x] **IX. License**: PASS — no new/reused components; nothing to add to
  `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — optional payload fields defaulting
  to absent, optional query params defaulting to the existing listing, new
  endpoints only; with the feature unused, behavior is byte-identical; veto loop
  untouched.
- [x] **XI. English everywhere**: PASS — all artifacts and code in English.

**Post-Phase-1 re-check (2026-07-05)**: design artifacts (data-model, contracts,
quickstart) introduce no new violations — all gates hold as above.

## Project Structure

### Documentation (this feature)

```text
specs/006-clients-projects/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── taxonomy-api.md  # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
agency_studio/
├── taxonomy.py          # NEW — normalization, resolution order, registry IO, store scan
└── server.py            # MODIFIED — payload fields, 2 new routes, filter params,
                         #   post-completion tag merge, checkpoint envelope carries tags

app/studio/src/
├── App.tsx              # MODIFIED — mission-start form: client/project/campaign inputs
├── api.ts               # MODIFIED — taxonomy fetch/assign + typed payload additions
├── types.ts             # MODIFIED — taxonomy types
└── components/
    ├── TaxonomyBrowser.tsx        # NEW — grouped history (by client / by campaign)
    └── TaxonomyBrowser.test.tsx   # NEW — Vitest coverage

tests/
├── test_taxonomy.py             # NEW — unit: normalization, resolution, registry IO
├── test_server_taxonomy.py      # NEW — endpoints, tagging flow, migration fixture,
│                                #   byte-identity assertion
└── (fixtures built in-test: pre-Brick-6 dossiers written to the tmp store)
```

**Structure Decision**: Extend the existing web-application pair — stdlib backend
in `agency_studio/`, React frontend in `app/studio/src/` — with one new backend
module and one new frontend component. No new top-level directories; vendored
subtrees untouched.

## Complexity Tracking

No constitution violations — table intentionally empty.
