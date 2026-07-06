# Tasks: Deliverable Library — The Permanent Home for Everything the Agency Has Produced (Brick 7 · Screen S4)

**Input**: Design documents from `/specs/010-s4-deliverable-library/`

**Prerequisites**: plan.md, spec.md (clarified 2026-07-06), research.md (R1–R8), data-model.md, contracts/ (library-projection.md, actions-and-filing.md), quickstart.md

**Tests**: Per Constitution Principle VII, every code change ships offline tests (Vitest + @testing-library/react + jsdom, `listMissions`/`fetchTaxonomy`/`assignMission`/`getMission`/`fetchMissionPdf` mocked — no network, no CLI, no live server). Within each story, tests are written FIRST and must fail before implementation. The root `pytest` suite is untouched (zero server changes) and must stay green.

**Organization**: Tasks are grouped by user story (spec.md US1–US3) so each story is an independently testable increment. All paths are frontend (`app/studio/src/`) per plan.md — no files are touched outside the new `screens/library/` module and the five declared integration points (router, Shell mount, i18n trio, placeholders, and the S3 `TerminalPanel` completion hand-off re-point). `api.ts`, `components/MissionDetail.tsx`, and `components/AssetGallery.tsx` are reused unchanged; the dev console's `components/TaxonomyBrowser.tsx` stays byte-identical.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1–US3 from spec.md (user-story phases only)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module skeleton and i18n namespace that both foundational work and stories build on

- [X] T001 Create the library module skeleton: `app/studio/src/screens/library/libraryModel.ts` with the typed core only — `Deliverable`, `TaxonomyPlacement`, `DeliverablePreview`, `LibraryModel`, `Shelf`, `LibraryViewState`, `Outcome` (`"successful" | "needs-attention"`) shapes per data-model.md, and the `buildLibraryModel(...)` signature stubbed to return an empty model (`{ shelves: [], unassigned: [], total: 0, isEmptyFirstRun: true, isEmptyForContext: false, isEmptyForQuery: false }`)
- [X] T002 [P] Add the `library.*` i18n namespace scaffolding — shared strings only (screen title/subtitle, unassigned-shelf label, first-run & empty-for-context states, generic load/connection error) — as typed keys in `app/studio/src/i18n/catalog.ts` with EN values in `app/studio/src/i18n/en.ts` and FR values in `app/studio/src/i18n/fr.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The screen must exist, be routed, and replace its placeholder before any story renders

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create `app/studio/src/screens/library/DeliverableLibrary.tsx` — screen shell only: loads `listMissions()` + reads `useClientContext()` (taxonomy + active scope), renders the design-system shared states (`Loading`/`Empty`/`ErrorState` from `ui/states`), localized via `library.*` keys; mode skeleton (`loading → empty → populated` as stubs, no grouping/search yet)
- [X] T004 Wire the route: flip `library` status `"placeholder"` → `"shipped"` in `app/studio/src/shell/router.ts`, remove the `library` entry from `app/studio/src/screens/placeholders.tsx`, and mount `<DeliverableLibrary />` for route id `"library"` in the shell Outlet (`app/studio/src/shell/Shell.tsx`)
- [X] T005 Update the existing tests the route flip breaks — `app/studio/src/shell/router.test.ts`, `app/studio/src/screens/placeholders.test.tsx`, `app/studio/src/shell/Shell.test.tsx` (library no longer a coming-soon surface; navigation to `#/library` renders the screen)

**Checkpoint**: `#/library` renders the localized screen shell inside the app shell, scoped by the client-context selector — stories can now proceed

---

## Phase 3: User Story 1 — Find and open everything produced for a client (Priority: P1) 🎯 MVP

**Goal**: Finished deliverables grouped by client → project → campaign (+ an unassigned shelf), each a plain-language card (headline, produced date, outcome at a glance), scoped by the shell client context, opening to the existing full dossier detail — with friendly first-run and empty-for-context states and zero machinery terms

