# Tasks: The Magic Box — App Shell, Navigation, i18n & Screen Inventory (Brick 7 umbrella)

**Input**: Design documents from `/specs/007-magic-box/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/routes.md, contracts/i18n-catalog.md, quickstart.md

**Tests**: Per Constitution Principle VII, every code change ships offline tests. All new tests are Vitest + @testing-library/react with fetch mocked (no network, no CLI, no live server); the root `pytest` suite is untouched (zero Python changes in this feature).

**Organization**: Tasks are grouped by user story (US1–US5 from spec.md) so each story is an independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1–US5 for user-story phases; setup/foundational/polish tasks carry no story label
- Every path is exact; all frontend paths are under `app/studio/src/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory skeleton and design tokens — no new dependencies to install (plan: zero new npm deps)

- [X] T001 Create the Brick 7 layer directories `app/studio/src/shell/`, `app/studio/src/i18n/`, `app/studio/src/ui/`, `app/studio/src/screens/` (empty modules; structure per plan.md)
- [X] T002 [P] Create design tokens in `app/studio/src/ui/tokens.css` — color pairs with WCAG AA contrast documented inline, type scale, spacing, visible focus-ring token — and import it from `app/studio/src/styles.css` (spec FR-010/FR-011a; research R4)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: i18n scaffolding, hash router, and shared states — every user story consumes these

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Define the typed key inventory in `app/studio/src/i18n/catalog.ts` — `CatalogKey` string-literal union with the base keys from contracts/i18n-catalog.md (`nav.*`, `home.question`, `state.*`, `conn.*`, `context.*`, `lang.*`)
- [X] T004 [P] Write the complete English catalog `app/studio/src/i18n/en.ts` as `Record<CatalogKey, string>` (fallback source of truth, FR-007)
- [X] T005 [P] Write the complete French catalog `app/studio/src/i18n/fr.ts` as `Record<CatalogKey, string>` (compile-time complete; values French, keys/comments English per Constitution XI)
- [X] T006 Implement `app/studio/src/i18n/I18nProvider.tsx` — React context with `locale`, `setLocale`, `t(key, params?)` with `{param}` interpolation, runtime English fallback, first-run default from `navigator.language` (`fr*` → fr, else en), persistence to `localStorage["agency-studio.prefs"]` with defensive read of malformed JSON (data-model User Preferences; FR-006/FR-008)
- [X] T007 [P] Offline tests in `app/studio/src/i18n/i18n.test.tsx` — EN/FR key-set equality + no raw-key leak (SC-004), interpolation, missing-key fallback to English, browser-language default, persistence round-trip, malformed-prefs recovery
- [X] T008 Implement the hash router in `app/studio/src/shell/router.ts` — the 9-entry route table exactly as contracts/routes.md (id, hash, titleKey, status, taxonomyScoped), `useRoute()` subscription hook, `navigate()`, empty/`#/` → home, unknown hash → notFound fallback, `#/brief?intent=…` search-part passthrough (research R1; data-model Route)
- [X] T009 [P] Offline tests in `app/studio/src/shell/router.test.ts` — table completeness vs inventory ids S1–S8 + console with distinct hashes and catalog-backed titleKeys, empty-hash → home, unknown → notFound, navigate round-trip, intent param preserved
- [X] T010 Implement shared states in `app/studio/src/ui/states.tsx` — localized Loading / Empty / Error / ComingSoon / NotFound components with back-home action, styled from tokens (FR-011)
- [X] T011 [P] Offline tests in `app/studio/src/ui/states.test.tsx` — each state renders localized text in both locales, ComingSoon/NotFound expose a working back-home action, no raw catalog keys in output

**Checkpoint**: i18n + router + states ready — user stories can begin

---

## Phase 3: User Story 1 - Single entry point: "What do you want to produce?" (Priority: P1) 🎯 MVP

**Goal**: Launching the studio lands on the magic box home; a persistent localized nav reaches every inventoried area; the pre-Brick-7 console survives intact at `#/console`; service reachability is surfaced in plain language.

