# Tasks: Import — The Front Door for the Operator's Own Material (Brick 7 · Screen S5)

**Input**: Design documents from `/specs/011-s5-import/`

**Prerequisites**: plan.md, spec.md (clarified 2026-07-06), research.md (R1–R7), data-model.md, contracts/ (import-model.md, brief-attachment.md), quickstart.md

**Tests**: Per Constitution Principle VII, every code change ships offline tests (Vitest + @testing-library/react + jsdom, `ingestDoc`/`listDocs`/`deleteDoc`/`uploadVisual`/`listVisual`/`deleteVisual` and `localStorage` mocked — no network, no CLI, no live server). Within each story, tests are written FIRST and must fail before implementation. The root `pytest` suite is untouched (zero server changes) and must stay green.

**Organization**: Tasks are grouped by user story (spec.md US1–US3) so each story is an independently testable increment. All paths are frontend (`app/studio/src/`) per plan.md — no files are touched outside the new `screens/import/` module and the declared integration points (router, Shell mount, i18n trio, placeholders, and the S2 brief affordance: `briefDraft.ts`, `composeMission.ts`, `Review.tsx`). `api.ts` and `screens/session/missionSession.ts` are reused unchanged (the launch path already spreads `draft.opts` into `runMission`, so new `knowledge`/`visual` opts flow through with no session-layer edit). The dev console's docs/visual surfaces stay byte-identical.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1–US3 from spec.md (user-story phases only)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module skeleton and i18n namespace that both foundational work and stories build on

- [X] T001 Create the import module skeleton: `app/studio/src/screens/import/importModel.ts` with the typed core only — `MaterialKind` (`"document" | "image"`), `ImportedMaterial`, `ClientAssociation`, `AssociationMap`, `ImportModel`, `ClientShelf`, `BringInResult`, `ImportViewState` shapes per data-model.md, and the `buildImportModel(...)` signature stubbed to return an empty model (`{ shelves: [], unassigned: [], total: 0 }`)
- [X] T002 [P] Add the `import.*` i18n namespace scaffolding — shared strings only (screen title/subtitle, unassigned-shelf label, first-run & empty-for-context states, generic load/connection error) — as typed keys in `app/studio/src/i18n/catalog.ts` with EN values in `app/studio/src/i18n/en.ts` and FR values in `app/studio/src/i18n/fr.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The screen must exist, be routed (client-context-scoped), and replace its placeholder before any story renders

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create `app/studio/src/screens/import/Import.tsx` — screen shell only: loads `listDocs()` + `listVisual()` and reads `useClientContext()` (taxonomy + active scope), renders the design-system shared states (`Loading`/`Empty`/`ErrorState` from `ui/states`), localized via `import.*` keys; mode skeleton (`loading → empty → populated` as stubs, no bring-in/grouping yet)
- [X] T004 Wire the route: in `app/studio/src/shell/router.ts` flip the `import` entry `status "placeholder" → "shipped"` **and** `taxonomyScoped false → true` (so the shell client-context selector shows for association — FR-006); remove the `import` entry from `app/studio/src/screens/placeholders.tsx`; and mount `<Import />` for route id `"import"` in the shell Outlet (`app/studio/src/shell/Shell.tsx`)
- [X] T005 Update the existing tests the route flip breaks — `app/studio/src/shell/router.test.ts`, `app/studio/src/screens/placeholders.test.tsx`, `app/studio/src/shell/Shell.test.tsx` (import no longer a coming-soon surface; it is now taxonomy-scoped; navigation to `#/import` renders the screen)

**Checkpoint**: `#/import` renders the localized screen shell inside the app shell, scoped by the client-context selector — stories can now proceed

---

## Phase 3: User Story 1 — Bring my own material in and see it ready to use (Priority: P1) 🎯 MVP

**Goal**: The operator brings in supported material (documents + images) from their machine; each is validated with plain-language accept/reject feedback, appears on a client → project → campaign shelf (or unassigned, defaulting to the active client context), with a friendly first-run empty state and a localized "not available here" state when an ingestion capability is absent — zero machinery terms, video/audio clearly out of scope

