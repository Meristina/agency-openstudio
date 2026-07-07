---

description: "Task list for S8 Settings implementation"
---

# Tasks: S8 Settings — One Home for Studio Preferences (Brick 7 · Screen S8)

**Input**: Design documents from `/specs/014-s8-settings/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: MANDATORY (Constitution VII) — S8 has a runtime UI surface **and** one new server endpoint; every code change ships offline coverage (Vitest with `api.ts` wrappers mocked and `localStorage` in jsdom — no network/CLI/Node-beyond-jsdom/GPU; **plus** an offline pytest for `GET /api/system`).

**Organization**: Tasks grouped by user story. S8 is a frontend `screens/settings/` module **plus** one minimal read-only endpoint (`GET /api/system`) required by Principle III (no invented version/data-path). It reuses the existing single sources of truth (`setLocale`, `useClientContext`, the `localStorage` prefs) and reuses `fetchCapabilities` read-only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (from spec.md); Setup/Foundational/Polish have no story label
- Frontend paths are under `app/studio/src/`; the one server change is in `agency_studio/`; the endpoint test is under `tests/`

## Path Conventions

New frontend module: `app/studio/src/screens/settings/`. Edited: `app/studio/src/i18n/{catalog,en,fr}.ts`, `app/studio/src/shell/{Shell,router}.tsx`, `app/studio/src/screens/placeholders.tsx`, `app/studio/src/api.ts`, `app/studio/src/types.ts`. One server change: `agency_studio/server.py` (+ `tests/test_system_endpoint.py`). The Brick 4 `SelectionStore`, `components/Capabilities.tsx`, the mission loop, and every existing endpoint are **unchanged**.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module scaffold and typed i18n key surface

- [X] T001 Create the `app/studio/src/screens/settings/` module skeleton — empty compiling stubs `SettingsScreen.tsx`, `PreferencesSection.tsx`, `SystemStatusSection.tsx`, `ResetSection.tsx`, `settingsModel.ts`
- [X] T002 [P] Add the `settings.*` typed keys to the `CatalogKey` union in `app/studio/src/i18n/catalog.ts` and remove the `settings.comingSoon.*` pair (key set per `contracts/settings-screen-model.md`); `lang.*` and `context.*` keys are reused unchanged

**Checkpoint**: Module files exist and the typed key surface compiles

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Localized strings + the screen shell + route wiring that ALL three stories mount into

**⚠️ CRITICAL**: the orchestrator and route wiring make `#/settings` render the real screen — US1/US2/US3 sections plug into it, so complete this phase first

- [X] T003 [P] Add EN strings for every `settings.*` key in `app/studio/src/i18n/en.ts` (fallback source of truth — section titles, system connected/offline/unknown, version, data-location **labeled as the primary documents/settings folder, e.g. "Documents & settings folder" — never "all your files"** (FR-004), local-first note, model-summary + link label, reset title/body/confirm/cancel/done, per-mission network note); remove the two `settings.comingSoon.*` strings
- [X] T004 [P] Add FR strings for every `settings.*` key in `app/studio/src/i18n/fr.ts` (EN/FR parity — no key missing on either side); remove the two `settings.comingSoon.*` strings
- [X] T005 Implement the `app/studio/src/screens/settings/SettingsScreen.tsx` orchestrator shell — page heading (`settings.title`) + landmark structure, composes `<PreferencesSection/>` `<SystemStatusSection/>` `<ResetSection/>`, shared loading/error scaffolding; each section owns its own data. WCAG-AA headings/landmarks
- [X] T006 Wire the route: add `if (match.route.id === "settings") return <SettingsScreen />;` in `app/studio/src/shell/Shell.tsx`; flip the `settings` route `status: "placeholder" → "shipped"` in `app/studio/src/shell/router.tsx`; drop the `settings` entry from `app/studio/src/screens/placeholders.tsx` and update `app/studio/src/screens/placeholders.test.tsx`
- [X] T007 [P] Add the orchestrator test `app/studio/src/screens/settings/SettingsScreen.test.tsx` — `#/settings` resolves to `<SettingsScreen/>` (shipped, not the placeholder), renders the three section landmarks, keyboard-reachable

