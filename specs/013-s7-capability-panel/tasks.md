---

description: "Task list for S7 Capability & Model Panel implementation"
---

# Tasks: Capability & Model Panel — See What This Machine Can Produce and Choose Models (Brick 7 · Screen S7)

**Input**: Design documents from `/specs/013-s7-capability-panel/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: MANDATORY (Constitution VII) — S7 has a runtime UI surface; every code change ships offline Vitest coverage (no network, no CLI, no Node beyond jsdom, no GPU; the `api.ts` wrappers mocked). **No pytest change** (S7 adds no server surface).

**Organization**: Tasks grouped by user story. **S7 is pure frontend** over the existing Brick 4 endpoints — no server file, no new endpoint, no persistence, no `api.ts` change, no router change.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 (from spec.md); Setup/Foundational/Polish have no story label
- All paths are under `app/studio/src/` unless noted

## Path Conventions

Web-app frontend module: `app/studio/src/screens/models/` (new), `app/studio/src/i18n/` (edited), `app/studio/src/screens/Models.tsx` (rewired). The developer Console's `app/studio/src/components/Capabilities.tsx` and `app/studio/src/api.ts` are **unchanged**.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module scaffold and typed i18n key surface

- [X] T001 Create the `app/studio/src/screens/models/` module skeleton — empty `ModelsScreen.tsx`, `FamilyCard.tsx`, `ModelOption.tsx`, `capabilityModel.ts` placeholder files (compiling stubs)
- [X] T002 [P] Add the `models.*` typed keys to the `CatalogKey` union in `app/studio/src/i18n/catalog.ts` (family names/descriptions ×9, cost, status, reason, chooser, honesty, secrets, states — per `contracts/capability-panel-model.md §3`); `models.title` reused

**Checkpoint**: Module files exist and typed keys are declared

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The pure presentation model + localized strings that BOTH user stories render from

**⚠️ CRITICAL**: `capabilityModel.ts` and the EN/FR strings block US1 and US2 — complete this phase first

- [X] T003 [P] Add EN strings for every `models.*` key in `app/studio/src/i18n/en.ts` (fallback source of truth — plain-language family names: images / video / visual understanding / search & memory / knowledge extraction / transcription / voice & narration / production tools / integrations & connectors)
- [X] T004 [P] Add FR strings for every `models.*` key in `app/studio/src/i18n/fr.ts` (EN/FR parity — no key missing on either side)
- [X] T005 [P] Write the pure-model unit tests in `app/studio/src/screens/models/capabilityModel.test.ts` (write FIRST, must FAIL): family→plain name/description for all 9 families; `cost`→plain `costKind`; `availability`+`reason`+`enablement`→plain status/hint; `selectable`→`displayKind` (`chooser` for the 7, `readonly` for `production-tools`/`mcp`); `env_override`→`isEnvOverridden`; `selected_stale`→`isStale`; enablement hint = env-var **name** only (never a `key_env` value); no `family`/`id`/`tier`/`reason` code returned as display content
- [X] T006 Implement the pure `app/studio/src/screens/models/capabilityModel.ts` (`toCapabilityViews`, `familyNameKey`, `costKind`, `reasonHintKey`, view-model shapes per `data-model.md`) so T005 passes — no DOM, no network, no persistence

**Checkpoint**: Raw inventory → plain-language view-model is proven offline; localized strings exist in both locales

---

## Phase 3: User Story 1 - See what this machine can produce, in plain language (Priority: P1) 🎯 MVP

**Goal**: The operator opens `#/models` and sees every capability (all 9 families) named and described in plain language with a plain-language availability/cost status, a re-check control, and friendly empty/error states — machine-level, fully localized, no raw identifiers or secrets.

**Independent Test**: Load the screen on a machine with a mix of available/unavailable capabilities: every family shows a plain name + status; an unavailable one shows "not available yet — how to enable" (no raw reason code); a paid/cloud option is marked paid/cloud and shows key-configured or "set `$VAR`" (name only, no field); EN↔FR switches every string; switching client context leaves content identical (machine-level). No chooser is required for this story.