**Independent Test**: With saved missions (some filed across clients/projects/campaigns, some unassigned, at least one that ended in error), open the Library and verify the grouped shelves + unassigned shelf, plain-language cards, client-context scoping, and that opening a card reaches its full saved detail — offline, no live server, no mission ids/kit names/paths shown (spec US1 Independent Test). Additionally verify the **S3 completion hand-off** (FR-017/SC-007): finishing a production and choosing "view your deliverable" lands on the Library with that finished deliverable opened.

### Tests for User Story 1 (write first — must fail) ⚠️

- [X] T006 [P] [US1] Projection tests in `app/studio/src/screens/library/libraryModel.test.ts` per contracts/library-projection.md: `buildLibraryModel([], …)` ⇒ `isEmptyFirstRun`; missions across clients/projects/campaigns ⇒ correct nested shelves; a no-client mission ⇒ **unassigned** shelf; a mission attached to a taxonomy node absent from the tree ⇒ **orphaned** on the unassigned shelf (FR-013); a repeated `mission_id` ⇒ **one** Deliverable (dedup, R3/FR-014a); `scope.client` set ⇒ only that client's deliverables (unassigned hidden), cleared ⇒ all; `classifyOutcome` maps delivered+pass ⇒ `successful`, error/cancel/veto ⇒ `needs-attention`; no `route`/verdict-code/path leaks into the model (FR-003)
- [X] T007 [P] [US1] Screen tests in `app/studio/src/screens/library/DeliverableLibrary.test.tsx`: renders grouped shelves + cards from a mocked `listMissions`/taxonomy; first-run empty state (no missions) shows the friendly CTA (FR-012); empty-for-context state when scope has no deliverables; connection/load failure shows the shared error state; opening a card calls `getMission` and mounts the detail surface (FR-005); shelves/cards are keyboard-operable and screen-reader-labeled using `app/studio/src/testing/a11y.tsx` helpers (FR-016)

### Implementation for User Story 1

- [X] T008 [US1] Implement the projection in `app/studio/src/screens/library/libraryModel.ts`: pure `buildLibraryModel(missions, taxonomy, scope, view)` with dedup-by-`mission_id`, `placementOf` (filed/unassigned/orphaned), `classifyOutcome` (reusing `types.ts::lastVerdict`/`summaryVerdictClass` semantics), client-context scoping, taxonomy grouping (client → project → campaign + unassigned shelf), stable newest-first order, and the empty-state flags — emitting only plain fields (title, producedAt, outcome, placement labels), never raw ids/verdict codes (contracts/library-projection.md)
- [X] T009 [P] [US1] Add US1 catalog keys — EN in `app/studio/src/i18n/en.ts`, FR in `app/studio/src/i18n/fr.ts`, typed in `app/studio/src/i18n/catalog.ts` (`library.shelf.unassigned`, `library.card.untitled`, `library.card.producedOn`, `library.outcome.successful`, `library.outcome.needsAttention`, `library.empty.firstRun.{title,body,cta}`, `library.empty.context.{title,body}`, `library.state.loadError`) — plain production language, zero machinery terms (FR-003, SC-004)
- [X] T010 [US1] Implement `app/studio/src/screens/library/ShelfTree.tsx`: renders the grouped `LibraryModel.shelves` (client → project → campaign) plus the `unassigned` shelf, delegating each deliverable to `DeliverableCard`; design-system components, WCAG AA labels/focus, collapsible groups keyboard-operable (FR-002, FR-016)
- [X] T011 [US1] Implement `app/studio/src/screens/library/DeliverableCard.tsx`: one deliverable as a plain-language card (headline from `title`, friendly `producedAt`, localized `outcome` badge), with an "open" trigger; no mission id/kit name/path rendered (FR-003)
- [X] T012 [US1] Wire browse + open in `app/studio/src/screens/library/DeliverableLibrary.tsx`: `listMissions()` + `useClientContext()` → `buildLibraryModel(scope)` → `ShelfTree`; render first-run/empty-for-context/load-error states; open a card → `getMission(id)` → mount the existing `components/MissionDetail` for the full detail surface (FR-004, FR-005, FR-012)