**Checkpoint**: `#/settings` shows the real (initially sparse) Settings screen with three section slots, localized in EN/FR

---

## Phase 3: User Story 1 - Manage core studio preferences in one place (Priority: P1) 🎯 MVP

**Goal**: The user sets interface language (EN/FR) and default working context (client/project/campaign) from Settings, sees each change confirmed immediately, and finds it still applied next session — edited through the existing single sources of truth so the top-bar controls never disagree.

**Independent Test**: Open `#/settings`, switch language → whole UI + top-bar control update together; set a default context → a newly started brief/mission opens pre-scoped to it and it persists across reload; a default context pointing at a deleted node is surfaced as stale, not silently applied.

### Tests for User Story 1 (MANDATORY — Constitution VII, offline) ⚠️

> Write these FIRST; ensure they FAIL before implementation

- [X] T008 [P] [US1] `app/studio/src/screens/settings/PreferencesSection.test.tsx`: language `<select>` change → `useI18n().setLocale` persists `PREFS_KEY` and the top-bar `LanguageSwitch` reflects the same value (single source of truth); default context set → `useClientContext()` setters persist `PREFS_KEY.clientContext`; clear → context returns to unassigned; a stale saved context is surfaced (not applied); honest confirmation (no false "saved"); a11y/keyboard

### Implementation for User Story 1

- [X] T009 [US1] Implement `app/studio/src/screens/settings/PreferencesSection.tsx` — language control via `useI18n().setLocale` (reuse `lang.*` keys); default working context via `useClientContext()` setters + clear (reuse `context.*` keys) with the provider's existing stale-selection surfacing; immediate honest confirmation; keyboard/labels. Passes T008

**Checkpoint**: US1 is independently functional — language + default context editable in one place, no drift with the top bar, persisted. MVP demoable.

---

## Phase 4: User Story 2 - See the studio is healthy and local-first (Priority: P2)

**Goal**: A read-only System / About panel shows connection state, the studio version, where the user's data lives, and a plain-language model-selection summary with a link to the S7 `#/models` panel — sourcing version and data path from the server (never invented), degrading honestly when offline.

**Independent Test**: With the server running, the panel shows connected + version + data location + model summary, and the model link opens `#/models`; stop the server and the panel shows offline/unknown while Preferences still works; no secret is ever rendered.

### Tests for User Story 2 (MANDATORY — Constitution VII, offline) ⚠️

> Write these FIRST; ensure they FAIL before implementation

- [X] T010 [P] [US2] `tests/test_system_endpoint.py` (offline pytest): `GET /api/system` → 200 JSON with string `version` == `agency_studio.__version__` and `data_dir` == `str(rag.data_dir())` (monkeypatch `data_dir` to a temp path and assert the response reflects it); response has no secret-looking field; endpoint is GET-only and mutates nothing (per `contracts/system-endpoint.md`)
- [X] T011 [P] [US2] System-view cases in `app/studio/src/screens/settings/settingsModel.test.ts`: `deriveSystemView(info, capabilities, reachable)` → `connection` = `unknown` before load / `offline` on transport failure / `connected` when loaded, plus `version` + `dataLocation`; `deriveModelSummary(capabilities)` → selectable families → the selected/active model as a plain-language label (reuse S7 family-name keys)
- [X] T012 [P] [US2] `app/studio/src/screens/settings/SystemStatusSection.test.tsx`: mocked `getSystemInfo` + `fetchCapabilities` → renders connected + version + data location + model summary + a link to `#/models`; transport failure → offline/unknown state with Preferences unaffected; no secret rendered; a11y

### Implementation for User Story 2