**Independent Test**: On `#/import` with document & image ingestion available, bring in a supported document and image → each shows progress then a plain confirmation and lands on the correct shelf (active client vs unassigned); bring in an unsupported kind / oversized / unreadable file → each rejected with a plain reason naming what *is* supported; run without the `[visual]` extra → the localized capability-absent state, documents still importable; fresh machine → the friendly empty state — all offline, no live server, no store ids/MIME/paths shown (spec US1 Independent Test)

### Tests for User Story 1 (write first — must fail) ⚠️

- [X] T006 [P] [US1] Model tests in `app/studio/src/screens/import/importModel.test.ts` per contracts/import-model.md: `buildImportModel([], [], {}, …)` ⇒ empty (`total: 0`); docs+visuals merge with correct `kind` tags; grouping via the association map (client → project → campaign + unassigned); an id absent from the map ⇒ **unassigned** shelf; `scope.client` set ⇒ only that client's shelves, cleared ⇒ all; dedup so each id appears once per kind; `name` prefers `title` then `filename`, never an id/path/MIME (FR-013); `classifyBringInResult` maps `201 → accepted`, `400 → rejected(unreadable/tooLarge)`, `501 → capabilityAbsent`, and a client-side unsupported kind ⇒ `rejected(unsupportedKind)` (FR-002, FR-003, FR-012)
- [X] T007 [P] [US1] Association-store tests in `app/studio/src/screens/import/associationStore.test.ts` per contracts/import-model.md: an id with no entry ⇒ `null` (unassigned default); writing the active client context on accept then reading it back; `localStorage` unavailable ⇒ all-unassigned, no crash (graceful degrade). (`prune`/re-associate covered in US3)
- [X] T008 [P] [US1] Screen tests in `app/studio/src/screens/import/Import.test.tsx`: renders grouped shelves from mocked `listDocs`/`listVisual` + association map; first-run empty state (no material) shows the friendly CTA (FR-014); empty-for-context state when the active client has no material; connection/load failure shows the shared error state; the capability-absent (501) state renders with an enable hint (FR-011); shelves are keyboard-operable and screen-reader-labeled using `app/studio/src/testing/a11y.tsx` helpers (FR-017)
- [X] T009 [P] [US1] Bring-in tests in `app/studio/src/screens/import/BringInPanel.test.tsx`: a supported document → `ingestDoc` called, progress shown, `accepted` feedback, item appears on the active-context shelf; a supported image → `uploadVisual` called **without** `cloud` unless the per-item opt-in is set (default off, FR-010); an unsupported kind (e.g. a video) → `rejected(unsupportedKind)` with **no** network call, naming supported kinds (FR-012); a `400` → `rejected(unreadable/tooLarge)`; a `501` → `capabilityAbsent` (FR-011); never a silent drop / raw error (FR-003)

### Implementation for User Story 1

