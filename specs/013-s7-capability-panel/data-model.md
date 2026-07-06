# Phase 1 Data Model — S7 Capability & Model Panel

**Feature**: Capability & Model Panel (Brick 7 · Screen S7) · **Date**: 2026-07-06

S7 introduces **no new persisted entity** and **no server-side type**. Every entity below is a
**read-only view** of the existing Brick 4 inventory or an **ephemeral view-model** computed in
the frontend for presentation. The one write path (choosing/reverting a model) mutates the
**existing** server-side `SelectionStore`, whose shape is inherited unchanged.

## Source-of-truth types (existing, unchanged)

From `app/studio/src/types.ts` (emitted by `GET /api/capabilities`):

| Type | Key fields | S7 use |
|---|---|---|
| `CapabilityInventory` | `families: CapabilityFamilyView[]`, `generated_at` | The whole panel's input |
| `CapabilityFamilyView` | `family: Family`, `selectable: bool`, `entries: CapabilityEntry[]`, `selected: string\|null`, `selected_stale: bool`, `env_override: string\|null`, `active: string` | One capability family |
| `CapabilityEntry` | `id`, `label`, `family`, `cost: "free"\|"paid"\|"free_paid"`, `availability: "available"\|"unavailable"`, `reason: string\|null`, `enablement: string\|null`, `tier: string\|null`, `note: string`, `default: bool`, `key_env: string\|null` | One model option |
| `Family` | `"image"\|"video"\|"visual"\|"embedding"\|"kg-extraction"\|"stt"\|"tts"\|"production-tools"\|"mcp"` | 7 selectable + 2 non-selectable |

**Invariant**: S7 reads these and **never** renders `family` (code), `entry.id`, `tier`, or a
`key_env` **value** as operator-facing content. `key_env` yields only the variable **name** as an
enablement hint (FR-013's one permitted technical token).

## Ephemeral view-model (new, frontend-only — `capabilityModel.ts`)

Pure functions map the raw inventory to presentation view-models. None is persisted.

### `CapabilityView` (per family)

| Field | Type | Derivation |
|---|---|---|
| `family` | `Family` | passthrough (used as React key / catalog lookup, never rendered raw) |
| `nameKey` | `CatalogKey` | fixed map: `image`→`models.family.image`, … , `mcp`→`models.family.mcp` |
| `descriptionKey` | `CatalogKey` | fixed map per family |
| `displayKind` | `"chooser" \| "readonly"` | `selectable ? "chooser" : "readonly"` |
| `status` | `CapabilityStatus` | from the family's entries (see below) |
| `options` | `ModelOptionView[]` | `entries.map(...)` |
| `activeOptionId` | `string` | `active` (matched to an option for display; not rendered raw) |
| `selectedId` | `string \| null` | `selected` (the operator's stored standing default, or null = built-in default) |
| `isEnvOverridden` | `boolean` | `env_override != null` |
| `envVarName` | `string \| null` | `env_override` (a variable **name** only) |
| `isStale` | `boolean` | `selected_stale` |

### `ModelOptionView` (per entry)

| Field | Type | Derivation |
|---|---|---|
| `id` | `string` | `entry.id` (form value only; never shown as content) |
| `label` | `string` | `entry.label` (product name — shown as-is, not translated) |
| `costKind` | `"free_local" \| "paid_cloud" \| "free_or_paid"` | `cost` → plain class (`free`→free_local, `paid`→paid_cloud, `free_paid`→free_or_paid) |
| `available` | `boolean` | `availability === "available"` |
| `isDefault` | `boolean` | `entry.default` |
| `enablementHintKey` + `envVarName?` | `CatalogKey`, `string?` | when unavailable: plain "how to enable" from a `reason`→key map; if `key_env` set, the var **name** for the hint |
| `keyConfigured` | `boolean \| null` | for a paid/cloud option: `available` ⇒ configured; unavailable-with-`key_env` ⇒ not configured; else `null` |

### `CapabilityStatus` (per family, plain-language)

Enum resolved from the family's entries → one localized status:

| Status | Condition | Catalog key |
|---|---|---|
| `ready_free_local` | an available `free` option exists and is/would be active | `models.status.readyFreeLocal` |
| `ready_cloud` | active choice is an available `paid`/`free_paid` (configured) option | `models.status.readyCloud` |
| `not_available` | no available option in the family | `models.status.notAvailable` (+ enablement hint) |

## Reason → plain-language map (raw suppression)

Raw `entry.reason` codes are **never** shown; they map to localized hints:

| Raw reason (`CapabilityEntry.reason`) | Plain status key |
|---|---|
| `missing_binary` | `models.reason.missingBinary` |
| `missing_model_files` | `models.reason.missingModelFiles` |
| `model_files_mismatch` | `models.reason.modelFilesMismatch` |
| `gateway_down` | `models.reason.gatewayDown` |
| `API key not set` (paid, `key_env` set) | `models.reason.keyNotSet` (+ "set `$VAR`") |
| other / unknown | `models.reason.generic` (falls back to `entry.enablement` prose if present) |

## Write path (existing store, unchanged shape)

| Action | Call | Effect |
|---|---|---|
| Choose a model | `selectCapability(family, id)` → `PUT /api/capabilities/selection` | Sets the family's **standing default** in `SelectionStore`; applied on **next production** (server invalidates lazy consumers); returns updated `CapabilityFamilyView` |
| Revert to default | `clearCapability(family)` → `DELETE /api/capabilities/selection/{family}` | Removes the family's stored selection → built-in default resumes |
| Re-check | `fetchCapabilities(true)` → `GET /api/capabilities?refresh=1` | Re-probes and re-reads the whole inventory |

**Precedence (inherited, unchanged)**: env > selection > default. A non-null `env_override`
means the environment is in force regardless of `selected` — surfaced honestly (`isEnvOverridden`).

## State transitions (view-level, no persistence)

```text
load → { loading }
      → success: inventory rendered (per-family: chooser | readonly)
      → error: plain retry

choose(available option)  → PUT → re-read → option is the standing default (persists on reload)
revert                    → DELETE → re-read → built-in default in force
recheck                   → GET ?refresh=1 → re-read (availability changes reflected)

env_override present  → family shown "environment is deciding" (selected retained, not in force)
selected_stale        → family shown "prior choice unavailable; <active> in force" + pick-again/revert
```

**No new entity persists.** The only durable effect is a row in the **existing** `selections.json`
via the **existing** endpoints; the store shape and the env>selection>default precedence are
untouched (FR-006, FR-018).
