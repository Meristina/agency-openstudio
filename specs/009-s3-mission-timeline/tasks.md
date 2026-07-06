# Tasks: Mission Timeline — Follow a Running Production, Live and in Human Terms (Brick 7 · Screen S3)

**Input**: Design documents from `/specs/009-s3-mission-timeline/`

**Prerequisites**: plan.md, spec.md (clarified 2026-07-06), research.md (D1–D8), data-model.md, contracts/ (event-stage-mapping.md, session-handoff.md), quickstart.md

**Tests**: Per Constitution Principle VII, every code change ships offline tests (Vitest + jsdom, fetch/SSE mocked — no network, no CLI, no live server). Within each story, tests are written FIRST and must fail before implementation. The root `pytest` suite is untouched (zero server changes) and must stay green.

**Organization**: Tasks are grouped by user story (spec.md US1–US5) so each story is an independently testable increment. All paths are frontend (`app/studio/src/`) per plan.md — no files are touched outside the new `screens/missions/` module, the promoted `screens/session/missionSession.ts`, and the four declared integration points (router, Shell mount, i18n trio, placeholders). `timeline.ts` and `api.ts` are reused unchanged.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1–US5 from spec.md (user-story phases only)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module skeleton and i18n namespace both foundational work and stories build on

- [X] T001 Create the missions module skeleton: `app/studio/src/screens/missions/humanStages.ts` with the typed core only — `HumanStageKey` ("prepare" | "departments" | "synthesis" | "inspection" | "media"), `HumanStage`, `HumanDetail`, `HumanIteration` shapes per data-model.md and contracts/event-stage-mapping.md (the `humanStages()` projection body a stub returning `[]` for now)
- [X] T002 [P] Add the `missions.*` i18n namespace scaffolding — shared strings only (screen title, empty state, connection-lost note, generic stop/confirm, generic terminal labels) — as typed keys in `app/studio/src/i18n/catalog.ts` with EN values in `app/studio/src/i18n/en.ts` and FR values in `app/studio/src/i18n/fr.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The launch session must be shared, and the screen must exist, be routed, and replace its placeholder before any story renders

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Promote the launch session: move `app/studio/src/screens/brief/missionSession.ts` → `app/studio/src/screens/session/missionSession.ts` and its test `missionSession.test.ts` alongside; update the import in `app/studio/src/screens/brief/GuidedBrief.tsx` (and any other importer). Behavior byte-identical — the existing session test must still pass unchanged (Constitution X)
- [X] T004 Create `app/studio/src/screens/missions/MissionTimeline.tsx` — screen shell only: subscribes to `missionSession`, top-level mode skeleton (`live-follow → empty → terminal → resume-offer` as stubs) rendering design-system shared states (`Loading`/`Empty`/`ErrorState`), localized via `missions.*` keys
- [X] T005 Wire the route: flip `missions` status `"placeholder"` → `"shipped"` in `app/studio/src/shell/router.ts`, remove the `missions` entry from `app/studio/src/screens/placeholders.tsx`, and mount `MissionTimeline` in the shell's route rendering (`app/studio/src/shell/Shell.tsx`)
- [X] T006 Update the existing tests the route flip breaks — `app/studio/src/shell/router.test.ts`, `app/studio/src/screens/placeholders.test.tsx`, `app/studio/src/shell/Shell.test.tsx` (missions no longer a coming-soon surface; navigation to `#/missions` renders the screen)

**Checkpoint**: `#/missions` renders the localized screen shell inside the app shell, and the shared `missionSession` imports resolve — stories can now proceed

---

## Phase 3: User Story 1 — Watch the production happen, in plain language (Priority: P1) 🎯 MVP

**Goal**: The live human-stage timeline — the raw event stream folded (existing `timeline.ts`) then projected into curated plain-language stages (gather facts → departments → synthesis → quality inspection incl. fix loops, media when present), each with optional drill-down, updating live with no manual refresh and zero machinery terms

**Independent Test**: Feed a recorded representative event stream (route + several departments + ≥1 synthesis/inspection fix loop + a present and an absent optional step + completion) and verify an ordered, plain-language timeline whose stages transition upcoming → running → done in step with the stream — offline, no live engine (spec US1 Independent Test)

### Tests for User Story 1 (write first — must fail) ⚠️

