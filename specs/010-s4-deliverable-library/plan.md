# Implementation Plan: Deliverable Library — The Permanent Home for Everything the Agency Has Produced (Brick 7 · Screen S4)

**Branch**: `010-s4-deliverable-library` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-s4-deliverable-library/spec.md`

## Summary

S4 replaces the `#/library` coming-soon placeholder with the Deliverable Library screen:
the operator-facing shelf where every **finished** production is found again, organized by
the Brick 6 **client → project → campaign** taxonomy (with an **unassigned** shelf), long
after the run that made it. It is a **pure presentation + organization layer** over
infrastructure that already exists — it reuses the existing mission client
(`listMissions({client,project,campaign})`, `fetchTaxonomy`, `assignMission`,
`getMission`, `fetchMissionPdf` in `api.ts`), the shell's client-context selector
(`useClientContext()`), and the existing dossier renderer (`components/MissionDetail`
with its `AssetGallery` media) — and adds a **library projection** that turns the flat
`MissionSummary[]` into grouped, searchable, outcome-classified deliverable cards, an
**in-place preview**, and the everyday **non-destructive** per-deliverable actions
(open full detail · download PDF · file/refile in the taxonomy).

The developer console already carries a raw equivalent (`components/TaxonomyBrowser`); S4
does **not** touch it — S4 is the plain-language, WCAG 2.1 AA, operator surface built from
the same endpoints, phrased with zero machinery terms. It is also the permanent
destination for the S3 Mission Timeline completion hand-off (which today points at the
interim `MissionDetail` view): once S4 ships, a finished run lands in its library home.

Technically: a new self-contained `screens/library/` module in the React 19 + Vite app
(`app/studio/`), new `library.*` EN/FR catalog keys, and five declared integration edits
(router status flip `placeholder → shipped`, Shell `Outlet` mount, placeholder-list
removal, i18n catalog additions, and re-pointing the S3 `TerminalPanel` completion
hand-off from the interim `#/console` to the Library deep-link — FR-017/SC-007). **Zero
server changes, zero new dependencies**: grouping,
search, outcome-filter, and per-mission dedup are pure functions over the existing
`MissionSummary[]`; filing reuses the existing `POST /api/mission/{id}/assign`; open/PDF
reuse the existing `getMission` / `fetchMissionPdf`. Non-destructive by clarification —
**no delete** in v1.

## Technical Context

**Language/Version**: TypeScript ~5.7 (frontend only); Python 3.11+ server **unchanged**.

**Primary Dependencies**: React 19, Vite 6, react-markdown (all pre-existing, via the reused `MissionDetail`). **Zero new runtime or dev dependencies** — the library projection (group / search / outcome-classify / dedup) is a pure function over the existing `MissionSummary[]`.

**Storage**: None added. The Library reads durable dossiers via the existing `GET /api/missions` (+ taxonomy filters) and mutates only taxonomy attachment via the existing `POST /api/mission/{id}/assign`. View state (query, outcome filter) is ephemeral React state; the active client context comes from the shell's existing `localStorage`-backed selector. No new persisted field, no new store.

**Testing**: Vitest 3 + @testing-library/react + jsdom (existing setup), `listMissions` / `fetchTaxonomy` / `assignMission` / `getMission` / `fetchMissionPdf` mocked via the existing `api.ts` test doubles; root `pytest` suite untouched and stays green (server not modified).

**Target Platform**: Desktop browser on the operator's machine, served by the local stdlib server at `127.0.0.1` from `app/studio/dist` (existing static route).

**Project Type**: Web application frontend feature (one inventoried screen) over the existing local HTTP server.

**Performance Goals**: Group/search/filter over the full finished-mission set resolves within one render frame (< ~100 ms; pure local fold, no per-keystroke network) for the expected local single-user volume (tens–low hundreds of missions); opening a deliverable reflects its detail within one frame of `getMission` returning; filing reflects the new shelf placement within one frame of `assignMission` returning.

