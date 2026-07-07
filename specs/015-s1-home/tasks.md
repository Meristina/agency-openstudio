---

description: "Task list for S1 Home implementation"
---

# Tasks: S1 Home — The Enriched Entry Point (Brick 7 · Screen S1)

**Input**: Design documents from `/specs/015-s1-home/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: MANDATORY (Constitution VII) — S1 has a runtime UI surface; every code change ships offline coverage (Vitest with `api.ts` wrappers mocked, and `localStorage` / `navigate` exercised in jsdom — no network / CLI / Node-beyond-jsdom / GPU). **No server surface → no pytest** (the root suite is run once in Polish only as a non-regression sanity).

**Organization**: Tasks grouped by user story. S1 is a **pure-frontend** enrichment: a new self-contained `screens/home/` module that replaces today's single-file `screens/Home.tsx`, reusing the existing sources of truth (`loadBriefDraft`, `listMissions`, `followPointer.read`, `useClientContext`, `navigate`). **No new endpoint, no new store, no `api.ts`/`types.ts` change, no router-table change** (the `home` route is already `shipped`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (from spec.md); Setup / Foundational / Polish have no story label
- All paths are under `app/studio/src/`

## Path Conventions

New frontend module: `app/studio/src/screens/home/`. Edited: `app/studio/src/i18n/{catalog,en,fr}.ts`, `app/studio/src/shell/Shell.tsx`. Removed (superseded by the module): `app/studio/src/screens/Home.tsx` and `app/studio/src/screens/Home.test.tsx`. **Unchanged**: `api.ts`, `types.ts`, `shell/router.tsx` (route table), the guided brief, mission timeline, library, models panel, capability probing / Brick 4 `SelectionStore`, the mission loop, and the `agencykit/` subtree.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module scaffold and typed i18n key surface

- [X] T001 Create the `app/studio/src/screens/home/` module skeleton — empty compiling stubs `Home.tsx`, `StartSection.tsx`, `ResumeSection.tsx`, `ShortcutsSection.tsx`, `ContextLabel.tsx`, `homeModel.ts`
- [X] T002 [P] Add the `home.*` typed keys to the `CatalogKey` union in `app/studio/src/i18n/catalog.ts` (new key set per `contracts/home-screen-model.md §F`); the existing `home.question` / `home.intentLabel` / `home.intentPlaceholder` / `home.start` and reused `nav.*` / `context.*` / `brief.draft.*` / `state.*` keys stay unchanged

**Checkpoint**: Module files exist and the typed key surface compiles

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Localized strings + the screen orchestrator + Shell wiring that ALL three stories mount into

**⚠️ CRITICAL**: the orchestrator makes `#/` render the new module and renders sections as they land — US1/US2/US3 plug into it, so complete this phase first

- [X] T003 [P] Add EN strings for every new `home.*` key in `app/studio/src/i18n/en.ts` (fallback source of truth — resume/recent titles, recent statuses in-progress/delivered/needs-attention, recent empty + load-error notes, see-all label, shortcut labels, context scoped-to + `home.context.none`)
- [X] T004 [P] Add FR strings for every new `home.*` key in `app/studio/src/i18n/fr.ts` (EN/FR parity — no key missing on either side)
- [X] T005 Implement the `app/studio/src/screens/home/Home.tsx` orchestrator — landmark/heading structure; renders `<StartSection/>` **synchronously** (never gated on data), then `<ResumeSection/>`, `<ShortcutsSection/>`, `<ContextLabel/>`; each section owns its own data/state. WCAG-AA landmarks/headings
- [X] T006 Rewire the entry point: change the `Home` import in `app/studio/src/shell/Shell.tsx` to `screens/home/Home`; delete the superseded `app/studio/src/screens/Home.tsx` and `app/studio/src/screens/Home.test.tsx`. The `home` route stays `shipped` (no `router.tsx` table change)

**Checkpoint**: `#/` renders the new (initially sparse) Home orchestrator with the four section slots, localized in EN/FR; the build compiles

---

## Phase 3: User Story 1 - Start new work from a calm, welcoming entry point (Priority: P1) 🎯 MVP