- [X] T007 [P] [US1] Projection contract tests in `app/studio/src/screens/missions/humanStages.test.ts` per contracts/event-stage-mapping.md: `humanStages(groupTimeline([]))` ⇒ `[]`; representative stream ⇒ stages in fixed order with `prepare` present (sources row) and `media` absent (FR-003); a dept-`start`-only model ⇒ `departments` running, adding `done` ⇒ done; **two** inspection rounds render as two `HumanIteration`s (fix loop, FR-004); zero raw dept keys / phase codes in emitted keys+values and unknown dept key ⇒ `missions.dept.generic` (FR-005, SC-002)
- [X] T008 [P] [US1] Live-follow tests in `app/studio/src/screens/missions/MissionTimeline.test.tsx`: a simulated `MissionEvent` stream drives live stage updates with no manual refresh (FR-001); drill-down expands a stage to per-activity detail (FR-001); a fix loop shows successive quality rounds, never an error (FR-004); an interface-language switch mid-run re-renders every stage with progress intact (edge case); stage changes are announced via an ARIA live region and the view is keyboard-operable using `app/studio/src/testing/a11y.tsx` helpers (FR-019)

### Implementation for User Story 1

- [X] T009 [US1] Implement the projection in `app/studio/src/screens/missions/humanStages.ts`: total pure fold `TimelineModel → HumanStage[]` with the ordered presence rules, per-stage `state` derivation, `HumanDetail` rows for present sub-activities only, and `HumanIteration` rounds for the inspection fix loop — emitting catalog keys + interpolation values, never English literals (contracts/event-stage-mapping.md)
- [X] T010 [US1] Add all stage/status/round/detail and department-name catalog keys — EN in `app/studio/src/i18n/en.ts`, FR in `app/studio/src/i18n/fr.ts`, typed in `app/studio/src/i18n/catalog.ts` (`missions.stage.*`, `missions.state.*`, `missions.round`, `missions.detail.*`, `missions.dept.*` incl. `.generic`) — plain production language, zero machinery terms (FR-005, SC-002)
- [X] T011 [US1] Implement `app/studio/src/screens/missions/StageList.tsx`: renders the `HumanStage[]` rows with per-stage status, an optional drill-down expander showing `HumanDetail`/`HumanIteration` (absent when `detail` empty), design-system components, WCAG AA labels/focus (FR-019)
- [X] T012 [US1] Wire live-follow in `app/studio/src/screens/missions/MissionTimeline.tsx`: subscribe to `missionSession` → `groupTimeline(events)` → `humanStages(model, t)` → `StageList`, recomputed each publish (per-frame freshness), with an ARIA live region announcing stage transitions (FR-001, FR-019)

**Checkpoint**: US1 fully functional — a running (simulated) production renders as a live, plain-language, drill-downable timeline; offline tests green

---

## Phase 4: User Story 2 — Stop a run that shouldn't continue (Priority: P2)

**Goal**: A single, clearly labeled Stop action with a plain-language confirmation, reusing the existing cancel path, settling to an unambiguous "stopped — nothing saved" state, guarded against double-activation and the finish/cancel race

**Independent Test**: Drive a simulated running mission, invoke Stop, confirm, and verify the existing cancel path is exercised, the stream is torn down, and the timeline resolves to the stopped state with no lingering in-progress stage (spec US2 Independent Test)

### Tests for User Story 2 (write first — must fail) ⚠️

- [X] T013 [P] [US2] Cancel tests in `app/studio/src/screens/missions/CancelControl.test.tsx`: no cancellation occurs without an explicit confirm (FR-007); on confirm, `missionSession.cancel()` runs the cancel path (`cancelMission` mocked) and `status` settles to `cancelled` (FR-008); the control is absent when `status ∈ {done, failed, cancelled}` and cannot double-fire (FR-009); a stop racing a finishing run yields exactly one outcome (FR-009, US2 scenario 5)

### Implementation for User Story 2

- [X] T014 [US2] Implement `app/studio/src/screens/missions/CancelControl.tsx`: Stop button → plain-language confirm dialog (work will be lost) → on confirm calls `missionSession.cancel()`; disabled after first activation; rendered only while `status ∈ {launching, running}`; keyboard-operable, focus-managed dialog (FR-007–FR-009, FR-019)
- [X] T015 [US2] Add stop/confirm/stopped catalog keys — EN + FR + `catalog.ts` (`missions.stop.*`, `missions.terminal.stopped.*`) in plain production language
- [X] T016 [US2] Wire `CancelControl` into `MissionTimeline.tsx`: shown during live-follow, hidden once settled; on `cancelled` the screen renders the stopped terminal state off the session's final `status` (single-outcome guarantee)

**Checkpoint**: US2 functional — a run can be stopped with confirmation and settles cleanly; US1 + US2 offline tests green

---

## Phase 5: User Story 3 — Understand a run that ends — success or error (Priority: P3)

**Goal**: The three terminal panels (finished / error / stopped) each with plain-language summary and ≥1 forward action — finished → mission-detail view + PDF (interim until S4), error → retry, recoverable error → resume via the existing checkpoint path — never a dead end or raw dump

**Independent Test**: Replay simulated streams terminating in (a) success with a deliverable reference and (b) error, and verify each resolves to the matching plain-language terminal state with the correct forward action (spec US3 Independent Test)