- [X] T010 [US1] Implement the model in `app/studio/src/screens/import/importModel.ts`: pure `buildImportModel(docs, visuals, assoc, scope)` (merge + kind-tag + plain `name` + group by association into client→project→campaign + unassigned + client-context scoping + dedup-by-id-per-kind + stable newest-first order) and `classifyBringInResult(response|kind)` per contracts/import-model.md — emitting only plain fields, never raw ids/MIME/paths (FR-013)
- [X] T011 [P] [US1] Implement `app/studio/src/screens/import/associationStore.ts`: `getAssociation`/`setAssociation`/`clearAssociation` over a namespaced `localStorage` map (id → {client,project?,campaign?}), `localStorage`-unavailable-safe (all-unassigned fallback), plus a `defaultOnAccept(id, activeContext)` helper used by bring-in (`prune` added in US3) (FR-006, R4)
- [X] T012 [P] [US1] Add US1 catalog keys — typed in `app/studio/src/i18n/catalog.ts`, EN in `app/studio/src/i18n/en.ts`, FR in `app/studio/src/i18n/fr.ts`: `import.kind.{document,image}`, `import.bringIn.{cta,docHint,imageHint,progress}`, `import.reject.{unsupportedKind,tooLarge,unreadable,generic}`, `import.capabilityAbsent.{title,body,hint}`, `import.cloud.{optInLabel,offMachineWarning}`, `import.shelf.unassigned`, `import.card.importedOn` — plain production language, zero machinery terms (FR-003, FR-013, SC-004)
- [X] T013 [US1] Implement `app/studio/src/screens/import/MaterialShelf.tsx`: renders the grouped `ImportModel.shelves` (client → project → campaign) plus the `unassigned` shelf, delegating each item to `MaterialCard`; design-system components, WCAG AA labels/focus, collapsible groups keyboard-operable (FR-008, FR-017)
- [X] T014 [US1] Implement `app/studio/src/screens/import/MaterialCard.tsx`: one imported item as a plain-language card (plain `name`, localized `kind` badge, friendly `importedOn`); display-only in US1 (re-associate + remove controls land in US3); no id/path/MIME rendered (FR-013)
- [X] T015 [US1] Implement `app/studio/src/screens/import/BringInPanel.tsx`: file picker + drag-drop; per-item **client-side** kind validation (document vs image allow-list) → route `document → ingestDoc`, `image → uploadVisual(file,{cloud})` with `cloud` from a per-item opt-in (default off); in-flight progress; map the response via `classifyBringInResult` to plain accept/reject/capability-absent feedback; on `accepted`, write the default association (active client context) via `associationStore.defaultOnAccept` (FR-002, FR-003, FR-004, FR-010, FR-011)
- [X] T016 [US1] Wire bring-in + browse in `app/studio/src/screens/import/Import.tsx`: `listDocs()` + `listVisual()` + `useClientContext()` → `buildImportModel(scope)` → `MaterialShelf`; mount `BringInPanel`; render first-run/empty-for-context/load-error/capability-absent states; on an accepted bring-in, re-read the lists and re-fold so the new item appears on its shelf within a frame (FR-004, FR-011, FR-014)

**Checkpoint**: US1 fully functional — the operator brings in documents & images, sees plain accept/reject feedback and the capability-absent state, and each accepted item appears on its client-scoped shelf; offline tests green (MVP delivered)

---

## Phase 4: User Story 2 — Feed my material into a production as its input (Priority: P2)

**Goal**: From the Import screen or the S2 Guided Brief, the operator directs a brief to build on their imported material; at launch the production's existing `knowledge`/`visual` opt-ins are enabled (whole-set, no per-item curation, no mission-bridge change), with a plain-language "this production will use your imported material" summary shown only when imported material exists

**Independent Test**: With material imported, open the Guided Brief, turn on "use the material you've imported" → the review shows the summary; launch → the mission runs with `knowledge` on (and `visual` when images exist). With the affordance off/absent, the composed launch opts are byte-identical to today (spec US2 Independent Test; contracts/brief-attachment.md)

### Tests for User Story 2 (write first — must fail) ⚠️

- [X] T017 [P] [US2] Extend `app/studio/src/screens/brief/composeMission.test.ts` per contracts/brief-attachment.md: with `useImportedMaterial: true` and imported documents present ⇒ `opts.knowledge === true`; with imported images present ⇒ `opts.visual === true`; with the flag `false`/absent ⇒ composed `opts` are **byte-identical** to the current output (regression guard, Principle X); no per-item ids ever appear in `opts`
- [X] T018 [P] [US2] Affordance test in `app/studio/src/screens/brief/Review.test.tsx`: the "use my imported material" control renders **only when** imported material exists (mocked `listDocs`/`listVisual` non-empty) and is hidden when empty; toggling it sets `brief.useImportedMaterial` and shows the plain summary line; no store ids/MIME/paths shown (FR-007, FR-013)

### Implementation for User Story 2