**Goal**: The existing question → guided-brief flow, preserved byte-for-byte, re-presented as a deliberate entry point: type an optional intent, start, and land in the guided brief carrying that intent unchanged.

**Independent Test**: Open `#/`, type an intent → start → the guided brief opens carrying exactly that intent (`#/brief?intent=…`); start with an empty intent → the brief still opens (`#/brief`); switch EN ↔ FR → all start-region copy follows.

### Tests for User Story 1 (MANDATORY — Constitution VII, offline) ⚠️

> Write these FIRST; ensure they FAIL before implementation

- [X] T007 [P] [US1] `app/studio/src/screens/home/Home.test.tsx` (start-flow cases): typing an intent and starting navigates to `#/brief?intent=<encoded>` **byte-identical to the prior behavior**; empty intent still navigates to `#/brief` (no query); the start region renders with `home.question` / `home.start`; EN and FR render; keyboard/label a11y (assert via `window.location.hash`)

### Implementation for User Story 1

- [X] T008 [US1] Implement `app/studio/src/screens/home/StartSection.tsx` — the question + intent `<textarea>` + start button; submit builds the **same** `#/brief?intent=${encodeURIComponent(intent.trim())}` URL as today (empty intent → `#/brief`) via `navigate`; reuse `home.*` intent keys; keyboard/labels. Mounted by the T005 orchestrator. Passes T007

**Checkpoint**: US1 independently functional — Home renders as the calm entry point and starts a brief exactly as before. MVP demoable (the byte-identical replacement of the old Home).

---

## Phase 4: User Story 2 - Resume work already in progress (Priority: P2)

**Goal**: Surface the unfinished brief and up to 5 recent missions (global, most-recent-first). Resuming the draft reopens the guided brief where it was left; selecting a mission opens the right existing surface for its state — the live timeline if in progress, its Library deliverable if complete. Degrades honestly on empty / load failure.

**Independent Test**: With an unfinished brief and ≥1 mission present, open `#/` → both appear; draft → `#/brief`; an in-progress mission → `#/missions`; a completed mission → `#/library?deliverable=<id>`; with nothing present → a calm empty state; with `listMissions()` failing → the start flow still works and an honest note shows (no false empty, no perpetual spinner).

### Tests for User Story 2 (MANDATORY — Constitution VII, offline) ⚠️

> Write these FIRST; ensure they FAIL before implementation

- [X] T009 [P] [US2] `app/studio/src/screens/home/homeModel.test.ts` (resume/recent cases): `recentMissionsView(missions, pointer)` caps at 5, preserves most-recent-first order, maps `delivered` / terminal-fail-verdict / in-progress → the correct `home.recent.*` `statusKey`, and sets `target` = `#/missions` for the live-run match vs `#/library?deliverable=<mission_id>` otherwise; **never** emits a raw `mission_id` / `runId` / `verdict` as label or status; `hasResumableDraft(draft)` true for a non-empty draft, false for null/empty; `isLiveRun(mission, pointer)` matches only the running follow-pointer
- [X] T010 [P] [US2] `app/studio/src/screens/home/ResumeSection.test.tsx`: a resumable draft → resume control navigates to `#/brief`; a recent list renders up to 5 plain-label + status items and opens each by state (`#/missions` vs `#/library?deliverable=<id>`); "see all" → `#/library` (the full browsable list, **not** `#/missions`); no draft + no missions → calm empty state (no dead control); `listMissions()` rejection → honest `home.recent.loadError` note **and** the start flow remains usable (assert no false empty, no infinite spinner); a11y/keyboard (mock `listMissions` via the existing `api.ts` test-double; `loadBriefDraft` / `followPointer` via `localStorage` in jsdom)

### Implementation for User Story 2