**Independent Test**: Load the app fresh → first surface is the localized "What do you want to produce?" question; every route-table entry is reachable from the nav (≤2 interactions); `#/console` renders the legacy console; killing the mocked backend shows the localized banner, restoring it clears the banner.

### Tests for User Story 1 (MANDATORY — Constitution VII, offline) ⚠️

> Write these first; ensure they FAIL before implementation

- [X] T012 [P] [US1] Shared a11y test helpers in `app/studio/src/testing/a11y.tsx` (assert keyboard operability + accessible name on every interactive element — the reusable design-system checks of contracts/routes.md) plus shell tests in `app/studio/src/shell/Shell.test.tsx` — default landing is home, all 9 nav entries present/localized/reachable with `aria-current` on the active route (SC-002), arrow-key roving works, console route renders the legacy app
- [X] T013 [P] [US1] Home tests in `app/studio/src/screens/Home.test.tsx` — the catalog-backed question renders, submitting an intent navigates to `#/brief?intent=<encoded>` (contract guarantee 2)
- [X] T014 [P] [US1] Connection tests in `app/studio/src/shell/ConnectionBanner.test.tsx` — transport-level fetch failure shows the localized banner, HTTP 500 does NOT, periodic retry success clears it and user context survives (FR-005; research R6)

### Implementation for User Story 1

- [X] T015 [US1] Implement `app/studio/src/shell/Nav.tsx` — persistent navigation generated from the router's route table, localized labels via `t()`, ARIA-patterned roving tabindex (same pattern as the console tablist), `aria-current="page"`, focus-ring token
- [X] T016 [US1] Implement `app/studio/src/shell/ConnectionBanner.tsx` — reachability state derived from transport-level failures of shell fetches (taxonomy boot fetch), localized message, periodic retry, auto-clear on first success
- [X] T017 [US1] Implement `app/studio/src/shell/Shell.tsx` — app frame (topbar, Nav, ConnectionBanner, route outlet); the outlet renders the route's component, the shared ComingSoon for `status: "placeholder"` routes, and NotFound for unknown hashes (depends on T015, T016)
- [X] T018 [P] [US1] Implement `app/studio/src/screens/Home.tsx` — the magic box question (`home.question`), an intent input, and hand-off to `#/brief?intent=…`; no terminal, no machinery vocabulary (FR-001/FR-003)
- [X] T019 [P] [US1] Implement `app/studio/src/screens/Console.tsx` — thin wrapper rendering the existing `App.tsx` unchanged (research R3; Constitution X)
- [X] T020 [US1] Switch the entry point `app/studio/src/main.tsx` to mount `<I18nProvider><Shell/></I18nProvider>`; `App.tsx` and its tests remain untouched (FR-018)

**Checkpoint**: MVP — a navigable, localized-chrome application with the magic box as default and the console preserved

---

## Phase 4: User Story 2 - The whole application speaks my language (EN/FR) (Priority: P2)

**Goal**: A language switcher in the shell chrome flips every visible string EN↔FR in place, persists across sessions, and defaults from the browser language.

**Independent Test**: Toggle the switcher on any screen → all chrome text changes locale without losing the current route or screen state; reload → choice persists; fresh profile with `fr-FR` browser locale → opens in French.

### Tests for User Story 2 (MANDATORY — Constitution VII, offline) ⚠️

- [X] T021 [P] [US2] Tests in `app/studio/src/shell/LanguageSwitch.test.tsx` — switching updates nav labels and the active screen's chrome in place (route and component state preserved), persists across a full remount, exposes an accessible label, and both options are announced in their own language (FR-008; SC-003)

### Implementation for User Story 2

- [X] T022 [US2] Implement `app/studio/src/shell/LanguageSwitch.tsx` — accessible EN/FR switcher using `useI18n().setLocale` (keys `lang.label`/`lang.en`/`lang.fr`)
- [X] T023 [US2] Integrate the switcher into the Shell topbar in `app/studio/src/shell/Shell.tsx`, verifying a locale change re-renders in place without resetting the route outlet