### Tests for User Story 3 (write first — must fail) ⚠️

- [X] T017 [P] [US3] Terminal tests in `app/studio/src/screens/missions/TerminalPanel.test.tsx`: `done` ⇒ finished panel with verdict, and "Open details"/"Download PDF" call `getMission`/`fetchMissionPdf` (mocked) (FR-010); `error` + resumable checkpoint ⇒ Resume calls `runMission` with `{ resumeFrom }` (FR-012); `error` without checkpoint ⇒ only retry/return, no raw stack/phase code as primary text (FR-011); `cancelled` ⇒ stopped panel; every terminal exposes ≥1 forward action (FR-013)

### Implementation for User Story 3

- [X] T018 [US3] Implement `app/studio/src/screens/missions/TerminalPanel.tsx`: selects finished/error/stopped by `Terminal.kind` + follow pointer; forward actions reuse existing calls — `getMission(missionId)` (mission-detail handoff) and `fetchMissionPdf(missionId)` for done, `runMission(goal, onEvent, { resumeFrom: runId })` for recoverable error, `navigate("#/brief")` for retry/start-another; error `message` rendered through a plain-language wrapper (FR-010–FR-013)
- [X] T019 [US3] Add terminal catalog keys — EN + FR + `catalog.ts` (`missions.terminal.finished.*`, `missions.terminal.error.*` incl. recoverable variant, verdict phrasing, forward-action labels) in plain production language
- [X] T020 [US3] Wire `TerminalPanel` into `MissionTimeline.tsx` terminal modes (done/failed/cancelled), keeping the launched production identifiable and consultable in every terminal (FR-013)

**Checkpoint**: US3 functional — every run end resolves to a clear, actionable terminal; US1–US3 offline tests green

---

## Phase 6: User Story 4 — Reach and re-open the timeline from anywhere (Priority: P4)

**Goal**: The timeline as a first-class navigable destination — live run shown when active in the session (surviving in-app navigation), a calm localized empty state pointing to the Guided Brief when none is active, never a broken or developer-facing page

**Independent Test**: With a production active in the session, navigate away and back and verify the live run persists; with none active, open the timeline and verify the localized empty state with a route to the Guided Brief (spec US4 Independent Test)

### Tests for User Story 4 (write first — must fail) ⚠️

- [X] T021 [P] [US4] Reachability tests in `app/studio/src/screens/missions/MissionTimeline.test.tsx` (extend): a live session shown, navigate away and back ⇒ same run at current progress (module-singleton survival, FR-015); no active session and no follow pointer ⇒ localized empty state with a CTA to `#/brief` (FR-014, US4 scenario 2); a settled run stays consultable until a new one is started (FR-015)

### Implementation for User Story 4

- [X] T022 [US4] Implement the empty state in `app/studio/src/screens/missions/MissionTimeline.tsx`: when the session is `idle` and no follow pointer applies, render a plain-language "nothing running" panel with a CTA navigating to `#/brief`; confirm re-subscription on route re-entry shows current progress (FR-014, FR-015)
- [X] T023 [US4] Add empty-state catalog keys — EN + FR + `catalog.ts` (`missions.empty.*`) in plain production language

**Checkpoint**: US4 functional — the screen is reachable and honest whether or not a run is active; US1–US4 offline tests green

---

## Phase 7: User Story 5 — Honest about what "live following" can and cannot survive (Priority: P5)

**Goal**: A local follow pointer that lets a full reload honestly offer checkpoint-resume (not fake live continuation), plus a calm connection-lost state that preserves already-rendered stages — the honesty layer over the core stories

**Independent Test**: Simulate a mid-run loss of the local service and verify a calm localized connection-lost state without discarding shown stages or crashing; verify the reload path offers checkpoint-resume when a checkpoint exists and never claims durability the run lacks (spec US5 Independent Test)

### Tests for User Story 5 (write first — must fail) ⚠️

- [X] T024 [P] [US5] Follow-pointer tests in `app/studio/src/screens/missions/followPointer.test.ts` per contracts/session-handoff.md §4: pointer recorded on launch and on each terminal; **exactly one** pointer at a time; mount with a `status:"error"` + `resumable:true` pointer ⇒ resume offer; with `status:"done"` ⇒ completion handoff; dismiss clears; the record contains **no secret fields** (FR-016–FR-018)
- [X] T025 [P] [US5] Connection/reload tests in `app/studio/src/screens/missions/MissionTimeline.test.tsx` (extend): a mid-run failure surfaces a calm connection-lost state that **preserves** already-rendered stages, never a raw error or frozen spinner (FR-016); a reload with a resumable pointer ⇒ resume offer whose Resume re-enters live-follow via `runMission({ resumeFrom })` (FR-017)

### Implementation for User Story 5

