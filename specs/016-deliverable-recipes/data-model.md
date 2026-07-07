# Phase 1 — Data Model: Deliverable Recipes (Brick 8)

All types are **additive**. Backend types live in `agency_studio/recipes/models.py`
(stdlib dataclasses); the registry is **default-empty** (absent ⇒ no catalog, existing
behavior byte-identical). No new persistent store: a run's outputs live on the existing
dossier record in `agency_kit.store`; resume state lives in the existing checkpoint pattern.
Frontend view-models are **pure, read-only projections** — no raw ids/tokens ever shown as
operator content.

---

## Backend entities

### Recipe (registry entry)

The immutable definition of a launchable recipe. Two kinds share one shape.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `str` | Stable slug (e.g. `full-campaign`, `talking-head`). Internal; never shown raw. |
| `kind` | `"composed" \| "production"` | Composed = agency chain; production = one OM pipeline. |
| `name_key` | `CatalogKey` | i18n key → plain-language name (EN/FR). |
| `desc_key` | `CatalogKey` | i18n key → "what it produces + what it needs". |
| `required_inputs` | `list[InputSpec]` | Inputs the user must give (at least a subject/brief for composed). |
| `stages` | `list[Stage]` | Ordered, **per-recipe** — production recipes have exactly one `pipeline` stage; composed recipes declare their own subset of the canonical chain (always incl. `mission` + a final collect/`export`). |
| `pipeline` | `str \| None` | For `production`: the `pipeline_defs/<name>.yaml` id it drives. `None` for composed. |

**Validation**: `id` unique across the registry; `kind == "production"` ⇒ exactly one
`Stage(kind="pipeline")` and `pipeline` set; `kind == "composed"` ⇒ first stage is
`mission` and the run ends by collecting outputs; every `name_key`/`desc_key` resolves in
both EN and FR (parity checked in tests).

### Stage

One step of a recipe. Drives across a subprocess/mission boundary; carries its tier.

| Field | Type | Notes |
|-------|------|-------|
| `kind` | `"mission" \| "compose" \| "pipeline" \| "export"` | Selects the driver in `stages.py`. Image/voice **assets are produced within the `mission` stage** (the existing `asset_clause` step) — there is no standalone `assets` driver; the conceptual "mission → assets → composition → export" chain maps to orchestrated stages **mission → compose → export**. |
| `tier` | `"local" \| "cloud"` | **Defaults `local`.** `cloud` requires explicit per-run opt-in. For a `pipeline` stage the tier is **derived from the OpenMontage pipeline's manifest** (paid-provider need ⇒ `cloud`/opt-in, else `local`). |
| `label_key` | `CatalogKey` | Plain-language stage label for the timeline. |
| `params` | `dict` | Renderer-fixed / whitelisted; the untrusted subject never chooses compute or filesystem. |

**State (per run, transient)**: `pending → running → done` on success; `→ failed` on error;
`→ vetoed` when the mission stage's inspector holds; `→ cancelled` on kill-tree. Only one
stage is `running` at a time. A `failed`/`vetoed` stage stops the run and is the resume
entry point; already-`done` stages are preserved.

### RecipeRun (transient, in-flight)

The single active execution. Not a new persistent record — its durable footprint is the
dossier (outputs) + the checkpoint envelope (resume).

| Field | Type | Notes |
|-------|------|-------|
| `run_id` | `str` | Registry key in `server.runs`; guarded by `runs_lock`; id→path uses a `_safe_*` guard. |
| `recipe_id` | `str` | The launched recipe. |
| `subject` | `str` | The user's brief/subject (untrusted; treated like a mission goal). |
| `cloud_optins` | `set[str]` | Which stages the user explicitly opted into cloud for (default empty ⇒ fully local). |
| `stage_index` | `int` | Cursor; on resume, starts at the first non-completed stage. |
| `outputs` | `dict` | Per-stage outputs (dossier id, media paths) — collected into the final package. |

**Singleton invariant**: at most one `RecipeRun` is active; a launch while one is active is
rejected (409 + localized message), never a second run.

**Output record (both kinds, one retrieval path)**: a **composed** run's outputs attach to
the mission's full dossier record in `agency_kit.store`. A **production** run (no mission
stage, hence no full dossier) writes a **lightweight deliverable record** to the same store —
the recipe subject as its label, the produced media attached — so its single artifact lands
in the existing library/export exactly like any deliverable (FR-018). No separate parallel
store is introduced.

### RecipeRunCheckpoint (resume envelope — reuses the existing pattern)

Written on failure/veto; consumed on resume; deleted on clean finish or explicit stop
(mirrors the mission checkpoint disposition).

| Field | Type | Notes |
|-------|------|-------|
| `id` | `str` | Checkpoint id (via `_checkpoint_path`). |
| `recipe_id` / `subject` | `str` | To re-enter the same recipe/subject. |
| `completed_stages` | `list[str]` | Stage kinds already `done` — skipped on resume. |
| `outputs` | `dict` | Their recorded outputs, replayed so completed stages don't re-run (mission never re-runs). |
| `cloud_optins` | `list[str]` | Re-applied unless the user changes them. |

---

## Frontend view-models (pure, read-only — `recipesModel.ts`)

Derived from the catalog/run data; catalog-key driven; never emit a raw `id`, `pipeline`
slug, or stage token as operator content.

### CatalogRowView

`catalogView(Recipe[]) → CatalogRowView[]`, grouped **Composed** then **Production**.

| Field | Derivation |
|-------|------------|
| `name` / `description` | `t(name_key)` / `t(desc_key)` in the active language. |
| `produces` / `needs` | Plain-language summary from `desc_key` + `required_inputs`. |
| `stageTiers` | `stageTierBadges(stages)` → ordered `{labelKey, tier}` badges (local = free, cloud = opt-in). |
| `available` | `false` ⇒ show honest "needs install" note (from the run/probe error), still listed. |

### LaunchView

For `RecipeLaunch.tsx`: the resolved `required_inputs` (fed through the guided brief /
`composeMission`), the per-stage tier badges, and the **explicit cloud opt-in** toggles
(default off). `requiredInputsMissing(inputs, values)` gates launch and drives the
plain-language "we need X" prompt (FR-015).

### RunView (reuses S3)

No new model — the run's SSE frames flow through the **existing** `timeline.ts::groupTimeline`
+ `MissionTimeline`. A thin stage label (from `label_key`) groups the phases per stage. On
failure/veto the terminal frame carries the **resume** affordance (FR-013a); on completion the
collected package (dossier + creatives) is reachable via the existing library/export
(`fetchMissionBundle`).

---

## Relationships & flow

```
Recipe (registry, immutable)
  └── Stage[]  (per-recipe; mission | compose | pipeline | export — assets render within mission)

Launch → RecipeRun (singleton, transient)
  ├── registered in server.runs  (cancel + kill-tree, single-active guard)
  ├── streams mission-vocabulary SSE  → S3 timeline (unchanged)
  ├── outputs → agency_kit.store dossier + media  → existing bundle/pdf/media.zip
  └── on failure/veto → RecipeRunCheckpoint → resume-from-failed-stage
```

**No new persistence, no new store, no new render system, no in-process OpenMontage import.**
The inspector veto loop, both vendored subtrees, and every existing screen/endpoint stay
byte-identical.