- [X] T013 [US2] Add the `GET /api/system` route + `_handle_system()` in `agency_studio/server.py` returning `{"version": __version__, "data_dir": str(rag.data_dir())}` — stdlib `json`, no user input (no `path_inside`/traversal surface), no secret, loopback bind inherited. Passes T010
- [X] T014 [P] [US2] Add `getSystemInfo(): Promise<SystemInfo>` (GET `/api/system`) to `app/studio/src/api.ts` and `interface SystemInfo { version: string; dataDir: string }` to `app/studio/src/types.ts` (mapping JSON `data_dir` → `dataDir`)
- [X] T015 [US2] Implement `deriveSystemView` + `deriveModelSummary` in `app/studio/src/screens/settings/settingsModel.ts` per `data-model.md §3` (pure; no DOM/network/persistence). Passes T011
- [X] T016 [US2] Implement `app/studio/src/screens/settings/SystemStatusSection.tsx` — parallel load `getSystemInfo()` + reuse `fetchCapabilities()`; render connection/version/dataLocation/modelSummary via `settingsModel` + a link to `#/models`; honest offline/unknown degrade (FR-009); read-only, no chooser, no secret. Passes T012. Depends on T014, T015

**Checkpoint**: US1 and US2 both work independently — preferences (US1) and an honest, local-first System panel with a model link (US2)

---

## Phase 5: User Story 3 - Reset preferences and recover (Priority: P3)

**Goal**: A guarded action clears the studio's own local preference keys back to defaults, behind an explicit confirmation, without deleting any deliverable, mission, or the persisted model selection.

**Independent Test**: With deliverables/missions and a saved model selection present, reset local preferences → language and context return to defaults while all server-side work and the `SelectionStore` remain intact; dismissing the confirmation changes nothing.

### Tests for User Story 3 (MANDATORY — Constitution VII, offline) ⚠️

> Write these FIRST; ensure they FAIL before implementation

- [X] T017 [P] [US3] Reset cases in `app/studio/src/screens/settings/settingsModel.test.ts`: `PREFERENCE_KEYS` equals the four studio keys sourced from their owners (`PREFS_KEY`, `${PREFS_KEY}.importAssociations`, `BRIEF_DRAFT_KEY`, `FOLLOW_POINTER_KEY`); `clearLocalPreferences(storage)` removes exactly those keys, leaves an unrelated key intact, and is no-op-safe when a key is absent or storage is unavailable (never calls `localStorage.clear()`)
- [X] T018 [P] [US3] `app/studio/src/screens/settings/ResetSection.test.tsx`: confirm → `clearLocalPreferences` invoked, language/context back to defaults, success note shown; dismiss → nothing changes; asserts **no** network call is made (server data + `SelectionStore` untouched)

### Implementation for User Story 3

- [X] T019 [US3] Implement `PREFERENCE_KEYS` + `clearLocalPreferences(storage)` in `app/studio/src/screens/settings/settingsModel.ts` — import the key constants from their owners (never re-hardcode), remove each key, no `localStorage.clear()`. Passes T017. Shares `settingsModel.ts` with T015 — sequence after US2
- [X] T020 [US3] Implement `app/studio/src/screens/settings/ResetSection.tsx` — guarded reset using `settings.reset.*` keys (explicit confirm/cancel) → `clearLocalPreferences(localStorage)` → success confirmation; issues no network call. Passes T018

**Checkpoint**: All three stories work independently — preferences (US1), system/about (US2), and safe reset (US3)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Prove nothing else regressed and validate the build/suites

- [X] T021 [P] Verify non-regression: `app/studio/src/components/Capabilities.tsx`, the mission loop, capability probing / Brick 4 `SelectionStore`, and every existing endpoint response are unchanged; confirm Settings adds **no** global network toggle (per-mission opt-in preserved) and no API-key input anywhere
- [X] T022 Run `cd app/studio && npm run test && npm run build` — Vitest green (`settingsModel` + `SettingsScreen`/`PreferencesSection`/`SystemStatusSection`/`ResetSection` + updated `placeholders.test.tsx`), typed `settings.*` keys resolve, `settings.comingSoon.*` fully removed, production build clean
- [X] T023 Run `pytest tests/test_system_endpoint.py tests/` — the new `/api/system` test and the root offline suite are green (no other Python changed)
- [X] T024 Execute the `quickstart.md` manual smoke checklist (language+context change with no top-bar drift; system connected/local-first + version + data location; model link → `#/models`; reset preserves deliverables/missions/`SelectionStore`; EN/FR; keyboard-operable; offline degrade)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS US1/US2/US3** (strings + orchestrator + route wiring)
- **US1 (Phase 3)**: Depends on Foundational — the MVP; self-contained `PreferencesSection`
- **US2 (Phase 4)**: Depends on Foundational; independent of US1 (own endpoint + section). Adds the `deriveSystemView`/`deriveModelSummary` half of `settingsModel.ts`
- **US3 (Phase 5)**: Depends on Foundational; shares `settingsModel.ts` with US2 (adds the reset half) — sequence after US2 to avoid same-file conflict; still independently testable
- **Polish (Phase 6)**: Depends on the stories being implemented

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational — reuses `setLocale` + `useClientContext`; no endpoint
- **US2 (P2)**: Independent after Foundational — adds `/api/system` + `SystemStatusSection`; reuses `fetchCapabilities`
- **US3 (P3)**: Independent after Foundational; shares only `settingsModel.ts` with US2 (different functions), so sequence US2 → US3