**Checkpoint**: US1 + US2 — the shell is fully bilingual with persistent choice

---

## Phase 5: User Story 3 - My work is organized by client (Priority: P3)

**Goal**: A shell-owned client → project → campaign context selector backed by the Brick 6 taxonomy; taxonomy-scoped areas receive the active context; no client is ever required to produce.

**Independent Test**: With a mocked `GET /api/taxonomy` returning clients, pick a client in the shell selector → scoped routes receive it; clear it → "all work + unassigned bucket" semantics; empty taxonomy → friendly state, producing still possible.

### Tests for User Story 3 (MANDATORY — Constitution VII, offline) ⚠️

- [X] T024 [P] [US3] Tests in `app/studio/src/shell/ClientContext.test.tsx` — selector lists clients/projects/campaigns from the mocked taxonomy, hierarchical invariant (changing client clears project/campaign), selection persists to prefs and survives remount, a stale persisted context (entities gone) degrades silently to no-context, empty taxonomy never blocks (FR-012/FR-013/FR-013a; data-model Client Context)

### Implementation for User Story 3

- [X] T025 [US3] Implement `app/studio/src/shell/ClientContext.tsx` — React context + selector UI fed by the existing `fetchTaxonomy()` from `app/studio/src/api.ts`; `null` client = no context with the unassigned bucket visible to scoped screens; persistence via the shared prefs record (research R5/R7)
- [X] T026 [US3] Wire the provider and selector into `app/studio/src/shell/Shell.tsx`; taxonomy-scoped placeholder routes (missions, library) display the active scope (or `context.none`) so the contract is observable before child specs ship

**Checkpoint**: US1–US3 — the shell thinks in clients, without gatekeeping production

---

## Phase 6: User Story 4 - Models and capabilities without leaving the app (Priority: P4)

**Goal**: The Brick 4 capability & model panel is a first-class screen at `#/models`, inside the shell, with no secret-entry surface.

**Independent Test**: Navigate to `#/models` → the existing Capabilities panel renders inside the shell frame under a localized title; no input on the screen accepts an API key.

### Tests for User Story 4 (MANDATORY — Constitution VII, offline) ⚠️

- [X] T027 [P] [US4] Tests in `app/studio/src/screens/Models.test.tsx` — the route renders the embedded panel inside the shell (nav still present), the screen title comes from the catalog in both locales, and no rendered input requests or accepts a key/secret (FR-014/FR-015)

### Implementation for User Story 4

- [X] T028 [US4] Implement `app/studio/src/screens/Models.tsx` — localized screen title + embed of the existing `Capabilities` component from `app/studio/src/components/Capabilities.tsx`, registered as the `models` route component (research R8)

**Checkpoint**: US1–US4 — Brick 4 lives inside the magic box

---

## Phase 7: User Story 5 - Not-yet-built areas fail gracefully (Priority: P5)

**Goal**: Every unshipped inventoried area renders a per-screen localized ComingSoon; unknown routes render NotFound; no dead ends anywhere.

**Independent Test**: Visit `#/brief`, `#/missions`, `#/library`, `#/import`, `#/export`, `#/settings` → each shows its own localized coming-soon copy with a working way home; visit `#/nope` → localized NotFound with a way home.

### Tests for User Story 5 (MANDATORY — Constitution VII, offline) ⚠️

- [X] T029 [P] [US5] Tests in `app/studio/src/screens/placeholders.test.tsx` — every `status: "placeholder"` route renders its own localized title + ComingSoon body with back-home in both locales; unknown hash renders NotFound; a route-table sweep proves zero dead ends across the inventory (SC-005; US5 acceptance scenarios)

### Implementation for User Story 5

- [X] T030 [US5] Implement `app/studio/src/screens/placeholders.tsx` — parameterized per-screen ComingSoon (screen-specific catalog keys for brief, missions, library, import, export, settings) built on the shared state from `app/studio/src/ui/states.tsx`, plus the catalog additions in `app/studio/src/i18n/catalog.ts`, `en.ts`, `fr.ts`
- [X] T031 [US5] Bind the per-screen placeholders into the route table in `app/studio/src/shell/router.ts` (replacing the generic ComingSoon fallback from T017 for inventoried routes; the NotFound fallback stays shell-owned)