#### S3 completion hand-off — closes FR-017 / SC-007

- [X] T012a [US1] Deep-link support in the Library: pass `search={match.search}` to `<DeliverableLibrary />` in `app/studio/src/shell/Shell.tsx`, and in `app/studio/src/screens/library/DeliverableLibrary.tsx` read an optional `?deliverable=<missionId>` param on mount — when present and the deliverable exists, auto-open its full detail (reusing the T012 open path); when absent or unknown, ignore silently (no error). Add an assertion to `app/studio/src/screens/library/DeliverableLibrary.test.tsx`: `#/library?deliverable=<id>` auto-opens that deliverable; an unknown/missing id opens nothing and shows the normal grouped view (FR-017, SC-007)
- [X] T012b [US1] Re-point the S3 hand-off: in `app/studio/src/screens/missions/TerminalPanel.tsx`, change `openDetails()` from the interim `navigate("#/console")` to `navigate("#/library?deliverable=" + encodeURIComponent(missionId))` and update the interim comment to reflect that S4 has shipped; update `app/studio/src/screens/missions/TerminalPanel.test.tsx` to assert the finished panel's "view your deliverable" action now targets the Library deep-link (not the console). Behavior otherwise unchanged — PDF/resume/start-another paths byte-identical (Constitution X; FR-017, SC-007)

**Checkpoint**: US1 fully functional — saved productions render as grouped, plain-language, openable deliverables scoped by client context, and a finished S3 production lands on its Library home with the deliverable opened; offline tests green (MVP delivered)

---

## Phase 4: User Story 2 — Search and filter to the one deliverable I need (Priority: P2)

**Goal**: A text search that narrows deliverables as typed (matching title + taxonomy placement) plus an outcome filter (successful / needs-attention), combinable with the active client context, with a clear nothing-found state and one-step clear

**Independent Test**: With many saved deliverables, type a query matching a subset → the list narrows (by title and by client/project/campaign); apply the needs-attention filter → only troubled runs remain; a no-match query → the nothing-found state; clear → the full grouped view returns (spec US2 Independent Test)

### Tests for User Story 2 (write first — must fail) ⚠️

- [X] T013 [P] [US2] Extend `app/studio/src/screens/library/libraryModel.test.ts`: `view.query` narrows by title AND by placement text (client/project/campaign), case-insensitive substring, empty query ⇒ no narrowing; `view.outcomeFilter` narrows to that outcome and combines (AND) with query + scope; a query/filter matching nothing sets `isEmptyForQuery` (not `isEmptyFirstRun`/`isEmptyForContext`) (FR-006, FR-007, US2-AC3)
- [X] T014 [P] [US2] Extend `app/studio/src/screens/library/DeliverableLibrary.test.tsx`: typing in the search box narrows shelves as-typed; the outcome filter narrows results; a no-match query renders the nothing-found state with a one-step clear; clearing search/filter restores the grouped view respecting the active client context (FR-006, FR-007)

### Implementation for User Story 2

- [X] T015 [US2] Extend `buildLibraryModel` in `app/studio/src/screens/library/libraryModel.ts` with `matchQuery` (title + placement text) and `outcomeFilter` application over the deduped/scoped set, and the `isEmptyForQuery` flag — all pure, order-stable (contracts/library-projection.md)
- [X] T016 [P] [US2] Add US2 catalog keys — typed in `catalog.ts`, EN in `en.ts`, FR in `fr.ts` (`library.search.placeholder`, `library.search.clear`, `library.search.noResults`, `library.outcomeFilter.{all,successful,needsAttention}`) — plain language (SC-004)
- [X] T017 [US2] Add the search box + outcome-filter controls to `app/studio/src/screens/library/DeliverableLibrary.tsx`, wired to `LibraryViewState` (`query`, `outcomeFilter`) that feeds `buildLibraryModel`; render the nothing-found state and the one-step clear; keyboard-operable and labeled (FR-006, FR-007, FR-016)

