# Tasks: Guided Brief — From Intent to a Launch-Ready Production (Brick 7 · Screen S2)

**Input**: Design documents from `/specs/008-s2-guided-brief/`

**Prerequisites**: plan.md, spec.md (clarified), research.md (D1–D9), data-model.md, contracts/ (brief-mission-mapping.md, question-set.md), quickstart.md

**Tests**: Per Constitution Principle VII, every code change ships offline tests (Vitest + jsdom, fetch mocked — no network, no CLI, no live server). Within each story, tests are written FIRST and must fail before implementation. The root `pytest` suite is untouched (zero server changes) and must stay green.

**Organization**: Tasks are grouped by user story (spec.md US1–US5) so each story is an independently testable increment. All paths are frontend (`app/studio/src/`) per plan.md — no files are touched outside `screens/brief/` and the four declared integration points (router, i18n trio, placeholders, `runMission` assets opt).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1–US5 from spec.md (user-story phases only)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module skeleton and i18n namespace both foundational work and stories build on

- [X] T001 Create the brief module skeleton: `app/studio/src/screens/brief/questionSets.ts` with the typed core only — `DeliverableType` ("research" | "strategy" | "video"), `Answer`, `Question`, `QuestionSet`, partial `Brief` shapes per data-model.md and contracts/question-set.md (sets themselves empty for now)
- [X] T002 [P] Add the `brief.*` i18n namespace scaffolding — shared flow strings only (screen title, progress, back/next, start, review, launch, generic validation/error/launched states) — as typed keys in `app/studio/src/i18n/catalog.ts` with EN values in `app/studio/src/i18n/en.ts` and FR values in `app/studio/src/i18n/fr.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The screen must exist, be routed, and replace its placeholder before any story renders

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create `app/studio/src/screens/brief/GuidedBrief.tsx` — screen shell only: parse `?intent=` from the route search (URL-decode, trim; blank/whitespace ⇒ treated as absent per spec edge case), top-level state machine skeleton (`flow → review → launching → launched/failed` as stubs) rendering design-system shared states, localized via `brief.*` keys
- [X] T004 Wire the route: flip `brief` status `"placeholder"` → `"shipped"` in `app/studio/src/shell/router.ts`, remove the S2 entry from `app/studio/src/screens/placeholders.tsx`, and mount `GuidedBrief` in the shell's route rendering (`app/studio/src/shell/Shell.tsx`)
- [X] T005 Update the existing tests the route flip breaks — `app/studio/src/shell/router.test.ts`, `app/studio/src/screens/placeholders.test.tsx`, `app/studio/src/shell/Shell.test.tsx` (brief no longer a coming-soon surface; home → brief handoff still routes)

**Checkpoint**: `#/brief?intent=hello` renders the localized screen shell inside the app shell — stories can now proceed

---

## Phase 3: User Story 1 — Answer a few plain questions, get a complete brief (Priority: P1) 🎯 MVP

**Goal**: The adaptive question flow — intent carried from home, deliverable type → sector/domain → type-specific essentials → deliverable language, defaults/skip everywhere, back/next without loss — producing one complete brief object

**Independent Test**: From a stated intent, complete the flow for each of the three deliverable types using only plain-language inputs; the result is a single Brief containing every answer — no launch involved (spec US1 Independent Test)

### Tests for User Story 1 (write first — must fail) ⚠️

- [X] T006 [P] [US1] Contract tests for question sets in `app/studio/src/screens/brief/questionSets.test.ts`: three sets exist; only intent / deliverable type / deliverable language are non-defaultable+non-skippable (rule 2); `relevant` predicates pure and deterministic (rule 3); every referenced catalog key exists in EN and FR (rule 1); adding a type touches data only (rule 4 — assert engine imports no per-type logic)
- [X] T007 [P] [US1] Flow tests in `app/studio/src/screens/brief/GuidedBrief.test.tsx`: `?intent=` pre-filled and editable, absent ⇒ asked first (FR-001); only type-relevant questions asked (FR-002); progress visible, back/next preserves answers (FR-006); accept-all-defaults reaches a complete brief (FR-005); deliverable-type switch preserves still-relevant answers and flags newly relevant ones (edge case); interface-language switch mid-flow keeps answers and the deliverable-language choice (FR-008); keyboard-only completion via `app/studio/src/testing/a11y.tsx` helpers (FR-022)

### Implementation for User Story 1

