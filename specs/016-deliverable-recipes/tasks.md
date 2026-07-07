---

description: "Task list — Deliverable Recipes (Brick 8)"
---

# Tasks: Deliverable Recipes — Mission → Production in One Run (Brick 8)

**Input**: Design documents from `/specs/016-deliverable-recipes/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/recipe-engine.md ✅

**Tests**: Per Constitution VII, every code change ships offline tests (no network, no CLI, no
Node, no GPU — the three boundaries `runner_bridge.run`, the OM-pipeline subprocess spawn, and
`openmontage_backend._spawn_render` are monkeypatched). Test tasks are included and written
FIRST for each code phase.

**Organization**: Tasks are grouped by the spec's four user stories so each is an
independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3 / US4 (Setup / Foundational / Polish carry no story label)
- Exact file paths are in every task.

## Path Conventions

Backend: `agency_studio/recipes/`, endpoints in `agency_studio/server.py`, tests in `tests/`.
Frontend: `app/studio/src/screens/recipes/`, reusing `timeline.ts` / `screens/missions/` /
`screens/brief/` / `screens/home/` / `i18n/`. Reuse over rebuild — see quickstart.md.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Additive skeletons only — with these in place and empty, the studio is byte-identical.

- [X] T001 Create the recipe package skeleton `agency_studio/recipes/__init__.py` exporting a default-empty `RECIPES` placeholder, per plan.md Project Structure
- [X] T002 [P] Scaffold the frontend module `app/studio/src/screens/recipes/` (empty `RecipeCatalog.tsx`, `RecipeLaunch.tsx`, `recipesApi.ts`, `recipesModel.ts`) and register route id `recipes` → `<RecipeCatalog />` in `app/studio/src/shell/Shell.tsx` (existing routes unchanged)
- [X] T003 [P] Add the `recipes.*` CatalogKey block to `app/studio/src/i18n/catalog.ts` with matching (empty) EN/FR entries in `app/studio/src/i18n/en.ts` and `fr.ts` (parity scaffolding)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core types, the default-empty registry mechanism, endpoint dispatch, and the
orchestrator seam that ALL user stories build on.

**⚠️ CRITICAL**: No user story work begins until this phase is complete.

- [X] T004 [P] Define `Recipe`, `Stage`, `RecipeRun` dataclasses in `agency_studio/recipes/models.py` (Stage.kind ∈ {mission,compose,pipeline,export} — assets are produced within the mission stage, no standalone `assets` driver; Stage.tier default `local`, `pipeline` tier derived from the OM manifest; per-recipe stage set) per data-model.md
- [X] T005 Implement the default-empty registry mechanism in `agency_studio/recipes/registry.py` — `RECIPES: dict[str, Recipe]` plus an inert-data reader for `openmontage/pipeline_defs/*.yaml` catalog metadata (name/description/category read as data — **no in-process import** of `openmontage/`)
- [X] T006 Add recipe endpoint dispatch in `agency_studio/server.py` for `GET /api/recipes`, `POST /api/recipe`, `POST /api/recipe/{id}/cancel` → handler stubs reusing `_register_run`/`_unregister_run`, the SSE header helper, `path_inside`, and a `_safe_*` run-id→path guard (stubs return empty/501 until stories fill them; existing routes byte-identical)
- [X] T007 [P] Define the stage-driver interface and the sequential `orchestrator` seam in `agency_studio/recipes/orchestrator.py` and `agency_studio/recipes/stages.py` (stage loop + mission-vocabulary SSE emit shape; drivers are `NotImplemented` placeholders)

**Checkpoint**: Foundation ready — user stories can proceed.

---

## Phase 3: User Story 1 - Launch a campaign for X → dossier + creatives in one run (Priority: P1) 🎯 MVP

**Goal**: A single run of the `full-campaign` recipe chains mission → compose → export (image/
voice assets render within the mission stage) and yields the sourced, inspector-gated strategy
dossier AND its creatives, collected together — no terminal touched.

**Independent Test**: Launch `full-campaign` with a subject; confirm one run produces (a) a
sourced dossier that passed the unchanged inspector gate and (b) creatives, both retrievable
together from the existing library/export.

### Tests for User Story 1 (offline — write first, ensure they FAIL) ⚠️

- [X] T008 [P] [US1] Orchestrator chain test in `tests/test_recipes_orchestrator.py` — `full-campaign` runs mission→compose→export, stream ends `done`, the dossier record carries strategy content AND creatives (monkeypatch `runner_bridge.run` + `openmontage_backend._spawn_render`)
- [ ] T009 [P] [US1] Veto-parity test in `tests/test_recipes_veto.py` — a mission-stage VETO holds the run identically to a standalone mission; no downstream compose/export runs on unapproved strategy
- [X] T010 [P] [US1] Run-endpoint test in `tests/test_recipes_endpoint_run.py` — `POST /api/recipe` streams SSE mission-vocabulary frames and a terminal `done` carrying the collected `mission_id`; 400 on a missing required input

### Implementation for User Story 1

- [X] T011 [US1] Add the `full-campaign` composed recipe definition (orchestrated stages mission→compose→export — image/voice assets are rendered within the mission stage; all `tier=local`, required `subject` input) to `agency_studio/recipes/registry.py`
- [X] T012 [US1] Implement the `mission` stage driver in `agency_studio/recipes/stages.py` — calls `agency_cli.runner_bridge.run(**run_kwargs)` exactly as `server._handle_run_mission` (**inspector veto + source-verification UNCHANGED**), rendering assets via the existing `asset_clause`/`_build_render_assets` hook; returns dossier id + media
- [X] T013 [US1] Implement the `compose` stage driver in `agency_studio/recipes/stages.py` — drives `agency_studio/openmontage_backend.py` across the subprocess boundary to render the campaign composition video onto the dossier
- [X] T014 [US1] Implement the `export` stage driver in `agency_studio/recipes/stages.py` — collects the dossier + creatives into one package via the existing `agency_studio/bundler.py` + `agency_kit.store`
- [X] T015 [US1] Implement the sequential `orchestrator.run()` in `agency_studio/recipes/orchestrator.py` — drive declared stages in order, stream mission-vocabulary SSE per stage, register the run in `server.runs`, and stop honestly on failure/veto preserving completed outputs
- [X] T016 [US1] Wire `POST /api/recipe` in `agency_studio/server.py` to launch the orchestrator and stream SSE (reuse the mission SSE header + drain loop); reject a missing required input with a localized 400
- [X] T017 [P] [US1] Implement `startRecipe()` (SSE, mission-stream shape) plus `listRecipes()`/`cancelRecipe()` in `app/studio/src/screens/recipes/recipesApi.ts`
- [ ] T018 [US1] Implement `RecipeLaunch.tsx` in `app/studio/src/screens/recipes/` — collect the subject via the guided brief (`screens/brief/composeMission`), POST `/api/recipe`, and hand the stream to the existing `screens/missions/MissionTimeline`
- [X] T019 [P] [US1] Frontend test `app/studio/src/screens/recipes/RecipeLaunch.test.tsx` — launching a recipe posts the subject (+ chosen opt-ins) via `missionSession.launchRecipe` and hands off to the `#/missions` unified timeline; an empty subject does not launch

**Checkpoint**: MVP — the done-when is met; dossier + creatives collected in one run.

---

## Phase 4: User Story 2 - Choose the right recipe from a plain-language catalog (Priority: P2)

**Goal**: All 13 OpenMontage production pipelines + 4 composed recipes are listed with
plain-language name/produces/needs and launchable from Home/Brief; a missing production
capability degrades to an honest 501 + install hint.

**Independent Test**: Open the catalog; confirm all 17 recipes appear with descriptions and
required inputs; launch one of each family; a recipe whose capability is absent shows a clean
install hint and other recipes stay usable.

### Tests for User Story 2 (offline — write first) ⚠️

- [X] T020 [P] [US2] Registry test in `tests/test_recipes_registry.py` — 4 composed + 13 production recipes present; production defs carry inert pipeline metadata; per-recipe stage sets valid (e.g. `social-content-pack` omits long-form compose); a production recipe whose manifest needs paid providers is marked `cloud`/opt-in (tier derived from the manifest)
- [X] T021 [P] [US2] Catalog-endpoint test in `tests/test_recipes_endpoint_catalog.py` — `GET /api/recipes` returns all 17 with i18n **keys only** (no localized prose, no raw pipeline slug as operator content)
- [X] T022 [P] [US2] Pipeline-501 + output test in `tests/test_recipes.py` — a production recipe whose `om_bridge` probe fails returns an honest error frame + hint (catalog and other recipes stay usable); a successful production run writes a **lightweight deliverable record** to the store so its artifact is retrievable via the library/export path (FR-018); plus an OM_ERROR honest-failure (no record) and a work-dir escape rejection

### Implementation for User Story 2

- [X] T023 [US2] Add the 3 remaining composed recipe defs (`client-pitch`, `turnkey-event`, `social-content-pack`) with per-recipe stage sets to `agency_studio/recipes/registry.py`
- [X] T024 [US2] Register the 13 production recipes in `agency_studio/recipes/registry.py` from `openmontage/pipeline_defs/*.yaml` metadata (read as inert data; one `pipeline` stage each, its `tier` **derived from the manifest** — paid-provider need ⇒ `cloud`/opt-in, else `local`)
- [X] T025 [US2] Implement the subprocess-only pipeline driver in `agency_studio/recipes/om_bridge.py` — probe (Node/npx/engine/manifest/executive-producer skill) → `RecipeStageUnavailable` (501 + hint); spawn a CLI-agent run in `openmontage/` (cwd = subtree) driving the pipeline's executive-producer skill, with kill-tree cancel, hard timeout, atomic output, and work-dir-escape rejection; **no in-process import** (orchestration read as inert manifest data)
- [X] T026 [US2] Implement the `pipeline` stage driver in `agency_studio/recipes/stages.py` (delegates to `om_bridge`, unavailable → honest error frame) and write the produced artifact into a **lightweight deliverable record** in `agency_kit.store` (subject as label, media attached) so it lands in the existing library/export (FR-018)
- [X] T027 [US2] Wire `GET /api/recipes` in `agency_studio/server.py` to serialize the registry (keys only, immediate — no probe on list)
- [X] T028 [P] [US2] Implement `catalogView()` + Composed/Production grouping in `app/studio/src/screens/recipes/recipesModel.ts` (localized, no raw ids/slugs as operator content)
- [ ] T029 [US2] Implement `RecipeCatalog.tsx` in `app/studio/src/screens/recipes/` — plain-language rows (name / produces / needs), honest "needs install" note for an unavailable recipe, launch entry into `RecipeLaunch`
- [X] T030 [US2] Add the additive "start from a recipe" entry on Home (`app/studio/src/screens/home/`) and the recipes deliverable-type path in the Guided Brief (`app/studio/src/screens/brief/`) — existing behavior intact
- [X] T031 [P] [US2] Fill EN + FR strings for every `recipes.*` key in `app/studio/src/i18n/en.ts` and `fr.ts` (parity)
- [X] T032 [P] [US2] Frontend test `app/studio/src/screens/recipes/RecipeCatalog.test.tsx` — renders composed + production recipes in EN + FR with plain-language tier badges (no raw ids/slugs); launch reaches the run surface (the honest 'needs install' note is a launch-time 501 error frame on the timeline, not a catalog probe)

**Checkpoint**: The full menu is browsable and launchable.

---

## Phase 5: User Story 3 - Stay local-first, explicit opt-in for anything paid (Priority: P3)

**Goal**: Each stage shows its local(free)/cloud tier before launch; a default launch stays
fully local; a paid cloud stage requires an explicit per-run opt-in; keys stay env-only.

**Independent Test**: Open any recipe, confirm stages are local by default, launch without
opting in and confirm no cloud/network beyond sanctioned mission research; opt a stage into
cloud and confirm the choice is required and visible before launch.

### Tests for User Story 3 (offline — write first) ⚠️

- [X] T033 [P] [US3] Local-first test in `tests/test_recipes_local_first.py` — a default launch sets no cloud backend and makes no network call beyond sanctioned mission research; a cloud stage runs only when `cloud_optins` includes it; no key is ever read from the request body

### Implementation for User Story 3

- [ ] T034 [US3] Resolve each stage's `tier` in `agency_studio/recipes/stages.py` — mission/compose via the existing `IMAGE_MODELS`/`VIDEO_MODELS` local selection, and a `pipeline` stage's tier from its manifest; a `cloud` stage runs cloud only when `RecipeRun.cloud_optins` includes it (keys read from env only)
- [X] T035 [US3] Honor `cloud_optins` in `POST /api/recipe` (`agency_studio/server.py`) — never accept a key field; ignore/reject any secret present in the body
- [ ] T036 [P] [US3] Implement `stageTierBadges()` in `app/studio/src/screens/recipes/recipesModel.ts` and the explicit cloud opt-in toggles (default off) in `RecipeLaunch.tsx`
- [X] T037 [P] [US3] Tier-opt-in coverage folded into `RecipeLaunch.test.tsx` — tier badges show local(free)/cloud; a local stage is never opt-in-able and the cloud opt-in defaults off (a default launch stays local); opting a stage into cloud is explicit + visible before launch

**Checkpoint**: Cost/privacy control is visible and default-safe.

---

## Phase 6: User Story 4 - Follow the whole run on one timeline (Priority: P3)

**Goal**: The run is one unified S3 timeline; only one run is active at a time; the user can
cancel (kill-tree) or resume from a failed stage; partial failures are honest.

**Independent Test**: Launch a composed recipe, confirm all stages appear as one continuous
`MissionTimeline`; a 2nd launch is blocked with a plain message; cancel stops the whole tree
with no orphan; a failure offers resume-from-failed-stage without re-running the mission.

### Tests for User Story 4 (offline — write first) ⚠️

- [X] T038 [P] [US4] Single-active-run test in `tests/test_recipes_single_active.py` — a 2nd `POST /api/recipe` during an active run returns 409; no second run starts
- [X] T039 [P] [US4] Resume test in `tests/test_recipes.py` — a run that fails at compose writes a checkpoint; resuming replays the completed mission (the mission does NOT re-run) and restarts at compose
- [X] T040 [P] [US4] Cancel test in `tests/test_recipes_cancel.py` — cancel mid-run kills the active stage's tree (no orphan), emits a `cancelled` terminal frame

### Implementation for User Story 4

- [X] T041 [US4] Enforce the single-active-run guard in `POST /api/recipe` (`agency_studio/server.py`) via a `server.runs`/`runs_lock` slot → localized 409 when a run is active
- [X] T042 [US4] Wire `POST /api/recipe/{id}/cancel` in `agency_studio/server.py` reusing `_handle_cancel_mission` semantics (explicit + cancel events, kill-tree); 404 on unknown/finished run
- [X] T043 [US4] Implement the recipe-run checkpoint envelope in `agency_studio/recipes/checkpoint.py` (`completed_stages` + `outputs`, reusing the mission `_write_checkpoint`/`_load_checkpoint`/`_checkpoint_path` seam; distinguished by `kind`) and resume handling in `agency_studio/recipes/orchestrator.py` + `POST /api/recipe` `resume_from` (replay completed stages, reload the mission dossier instead of re-running it, restart at the failed stage; a fatal post-mission stage writes the checkpoint and returns an error result carrying the resume affordance). Only checkpoints when the mission is complete (nothing to skip otherwise).
- [X] T044 [US4] Emit the thin per-stage `stage` framing on the SSE stream in `agency_studio/recipes/orchestrator.py` so the existing `timeline.ts::groupTimeline` / `MissionTimeline` render the whole chain as one unified timeline; carry the resume affordance (`resumable`/`checkpoint`) on error terminal frames (replayed stages flagged `replayed`)
- [X] T045 [P] [US4] Timeline-reuse covered in `RecipeLaunch.test.tsx` (the run hands off to the `#/missions` MissionTimeline). Resume affordance wired: `missionSession.resume` dispatches a recipe run to `POST /api/recipe {resume_from}` (via `recipesApi.resumeRecipe`) instead of the mission path — the existing timeline/TerminalPanel resume button reuses it unchanged since the recipe error frame already carries `resumable`/`checkpoint` (#23). Tested in `missionSession.test.ts`. Minor deferred edge: after a full page reload the in-memory run kind is lost, so a reload-then-resume would need the kind persisted in `followPointer` (immediate same-session resume — the common path — works). The 2nd-launch block is backend-enforced (409)

**Checkpoint**: Full run model — one timeline, one active run, cancel, resume.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Parity, additivity, security, and the done-when validation across all stories.

- [X] T046 [P] Confirm no new third-party runtime component was introduced (expected none); note the recipe engine in module docstrings and update `docs/LICENSES.md` only if that changed
- [ ] T047 [P] Add an EN/FR parity assertion for all `recipes.*` keys to the i18n test (`app/studio/src/i18n/*.test.ts`) — zero missing/hard-coded strings
- [ ] T048 Additivity regression in `tests/` — with `RECIPES` empty, `GET /api/recipes` is empty and the mission/brief flow is byte-identical; root offline suite (`pytest` + `vitest`) green
- [ ] T049 Run `quickstart.md` validation end-to-end in a monkeypatched harness — launch `full-campaign` → dossier + creatives collected together
- [ ] T050 Security pass — verify `127.0.0.1` bind, no CORS `*`, `path_inside()` on recipe media/download, `_safe_*` on run ids, no key in body/logs, renderer-fixed OM params (subject never chooses compute/filesystem)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (P1)**: no dependencies — start immediately.
- **Foundational (P2)**: depends on Setup — **BLOCKS all user stories**.
- **US1 (P3 phase)**: depends on Foundational. The MVP.
- **US2 (P4)**: depends on Foundational. Catalog + `GET /api/recipes` are independent of US1's run; reuses the launch surface once present.
- **US3 (P5)**: depends on Foundational + US1's stage drivers (tier resolution lives in `stages.py`).
- **US4 (P6)**: depends on Foundational + US1's `POST /api/recipe`/orchestrator (adds guard, cancel, resume, unified-timeline framing).
- **Polish (P7)**: after all desired stories.

### Within Each User Story

- Tests written FIRST and failing before implementation (Constitution VII).
- Models → registry defs → stage drivers → orchestrator → endpoint → frontend.
- Story complete and independently testable before the next priority.

### Parallel Opportunities

- Setup T002/T003 in parallel; Foundational T004/T007 in parallel.
- Within US1: tests T008/T009/T010 in parallel; T017/T019 (frontend, different files) in parallel with backend T011–T016.
- Within US2: tests T020/T021/T022 in parallel; T028/T031/T032 in parallel.
- US2 (catalog) can largely proceed in parallel with US1 (run) once Foundational is done — they touch different endpoints/files.

---

## Parallel Example: User Story 1

```bash
# Tests first (parallel — different files):
Task: "Orchestrator chain test in tests/test_recipes_orchestrator.py"
Task: "Veto-parity test in tests/test_recipes_veto.py"
Task: "Run-endpoint test in tests/test_recipes_endpoint_run.py"

# Then stage drivers (same file stages.py → sequential T012→T013→T014), while the frontend runs in parallel:
Task: "Implement startRecipe()/listRecipes()/cancelRecipe() in recipesApi.ts"   # [P]
Task: "Frontend RecipeLaunch.test.tsx"                                          # [P]
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational (blocks everything) → 3. Phase 3 US1 →
4. **STOP & VALIDATE**: launch `full-campaign` in the monkeypatched harness → dossier +
creatives collected in one run, inspector veto unchanged. That is the brick's done-when.

### Incremental Delivery

Foundational → **US1 (MVP, the done-when)** → US2 (the full 13+4 catalog) → US3 (local-first
opt-in) → US4 (single-run / cancel / resume / unified-timeline polish). Each ships value
without breaking the prior increment; with `RECIPES` empty at any point, the studio is
byte-identical.

---

## Notes

- Reuse over rebuild: mission+veto (`runner_bridge.run`), assets/compose
  (`asset_clause`/`openmontage_backend`), single-run+cancel (`server.runs`), resume
  (checkpoint pattern), output/export (`store` + bundle endpoints), timeline (`groupTimeline`).
- Non-negotiables enforced per task: subprocess-only OpenMontage, inspector veto byte-identical,
  local-first + env-only keys, security invariants, additive default-empty registry, EN/FR,
  English repo, offline tests.
- `stages.py` is touched by T012–T014 (US1), T026 (US2), T034 (US3) — sequence those edits;
  they are not `[P]` with each other.
- Commit after each task or logical group; stop at any checkpoint to validate a story.
