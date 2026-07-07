# Contract — Recipe Engine (Brick 8)

Two contracts: the **registry hook** (how recipes are declared, additively) and the **three
HTTP endpoints**. Both are additive: absent registry ⇒ `GET /api/recipes` returns an empty
catalog and the frontend shows no recipe surface; existing mission routes are byte-identical.

All endpoints obey the studio invariants: bound to `127.0.0.1`, no `Access-Control-Allow-
Origin: *`, `path_inside()` on any media/download path, a `_safe_*` id→path guard on every
run id, https-only outbound, keys env-only (never in a request body / persisted / logged).

---

## 1. Registry hook (additive, default-empty)

`agency_studio/recipes/registry.py` exposes `RECIPES: dict[str, Recipe]` (see
`data-model.md`). It is populated by:

- **4 composed recipes** — `full-campaign`, `client-pitch`, `turnkey-event`,
  `social-content-pack` — each declaring its own `Stage[]` (per-recipe subset of
  `mission → compose → export`, always including `mission` + a final collect; image/voice
  **assets are produced within the `mission` stage**, not a standalone stage).
- **13 production recipes** — one per `openmontage/pipeline_defs/<name>.yaml`
  (`animated-explainer`, `animation`, `avatar-spokesperson`, `character-animation`,
  `cinematic`, `clip-factory`, `documentary-montage`, `framework-smoke`, `hybrid`,
  `localization-dub`, `podcast-repurpose`, `screen-demo`, `talking-head`) — each a single
  `pipeline` stage whose **`tier` is derived from the pipeline manifest** (paid-provider
  need ⇒ `cloud`/opt-in, else `local`). Catalog metadata (name/description/category) is read
  from the manifest as **inert data**; the manifest is **never imported in-process**. A
  production run writes a **lightweight deliverable record** to `agency_kit.store` so its
  single artifact lands in the existing library/export (FR-018).

**Invariant**: with `RECIPES` empty (or the `recipes` package absent), the server exposes no
recipe behavior and nothing else changes.

---

## 2. `GET /api/recipes` — the catalog

Read-only. Renders **immediately** (no probe on list — availability is reported per-run).

**200** →
```json
{
  "recipes": [
    {
      "id": "full-campaign",
      "kind": "composed",
      "name_key": "recipes.full_campaign.name",
      "desc_key": "recipes.full_campaign.desc",
      "required_inputs": [{ "key": "subject", "label_key": "recipes.input.subject" }],
      "stages": [
        { "kind": "mission",  "tier": "local", "label_key": "recipes.stage.mission" },
        { "kind": "compose",  "tier": "local", "label_key": "recipes.stage.compose" },
        { "kind": "export",   "tier": "local", "label_key": "recipes.stage.export" }
      ]
    }
  ]
}
```
- Only **keys** cross the wire (i18n resolved client-side) — no localized prose baked in,
  no raw pipeline slug shown as operator content.
- `stages[].tier` defaults `"local"`; a `"cloud"` tier signals the frontend to require an
  explicit opt-in before launch.

---

## 3. `POST /api/recipe` — launch a run (SSE)

Starts the **single active run** and streams the **mission SSE vocabulary** so the existing
`timeline.ts::groupTimeline` + `MissionTimeline` render the whole chain.

**Request body**
```json
{
  "recipe_id": "full-campaign",
  "subject": "a launch campaign for our new coffee subscription",
  "inputs": { "...": "..." },
  "cloud_optins": ["compose"],        // OPTIONAL; absent/empty ⇒ fully local
  "resume_from": "chk_..."             // OPTIONAL; resume-from-failed-stage
}
```
- **No key field** — cloud stages read credentials from the environment only.
- `subject`/`inputs` are untrusted text, handled like a mission goal (bounded body, no
  filesystem reference).

**Responses**
- **200** `text/event-stream` — the run stream (below).
- **409** — a run is already active (single-active-run). Body: localized message key +
  the active `run_id`. Never starts a second run.
- **400** — missing a required input (localized "we need X"); malformed/oversized body.
- **501** — the launched recipe's required capability is unavailable on this machine
  (e.g. a production pipeline whose Node/skills/tools are absent). Body carries the honest
  install hint. Other recipes remain launchable.

**Run stream (SSE frames)** — the existing `MissionEvent` phases, wrapped per stage:
```
event: message
data: {"stage":"mission","phase":"router", ...}          # existing mission phases flow through
data: {"stage":"mission","phase":"inspect","verdict":"PASS"}   # inspector veto UNCHANGED
data: {"stage":"mission","phase":"asset","asset":{...}}  # image/voice assets stream WITHIN the mission stage
data: {"stage":"compose","phase":"asset","asset":{...}}  # composition via openmontage_backend (subprocess)
data: {"stage":"export","phase":"asset","asset":{...}}   # bundle collected
data: {"phase":"done","mission_id":"..."}                # terminal → dossier + creatives in the library/export
```
Terminal frames reuse the mission vocabulary:
- `done` → the collected package (dossier + creatives) is reachable via the existing
  `fetchMissionBundle(mission_id)` / library.
- `error` / `vetoed` → **stops honestly**, preserves completed stages' outputs, and carries a
  **resume** affordance (`checkpoint` id) so the run resumes from the failed stage.
- `cancelled` → kill-tree completed, no orphan work, honest cancelled state.

---

## 4. `POST /api/recipe/{run_id}/cancel`

Reuses the mission cancel path. Sets the run's `explicit` + `cancel` events in
`server.runs`; the orchestrator polls `should_cancel` and **kill-tree**s the active stage's
child (each stage's subprocess runs in its own session — `killpg` the whole tree, Remotion's
headless Chromium and any CLI-agent grandchildren included).

- **202** `{ "status": "cancelling", "run_id": "..." }`
- **404** — unknown/already-finished run (unregistered the moment it ends; idempotent).

---

## Test contract (offline)

Backend (`pytest`, all three boundaries monkeypatched — `runner_bridge.run`, the OM-pipeline
subprocess spawn, `openmontage_backend._spawn_render`):

1. **Done-when** — `full-campaign` runs `mission → compose → export` (image/voice assets render within the mission stage); the stream
   ends `done`; the dossier record carries both the strategy content and the creatives.
2. **Veto parity** — a mission-stage `VETO` holds the run identically to a standalone mission;
   no downstream creative stage runs on unapproved strategy.
3. **Single active run** — a 2nd `POST /api/recipe` during an active run gets **409**; no
   second run starts.
4. **Resume-from-stage** — a run that fails at `compose` writes a checkpoint; resuming skips
   `mission`/`assets` (replays outputs, mission does **not** re-run) and restarts at `compose`.
5. **501-degradation** — a production recipe whose `om_bridge` probe fails returns **501** +
   hint; the catalog and other recipes stay usable.
6. **Local-first** — a default launch sets no cloud backend and makes no network call beyond
   sanctioned mission research; an explicit `cloud_optins` entry is required to reach cloud;
   no key is ever read from the body.
7. **Cancel** — cancel mid-run kills the active stage's tree; no orphan process; `cancelled`
   terminal frame.

Frontend (`Vitest`): catalog renders EN + FR with parity; launch reachable from **both** Home
and the Guided Brief; missing-input prompt; per-stage tier badges + explicit cloud opt-in;
the run view reuses `MissionTimeline` (SSE frames replayed through `groupTimeline`).