- [X] T008 [US1] Fill `app/studio/src/screens/brief/questionSets.ts`: the research / strategy / video question sets (audience, objective, key messages, constraints…), curated sector list with "other" free-text escape (FR-004), mission-research toggle defaulting **on** (FR-012a), deliverable-language question defaulting to the interface language (FR-008), intent length limit — each question carrying its `compose` rule per contracts/question-set.md
- [X] T009 [US1] Add all question/choice/help/validation catalog keys for the three sets — EN in `app/studio/src/i18n/en.ts`, FR in `app/studio/src/i18n/fr.ts`, typed in `app/studio/src/i18n/catalog.ts` — plain production language, zero machinery terms (FR-007, SC-007)
- [X] T010 [US1] Implement `app/studio/src/screens/brief/FlowStep.tsx`: renders one Question by `kind` (choice / shortText / longText / language / sector / toggle), default-accept and skip affordances, localized inline validation (over-limit flagged, never truncated), design-system components, WCAG AA labels/focus (FR-022)
- [X] T011 [US1] Implement the flow engine in `app/studio/src/screens/brief/GuidedBrief.tsx`: ordered relevant-question sequence from the active set, progress indication, back/next with answer preservation, type-switch answer reconciliation, flow completion → complete Brief handed to the (stub) review state

**Checkpoint**: US1 fully functional — a complete Brief is built for each deliverable type, offline tests green

---

## Phase 4: User Story 2 — Review everything, then launch with one action (Priority: P2)

**Goal**: The single editable review of every answer and effective option, and the one-action launch through the existing `POST /api/mission` — run id confirmation, failures keep the brief intact

**Independent Test**: Complete a brief, verify the review lists 100% of answers, edit one from the review, launch against a mocked service, verify the composed request and the routing to the launched state (spec US2 Independent Test)

### Tests for User Story 2 (write first — must fail) ⚠️

- [X] T012 [P] [US2] Composer contract tests in `app/studio/src/screens/brief/composeMission.test.ts` per contracts/brief-mission-mapping.md: answers verbatim (never paraphrased), labeled sections in order, skipped answers produce no line, deterministic snapshot; default body has `web_search: true` and zero paid/off-machine flags (SC-004); `escalation`/`verification` omitted (research D8); `engine`/`resume_from` never set; taxonomy fields only when attached
- [X] T013 [P] [US2] Session tests in `app/studio/src/screens/brief/missionSession.test.ts` with mocked `runMission`: state transitions, run-id capture from first event, event buffering, double-launch guard (edge case), session survives component unmount (research D7), `cancelMission` path, transport failure ⇒ `failed` with localized error
- [X] T014 [P] [US2] Review tests in `app/studio/src/screens/brief/Review.test.tsx`: every answer and effective option visible — deliverable language, research on/off, attachment or unassigned, read-only server defaults ("at least 3 sources") (FR-015, research D8); edit-one-answer returns to review with others intact (FR-016); rejected launch / unreachable service shows plain-language error, brief intact, retry available (FR-019)

### Implementation for User Story 2

