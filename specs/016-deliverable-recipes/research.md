# Phase 0 — Research: Deliverable Recipes (Brick 8)

Six decisions resolve the plan's approach. Each is grounded in the existing studio
architecture (investigated at plan time) and the constitution. No `NEEDS CLARIFICATION`
remains — the spec's four clarifications (single active run, resume-from-stage, Home+Brief,
per-recipe stage set) are already encoded.

---

## D1 — Composed recipes chain OVER the existing mission+asset path (do not rebuild)

**Decision**: A composed agency recipe's `mission → assets → composition` stages are
delivered by the studio's **existing** mission machinery, not a new production engine. The
mission stage calls `agency_cli.runner_bridge.run(**run_kwargs)` exactly as
`POST /api/mission` does today; the additive `asset_clause` / `_build_render_assets` hook
already renders images and — via `openmontage_backend` — local composition video onto the
dossier, which is saved to `agency_kit.store` and exported through the existing
`/api/mission/{id}/bundle.zip` · `pdf` · `media.zip`.

**Rationale**: The done-when ("launch a campaign for X → dossier AND creatives in one run")
is *already* most of what a mission with asset rendering does. Reusing it (a) keeps the
**inspector veto loop byte-identical** (Principle III/X), (b) makes the P1 slice
**offline-testable** on a machine with no GPU/agentic stack (monkeypatch `runner_bridge.run`
and `_spawn_render`), and (c) means the recipe engine is orchestration + configuration, not
a second rendering system.

**Alternatives considered**: Build a standalone production pipeline for composed recipes —
rejected: it would duplicate the asset/veto/store/export machinery, risk diverging from the
veto path, and be far harder to test offline. Drive composed recipes entirely through
OpenMontage agentic pipelines — rejected: that is the heavy, GPU/Node-dependent A2 work and
would make the done-when unreachable on most machines.

---

## D2 — OpenMontage production pipelines are driven ONLY across the subprocess boundary

