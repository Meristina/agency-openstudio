# Implementation Plan: Deliverable Recipes — Mission → Production in One Run (Brick 8)

**Branch**: `016-deliverable-recipes` | **Date**: 2026-07-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/016-deliverable-recipes/spec.md`

## Summary

Brick 8 adds a **recipe layer** on top of the shipped magic box: a user picks a named,
plain-language recipe from Home/Brief, launches it, follows **one unified timeline** (the
S3 surface), and retrieves the **strategy dossier AND the associated creatives** from a
single run. Two families:

1. **Composed agency recipes** (P1 — the done-when): *full campaign*, *client pitch*,
   *turnkey event*, *social content pack*. Each declares its own stage set; the orchestrated
   stages are **mission → compose → export** (image/voice assets render **within** the mission
   stage — "assets" is the mission's creative output, not a standalone orchestrated step).
2. **Production recipes** (P2): the **13 OpenMontage pipelines** exposed one-to-one, each a
   single-stage recipe driving that pipeline.

**The pivotal design fact — most of the chain already exists.** The studio's mission path
(`POST /api/mission` → `agency_cli.runner_bridge.run`, streamed as SSE) **already**
produces a sourced, **inspector-gated** dossier *and* its creatives: the additive
`asset_clause`/`_build_render_assets` hook renders images and — via
`openmontage_backend` (`npx remotion render`, across the subprocess boundary) — local
composition video, saved onto the dossier in `agency_kit.store` and exportable through the
existing `/api/mission/{id}/bundle.zip` · `pdf` · `media.zip`. The S3 timeline already
folds `AssetStep`/`InspectStep`/dept phases (`timeline.ts::groupTimeline`). So a composed
recipe is **primarily an orchestration + configuration layer over machinery that already
runs**, which is why the P1 done-when is deliverable *and* offline-testable on a machine
with no GPU and no OpenMontage agentic stack.

**What is genuinely new (kept additive):** a small **recipe engine** —
`agency_studio/recipes/` (a **default-empty registry** of recipe definitions + a
sequential **orchestrator** that chains stages, enforces a **single active run**, streams
the mission SSE vocabulary so S3 renders the whole chain unchanged, and supports
**resume-from-failed-stage** via the existing checkpoint pattern) — plus three thin
endpoints (`GET /api/recipes`, `POST /api/recipe` streaming, `POST /api/recipe/{id}/cancel`
reusing the run registry), and a frontend `screens/recipes/` catalog surfaced from **both**
Home and the Guided Brief, reusing `timeline.ts`/MissionTimeline for the run view and the
existing library/export for output. The **13 production pipelines** are exposed and
launchable through the same catalog/launch/timeline, each driven across the **subprocess
boundary** (a CLI-agent run in `openmontage/` for the pipeline's `executive-producer`
skill; `npx remotion` for composition), degrading to a clean **501 + install hint** exactly
like `openmontage_backend` when a machine lacks the pipeline's prerequisites.

**Untouched (byte-identical):** the mission loop, routing engine, the **inspector veto
loop** and source-verification gate, the guided-brief internals, the mission timeline, the
library, models panel, capability probing/selection, developer Console, and the
`openmontage/` + `agencykit/` subtrees. With no recipe selected, the studio behaves exactly
as before.

## Technical Context

**Language/Version**: Python 3.11+ (stdlib-only) for the recipe engine + endpoints;
TypeScript ~5.7 for the frontend. No change to `agencykit/` or `openmontage/`.

**Primary Dependencies**: Existing only — the stdlib `http.server` studio, React 19 +
Vite 6, `agency_cli`/`agency_kit` (the one permitted imported library),
`openmontage_backend` (already vendored). **Zero new runtime dependencies in the core**;
the recipe registry, orchestrator, and OM-pipeline bridge are pure stdlib + subprocess.
OpenMontage pipeline manifests (`openmontage/pipeline_defs/*.yaml`) are read for their
plain-language catalog metadata **only across the subprocess boundary or as inert data** —
never by importing `openmontage/` in-process.

**Storage**: **No new store.** A recipe run reuses `agency_kit.store` for its dossier
record (creatives already attach there), the existing media directory (served through
`path_inside`), and the existing per-mission **checkpoint** envelope pattern
(`_checkpoint_path`/`_on_checkpoint`/`_resolve_resume`) extended with a **recipe-run
envelope** that records completed stages and their outputs so a failed run resumes from the
failed stage without re-running the mission.

**Testing**: `pytest` (backend) with the three existing monkeypatch seams —
`runner_bridge.run` (mission stage), the OM-pipeline subprocess spawn, and
`openmontage_backend._spawn_render` (composition) — so the full chain, single-active-run
guard, resume, and 501-degradation are exercised offline (no network, no CLI, no Node, no
GPU). `Vitest` + @testing-library/react for the recipe catalog, launch-from-Home/Brief,
per-stage local/cloud indicator, and unified-timeline reuse (SSE frames replayed through
the existing `groupTimeline` test-double). Root offline suite stays green.

**Target Platform**: Local stdlib server bound to `127.0.0.1`, serving the built
`app/studio/dist` to a desktop browser on the operator's machine.

**Project Type**: Web application feature — additive backend orchestration module + thin
endpoints + one new frontend screen reusing existing surfaces.

**Performance Goals**: The catalog renders **immediately** (a static read of the in-process
registry; no probe on list). A run **streams SSE** exactly like a mission; the mission
stage dominates early, composition is minutes (existing 900 s render cap), and an agentic
OM pipeline is the long pole (budget-capped in its own manifest). Launch is rejected fast
when a run is already active (single-active-run guard) and when a required input is missing.

**Constraints**: Constitution I–XI. **Subprocess boundary (V):** OpenMontage is driven only
via subprocess — the composition backend (`npx remotion`) and, for production recipes, a
CLI-agent run inside `openmontage/`; **no in-process import** of `openmontage/`.
**Inspector veto (III, X):** the mission stage calls `runner_bridge.run` unchanged — the
veto loop and source-verification gate are byte-identical; a recipe is never a path around
them. **Local-first (IV):** every stage defaults to local/free using the existing
`IMAGE_MODELS`/`VIDEO_MODELS` backend selection; cloud is an explicit per-run, env-keyed
opt-in (keys env-only, never in the request/persisted/logged). **Security (VI):**
`127.0.0.1`, no CORS `*`, `path_inside()` on any media/download path, https-only outbound;
the recipe subject is untrusted text handled like the mission goal; OM render parameters
stay renderer-fixed/whitelisted (the marker never chooses compute or touches the
filesystem — the `openmontage_backend` model). **Single active run**, **resume-from-failed-
stage**, **EN/FR**, **additive (X):** recipes are registry entries + default-`None`/empty
hooks; with none selected the mission/brief flow is byte-identical.

**Scale/Scope**: One new backend package `agency_studio/recipes/` (registry + orchestrator
+ OM-pipeline subprocess bridge + a recipe-run checkpoint helper); **3** new endpoints
(`GET /api/recipes`, `POST /api/recipe` SSE, `POST /api/recipe/{id}/cancel`); one new
frontend module `screens/recipes/` (catalog + launch), reusing `timeline.ts`,
`MissionTimeline`, `GuidedBrief`/`composeMission`, `followPointer`, `listMissions`,
`fetchMissionBundle`, `navigate`; **4** composed-recipe definitions + **13** production-
recipe registry entries (metadata sourced from the pinned `pipeline_defs/`); ~20–30 EN/FR
catalog keys; new pytest + Vitest files. Mission loop, routing engine, guided-brief
internals, timeline rendering, library, models panel, inspector veto loop, Console, and
both vendored subtrees: **untouched**.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — the mission stage runs through the CLI
  engine via `runner_bridge.run` (no token-billed API); production-recipe pipelines are
  driven by a **CLI agent** executing the pipeline's `executive-producer` skill in a
  subprocess. The recipe orchestrator is deterministic plumbing (sequence, guard, stream) —
  it does no billed reasoning. Marginal cost stays zero.
- [x] **II. Engine neutrality**: PASS — the mission stage rides the existing Engine contract
  and production guard unchanged; the recipe layer adds no engine-specific assumption and
  cannot run a mission on an unvalidated engine (that gate is `runner_bridge`'s, untouched).
- [x] **III. No invented information**: PASS — the mission stage calls `runner_bridge.run`
  with the **inspector veto loop and source-verification gate byte-identical**; a veto holds
  the run exactly as today, and a recipe is never a bypass. Creatives are production output,
  not facts. Recipe status reflects only real stage outcomes (no false "delivered").
- [x] **IV. Local-first & offline-by-default**: PASS — every stage defaults to local/free via
  the existing backend selection; cloud is an explicit per-run, env-keyed opt-in. A run makes
  no network calls beyond the mission's own sanctioned research and any explicitly opted-in
  cloud stage. Non-Mac not regressed: composition is cross-platform Node; agentic pipelines
  degrade to a clean 501 where prerequisites are absent.
- [x] **V. Subprocess boundaries**: PASS — OpenMontage is driven **only** via subprocess
  (`npx remotion` for composition; a CLI-agent run in `openmontage/` for production
  pipelines). **No in-process import** of `openmontage/`; pipeline metadata is read as inert
  data. `agencykit/` remains the only imported library; both subtrees are untouched.
- [x] **VI. Security**: PASS — `127.0.0.1` bind, no CORS `*`, `path_inside()` on every new
  media/download path, https-only outbound, keys env-only (never in the request, persisted,
  or logged). The recipe subject is untrusted text treated like the mission goal; OM render
  parameters stay renderer-fixed/whitelisted (no marker-chosen compute or filesystem access).
- [x] **VII. Offline tests**: PASS — the orchestrator, single-active-run guard, resume, and
  501-degradation are covered by pytest with the three subprocess/mission boundaries
  monkeypatched; the frontend by Vitest with SSE frames replayed. No network/CLI/Node/GPU.
- [x] **VIII. End-user simplicity**: PASS — one catalog, one click from Home or the Brief, one
  unified timeline, one collected package, plain-language names/inputs/statuses, no terminal,
  no raw machine tokens shown.
- [x] **IX. License**: PASS — reuses React/Vite + stdlib + the AGPL `openmontage/` subtree via
  subprocess; no new third-party runtime component is introduced, so `docs/LICENSES.md` needs
  no new entry. (Re-checked in Phase 1; a new component would be recorded there.)
- [x] **X. Additive over invasive**: PASS — recipes land as **registry entries + default-empty
  hooks**; the new endpoints sit alongside the existing ones; with **no recipe selected the
  mission/brief flow and every prior screen are byte-identical**. The inspector veto loop is
  not modified. New surface is justified (see Complexity Tracking note), not a rewrite of a
  working path.
- [x] **XI. English everywhere**: PASS — all code, docs, and commits in English;
  operator-facing strings live only in the EN/FR end-user catalogs (explicitly permitted).

**Post-Phase-1 re-check (2026-07-07)**: the design artifacts (research, data-model,
contracts, quickstart) confirm the footprint above — a recipe engine that reuses
`runner_bridge.run` (veto untouched), the `asset_clause`/`openmontage_backend` render path,
the run registry (single-active + cancel/kill-tree), the checkpoint pattern (resume), the
S3 timeline vocabulary, and the existing store/media/export; OpenMontage driven only across
the subprocess boundary; every stage local-first with explicit cloud opt-in; all additive
behind a default-empty registry. All gates hold as marked.

## Project Structure

### Documentation (this feature)

```text
specs/016-deliverable-recipes/
├── spec.md              # Feature spec (clarified: single active run, resume-from-stage, Home+Brief, per-recipe stage set)
├── plan.md              # This file
├── research.md          # Phase 0 — 6 decisions (chain-over-existing-mission, OM-via-subprocess, timeline reuse,
│                         #   single-active-run, resume-from-stage, local-first per-stage tier)
├── data-model.md        # Phase 1 — Recipe / Stage / RecipeRun / recipe-run checkpoint + frontend view-models
├── quickstart.md        # Phase 1 — developer orientation, reuse checklist, non-negotiables
├── contracts/
│   └── recipe-engine.md  # Registry hook contract + 3 endpoints (catalog / run-SSE / cancel) + SSE stage framing
├── checklists/
│   └── requirements.md  # Spec quality checklist (all pass)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
agency_studio/
├── recipes/                          # NEW package — the recipe engine (additive; absent ⇒ no /api/recipes, no catalog)
│   ├── __init__.py
│   ├── registry.py                   # DEFAULT-EMPTY registry: RECIPES: dict[str, Recipe]. Composed defs (4) +
│   │                                 #   production defs (13, metadata from pipeline_defs/*.yaml read as inert data).
│   │                                 #   A recipe declares: id, i18n name/desc keys, required inputs, ordered Stage[]
│   ├── models.py                     # Recipe / Stage / RecipeRun dataclasses; Stage.kind ∈ {mission,pipeline,compose,export};
│   │                                 #   (assets produced WITHIN the mission stage — no standalone assets driver);
│   │                                 #   Stage.tier ∈ {local,cloud} (pipeline tier DERIVED from the OM manifest: paid ⇒ cloud/opt-in);
│   │                                 #   per-recipe stage set (stages may be omitted). Production run → lightweight deliverable record
│   ├── orchestrator.py               # Sequential runner: for each stage → drive it, stream SSE (mission vocabulary +
│   │                                 #   a thin `stage` framing), checkpoint completed stages; stop honestly on
│   │                                 #   failure/veto preserving outputs; enforce SINGLE ACTIVE RUN via the run registry;
│   │                                 #   cancel = kill-tree of the active stage's child (reuses existing pattern)
│   ├── stages.py                     # Stage drivers: mission → runner_bridge.run (veto UNCHANGED) + asset_clause;
│   │                                 #   compose → openmontage_backend (subprocess); export → existing bundler;
│   │                                 #   pipeline → om_bridge
│   ├── om_bridge.py                  # SUBPROCESS-ONLY driver for a production pipeline: spawns a CLI-agent run in
│   │                                 #   openmontage/ for the pipeline's executive-producer skill; probe → 501 + hint
│   │                                 #   when Node/skills/tools absent (the openmontage_backend model). NO in-process import.
│   └── checkpoint.py                 # Recipe-run envelope: {recipe_id, subject, completed_stages[], outputs{}} on the
│                                     #   existing checkpoint pattern → resume-from-failed-stage
├── server.py                         # + route dispatch for 3 endpoints (GET /api/recipes, POST /api/recipe SSE,
│                                     #   POST /api/recipe/{id}/cancel); reuses _register_run/_unregister_run, SSE headers,
│                                     #   path_inside, _safe_* guards. Existing mission routes byte-identical.
└── (runner_bridge / openmontage_backend / assets / bundler / store: reused, UNCHANGED)

app/studio/src/
├── screens/
│   └── recipes/                      # NEW frontend module — catalog + launch (the run view REUSES MissionTimeline)
│       ├── RecipeCatalog.tsx         # Plain-language catalog: 4 composed + 13 production, each name/desc/what-it-produces/
│       │                             #   what-it-needs + per-stage local/cloud tier; 501/unavailable shown honestly
│       ├── RecipeLaunch.tsx          # Collects required inputs via the guided brief (composeMission), shows tiers,
│       │                             #   explicit cloud opt-in; POST /api/recipe → follow the unified timeline
│       ├── recipesModel.ts           # PURE: catalogView(Recipe[]) → grouped, localized rows; requiredInputsMissing();
│       │                             #   stageTierBadges(); all catalog-key driven, no raw ids/tokens as operator content
│       └── recipesApi.ts             # listRecipes(); startRecipe() (SSE, same shape as the mission stream); cancelRecipe()
├── screens/home/                     # + a "Start from a recipe" entry (additive region; existing Home behavior intact)
├── screens/brief/                    # + recipes as a deliverable type inside the Guided Brief (additive question path)
├── shell/Shell.tsx                   # + route id "recipes" → <RecipeCatalog /> (new route; existing routes unchanged)
├── timeline.ts                       # REUSED unchanged: groupTimeline folds the run's mission-vocabulary SSE frames
├── screens/missions/MissionTimeline* # REUSED for the unified run view (one live run at a time)
└── i18n/{catalog,en,fr}.ts           # + recipes.* typed CatalogKeys (names/descs/inputs/tier/errors); EN + FR parity

Tests (offline):
├── tests/test_recipes_orchestrator.py   # chain runs mission→compose→export (assets within mission); veto holds the run identically;
│                                        #   single-active-run rejects a 2nd launch; resume skips completed stages;
│                                        #   pipeline stage 501-degrades when om_bridge probe fails; cancel kills the tree
├── tests/test_recipes_registry.py       # 4 composed + 13 production present; per-recipe stage sets; local-first defaults
└── app/studio/src/screens/recipes/*.test.{ts,tsx}  # catalog renders EN/FR; launch from Home + Brief; missing-input prompt;
                                                     #   tier badges + explicit cloud opt-in; unified timeline reuse
```

**Structure Decision**: a new **additive backend package** `agency_studio/recipes/`
(default-empty registry + sequential orchestrator + a subprocess-only OM-pipeline bridge +
a recipe-run checkpoint helper) exposed through **three thin endpoints**, plus a new
frontend `screens/recipes/` catalog surfaced from **both Home and the Guided Brief**, with
the run view **reusing** `MissionTimeline`/`timeline.ts`. Every heavy capability is
**reused, not rebuilt**: the mission + inspector veto (`runner_bridge.run`), the
image/composition render path (`asset_clause`/`openmontage_backend`), cancel/kill-tree and
single-run enforcement (the run registry), resume (the checkpoint pattern), and
output/export (`agency_kit.store` + the existing bundle endpoints). OpenMontage is driven
**only across the subprocess boundary**; both vendored subtrees and the inspector veto loop
stay byte-identical; with no recipe selected the studio is unchanged.

## Complexity Tracking

> No constitution **violations** — the table is intentionally empty. Brick 8 does introduce
> more surface than a pure-frontend screen (a backend orchestrator + three endpoints),
> because the done-when — chaining mission → assets → composition → export across
> **subprocess boundaries**, with a single active run, kill-tree cancel, and
> resume-from-failed-stage — cannot be done from the frontend alone. This is **additive, not
> invasive**: the engine is a default-empty registry (absent ⇒ no catalog, existing behavior
> byte-identical), the endpoints sit alongside the mission routes, and every heavy capability
> is reused rather than reimplemented. The simplest alternative — extending `POST /api/mission`
> — was rejected because it cannot model per-recipe stage sets, multi-stage resume, or a
> production-pipeline stage without overloading the single-phase mission contract and risking
> the inspector-veto path it must leave byte-identical.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