- [X] T011 [US2] Implement `recentMissionsView` + `hasResumableDraft` + `isLiveRun` in `app/studio/src/screens/home/homeModel.ts` per `data-model.md §2–3` (pure; no DOM/network/persistence; catalog-key-driven status; humanize goal with trim/truncate + generic fallback). Passes T009
- [X] T012 [US2] Implement `app/studio/src/screens/home/ResumeSection.tsx` — read `loadBriefDraft()` (resume → `navigate("#/brief")`); load `listMissions()` **independently and fail-soft** (never blocks Start), map via `recentMissionsView` using `followPointer.read()`; render up-to-5 items + "see all" (`#/library` — the full browsable list; `#/missions` shows only the live run); calm empty state; honest load-error note; keyboard/labels. Passes T010. Depends on T011

**Checkpoint**: US1 and US2 both work independently — start (US1) and resume of draft + recent missions with honest degrade (US2)

---

## Phase 5: User Story 3 - Orient toward the rest of the studio (Priority: P3)

**Goal**: Plain-language shortcuts to Library / Import / Models, plus a read-only label of the active default working context (from `useClientContext()`), with a plain "no context" state when unset. Home never edits the context (editing stays in S8 Settings).

**Independent Test**: From `#/`, each shortcut opens the right screen (`#/library`, `#/import`, `#/models`); the context label reflects the active `useClientContext()` scope, or shows `home.context.none` when nothing is set; removing this story leaves US1/US2 fully functional.

### Tests for User Story 3 (MANDATORY — Constitution VII, offline) ⚠️

> Write these FIRST; ensure they FAIL before implementation

- [X] T013 [P] [US3] `app/studio/src/screens/home/homeModel.test.ts` (context cases — appended to the shared file after US2): `contextLabelView({client,project,campaign})` composes a plain label from the set parts and returns `text: null` when nothing is set (→ `home.context.none`); never renders a raw taxonomy id where a plain label is expected
- [X] T014 [P] [US3] `app/studio/src/screens/home/ShortcutsSection.test.tsx` and `app/studio/src/screens/home/ContextLabel.test.tsx`: each shortcut navigates to `#/library` / `#/import` / `#/models`; the context label renders the active `useClientContext()` scope and the `home.context.none` state when unset (read-only — asserts no context mutation / no setter called); EN/FR; a11y/keyboard

### Implementation for User Story 3

- [X] T015 [US3] Implement `contextLabelView` in `app/studio/src/screens/home/homeModel.ts` per `data-model.md §4` (pure). Shares `homeModel.ts` with T011 — sequence after US2. Passes T013
- [X] T016 [US3] Implement `app/studio/src/screens/home/ShortcutsSection.tsx` (plain-language links → `#/library` / `#/import` / `#/models` via `navigate`, reuse `nav.*` where fitting) and `app/studio/src/screens/home/ContextLabel.tsx` (read-only label from `useClientContext()` via `contextLabelView`; `home.context.none` when unset; never a setter). Passes T014. Depends on T015

**Checkpoint**: All three stories work independently — start (US1), resume (US2), and orientation shortcuts + context label (US3)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Prove nothing else regressed and validate the build/suites

- [X] T017 [P] Verify non-regression: the guided brief, mission timeline, deliverable library, models panel, `shell/router.tsx` route table, capability probing / Brick 4 `SelectionStore`, and the mission loop are unchanged; confirm S1 added **no** endpoint, **no** store, **no** outbound network or network toggle, and renders **no** raw `mission_id` / `verdict` as operator content; the intent→brief URL is byte-identical to the pre-S1 behavior
- [X] T018 Run `cd app/studio && npm run test && npm run build` — Vitest green (`homeModel` + `Home` + `ResumeSection` + `ShortcutsSection` + `ContextLabel`), all typed `home.*` keys resolve in EN/FR, the old `screens/Home.tsx`/`Home.test.tsx` are gone, production build clean
- [X] T019 Run `pytest tests/` — root offline suite green (no Python changed; sanity that the pure-frontend change did not affect the server suite)
- [X] T020 Execute the `quickstart.md` manual smoke checklist (intent→brief incl. empty intent; resume draft; recent missions open by state; calm empty + honest load-error; read-only context label incl. "no context"; shortcuts → Library/Import/Models; EN/FR; keyboard-operable)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS US1/US2/US3** (strings + orchestrator + Shell rewire)
- **US1 (Phase 3)**: Depends on Foundational — the MVP; self-contained `StartSection`, no model/endpoint
- **US2 (Phase 4)**: Depends on Foundational; independent of US1 — adds the recent/draft half of `homeModel.ts` + `ResumeSection`
- **US3 (Phase 5)**: Depends on Foundational; shares `homeModel.ts` **and** `homeModel.test.ts` with US2 (adds the context half) — sequence after US2 to avoid same-file conflict; still independently testable
- **Polish (Phase 6)**: Depends on the stories being implemented

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational — reuses `navigate` only; no model, no endpoint
- **US2 (P2)**: Independent after Foundational — reuses `loadBriefDraft` / `listMissions` / `followPointer.read`; adds pure `recentMissionsView`/`hasResumableDraft`/`isLiveRun`
- **US3 (P3)**: Independent after Foundational; shares only `homeModel.ts` / `homeModel.test.ts` with US2 (different functions/cases), so sequence US2 → US3