**Checkpoint**: US1 AND US2 both work — deliverables can be browsed grouped, searched, and outcome-filtered, all scoped by client context

---

## Phase 5: User Story 3 — Preview and act on a deliverable without ceremony (Priority: P3)

**Goal**: An in-place preview (headline, outcome, key sources/decisions, media thumbnails) shown without navigating away, plus the everyday actions — open full detail (from US1), download PDF (progress + graceful failure), and file/refile within the taxonomy — with **no delete** control anywhere

**Independent Test**: On a finished deliverable, open the in-place preview (summarizes without navigating), then exercise download PDF (success + graceful failure) and file/refile (attach unassigned, move, return to unassigned — each reflected immediately and reversible), and confirm no delete control exists (spec US3 Independent Test)

### Tests for User Story 3 (write first — must fail) ⚠️

- [X] T018 [P] [US3] Tests in `app/studio/src/screens/library/DeliverablePreview.test.tsx` per contracts/actions-and-filing.md: preview renders headline, outcome, key sources (safe-URL) and decisions, and media thumbnails from a mocked `getMission` dossier without navigating away; a no-media (research-only) dossier renders no broken thumbnail placeholders; preview is keyboard-operable and announced (FR-008)
- [X] T019 [P] [US3] Tests in `app/studio/src/screens/library/DeliverableActions.test.tsx`: "download PDF" calls `fetchMissionPdf` and offers the blob on success with progress; on failure shows a localized hint and the deliverable stays usable (FR-011); a **no-delete guard** assertion — no delete/remove control is rendered anywhere in the actions (clarify: non-destructive v1)
- [X] T020 [P] [US3] Tests in `app/studio/src/screens/library/FilingControl.test.tsx`: attach an unassigned deliverable, move a filed one, and return one to unassigned each call `assignMission` with the correct body (`{client,project?,campaign?}` / `{clear:true}`), reflect the new shelf immediately, are reversible by filing again, and emit plain success/failure feedback; a failed assign leaves the prior placement intact (FR-009, FR-010, FR-011)

### Implementation for User Story 3

- [X] T021 [US3] Implement `app/studio/src/screens/library/DeliverablePreview.tsx`: an in-place summary panel assembled from the `getMission` dossier subset (headline, outcome, first-N sources/decisions, `assets[]` thumbnails via the existing `components/AssetGallery`), lazily loaded and cached on the Deliverable, no-media safe, WCAG AA + live-region announce, no navigation away (FR-008, R5)
- [X] T022 [US3] Implement `app/studio/src/screens/library/DeliverableActions.tsx`: the action row — open full detail (reuse the US1 `MissionDetail` path), download PDF via `fetchMissionPdf` with in-progress feedback and a graceful localized failure/enable-hint, and mount `FilingControl`; renders **no** delete/remove control (FR-005, FR-011; clarify non-destructive)
- [X] T023 [US3] Implement `app/studio/src/screens/library/FilingControl.tsx`: plain-language attach / move / return-to-unassigned using `assignMission`, choosing among clients/projects/campaigns from `useClientContext().taxonomy` (never creating/renaming/deleting taxonomy nodes — FR-018); optimistic placement update reconciled with the response so the card re-shelves within a frame; reversible; success/failure feedback (FR-009, FR-010, FR-011, R6)
- [X] T024 [P] [US3] Add US3 catalog keys — typed in `catalog.ts`, EN in `en.ts`, FR in `fr.ts` (`library.preview.*`, `library.action.{open,downloadPdf}`, `library.pdf.{inProgress,failed,hint}`, `library.filing.{attach,move,unassign,success,failed,pickClient,pickProject,pickCampaign}`) — plain language, zero machinery terms (SC-004)
- [X] T025 [US3] Wire preview + actions + filing into `DeliverableCard`/`DeliverableLibrary`: trigger the in-place preview (`previewId` view state) and mount `DeliverableActions` per card; on a successful filing, re-fold the model so the deliverable appears on its new shelf immediately (FR-008, FR-010)