- [X] T019 [US2] Add the default-off flag in `app/studio/src/screens/brief/briefDraft.ts`: `Brief.useImportedMaterial?: boolean` (default `false`), persisted with the existing draft; no other brief field changes (contracts/brief-attachment.md)
- [X] T020 [US2] Map it at compose time in `app/studio/src/screens/brief/composeMission.ts`: extend `MissionDraft.opts` with `knowledge?`/`visual?`; set `opts.knowledge = true` when `useImportedMaterial` and any document is imported, and `opts.visual = true` when any image is imported; leave `opts` byte-identical when the flag is off/absent (the `missionSession.launch` spread already forwards these to `runMission` — no session edit) (FR-005, FR-007, Principle X)
- [X] T021 [P] [US2] Add US2 catalog keys — typed in `catalog.ts`, EN in `en.ts`, FR in `fr.ts` (`import.brief.useMaterialLabel`, `import.brief.willUseSummary`) — plain language, zero machinery terms (SC-004)
- [X] T022 [US2] Implement the affordance in `app/studio/src/screens/brief/Review.tsx`: a plain-language toggle ("use the material you've imported") + summary line, visible only when imported material exists (from `listDocs`/`listVisual`), wired to `brief.useImportedMaterial`; keyboard-operable and labeled (FR-007, FR-017)
- [X] T023 [US2] Reachability parity from Import (FR-007): add a plain-language "use these in a production" action in `app/studio/src/screens/import/Import.tsx` that navigates to `#/brief` (visible only when material exists), so the intent is reachable from both surfaces; assert it in `app/studio/src/screens/import/Import.test.tsx`

**Checkpoint**: US1 AND US2 both work — imported material can be brought in and then directed to feed a production via the existing knowledge/visual opt-ins, with the launch byte-identical when the affordance is unused

---

## Phase 5: User Story 3 — See, organize, and clean up what I've imported (Priority: P3)

**Goal**: The imported list is organized by client with an unassigned shelf; the operator can re-associate a mis-filed item (or return it to unassigned) and remove material they no longer need — each with plain feedback; removing source material never touches any produced deliverable

**Independent Test**: With several items across clients and unassigned, re-associate a mis-filed item to another client (moves shelves immediately, reversible by re-associating); remove an item (confirmation + feedback, disappears, association pruned); confirm a deliverable previously produced from it stays intact in the S4 Library (spec US3 Independent Test; SC-009)

### Tests for User Story 3 (write first — must fail) ⚠️

- [X] T024 [P] [US3] Extend `app/studio/src/screens/import/associationStore.test.ts`: `setAssociation` then `clearAssociation` returns to unassigned; a second `setAssociation` overwrites (move); reversible; `pruneAssociations(knownIds)` drops entries whose id is absent after a removal (orphan cleanup, R6, FR-008)
- [X] T025 [P] [US3] Tests in `app/studio/src/screens/import/AssociateControl.test.tsx`: associate an unassigned item, move a filed one, and return one to unassigned each write the association map and reflect the new shelf immediately; reversible; plain success/failure feedback; taxonomy choices come from `useClientContext().taxonomy` (never creating/renaming/deleting nodes — FR-008)
- [X] T026 [P] [US3] Remove tests in `app/studio/src/screens/import/Import.test.tsx` (or a co-located `MaterialCard.test.tsx`): removing a document calls `deleteDoc(id)` and an image calls `deleteVisual(id)` (kind-routed), behind a confirmation; on success the item disappears and its association is pruned; on failure the item stays with a plain message; the delete path targets only the ingest-delete endpoints (never a mission/deliverable endpoint — FR-009, FR-016)

### Implementation for User Story 3

- [X] T027 [US3] Add `pruneAssociations(knownIds)` to `app/studio/src/screens/import/associationStore.ts` and call it after each load in `Import.tsx` so removed items leave no ghost shelf (R6)
- [X] T028 [US3] Implement `app/studio/src/screens/import/AssociateControl.tsx`: plain-language attach / move / return-to-unassigned using `associationStore` + taxonomy from `useClientContext()`; optimistic re-shelf reconciled on write; reversible; success/failure feedback (FR-008)
- [X] T029 [US3] Add remove to `app/studio/src/screens/import/MaterialCard.tsx`: a remove control → confirmation → kind-routed `deleteDoc`/`deleteVisual` → prune association → plain feedback; removal affects only the imported source material (FR-009, FR-016)
- [X] T030 [P] [US3] Add US3 catalog keys — typed in `catalog.ts`, EN in `en.ts`, FR in `fr.ts` (`import.associate.{attach,move,unassign,success,failed}`, `import.remove.{confirm,success,failed}`) — plain language (SC-004)
- [X] T031 [US3] Wire associate + remove into `MaterialCard`/`Import.tsx`: mount `AssociateControl` and the remove control per card; on a successful associate or remove, re-fold the model so the item re-shelves/disappears within a frame (FR-008, FR-009)

