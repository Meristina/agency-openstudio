# Phase 1 Data Model — S5 Import

S5 introduces **no server-side entity** and **no new persisted mission field**. It defines
frontend-only view models over the existing ingestion-store records (`DocMeta`,
`VisualMeta`) plus one small locally-persisted association map. All types below live in
`app/studio/src/screens/import/` (view models) except where they reuse existing `types.ts`
definitions.

## Reused existing records (source of truth — unchanged)

### `DocMeta` (from `types.ts`, via `GET /api/docs`)
`{ id, filename, title, n_chunks, created }` — one ingested document. `id` is stable.

### `VisualMeta` (from `types.ts`, via `GET /api/visual`)
`{ id, filename, title, n_chunks, created }` — one ingested image (its VLM caption is the
`title`). Mirrors `DocMeta`; `id` is stable.

> S5 reads these; it never redefines or extends their persisted shape.

## New frontend view models (ephemeral, derived)

### `MaterialKind`
`"document" | "image"` — the v1 supported kinds (video/audio excluded; FR-012). Determines
the ingest endpoint (`document → /api/docs`, `image → /api/visual`) and the mission
capability that consumes it (`document → knowledge`, `image → visual`).

### `ImportedMaterial`
The operator-facing representation of one brought-in item. Derived by merging a `DocMeta`
or `VisualMeta` with its association.

| Field | Type | Source / Notes |
|-------|------|----------------|
| `id` | string | store id (`DocMeta.id` / `VisualMeta.id`) |
| `kind` | `MaterialKind` | which store it came from |
| `name` | string | plain-language name — `title` if meaningful, else `filename`; **never** shown as a path/store id (FR-013) |
| `importedAt` | number | `created` (epoch) — rendered as a plain date |
| `association` | `ClientAssociation \| null` | from the association map; `null` ⇒ unassigned shelf |

> `ImportedMaterial` is a pure projection — no field is persisted by S5 beyond what the
> stores and the association map already hold.

### `ClientAssociation`
`{ client: string; project?: string; campaign?: string }` — the Brick 6 taxonomy placement
of an item. **Organizational metadata only** — it groups/scopes the operator's view; it does
**not** filter mission retrieval (per-client isolation deferred; spec Clarifications).

### `AssociationMap` (persisted — the only new persistence)
`Record<itemId, ClientAssociation>` in `localStorage` (key namespaced with the shell's
preference prefix). Owned by `associationStore.ts`. Operations: `get(id)`, `set(id, assoc)`,
`clear(id)` (→ unassigned), `prune(knownIds)` (orphan cleanup when an item was removed).
Mirrors the shell's existing `localStorage`-backed client-context/preferences.

### `ImportModel` (the grouped view model)
Output of the pure `importModel.ts` fold `(DocMeta[], VisualMeta[], AssociationMap, scope) → ImportModel`.

| Field | Type | Notes |
|-------|------|-------|
| `shelves` | `ClientShelf[]` | grouped client → project → campaign, ordered plainly |
| `unassigned` | `ImportedMaterial[]` | items with no association |
| `total` | number | count across all shelves + unassigned (for empty-state logic) |

`ClientShelf` = `{ client, projects: { project?, campaigns: { campaign?, items: ImportedMaterial[] } } }`
(same shape family as S4's library shelves, for design-system consistency).

### `BringInResult` (per-item accept/reject)
The outcome of one bring-in attempt (FR-003/FR-004).

| Field | Type | Notes |
|-------|------|-------|
| `status` | `"accepted" \| "rejected" \| "capabilityAbsent"` | drives the feedback UI |
| `kind` | `MaterialKind \| "unsupported"` | classified kind (or unsupported) |
| `reason` | `CatalogKey \| null` | plain-language reason for a rejection (`unsupportedKind` / `tooLarge` / `unreadable`) or the enable-hint for `capabilityAbsent` |
| `item` | `ImportedMaterial \| null` | present on `accepted` |

Mapping from the existing endpoints: `201 → accepted` (build `item` from the returned meta);
`400 → rejected` (`unreadable`/empty); `413`/streamed-cap overflow → `rejected` (`tooLarge`);
`501 → capabilityAbsent`; client-side kind filter → `rejected` (`unsupportedKind`) with no
network call.

### `ImportViewState` (ephemeral)
`{ activeClientContext, /* optional future filter */ }` — the operator's current lens; not
persisted by S5 (the client context comes from the shell selector).

## Brief-side additions (S2 integration — additive, default-off)

### `Brief.useImportedMaterial` (new optional field on the existing brief draft)
`boolean` (default `false`). Persisted with the existing brief draft (`briefDraft.ts`). When
`true` **and** imported material exists, `composeMission.ts` sets `opts.knowledge = true`
(and `opts.visual = true` when any image material exists). When `false`/absent, the composed
`opts` are **byte-identical** to today (Principle X). No other brief field changes.

## Relationships & lifecycle

```
DocMeta / VisualMeta  ──merge──►  ImportedMaterial  ──group by──►  ImportModel.shelves / .unassigned
        ▲                              ▲
        │ (existing stores)            │ AssociationMap (localStorage)
   bring-in: ingestDoc/uploadVisual    │ set/clear on associate
   remove:   deleteDoc/deleteVisual ───┘ prune on orphan

Brief.useImportedMaterial (default off) ──composeMission──► runMission opts.knowledge / opts.visual
```

**Lifecycle of an item**: *chosen* → client-kind-validated → *ingesting* (progress) →
`BringInResult` (*accepted* → appears on the active-context shelf / unassigned · *rejected* /
*capabilityAbsent* → plain feedback, nothing stored) → *associated/re-associated* (local map)
→ *removed* (delete endpoint + `prune`). Removing an item never touches any produced
deliverable (FR-016/SC-009).

## Validation rules (from requirements)

- **Kind** ∈ {document, image}; anything else → `rejected: unsupportedKind` (FR-003/FR-012).
- **Size** bounded by the server's existing caps → overflow surfaces as `rejected: tooLarge` (FR-003).
- **Readability** decided by the server (`400`) → `rejected: unreadable` (FR-003).
- **Capability** absent (`501`) → `capabilityAbsent` state with enable hint (FR-011).
- **Identity** never a path / store id / MIME as the primary label (FR-013).
- **Off-machine** cloud image-captioning opt-in is per-item and OFF by default (FR-010).