**Constraints**: Constitution I–XI; umbrella cross-cutting rules (i18n catalogs, design system + WCAG 2.1 AA incl. keyboard-operable grouping/preview/actions and screen-reader labels, shared loading/empty/error/connection states, tone of voice — zero machinery terms); additive delivery — server and dev console (`TaxonomyBrowser`) byte-identical; spec clarifications (2026-07-06): **no delete** (non-destructive v1), **in-place preview + full open**, **dedupe by mission identity**, **load-all client-side** (no pagination).

**Scale/Scope**: 1 screen; group/search/outcome-filter/dedup projection over the `MissionSummary` fields; client-context-scoped grouping (client → project → campaign + unassigned); 3 per-deliverable actions (open / PDF / file); 2 outcome classes (successful / needs-attention); 2 locales (~40–60 new catalog keys); ~5–6 test files. No backend files touched.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — no reasoning path added; S4 only lists, groups, and renders dossiers the existing mission loop already produced; opening a deliverable delegates to the existing `getMission` load.
- [x] **II. Engine neutrality**: PASS — the library never names an engine; a deliverable's outcome is read from its stored verdict/delivery signals, engine-agnostic; the Engine contract and production-engine guard are untouched.
- [x] **III. No invented information**: PASS — S4 shows only what a finished run actually produced (its stored sources, decisions, assets, verdict); it fabricates no deliverable, outcome, or source, and neither performs nor weakens verification; the veto loop is untouched.
- [x] **IV. Local-first & offline-by-default**: PASS — presentation/organization-only, no new network behavior; list/detail/PDF/assign reuse existing local endpoints; no per-mission network opt-in is added or changed; no cloud call.
- [x] **V. Subprocess boundaries**: PASS — frontend-only; no `openmontage/` import, no subtree edits; the mission subprocess and store are driven by the unchanged server.
- [x] **VI. Security**: PASS — server byte-identical (bind/CORS/`path_inside()`/https-only unchanged); no secret entry or secret display; PDF/detail/assign go through the existing validated endpoints; source links inherit `MissionDetail`'s `isSafeHttpUrl` + `rel="noopener noreferrer"` hardening; no new persisted data.
- [x] **VII. Offline tests**: PASS — all new behavior covered by Vitest with mocked `listMissions`/`fetchTaxonomy`/`assignMission`/`getMission`/`fetchMissionPdf` (grouping, unassigned shelf, client-context scoping, search, outcome filter, dedup, preview, open, PDF success/failure, file/refile, empty & connection-lost states, a11y/keyboard); no network/CLI/live server. Root pytest suite unaffected.
- [x] **VIII. End-user simplicity**: PASS — S4 *is* the "find it again" promise: plain-language cards grouped like an agency thinks, no machinery terms (wording audit SC-004), keyboard-operable, one-step actions, friendly empty states, never a dead end.
- [x] **IX. License**: PASS — zero new components; nothing to add to `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — a placeholder route becomes a shipped screen (the umbrella's designed lifecycle); server, mission loop, store, veto loop, and the dev console's `TaxonomyBrowser` are untouched; the only mutation is taxonomy filing via the pre-existing assign endpoint; **no delete** path is introduced.
- [x] **XI. English everywhere**: PASS — code/docs/commits in English; operator-facing strings live only in the EN/FR end-user catalogs (explicitly permitted).

**Post-Phase-1 re-check (2026-07-06)**: design artifacts (research, data-model, contracts,
quickstart) confirm zero server changes, zero new dependencies, no engine/mission-loop/store
surface, a presentation+organization projection over the existing list, reuse of the
existing detail/PDF/assign endpoints, and a strictly non-destructive action set — all gates
hold as marked.

## Project Structure

### Documentation (this feature)

```text
specs/010-s4-deliverable-library/
├── spec.md              # Feature spec (clarified 2026-07-06)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── library-projection.md    # MissionSummary[] → grouped/searched/classified/deduped LibraryModel + catalog-key contract
│   └── actions-and-filing.md     # open/PDF/file per-deliverable actions over existing endpoints; non-destructive guarantee
├── checklists/
│   └── requirements.md  # Spec quality checklist (18/18)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
app/studio/src/
├── screens/
│   ├── missions/
│   │   └── TerminalPanel.tsx        # S3 (edited): completion hand-off re-pointed #/console → #/library?deliverable=<id> (FR-017/SC-007); rest byte-identical
│   ├── library/
│   │   ├── DeliverableLibrary.tsx  # Screen: loads listMissions + taxonomy, renders grouped shelves / search / outcome filter / empty / connection states; reads ?deliverable=<id> deep-link to auto-open (S3 hand-off)
│   │   ├── ShelfTree.tsx           # Grouped client → project → campaign shelves + unassigned shelf; renders DeliverableCard list
│   │   ├── DeliverableCard.tsx     # One deliverable: plain-language headline, date, outcome badge; triggers preview + actions
│   │   ├── DeliverablePreview.tsx  # In-place preview panel (headline, outcome, key sources/decisions, media thumbnails via AssetGallery) — no navigation
│   │   ├── DeliverableActions.tsx  # Open full detail · download PDF (progress + failure) · file/refile control (reuses assign path) — no delete
│   │   ├── FilingControl.tsx       # Plain-language attach/move-within-taxonomy / return-to-unassigned; reuses taxonomy from useClientContext
│   │   └── libraryModel.ts         # Pure projection: (MissionSummary[], scope, query, outcomeFilter) → LibraryModel; dedup by mission_id; outcome classifier
│   └── placeholders.tsx            # `library` entry removed (import, export, settings remain)
├── shell/
│   ├── router.ts                   # `library` route status: "placeholder" → "shipped"
│   └── Shell.tsx                   # Outlet: mount <DeliverableLibrary /> for route id "library"
├── components/
│   ├── MissionDetail.tsx           # REUSED as-is for the "open full detail" surface (dossier + PDF + AssetGallery) — not modified
│   └── AssetGallery.tsx            # REUSED as-is for preview media thumbnails — not modified
├── i18n/
│   ├── catalog.ts                  # + library.* typed keys (shelves, unassigned, outcomes, search, actions, preview, empty, states)
│   ├── en.ts                       # + EN strings (fallback source of truth)
│   └── fr.ts                       # + FR strings
└── api.ts                          # REUSED as-is: listMissions, fetchTaxonomy, assignMission, getMission, fetchMissionPdf