**Checkpoint**: All three stories work independently — bring-in, use-in-a-production, and organize/remove are functional; offline tests green

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Parity, accessibility, wording, and the full-suite/guardrail gate

- [X] T032 [P] EN/FR catalog parity + wording audit across all `import.*` keys in `app/studio/src/i18n/{en.ts,fr.ts}`: every key present in both locales, and a tone pass confirming zero machinery terms (no store ids, MIME types, kit/engine names, or file paths) anywhere operator-facing, and that the video/audio limitation is stated plainly (FR-012, FR-013, SC-004)
- [X] T033 [P] Accessibility pass (WCAG 2.1 AA) across bring-in/browse/associate/remove and the brief affordance using `app/studio/src/testing/a11y.tsx` helpers — full keyboard operability, labels, visible focus, live-region announcements for bring-in/associate/remove outcomes (FR-017, SC-005)
- [X] T034 Run the quickstart.md manual verification (8 steps) and enforce the guardrails: `git diff` touches only `app/studio/src/**` (+ specs); no server file changed; no new `package.json` dependency; no new persisted mission field or endpoint; the dev console's docs/visual surfaces byte-identical; a default bring-in performs no off-machine call (FR-010; plan.md guardrails; Constitution X)
- [X] T035 Full frontend gate: `cd app/studio && npm run test && npm run build` green (new `screens/import/*` + updated shell/i18n/brief tests), and confirm the root `pytest -q` suite is untouched and green (server not modified) (Constitution VII)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001, T002 in parallel
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (screen must render + be routed + client-context-scoped)
- **User Stories (Phases 3–5)**: All depend on Foundational completion
  - **US1 (P1)** — the MVP; no dependency on US2/US3 (bring-in + validation + shelves + empty/capability-absent states)
  - **US2 (P2)** — the brief affordance; depends on US1 only for "imported material exists" signal (reads `listDocs`/`listVisual`); the compose mapping (T020) is independent of US1 internals
  - **US3 (P3)** — organize + remove; layers `AssociateControl`/remove onto US1's `MaterialCard`/model (T028/T029/T031 depend on T013/T014/T016); `prune` (T027) extends US1's `associationStore` (T011)
- **Polish (Phase 6)**: Depends on all targeted stories being complete

### Story Independence

- US1 is a complete, shippable increment on its own (bring your material in, see it validated and shelved).
- US2 (use in a production) and US3 (organize/remove) are additive; each can be built and tested without the other. US2 touches only the brief trio + one Import CTA; US3 extends US1's card/model.

### Within Each User Story

- Tests are written FIRST and must fail before implementation.
- Model/store before UI; UI before wiring.
- Catalog-key tasks ([P]) run alongside implementation (different files).

---

## Parallel Execution Examples

- **Setup**: T001 and T002 in parallel (different files: `importModel.ts` vs the i18n trio).
- **US1 tests-first**: T006 / T007 / T008 / T009 in parallel — four distinct test files, all must fail before implementation.
- **US1 implementation**: T011 (associationStore) and T012 (catalog keys) run parallel to T010 (model); T013/T014 (shelf/card) parallel; T015 (bring-in) then T016 (wire) integrate last.
- **US2**: T017 and T018 (two test files) in parallel; T021 (catalog) parallel to T019/T020.
- **US3 tests-first**: T024, T025, T026 all in parallel (three distinct test files).
- **Polish**: T032 and T033 in parallel (i18n audit vs a11y pass).

---

## Implementation Strategy

**MVP scope = Phase 1 + Phase 2 + Phase 3 (US1).** That alone replaces the `#/import`
placeholder with a real front door: the operator brings in their own documents and images,
sees plain accept/reject/capability-absent feedback, and each accepted item lands on its
client-scoped shelf — the founding "bring my own material in" promise.

**Incremental delivery**: ship US1 (MVP), then US2 (feed a production via the existing
knowledge/visual opt-ins) to make imported material actually shape a mission, then US3
(organize + remove) to keep the imported library tidy. Each story is an independently
testable checkpoint; the server, mission loop, veto loop, and the dev console's docs/visual
surfaces stay byte-identical throughout (zero server changes, zero new dependencies, whole-set
attachment with no mission-bridge change, and removal that never touches a produced
deliverable).