**Checkpoint**: All three stories work independently — browse, search/filter, preview, and the three non-destructive actions are functional; offline tests green

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Parity, accessibility, wording, and the full-suite/guardrail gate

- [X] T026 [P] EN/FR catalog parity + wording audit across all `library.*` keys in `app/studio/src/i18n/{en.ts,fr.ts}`: every key present in both locales, and a tone pass confirming zero machinery terms (no mission ids, kit/engine names, verdict/phase codes, or paths) anywhere operator-facing (FR-003, SC-004)
- [X] T027 [P] Accessibility pass (WCAG 2.1 AA) across browse/search/preview/actions/filing using `app/studio/src/testing/a11y.tsx` helpers — full keyboard operability, labels, visible focus, live-region announcements for preview/filing outcomes (FR-016, SC-005)
- [X] T028 Run the quickstart.md manual verification (10 steps) and enforce the guardrails: `git diff` touches only `app/studio/src/**`; `components/TaxonomyBrowser.tsx` byte-identical; no new `package.json` dependency; no new persisted field or endpoint (plan.md guardrails, Constitution X)
- [X] T029 Full frontend gate: `cd app/studio && npm run test && npm run build` green (new `screens/library/*` + updated shell/i18n tests), and confirm the root `pytest -q` suite is untouched and green (server not modified) (Constitution VII)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately (T001, T002 in parallel)
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (screen must render + be routed)
- **User Stories (Phases 3–5)**: All depend on Foundational completion
  - **US1 (P1)** — the MVP; no dependency on US2/US3. The S3 hand-off tasks come last in US1: T012a (Library deep-link) depends on T012 (open path) + T004 (shipped route); T012b (re-point S3 `TerminalPanel`) depends on T012a (the deep-link target must exist first)
  - **US2 (P2)** — extends the US1 projection + screen (T015 depends on T008; T017 depends on T012)
  - **US3 (P3)** — layers preview/actions/filing onto US1 cards (T025 depends on T011/T012); the "open" action reuses the US1 `MissionDetail` path
- **Polish (Phase 6)**: Depends on all targeted stories being complete

### Story Independence

- US1 is a complete, shippable increment on its own (browse + open + empty states).
- US2 and US3 are additive: each can be built and tested without the other (US2 = find; US3 = preview/act). Both build on US1's projection and cards.

---

## Parallel Execution Examples

- **Setup**: T001 and T002 in parallel (different files: `libraryModel.ts` vs the i18n trio).
- **US1 tests-first**: T006 (`libraryModel.test.ts`) and T007 (`DeliverableLibrary.test.tsx`) in parallel — different files, both must fail before implementation.
- **US1 implementation**: T009 (catalog keys) runs parallel to T008/T010/T011 (different files); T012 integrates last.
- **US3 tests-first**: T018, T019, T020 all in parallel (three distinct test files).
- **Polish**: T026 and T027 in parallel (i18n audit vs a11y pass).

---

## Implementation Strategy

**MVP scope = Phase 1 + Phase 2 + Phase 3 (US1).** That alone replaces the `#/library`
placeholder with a real, grouped, openable Deliverable Library scoped by client context —
the founding "find it again" promise and the permanent home for the S3 completion hand-off.

**Incremental delivery**: ship US1 (MVP), then US2 (search/filter) once volume warrants
finding-by-query, then US3 (preview + PDF + filing) to make the Library a place the operator
works from. Each story is an independently testable checkpoint; the server, mission store,
veto loop, and the dev console's `TaxonomyBrowser` stay byte-identical throughout (zero
server changes, zero new dependencies, non-destructive — no delete).