Co-located tests (existing convention):
├── screens/library/libraryModel.test.ts        # Grouping (client→project→campaign + unassigned), client-context scoping, search (desc + taxonomy), outcome classify/filter, dedup by mission_id, orphaned-attachment → unassigned
├── screens/library/DeliverableLibrary.test.tsx  # Load + render shelves, empty (first-run) & empty-for-context states, connection-lost, a11y/keyboard grouping
├── screens/library/DeliverablePreview.test.tsx  # In-place summary from a dossier, no-media case (no broken thumbnails), no navigation away
├── screens/library/DeliverableActions.test.tsx  # Open→detail, PDF success + graceful failure/hint, no delete action present
├── screens/library/FilingControl.test.tsx       # Attach unassigned, move mis-filed, return to unassigned; immediate reflect; reversible; plain feedback
├── screens/missions/TerminalPanel.test.tsx      # UPDATED: finished "view your deliverable" now targets #/library?deliverable=<id> (was #/console)
└── (existing MissionDetail.test.tsx / AssetGallery.test.tsx stay green — reused unchanged)

tests/                                            # Python suite — no changes (server untouched)
```

**Structure Decision**: one new self-contained module `screens/library/` inside the
existing frontend project, consuming the umbrella's shell/i18n/design-system layers, the
shell's `useClientContext()` selector, the existing `api.ts` client, and the existing
`components/MissionDetail` (+ `AssetGallery`) for the open-full-detail and preview-media
surfaces. The developer console's `components/TaxonomyBrowser` — the raw dev equivalent —
is left byte-identical; S4 is the operator-facing sibling, not its replacement. The only
edits outside the new module are the five declared integration points: the router status
flip, the Shell `Outlet` mount, the placeholder-list removal, the i18n catalog additions,
and the one-line re-point of the S3 `TerminalPanel` completion hand-off (`#/console` →
`#/library?deliverable=<id>`, closing FR-017/SC-007 — the interim target the S3 spec
explicitly earmarked for replacement when S4 ships). No backend directories are touched.

## Complexity Tracking

> No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
