# Phase 1 Data Model — Deliverable Library (S4)

S4 introduces **no persisted data**. Every structure below is an **ephemeral, in-browser
projection** derived from data the existing endpoints already return
(`MissionSummary[]` from `listMissions`, `TaxonomyTree` from the shell context,
`Dossier` from `getMission`). No new server field, no new store, no migration.

Source types (existing, in `app/studio/src/types.ts`) — **not modified**:
- `MissionSummary` = `{ mission_id, goal?, route?, verdict?, delivered?, [k]: unknown }`
- `Attribution` = `{ client, project, campaign|null }`
- `TaxonomyTree` = `{ clients: ClientNode[] }` (client → project → campaign, each with a mission count)
- `Dossier` = full saved dossier (`goal`, `route`, `delivered`, `verdicts[]`, `sources[]`, `decisions[]`, `open_to_verify[]`, `residual_risk`, `assets[]`, …)

---

## Entity: Deliverable (view model)

The operator-facing projection of one durable saved mission. Derived from a `MissionSummary`
(list view) and hydrated from its `Dossier` (preview / open).

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | string | `MissionSummary.mission_id` | The durable mission id; the **dedup key** (one Deliverable per id — R3). |
| `title` | string | `MissionSummary.goal` (plain) | Plain-language headline; falls back to a localized "untitled production" when goal is empty. Never a mission id or route. |
| `producedAt` | string \| null | derived from `mission_id` timestamp prefix | Timestamp+slug ids embed the produce time; render as a friendly date. Absent ⇒ omitted, never a raw id. |
| `outcome` | `"successful" \| "needs-attention"` | classifier over `verdict`/`delivered` (R4) | Drives the outcome badge and the outcome filter. |
| `placement` | `TaxonomyPlacement` | `MissionSummary` attribution vs `TaxonomyTree` | Which shelf it sits on (client/project/campaign) or `unassigned`; `orphaned` when its attachment no longer resolves in the taxonomy (→ shown on unassigned/orphaned shelf, FR-013). |
| `preview` | `DeliverablePreview \| null` | hydrated from `Dossier` on demand | Lazily loaded for the in-place preview (R5); null until requested. |

**Identity & uniqueness**: keyed by `id` (`mission_id`). The Library renders one card per
`id`; a defensive dedup collapses any repeat (SC-002 / FR-014a). Interrupted (checkpoint-
only) runs have no durable `MissionSummary` and thus no Deliverable — they never appear (R3).

**Validation / safety rules**:
- No field ever renders a raw `mission_id`, `route` kit name, engine name, verdict code, or
  file path to the operator (FR-003 / SC-004).
- `title` empty ⇒ localized placeholder, never the id.
- Source URLs shown in preview/detail pass `isSafeHttpUrl` and open with
  `rel="noopener noreferrer"` (inherited from `MissionDetail`).

---

## Entity: TaxonomyPlacement

Where a deliverable lives in the Brick 6 taxonomy.

| Field | Type | Notes |
|-------|------|-------|
| `kind` | `"filed" \| "unassigned" \| "orphaned"` | `filed` = resolves in the taxonomy; `unassigned` = no client; `orphaned` = attached to a client/project/campaign the taxonomy no longer contains. |
| `client` | string \| null | present when `kind = filed` (or the stale value when `orphaned`). |
| `project` | string \| null | optional deeper placement. |
| `campaign` | string \| null | optional deepest placement. |

**Transitions** (via filing, the only mutation — R6): `unassigned → filed`,
`filed → filed'` (moved), `filed → unassigned` (cleared), `orphaned → filed/unassigned`
(refiled). Each goes through `assignMission`; each is reversible by filing again.

---

## Entity: DeliverablePreview (view model)

The in-place summary (FR-008), assembled from the hydrated `Dossier` — a strict subset, no
new data.

| Field | Type | Source (`Dossier`) |
|-------|------|--------------------|
| `headline` | string | `goal` (plain) |
| `outcome` | `"successful" \| "needs-attention"` | same classifier as the card |
| `keySources` | string[] | first N `sources` (safe-URL rendered) |
| `keyDecisions` | string[] | first N `decisions` |
| `media` | AssetManifestItem[] | `assets[]` (thumbnails via existing `AssetGallery`); empty ⇒ no media, no broken placeholders (edge case) |

---

## Entity: LibraryModel (root projection)

The whole screen's derived state — pure output of
`buildLibraryModel(missions, taxonomy, scope, view)`.

| Field | Type | Notes |
|-------|------|-------|
| `shelves` | `Shelf[]` | Grouped client → project → campaign tree of Deliverables, in a stable order. |
| `unassigned` | `Deliverable[]` | The unassigned/orphaned shelf. |
| `total` | number | Count after scope+search+filter (drives empty vs populated states). |
| `isEmptyFirstRun` | boolean | No deliverables exist at all (first-run empty state, FR-012). |
| `isEmptyForContext` | boolean | Deliverables exist but none match the active client context (empty-for-context state). |
| `isEmptyForQuery` | boolean | Search/filter matched nothing (nothing-found state, US2-AC3). |

### Shelf

| Field | Type | Notes |
|-------|------|-------|
| `client` | string | Shelf label (plain client name). |
| `projects` | `{ project: string; campaigns: { campaign: string \| null; deliverables: Deliverable[] }[] }[]` | Nested grouping; a campaign of `null` holds project-level (no-campaign) deliverables. |

---

## Entity: LibraryViewState (ephemeral UI state)

The operator's current lens — plain React state, **not persisted** by S4.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `scope` | `{ client, project, campaign }` | shell `useClientContext()` | Active client context; when set, narrows the model (FR-004). |
| `query` | string | search box | Matches `title` + taxonomy placement (client/project/campaign), narrowing as typed (FR-006). |
| `outcomeFilter` | `"all" \| "successful" \| "needs-attention"` | filter control | Combines with query + scope (FR-007). |
| `previewId` | string \| null | preview trigger | Which deliverable's in-place preview is open. |
| `openId` | string \| null | open trigger | Which deliverable is opened to full `MissionDetail`. |

---

## Derivation pipeline (all pure, all client-side)

```text
listMissions()  ─┐
                 ├─► buildLibraryModel(missions, taxonomy, scope, view) ─► LibraryModel
useClientContext ┘        │
   (taxonomy, scope)      ├─ dedupeById (mission_id)            (R3 / FR-014a)
   viewState (query,      ├─ scopeToContext (client context)   (FR-004)
   outcomeFilter)         ├─ classifyOutcome (verdict/delivered)(R4 / FR-007)
                          ├─ matchQuery (title + placement)     (FR-006)
                          └─ groupByTaxonomy (+ unassigned/orphaned shelves) (FR-002/013)

getMission(id) ─► DeliverablePreview (subset)  /  MissionDetail (full open)   (R5)
assignMission(id, …) ─► placement change ─► re-fold model (immediate)         (R6 / FR-010)
```

No structure here is written to disk, sent off-machine, or added to any server response.
