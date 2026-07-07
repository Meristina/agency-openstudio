# Quickstart — Deliverable Recipes (Brick 8)

Developer orientation for implementing the recipe layer. Read the spec + plan first; this is
the "where things go and what you must not break" cheat sheet.

## The one-sentence mental model

A **recipe** is an ordered list of **stages**; the **orchestrator** runs them one at a time,
streaming the **existing mission SSE vocabulary** so the **existing S3 timeline** renders the
whole chain — reusing the mission (veto untouched), the asset/composition render path,
cancel/kill-tree, resume-checkpoints, and the store/export you already have.

## Files you create (all additive)

| Path | Job |
|------|-----|
| `agency_studio/recipes/registry.py` | **Default-empty** `RECIPES` dict — 4 composed + 13 production defs (metadata from `pipeline_defs/*.yaml` as inert data). |
| `agency_studio/recipes/models.py` | `Recipe` / `Stage` / `RecipeRun` dataclasses (see `data-model.md`). |
| `agency_studio/recipes/orchestrator.py` | Sequential runner: drive stage → stream SSE → checkpoint; single-active-run guard; honest stop + resume; cancel = kill-tree. |
| `agency_studio/recipes/stages.py` | Stage drivers: `mission`→`runner_bridge.run` (+`asset_clause`), `compose`→`openmontage_backend`, `export`→`bundler`, `pipeline`→`om_bridge`. |
| `agency_studio/recipes/om_bridge.py` | **Subprocess-only** driver for a production pipeline; probe → `RecipeStageUnavailable` (501+hint). **No `openmontage/` import.** |
| `agency_studio/recipes/checkpoint.py` | Recipe-run envelope on the existing checkpoint pattern → resume-from-failed-stage. |
| `app/studio/src/screens/recipes/{RecipeCatalog,RecipeLaunch}.tsx`, `recipesModel.ts`, `recipesApi.ts` | Catalog + launch; run view **reuses** `MissionTimeline`. |
| `tests/test_recipes_*.py`, `app/studio/src/screens/recipes/*.test.*` | Offline coverage. |

## Files you touch minimally

- `agency_studio/server.py` — add dispatch for `GET /api/recipes`, `POST /api/recipe` (SSE),
  `POST /api/recipe/{id}/cancel`, reusing `_register_run`/`_unregister_run`, the SSE header
  helper, `path_inside`, and the `_safe_*` id guards. Existing routes stay byte-identical.
- `app/studio/src/shell/Shell.tsx` — one route id `recipes` → `<RecipeCatalog />`.
- `app/studio/src/screens/home/*` + `screens/brief/*` — an additive "start from a recipe"
  entry (Home) and a recipes deliverable-type path (Brief). Existing behavior intact.
- `app/studio/src/i18n/{catalog,en,fr}.ts` — `recipes.*` keys, **EN + FR parity**.

## Reuse checklist (do NOT rebuild these)

- **Mission + inspector veto** → `agency_cli.runner_bridge.run(**run_kwargs)` — call it the
  way `_handle_run_mission` does; **do not touch the veto or source-verification path.**
- **Images + composition video** → the `asset_clause` / `_build_render_assets` hook and
  `openmontage_backend` (subprocess). Creatives already attach to the dossier.
- **Single active run + cancel/kill-tree** → the `server.runs` registry + `runs_lock`.
- **Resume** → the checkpoint helpers (`_checkpoint_path` / `_on_checkpoint` / `_resolve_resume`).
- **Output + export** → `agency_kit.store` + `/api/mission/{id}/bundle.zip|pdf|media.zip`.
- **Timeline** → `timeline.ts::groupTimeline` + `MissionTimeline` (emit the mission vocabulary).

## Non-negotiables (the gate will check these)

1. **Subprocess boundary** — never `import openmontage...`; drive it via `npx`/CLI-agent
   subprocess only. Read manifests as inert data.
2. **Inspector veto byte-identical** — a recipe is not a bypass; a VETO holds the run.
3. **Local-first** — every stage defaults `local`; cloud is explicit per-run opt-in; keys
   env-only (never in the body/persisted/logged); no network beyond sanctioned mission
   research + opted-in cloud.
4. **Security** — `127.0.0.1`, no CORS `*`, `path_inside()` on media, `_safe_*` on run ids,
   renderer-fixed OM params (subject never chooses compute/filesystem).
5. **Additive** — default-empty registry; with no recipe selected, the studio is
   byte-identical. No edits to `openmontage/` or `agencykit/`.
6. **Offline tests** — monkeypatch `runner_bridge.run`, the OM-pipeline spawn, and
   `_spawn_render`; no network/CLI/Node/GPU. Root `pytest` green.
7. **EN/FR + English repo** — operator strings in EN/FR catalogs; all code/docs/commits English.

## Definition of done (from the spec)

"Launch a campaign for X" → **one run** yields the strategy dossier **and** the associated
creatives, collected together and retrievable from the existing library/export, with the
inspector veto unchanged, no terminal touched — and all 13 production pipelines + 4 composed
recipes selectable from Home/Brief.