- [X] T026 [US5] Implement `app/studio/src/screens/missions/followPointer.ts`: a single namespaced `localStorage` record (`agency.studio.followPointer.v1`) with `record`/`read`/`clear`, storing only `{ runId, status, missionId?, resumable?, checkpoint?, updatedAt }` — non-secret, local-only, at most one (data-model.md)
- [X] T027 [US5] Wire the follow pointer in `app/studio/src/screens/missions/MissionTimeline.tsx`: write on launch and on each terminal; on mount with an idle session, read the pointer and route to resume-offer / completion handoff / empty per contracts/session-handoff.md §4; Resume calls `runMission(goal, onEvent, { resumeFrom: runId })` and re-enters live-follow (FR-017)
- [X] T028 [US5] Implement the connection-lost + resume-offer presentation in `MissionTimeline.tsx` (reuse the shell `ConnectionBanner`, add a calm in-screen note, preserve rendered stages) and add `missions.connection.*` / `missions.resume.*` catalog keys in EN + FR + `catalog.ts` (FR-016, FR-017)

**Checkpoint**: All five stories functional — live-follow, stop, terminals, reachability, and reload honesty all offline-tested green

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Whole-screen guarantees that span every story

- [X] T029 [P] Extend the i18n completeness test (`app/studio/src/i18n/i18n.test.tsx`) to assert every `missions.*` key resolves in both EN and FR with zero missing keys and zero raw-key leaks (SC-005)
- [X] T030 [P] Full a11y/keyboard pass across every state (live-follow, stop-confirm dialog, all three terminals, empty, resume-offer, connection-lost): keyboard-only operability, visible focus, AA contrast, and live-region stage announcements (FR-019, SC-005)
- [X] T031 Wording audit across both languages: zero internal machinery terms (department keys, engine names, pipelines, phase/status codes, flags, env vars) in any rendered surface (FR-005, SC-002, SC-007-equivalent)
- [X] T032 Run the full offline gate — `cd app/studio && npm run build && npm test`, then `pytest -q` at the repo root — all green; walk the quickstart.md manual smoke checklist (US1–US5) and confirm the acceptance mapping (SC-007, SC-008)

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** → **Phase 2 (Foundational)** are prerequisites for everything; T003 (session move) and T004–T006 (screen + route) block all stories.
- **User stories** are then independently implementable and testable in priority order:
  - **US1 (P1)** — the MVP; depends only on Foundational. Delivers the live timeline.
  - **US2 (P2)** — depends on Foundational; independent of US1 (adds the Stop control), but naturally demoed on top of US1's live view.
  - **US3 (P3)** — depends on Foundational; consumes the same `Terminal`/session; independent of US1/US2.
  - **US4 (P4)** — depends on Foundational; extends the screen's mode handling; independent of US1–US3.
  - **US5 (P5)** — depends on Foundational; the follow-pointer/reload honesty layer; independent of US1–US4 but references terminal state.
- **Phase 8 (Polish)** runs after the stories it audits are in place.

### Story completion order (recommended)

Foundational → US1 → US2 → US3 → US4 → US5 → Polish (strict priority order; each a shippable increment).

## Parallel Execution Examples

- **Setup**: T002 [P] (i18n scaffolding) runs alongside T001 (module skeleton) — different files.
- **Within US1**: T007 [P] (projection tests) and T008 [P] (live-follow tests) are written together (different files) before implementation; then T009→T010→T011→T012 proceed (T010 catalog can parallel T009 once keys are agreed).
- **Across stories' tests**: T013 [P] (US2), T017 [P] (US3), T021 [P] (US4), T024/T025 [P] (US5) touch distinct test files and can be authored in parallel once Foundational is done.
- **Polish**: T029 [P] and T030 [P] are independent (i18n test vs a11y pass).

## Implementation Strategy

- **MVP = Phase 1 + Phase 2 + Phase 3 (US1)**: a running production is watchable live in plain language with drill-down — the screen's founding purpose and the middle of the brick's exit journey (SC-008).
- **Incremental delivery**: each subsequent story (Stop → Terminals → Reachability → Reload honesty) is a self-contained, offline-tested increment layered on the MVP without restructuring.
- **Invariant every step**: zero server changes, zero new dependencies, `timeline.ts`/`api.ts`/dev-console untouched, offline suite + `pytest` green (Constitution VII, X).

## Task Summary

- **Total**: 32 tasks (T001–T032)
- **Setup**: 2 · **Foundational**: 4 · **US1**: 6 · **US2**: 4 · **US3**: 4 · **US4**: 3 · **US5**: 5 · **Polish**: 4
- **Tests**: 8 dedicated test tasks (T007, T008, T013, T017, T021, T024, T025 + the foundational test fix T006), plus the i18n/a11y/audit passes in Polish
- **Parallel opportunities**: ~11 tasks marked [P]