- [X] T015 [P] [US2] Add the optional `assets` field to `runMission` opts in `app/studio/src/api.ts` (absent ⇒ today's `true`, console callers byte-identical — plan integration point 4); extend `app/studio/src/api.test.ts` accordingly
- [X] T016 [US2] Implement `app/studio/src/screens/brief/composeMission.ts`: Brief → structured goal text (labeled sections, verbatim answers) + request fields (`web_search`, `video`, `assets` per set, taxonomy strings) per contracts/brief-mission-mapping.md
- [X] T017 [US2] Implement `app/studio/src/screens/brief/missionSession.ts`: module-scoped singleton owning the `runMission` SSE stream and AbortSignal — `launch()` with double-activation guard, run-id + event buffer, subscribe/unsubscribe, `cancel()`, localized error mapping (research D7)
- [X] T018 [US2] Implement `app/studio/src/screens/brief/Review.tsx`: grouped plain-language summary of all answers + effective options incl. read-only defaults, per-line edit action jumping to the question, launch button
- [X] T019 [US2] Wire review → launch in `app/studio/src/screens/brief/GuidedBrief.tsx`: edit-and-return flow, launch via the session, `launching` state, `launched` confirmation (run id + link to `#/missions` placeholder — FR-018), failure back to review with error, launch action disabled while in flight
- [X] T020 [US2] Add review/launch/confirmation/error catalog keys EN+FR in `app/studio/src/i18n/{catalog,en,fr}.ts`

**Checkpoint**: US1+US2 — intent → brief → review → launched mission (mocked), independently testable

---

## Phase 5: User Story 3 — File it under the right client, or not yet (Priority: P3)

**Goal**: Optional Brick 6 attachment inside the flow — pick existing client/project/campaign, active-context pre-selection, inline creation by name, skip ⇒ unassigned

**Independent Test**: With mocked taxonomy data: attach existing → launched request carries the fields; skip → no taxonomy fields (unassigned); new name → request carries it (inline creation, research D9); empty taxonomy never blocks (spec US3 Independent Test)

### Tests for User Story 3 (write first — must fail) ⚠️

- [X] T021 [US3] Attachment tests in `app/studio/src/screens/brief/GuidedBrief.test.tsx` (mocked `fetchTaxonomy`): browse/pick client and drill project/campaign (FR-009); shell active client context pre-selected, changeable, clearable; skip ⇒ composed request has no taxonomy fields (FR-011); inline create-by-name flows into the request (FR-010); empty taxonomy renders the step with skip + create, never blocks (FR-011); invalid names get localized client-side messages (data-model validation rule); `fetchTaxonomy()` failure degrades the step gracefully — shell connection-state language, skip and inline creation still offered, flow never blocked (spec edge case "service unreachable during the flow")

### Implementation for User Story 3

- [X] T022 [US3] Extend `app/studio/src/screens/brief/FlowStep.tsx` with the `attachment` question kind: taxonomy tree browser fed by `fetchTaxonomy()`, shell `ClientContext` pre-selection (`app/studio/src/shell/ClientContext.tsx` consumer side), inline new-client name input, explicit skip, and graceful degradation when `fetchTaxonomy()` fails (plain-language connection state; skip + inline creation remain available)
- [X] T023 [US3] Add the attachment step to all three sets in `app/studio/src/screens/brief/questionSets.ts` and the client-side name validation mirroring Brick 6 `clean_name` rules in `app/studio/src/screens/brief/composeMission.ts` (extend `composeMission.test.ts` for name-validation cases)
- [X] T024 [US3] Add attachment catalog keys EN+FR (pick/create/skip/unassigned wording) in `app/studio/src/i18n/{catalog,en,fr}.ts`

**Checkpoint**: Work can be filed under a client (existing or new) or left unassigned — all prior stories intact

---

## Phase 6: User Story 4 — Nothing paid, nothing off-machine, without saying so (Priority: P4)

**Goal**: Explicit free/local defaults with labeled paid/cloud opt-ins (video rendering), capability blockers surfaced at the review before launch, zero secret-entry surfaces

**Independent Test**: Drive a video brief against a mocked capability inventory: local backend ⇒ "on this machine (free)"; cloud key-gated backend ⇒ explicit paid/off-machine acknowledgement; missing capability ⇒ blocker panel with `#/models` link before launch; no credential input exists anywhere (spec US4 Independent Test)

### Tests for User Story 4 (write first — must fail) ⚠️

- [X] T025 [US4] Capability & labeling tests across `app/studio/src/screens/brief/Review.test.tsx` and `GuidedBrief.test.tsx` (mocked `fetchCapabilities`): effective video backend labeled local/free vs cloud/paid with required acknowledgement (FR-012, research D6); default launch enables zero paid/off-machine options (SC-004); unusable video family ⇒ blocker panel at review with `#/models` link, launch not attempted (FR-013, research D5); server 409 `{error, blockers[]}` rendered plain-language, brief intact (FR-019); no input of type password / key-shaped field anywhere in the flow (FR-014)

### Implementation for User Story 4

- [X] T026 [US4] Implement the review-time capability preflight in `app/studio/src/screens/brief/Review.tsx`: `fetchCapabilities()` when video/assets enabled, plain-language blocker panel with `#/models` link, launch gated while blocked
- [X] T027 [US4] Implement the video rendering `ProductionOption` presentation: effective-backend read from the capability inventory, paid/off-machine labeling + explicit acknowledgement in `app/studio/src/screens/brief/questionSets.ts` (video set) and `FlowStep.tsx`/`Review.tsx` display; where credentials would be relevant, state that keys are configured outside the app (FR-014)
- [X] T028 [US4] Handle the launch-time 409 blocker response in `app/studio/src/screens/brief/missionSession.ts` + `GuidedBrief.tsx` (map `blockers[]` to the same plain-language panel — server backstop of research D5)
- [X] T029 [US4] Add option/blocker/acknowledgement catalog keys EN+FR in `app/studio/src/i18n/{catalog,en,fr}.ts`

**Checkpoint**: Cost/network/capability transparency complete — a default launch is provably free and local (SC-004 asserted)

---

## Phase 7: User Story 5 — Life interrupts: the draft survives (Priority: P5)

**Goal**: Single local draft — autosaved on every answer, resume-or-discard on return, cleared on discard and successful launch, survives restart

**Independent Test**: Answer several questions, simulate restart (fresh mount + real localStorage in jsdom), verify the resume offer restores every answer at the left step; discard yields a clean start (spec US5 Independent Test)

### Tests for User Story 5 (write first — must fail) ⚠️

- [X] T030 [P] [US5] Draft store tests in `app/studio/src/screens/brief/briefDraft.test.ts`: save/load round-trip, versioned key `studio.briefDraft.v1`, version mismatch or corrupt JSON ⇒ null (no crash), discard removes the key, single-draft invariant, stored content is answers-only (no secrets — FR-020)
- [X] T031 [P] [US5] Draft UX tests in `app/studio/src/screens/brief/GuidedBrief.test.tsx`: remount with stored draft ⇒ resume-or-discard prompt, never silent overwrite (FR-021); resume restores answers + step; discard starts clean; successful launch clears the draft; resumed draft whose attached client no longer exists resurfaces the attachment step (edge case)

### Implementation for User Story 5

- [X] T032 [US5] Implement `app/studio/src/screens/brief/briefDraft.ts`: versioned single-entry localStorage store (load/save/discard) per data-model.md BriefDraft
- [X] T033 [US5] Wire the draft lifecycle in `app/studio/src/screens/brief/GuidedBrief.tsx`: autosave on every answer commit, entry-time resume-or-discard prompt, clear on discard and on successful launch, resume-time attachment re-validation against `fetchTaxonomy()`
- [X] T034 [US5] Add resume/discard catalog keys EN+FR in `app/studio/src/i18n/{catalog,en,fr}.ts`

**Checkpoint**: All five stories independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T035 [P] Add the SC-007 wording audit to `app/studio/src/i18n/i18n.test.tsx`: assert no machinery terms (department, engine, pipeline, flag, environment variable, API…) appear in any `brief.*` EN or FR value, and extend the existing catalog-completeness check to the `brief.*` namespace (SC-005)
- [X] T036 Full offline validation (SC-008): `cd app/studio && npx vitest run && npm run build`, then `python -m pytest` at the repo root — all green with no network, no CLI, no live services
- [X] T037 Run the quickstart.md manual smoke (5 scenarios: intent handoff, all-defaults research launch, video blocker, reload-resume, mid-flow language switch) against the locally served app and record the outcome in the PR description

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none — start immediately; T001 and T002 are parallel
- **Foundational (Phase 2)**: needs T001+T002; T003 → T004 → T005 (same/related files) — **blocks all stories**
- **User Stories (Phases 3–7)**: all need Phase 2. US2 needs US1's Brief object (T011) to review; US3/US4/US5 layer onto US1+US2 surfaces but each remains independently testable at its checkpoint
- **Polish (Phase 8)**: after the stories you intend to ship; T035 can start as soon as US1 keys exist

### Story Dependency Notes

- **US1 (P1)**: only Phase 2 — the MVP increment
- **US2 (P2)**: consumes the Brief from US1; mocked service only (offline)
- **US3 (P3)**: adds a step to US1's flow and fields to US2's composer
- **US4 (P4)**: enriches US2's review/launch and US1's video set
- **US5 (P5)**: wraps US1's flow state; only its launch-clear touches US2

### Within Each Story

Tests first (fail) → data/modules → components → wiring in `GuidedBrief.tsx` → catalog keys. Tasks touching `GuidedBrief.tsx`, `questionSets.ts`, or the i18n trio are sequential across phases (same files — no [P]).

### Parallel Opportunities

- Phase 1: T001 ∥ T002
- US1: T006 ∥ T007 (different test files)
- US2: T012 ∥ T013 ∥ T014, then T015 ∥ T016/T017 (api.ts vs brief module)
- US5: T030 ∥ T031
- Polish: T035 in parallel with any late story work (different file)

## Parallel Example: User Story 2

```bash
# Write the three test files together (they must fail first):
Task: "Composer contract tests in app/studio/src/screens/brief/composeMission.test.ts"
Task: "Session tests in app/studio/src/screens/brief/missionSession.test.ts"
Task: "Review tests in app/studio/src/screens/brief/Review.test.tsx"

# Then implement api.ts opt and the composer in parallel:
Task: "Optional assets opt on runMission in app/studio/src/api.ts"
Task: "Implement app/studio/src/screens/brief/composeMission.ts"
```

## Implementation Strategy

### MVP First (US1)

1. Phases 1–2 (setup + routed screen shell)
2. Phase 3 (US1) → **STOP and VALIDATE**: complete Brief for all three types, flow tests green
3. US1 alone already replaces the placeholder with a working guided flow

### Incremental Delivery

1. + US2 → the brick's core journey first half works end-to-end (intent → launched mission) — first demo-able increment for a real operator
2. + US3 → client filing · + US4 → cost/capability transparency · + US5 → draft resilience
3. Each checkpoint leaves every previous story green (offline suite run at each)

---

## Notes

- Zero server changes anywhere in this list — the root `pytest` suite must pass untouched at every checkpoint
- Commit after each task or logical group (Conventional Commits, branch `008-s2-guided-brief`)
- The umbrella's cross-cutting rules apply to every task: catalog-only strings, design-system components, WCAG 2.1 AA, tone of voice