**Decision**: A **production recipe** (one of the 13 pipelines) is driven by
`agency_studio/recipes/om_bridge.py`, which spawns a **CLI-agent subprocess** in the
`openmontage/` working directory to execute the pipeline's `executive-producer`
orchestration skill (as declared in `pipeline_defs/<name>.yaml`). `om_bridge` **never
imports `openmontage/` in-process**. It first runs a cheap **probe** (Node/npx present, the
subtree present, the pipeline's prerequisites installed) and raises a
`RecipeStageUnavailable` (→ HTTP 501 + install hint) when a prerequisite is missing —
exactly the `openmontage_backend._probe_local` model. Pipeline **catalog metadata** (name,
description, category) is read from the YAML manifests as **inert data**, not by importing
the package.

**Rationale**: Constitution V forbids importing `openmontage/` in-process (its
`tools/base_tool.py` autoloads `.env` at import); the manifests themselves declare
`orchestration.mode: executive-producer` with `required_skills` — i.e. they are **agentic
pipelines run by a CLI agent**, aligning with Principle I (the brain is a subscription CLI
agent). Graceful 501-degradation matches the studio's established "capability absent" UX and
keeps the offline suite green (the studio never runs `npm install` itself).

**Alternatives considered**: Import the pipeline loader in-process for a "richer" run —
rejected (violates V, autoloads `.env`, couples the core to the subtree). Reimplement the 13
pipelines natively in the studio — rejected (enormous, duplicates the pinned subtree, breaks
`git subtree pull`).

**Tier & output (analysis remediation C1/U1)**: an agentic pipeline may fan out to **paid
media providers** (its manifest carries `budget_default_usd`). Its **reasoning** runs on the
subscription CLI agent (Principle I satisfied — no billed reasoning path); only paid *media*
is at issue (Principle IV). So the `pipeline` stage's `tier` is **derived from the manifest**:
a pipeline that needs paid providers is surfaced as a **`cloud` stage requiring explicit
per-run opt-in** (never a silent paid run), a fully-local pipeline is **`local`/free**. A
production run has no mission stage, so it writes a **lightweight deliverable record** to
`agency_kit.store` (subject as label, media attached) — landing in the existing library/export
like any deliverable, one retrieval path for both recipe kinds.

---

## D3 — The run view REUSES the S3 mission timeline (one vocabulary, one surface)

**Decision**: A recipe run **streams the same SSE `MissionEvent` phase vocabulary** the
mission console already emits, wrapped with a thin `stage` marker so the client can label
"mission / assets / composition / export". The frontend renders it with the **existing**
`timeline.ts::groupTimeline` + `MissionTimeline` (S3) — no new progress surface. The mission
stage's phases (dept/synth/inspect/asset/verify) flow through unchanged; compose/export
stages emit `AssetStep`-shaped and terminal frames the folder already understands.

**Rationale**: The spec mandates a **single unified timeline reusing S3** (FR-011) and
forbids a competing surface. `timeline.ts` is already generic over phases and has an
exhaustiveness guard, so extending it with a stage wrapper is minimal and keeps one testable
event-ordering model.

**Alternatives considered**: A bespoke recipe-progress component — rejected (duplicates S3,
splits the "honest live status" logic, violates FR-011). A polling status endpoint —
rejected (the studio is SSE-first; polling loses the live per-phase honesty).

---

## D4 — Single active run enforced via the existing run registry

**Decision**: The orchestrator enforces **one active recipe run at a time**. On launch it
checks a single recipe-run slot guarded by the existing `server.runs_lock`; if a run is
active it answers a clear, plain-language rejection (HTTP 409 + localized message) rather
than starting a second run or silently dropping it. The active run is registered in the same
`server.runs` registry the mission cancel path uses, so
`POST /api/recipe/{id}/cancel` reuses `_register_run`/`_unregister_run` and the **kill-tree**
cancel semantics (each stage's child runs in its own session; cancel `killpg`s the whole
tree).

**Rationale**: The clarification chose single-active-run; S3 renders only the live session,
so the run model matches the surface. Reusing the run registry gives cancel + kill-tree for
free and avoids a parallel bookkeeping system.

**Alternatives considered**: Multiple concurrent runs — rejected by clarification (S3 can't
show them; parallel subprocess load risk). A queue — rejected for v1 (adds scheduling state;
the clear-rejection UX is simpler and honest).

---

## D5 — Resume-from-failed-stage via the existing checkpoint envelope

**Decision**: On a stage failure or veto, the run **stops honestly, preserves completed
stages' outputs**, and writes a **recipe-run checkpoint** — `{recipe_id, subject,
completed_stages[], outputs{}}` — on the existing checkpoint pattern
(`_checkpoint_path`/`_on_checkpoint`/`_resolve_resume`). Resuming re-enters the orchestrator,
**skips completed stages by replaying their recorded outputs**, and restarts at the failed
stage — so a run that failed at composition does **not** re-run the mission (with its
internet research and inspector gate). Resume re-applies the same local/cloud choices unless
the user changes them.

**Rationale**: The clarification chose resume-from-failed-stage precisely to avoid re-running
the slow, sourced, inspector-gated mission. The mission path already persists per-phase
checkpoints; lifting that to a per-**stage** envelope is the same mechanism one level up, and
keeps "preserve outputs, never claim false success" (FR-013) honest.

**Alternatives considered**: Restart the whole run — rejected (re-runs the expensive
mission). No resume (relaunch manually) — rejected by clarification. A durable job queue with
retries — rejected (heavy; the checkpoint envelope already exists and is offline-testable).

---

## D6 — Local-first per stage, explicit cloud opt-in, keys env-only

**Decision**: Each `Stage` carries a `tier` that **defaults to `local`**, resolved through
the **existing** backend selection (`IMAGE_MODELS`/`VIDEO_MODELS` local entries;
`openmontage_backend` composition is local Node). A stage that would use a paid cloud
provider is an **explicit per-run opt-in** the user turns on before launch; the catalog shows
each stage's tier up front. Cloud keys are read from the **environment only** — never
accepted in the `POST /api/recipe` body, never persisted, never logged (Principle VI). Absent
opt-in, a run makes **no network calls** beyond the mission's own sanctioned research.

**Rationale**: Constitution IV/VI. Recipes fan out into many production steps — exactly where
a silent paid call would hurt most — so the per-stage tier + explicit opt-in makes cost and
privacy a visible, deliberate choice, reusing the studio's existing local/cloud selection
rather than inventing a new one.

**Alternatives considered**: A single run-wide cloud toggle — rejected (too coarse; a user
may want a local mission but one cloud asset step). Accepting a key in the launch body for
convenience — rejected outright (violates VI).

---

## Cross-cutting notes

- **Deferred to `/speckit-tasks`/implementation, not the spec**: the exact stage set and
  default parameters of each of the 4 composed recipes (which asset kinds, whether a social
  content pack skips long-form composition, etc.) — the spec fixed only that each declares its
  own stage set and yields a coherent dossier + creatives package.
- **Untouched**: `agency_cli`/`agency_kit` internals, `openmontage/`, the inspector veto loop,
  the mission/timeline/library/models/console surfaces, and all existing endpoints.
- **Security posture reused wholesale**: `127.0.0.1`, no CORS `*`, `path_inside()` on media,
  `_safe_mission_id`-style id guards on any recipe-run id → path, https-only outbound,
  renderer-fixed OM parameters.