### Within Each User Story

- Tests written and FAILING before implementation (Constitution VII)
- US2: endpoint (T013) and `api.ts`/`types.ts` (T014) + pure model (T015) before the section (T016)
- US3: pure reset (T019) before the section (T020)

### Parallel Opportunities

- **Setup**: T002 [P] alongside T001
- **Foundational**: T003 / T004 [P] (different files `en.ts`/`fr.ts`); T005 → T006 (Shell/router/placeholders); T007 [P] after T005
- **US1**: T008 [P] test then T009
- **US2**: T010 / T011 / T012 all [P] (different test files: pytest, `settingsModel.test.ts`, `SystemStatusSection.test.tsx`); T013 (server) and T014 (api/types) [P]; T015 then T016
- **US3**: T017 / T018 [P]; T019 (shared file, after US2's T015) then T020
- **Polish**: T021 [P]; T022 / T023 / T024 gated on implementation

---

## Parallel Example: Foundational

```bash
# Different files — run together:
Task: "Add EN strings for settings.* in app/studio/src/i18n/en.ts"   # T003
Task: "Add FR strings for settings.* in app/studio/src/i18n/fr.ts"   # T004
# Then, once the orchestrator exists:
Task: "SettingsScreen.test.tsx — route resolves + three sections + a11y"  # T007
```

## Parallel Example: User Story 2 tests

```bash
Task: "tests/test_system_endpoint.py — /api/system returns version + data_dir, no secret"  # T010
Task: "settingsModel.test.ts — deriveSystemView + deriveModelSummary"                       # T011
Task: "SystemStatusSection.test.tsx — connected/offline/model-link/no-secret"               # T012
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup → 2. Phase 2 Foundational (CRITICAL) → 3. Phase 3 US1
4. **STOP & VALIDATE**: language + default context editable in one place, no drift with the top bar, persisted across reload — demoable as the replacement for the Settings placeholder
5. Deploy/demo

### Incremental Delivery

1. Setup + Foundational → strings + screen shell + route wired
2. US1 → Preferences (MVP) → validate → demo
3. US2 → `/api/system` + System/About panel with model link → validate → demo
4. US3 → guarded reset that preserves real work → validate → demo
5. Polish → non-regression + green build/suites + manual smoke

### Notes

- [P] = different files, no incomplete-task dependency
- The **only** server change is the read-only `GET /api/system`; it takes no user input, returns no secret, and adds no `path_inside`/traversal surface — loopback bind is inherited
- Never invent the version or data path — both come only from `/api/system`; connection state reflects the real probe; a stale context is shown, not silently applied; no false "saved"
- `data_dir` is the studio's **primary** data folder only (documents/settings/knowledge/selections); label it honestly and never imply it holds every deliverable — missions live under `project_root`, produced media under `assets_root`, both out of scope for `/api/system` (F1 remediation)
- Reset clears only the four enumerated studio local keys (never `localStorage.clear()`) and makes no network call — deliverables, missions, and the Brick 4 `SelectionStore` are provably untouched
- Add no global network toggle; the per-mission opt-in is preserved
- Language + default context use the same hooks as the top-bar controls — they can never drift (FR-002)
- Commit after each task or logical group; stop at any checkpoint to validate a story independently