**Checkpoint**: All five stories functional — the whole inventory is navigable with zero dead ends

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Visual coherence, docs accuracy, and full verification

- [X] T032 [P] Shell layout styling in `app/studio/src/styles.css` using only `ui/tokens.css` tokens — topbar/nav/outlet layout, laptop-half-width usability (spec edge case), focus-visible everywhere
- [X] T033 [P] Update `README.md` GUI section — magic box is the default surface, console at `#/console`, EN/FR switcher (docs must match the shipped behavior; docs-guard Rule 6)
- [X] T034 Full offline verification — `cd app/studio && npm test && npm run typecheck && npm run build`, then `pytest` at repo root (must stay green with zero Python diffs; Constitution VII / SC-008 / SC-009)
- [X] T035 Walk `specs/007-magic-box/quickstart.md` end-to-end against the built app (`agency-studio` → magic box home, nav, EN/FR, context, models, connection banner) and fix any quickstart drift found

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none — start immediately
- **Foundational (Phase 2)**: needs T001 (directories); T002 only blocks styling-dependent tasks (T010)
- **User Stories (Phases 3–7)**: all need Phase 2 complete
- **Polish (Phase 8)**: needs all desired stories complete (T034/T035 need everything)

### User Story Dependencies

- **US1 (P1)**: only Foundational — the MVP
- **US2 (P2)**: only Foundational (switcher exercises the provider); integrates into Shell topbar (T023 edits Shell.tsx after T017)
- **US3 (P3)**: only Foundational + Shell integration point (T026 edits Shell.tsx)
- **US4 (P4)**: only Foundational + route table (embeds a pre-existing component)
- **US5 (P5)**: only Foundational (T031 refines the route table; the generic fallback from US1 keeps US1 independently green)

### Within Each User Story

- Test tasks first, failing before implementation
- Same-file sequencing: T017 → T023 → T026 all touch `Shell.tsx` (US1 → US2 → US3 order); T030/T031 touch catalog files and `router.ts` after their foundational versions

### Parallel Opportunities

- Phase 2: T004 ∥ T005 (both after T003); T007 ∥ T009 ∥ T011 once their subjects exist
- Phase 3: T012 ∥ T013 ∥ T014 (tests), then T018 ∥ T019 while T015→T016→T017 proceed
- Phases 4–7 are mutually independent after Phase 2 (different files), except the noted `Shell.tsx` edit ordering
- Phase 8: T032 ∥ T033

## Parallel Example: User Story 1

```bash
# Write all US1 tests together (must fail first):
Task: "T012 a11y helpers + Shell tests in app/studio/src/shell/Shell.test.tsx"
Task: "T013 Home tests in app/studio/src/screens/Home.test.tsx"
Task: "T014 Connection tests in app/studio/src/shell/ConnectionBanner.test.tsx"

# Then implement the independent screens in parallel with the shell chain:
Task: "T018 screens/Home.tsx"          # ∥
Task: "T019 screens/Console.tsx"       # ∥
Task: "T015 → T016 → T017 shell chain" # sequential (Nav → Banner → Shell)
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 (T001–T002) → Phase 2 (T003–T011) → Phase 3 (T012–T020)
2. **STOP and VALIDATE**: `npm test && npm run typecheck && npm run build` + manual quickstart steps 1–2 — a navigable bilingual-chrome app with the magic box default and the console intact
3. Each later story (US2 → US3 → US4 → US5) is an independent, individually shippable increment; Phase 8 closes the brick's umbrella scope

### Notes

- Zero new npm/Python dependencies anywhere — if a task seems to need one, stop and re-read research.md
- `server.py` and everything under `agency_studio/` must show zero diff at T034
- Commit after each task or logical group (Conventional Commits)
