# Contract — Capability Panel Frontend Model & Surface (NEW, S7)

Defines the frontend presentation contract: the pure `capabilityModel.ts` API, the plain-language
family map, the catalog keys, and the screen behavior. Everything here is frontend-only; the
server contract it consumes is `capability-endpoints.md` (unchanged).

## 1. Pure model API (`screens/models/capabilityModel.ts`)

```ts
// Pure, deterministic, offline-testable. No DOM, no network, no persistence.
export type DisplayKind = "chooser" | "readonly";
export type CostKind = "free_local" | "paid_cloud" | "free_or_paid";
export type CapabilityStatusKind = "ready_free_local" | "ready_cloud" | "not_available";

export interface ModelOptionView {
  id: string;                 // form value only — never rendered as content
  label: string;              // product name — shown as-is (not translated)
  costKind: CostKind;
  available: boolean;
  isDefault: boolean;
  keyConfigured: boolean | null;      // paid/cloud only; else null
  enablementHintKey: CatalogKey | null;
  envVarName: string | null;          // variable NAME only — never a value
}

export interface CapabilityStatus {
  kind: CapabilityStatusKind;
  labelKey: CatalogKey;
  enablementHintKey: CatalogKey | null;
  envVarName: string | null;
}

export interface CapabilityView {
  family: Family;             // key/lookup only — never rendered raw
  nameKey: CatalogKey;
  descriptionKey: CatalogKey;
  displayKind: DisplayKind;   // selectable → "chooser", else "readonly"
  status: CapabilityStatus;
  options: ModelOptionView[];
  activeOptionId: string;
  selectedId: string | null;  // stored standing default, or null (= built-in default)
  isEnvOverridden: boolean;
  envVarName: string | null;  // when overridden — a NAME only
  isStale: boolean;
}

export function toCapabilityViews(inv: CapabilityInventory): CapabilityView[];
export function familyNameKey(f: Family): CatalogKey;          // fixed map (all 9 families)
export function costKind(cost: CostClass): CostKind;
export function reasonHintKey(reason: string | null): CatalogKey; // raw reason → plain key
```

**Hard invariants (unit-tested):**
- `displayKind === "chooser"` **iff** `family.selectable` is true (7 selectable model families);
  the 2 non-selectable families (`production-tools`, `mcp`) are `"readonly"` — **no chooser
  rendered** (FR-005).
- No function returns `family` code, `entry.id`, `tier`, `reason` code, or a `key_env` **value**
  as a display string; `envVarName` is a variable **name** only (FR-013, FR-010).
- `isEnvOverridden === (env_override != null)`; when true the family is shown "environment is
  deciding" and `selectedId` is retained but **not** presented as in force (FR-007).
- `isStale === selected_stale`; when true the family notes the prior choice is unavailable and
  `activeOptionId` is in force instead (FR-012).
- An option with `available === false` is **never** offered as selectable (FR-008).

## 2. Plain-language family map (all 9 families)

| `Family` | `nameKey` | `descriptionKey` | selectable? |
|---|---|---|---|
| `image` | `models.family.image` | `models.familyDesc.image` | yes → chooser |
| `video` | `models.family.video` | `models.familyDesc.video` | yes → chooser |
| `visual` | `models.family.visual` | `models.familyDesc.visual` | yes → chooser |
| `embedding` | `models.family.embedding` | `models.familyDesc.embedding` | yes → chooser |
| `kg-extraction` | `models.family.kg` | `models.familyDesc.kg` | yes → chooser |
| `stt` | `models.family.stt` | `models.familyDesc.stt` | yes → chooser |
| `tts` | `models.family.tts` | `models.familyDesc.tts` | yes → chooser |
| `production-tools` | `models.family.tools` | `models.familyDesc.tools` | no → readonly |
| `mcp` | `models.family.mcp` | `models.familyDesc.mcp` | no → readonly |

Plain-language intent (final EN wording finalized in `en.ts`): images / video / visual
understanding / search & memory / knowledge extraction / transcription / voice & narration /
production tools / integrations & connectors.

## 3. Catalog keys (EN/FR, added to `catalog.ts` + `en.ts` + `fr.ts`)

- **Title / chrome**: `models.title` (reused), `models.subtitle`, `models.recheck`,
  `models.rechecking`.
- **Family names/descriptions**: `models.family.*` and `models.familyDesc.*` (9 each per table).
- **Cost**: `models.cost.freeLocal`, `models.cost.paidCloud`, `models.cost.freeOrPaid`.
- **Status**: `models.status.readyFreeLocal`, `models.status.readyCloud`,
  `models.status.notAvailable`.
- **Reasons (plain)**: `models.reason.missingBinary`, `models.reason.missingModelFiles`,
  `models.reason.modelFilesMismatch`, `models.reason.gatewayDown`, `models.reason.keyNotSet`,
  `models.reason.generic`.
- **Chooser**: `models.choose.label`, `models.choose.builtinDefault`, `models.choose.revert`,
  `models.choose.default` (badge), `models.choose.unavailableOption`.
- **Honesty**: `models.override.note` (uses env var name), `models.stale.note`,
  `models.applies.nextProduction` (the "saved — used on your next production" confirmation).
- **Secrets**: `models.key.configured`, `models.key.setToEnable` (uses env var NAME only).
- **States**: `models.empty.family` (family with no available option), `models.error`,
  `models.error.retry`.

**Parity rule**: every key exists in both `en.ts` and `fr.ts`; EN is the fallback source of truth.

## 4. Screen behavior (`ModelsScreen.tsx` / `FamilyCard.tsx` / `ModelOption.tsx`)

- **Load**: `fetchCapabilities()` on mount → shared loading state → render every family. Machine-
  level: the shell client-context selector is **not** consumed (FR-015).
- **Re-check**: a `models.recheck` control calls `fetchCapabilities(true)` with the loading state;
  availability changes are reflected (FR-011).
- **Selectable family (`chooser`)**: a plain-language chooser lists **available** options (label +
  cost marker + default badge); picking one calls `selectCapability(family, id)` and confirms
  "saved — applies on your next production" (`models.applies.nextProduction`); a
  `models.choose.revert` action calls `clearCapability(family)`. Unavailable options are shown as
  not selectable with a plain reason + enablement hint. `env_override` → override note (env var
  **name**); `selected_stale` → stale note + what's in force.
- **Non-selectable family (`readonly`)**: plain name + description + availability status +
  enablement hint; **no chooser** (FR-005).
- **Paid/cloud option**: marked paid/cloud; shows `keyConfigured` or `models.key.setToEnable`
  (env var **name**); selecting it records a preference only — **no** outbound send, **no** key
  field (FR-009, FR-010).
- **Errors**: a read failure → `models.error` + retry; a save failure → plain retry, prior state
  intact (FR-014).
- **A11y**: WCAG 2.1 AA — the chooser, revert, and re-check are keyboard-operable and
  screen-reader-labeled; AA contrast; visible focus (FR-016).

## 5. Non-goals (contract boundaries)

- No new endpoint, no `api.ts` change, no server file, no persistence, no precedence change.
- No key entry/storage/transmission; no installer; no per-mission override; no per-client scope.
- The developer Console's raw `components/Capabilities.tsx` is untouched (coexistence).