### Within Each User Story

- Tests written and FAILING before implementation (Constitution VII)
- US2: pure model (T011) before the section (T012)
- US3: pure model (T015) before the sections (T016)

### Parallel Opportunities

- **Setup**: T002 [P] alongside T001
- **Foundational**: T003 / T004 [P] (different files `en.ts`/`fr.ts`); then T005 → T006
- **US1**: T007 [P] test then T008
- **US2**: T009 / T010 [P] (different files: `homeModel.test.ts`, `ResumeSection.test.tsx`); T011 then T012
- **US3**: T013 / T014 [P] (different files); T015 (shared `homeModel.ts`, after US2's T011) then T016
- **Polish**: T017 [P]; T018 / T019 / T020 gated on implementation

---

## Parallel Example: Foundational

```bash
# Different files — run together:
Task: "Add EN strings for home.* in app/studio/src/i18n/en.ts"   # T003
Task: "Add FR strings for home.* in app/studio/src/i18n/fr.ts"   # T004
```

## Parallel Example: User Story 2 tests

```bash
Task: "homeModel.test.ts — recentMissionsView cap/order/status/target + hasResumableDraft + isLiveRun"  # T009
Task: "ResumeSection.test.tsx — draft resume, recent-by-state, empty + honest load-error"               # T010
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup → 2. Phase 2 Foundational (CRITICAL) → 3. Phase 3 US1
4. **STOP & VALIDATE**: `#/` renders the calm entry point and starts a brief byte-identically (incl. empty intent) — demoable as the drop-in replacement of the old Home
5. Deploy/demo

### Incremental Delivery

1. Setup + Foundational → strings + orchestrator + Shell rewired
2. US1 → Start section (MVP) → validate → demo
3. US2 → Resume (unfinished brief + recent missions, open-by-state, honest degrade) → validate → demo
4. US3 → Shortcuts + read-only context label → validate → demo
5. Polish → non-regression + green build/suites + manual smoke

### Notes

- [P] = different files, no incomplete-task dependency
- **No server change**: every fact Home shows already exists client-side (`loadBriefDraft`, `followPointer`, `useClientContext`) or via existing `listMissions()` — adding an endpoint would violate Principle X for no honesty gain
- The **start flow renders synchronously** and is never blocked by the recent-work fetch (FR-007); a failed `listMissions()` shows an honest note, never a false "no work" and never a perpetual spinner (FR-008, Principle III)
- **No raw machine tokens** as operator content — `mission_id` / `runId` / `verdict` are internal only; the pure model emits a plain label + a `home.recent.*` status (Principle VIII)
- **Byte-identical intent→brief** — the start action builds the exact same `#/brief?intent=…` URL as today, including the empty-intent case (Principle X); the `home` route stays `shipped` (no router-table change)
- Open a recent mission via the two **existing** destinations by state (in-progress → `#/missions`; completed → `#/library?deliverable=<id>`); introduce **no** new per-mission route
- The context label is **read-only** — editing the working context stays in S8 Settings; Home calls no context setter
- Commit after each task or logical group; stop at any checkpoint to validate a story independently