### Tests for User Story 1 (MANDATORY — Constitution VII, offline) ⚠️

> Write these FIRST; ensure they FAIL before implementation

- [X] T007 [P] [US1] `app/studio/src/screens/models/ModelsScreen.test.tsx`: loads via mocked `fetchCapabilities`, renders all 9 families in plain language; re-check calls `fetchCapabilities(true)`; read failure → localized error + retry; family with no available option → `models.empty.family`; machine-level (client-context selector ignored); a11y/keyboard reachable
- [X] T008 [P] [US1] Read-only display cases in `app/studio/src/screens/models/FamilyCard.test.tsx`: plain name + description + status; non-selectable family (`production-tools`/`mcp`) shows read-only status with NO chooser; option row shows label + cost marker + availability + default badge + key-name hint with NO key value and NO input field

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement `app/studio/src/screens/models/ModelOption.tsx` — one option row: label (as-is), free/local vs paid/cloud marker, availability, default badge, `keyConfigured` / "set `$VAR` to enable" hint (env-var NAME only); no key input
- [X] T010 [US1] Implement `app/studio/src/screens/models/FamilyCard.tsx` read-only path — plain name/description/status + enablement hint; `readonly` families render status only (no chooser). Depends on T009
- [X] T011 [US1] Implement `app/studio/src/screens/models/ModelsScreen.tsx` — mount-load `fetchCapabilities()`, render every family via `toCapabilityViews`, `models.recheck` control → `fetchCapabilities(true)`, shared loading/error(retry)/empty states, machine-level (no `useClientContext`), WCAG-AA keyboard/labels. Depends on T010
- [X] T012 [US1] Rewire `app/studio/src/screens/Models.tsx` to render `<ModelsScreen />` (Shell's `models` route → the new surface); confirm the `models` route stays `shipped` + `taxonomyScoped:false` (no router edit needed)

**Checkpoint**: US1 is independently functional — the panel reads and shows what the machine can produce, localized and secret-free, with re-check and empty/error states. MVP demoable.

---

## Phase 4: User Story 2 - Choose which model each capability uses (Priority: P2)

**Goal**: On the same screen, for a selectable model family the operator picks an available model (or keeps the built-in default), sees it saved as the **standing default applied on the next production**, and can revert to default — with unavailable options non-selectable, paid/cloud a preference-only opt-in, and honest env-override / stale-selection messaging.

**Independent Test**: On a family with >1 available option, pick a non-default option → it becomes the standing default and persists across reload (confirmation says "applies on your next production", not "instantly active"); revert → default persists; an unavailable option cannot be selected; selecting a paid/cloud option records a preference with no key field and no outbound send; with an env override set, the family shows the environment is deciding; a stale prior choice is surfaced with what is in force.

### Tests for User Story 2 (MANDATORY — Constitution VII, offline) ⚠️

> Write these FIRST; ensure they FAIL before implementation

- [X] T013 [P] [US2] Chooser cases in `app/studio/src/screens/models/FamilyCard.test.tsx`: choose an available option → `selectCapability(family, id)` + "applies on next production" confirmation; revert → `clearCapability(family)`; unavailable option not selectable; paid/cloud selection records preference (no key field, no network send); `env_override` present → shown as environment-in-force (stored selection not presented as active); `selected_stale` → prior-choice-unavailable note + `active` in force; save failure → plain retry, prior state intact

### Implementation for User Story 2

- [X] T014 [US2] Extend `app/studio/src/screens/models/FamilyCard.tsx` chooser path — for `chooser` families render the plain-language option chooser + revert-to-default, wire `selectCapability` / `clearCapability`, show the `models.applies.nextProduction` confirmation, and render env-override (`models.override.note`, env-var name) and stale (`models.stale.note`) honesty; paid/cloud selection is preference-only (no send, no key field). Same file as T010 — sequential

**Checkpoint**: US1 and US2 both work independently — read the capabilities (US1) and choose/revert a model with honest timing and override/stale states (US2)

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Retire the raw embed cleanly, prove coexistence, and validate the build/suite

- [X] T015 [P] Rewrite/relocate `app/studio/src/screens/Models.test.tsx` for the new plain-language surface — preserve and strengthen the existing no-secret assertions (no `key|secret` label, no textbox) against the operator screen
- [X] T016 [P] Verify coexistence: `app/studio/src/components/Capabilities.tsx` is untouched and still rendered by the developer Console (`app/studio/src/App.tsx`); confirm `app/studio/src/api.ts` is unchanged (existing wrappers reused)
- [X] T017 Run `cd app/studio && npm run test && npm run build` — Vitest green (model + screen + family + relocated Models tests), typed `models.*` catalog keys resolve, production build clean
- [X] T018 Confirm the root `pytest` suite is untouched and green (S7 adds no server surface) — no new/changed Python
- [X] T019 Execute the `quickstart.md` manual smoke checklist (plain language, choose/revert/persist, paid key-name-only + no field, env-override honesty, EN/FR, machine-level)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS US1 and US2** (`capabilityModel.ts` + EN/FR strings)
- **US1 (Phase 3)**: Depends on Foundational — the MVP; delivers the read-only panel + in-app wiring
- **US2 (Phase 4)**: Depends on Foundational; builds on US1's `FamilyCard.tsx` (extends the same file) — implement after US1
- **Polish (Phase 5)**: Depends on US1 (and US2 if shipping both)

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational — read-only display, re-check, empty/error, machine-level
- **US2 (P2)**: After Foundational; shares `FamilyCard.tsx` with US1 (chooser path extends the read-only card), so sequence US1 → US2 to avoid same-file conflict; still independently testable (chooser behavior)

### Within Each User Story

- Tests written and FAILING before implementation (Constitution VII)
- Pure model (Foundational) before components; `ModelOption` → `FamilyCard` → `ModelsScreen`; wiring last

### Parallel Opportunities

- **Setup**: T002 [P] alongside T001
- **Foundational**: T003 / T004 / T005 all [P] (different files: `en.ts`, `fr.ts`, `capabilityModel.test.ts`); T006 after T005
- **US1**: T007 / T008 [P] (different test files); T009 [P] then T010 → T011 → T012 (dependency chain / shared files)
- **US2**: single implementation file (T014) after its test (T013)
- **Polish**: T015 / T016 [P]; T017 / T018 / T019 gated on implementation

---

## Parallel Example: Foundational

```bash
# Different files — run together:
Task: "Add EN strings for models.* in app/studio/src/i18n/en.ts"          # T003
Task: "Add FR strings for models.* in app/studio/src/i18n/fr.ts"          # T004
Task: "Write capabilityModel.test.ts (fails first)"                        # T005
# Then, once T005 exists:
Task: "Implement capabilityModel.ts to pass T005"                          # T006
```

## Parallel Example: User Story 1 tests

```bash
Task: "ModelsScreen.test.tsx — load/render/recheck/error/empty/machine-level/a11y"   # T007
Task: "FamilyCard.test.tsx — read-only display, non-selectable no-chooser, key-name-only, no field"  # T008
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup → 2. Phase 2 Foundational (CRITICAL) → 3. Phase 3 US1
4. **STOP & VALIDATE**: the panel reads and shows every capability in plain language, localized, secret-free, with re-check and empty/error — demoable as the replacement for the raw embed
5. Deploy/demo

### Incremental Delivery

1. Setup + Foundational → model + strings ready
2. US1 → read-only Capability Panel (MVP) → validate → demo
3. US2 → model chooser + revert + honest timing/override/stale → validate → demo
4. Polish → retire raw embed test, prove coexistence, green build/suite

### Notes

- [P] = different files, no incomplete-task dependency
- S7 touches **only** the frontend: `screens/models/*`, `i18n/{catalog,en,fr}.ts`, `screens/Models.tsx`; `api.ts`, `components/Capabilities.tsx`, the server, and the router are **unchanged**
- Never render a raw `family` code, `entry.id`, `tier`, `reason` code, or a `key_env` **value**; env-var **name** is the only permitted technical token
- Honor env > selection > default: show env-override and stale states honestly; frame a pick as the standing default applied on the next production
- Commit after each task or logical group; stop at any checkpoint to validate a story independently
