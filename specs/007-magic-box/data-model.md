# Data Model — Brick 7 umbrella (app shell, navigation, i18n)

All entities are frontend-local. No server-side schema, file format, or endpoint
changes; the only persisted artifact is the browser-local preferences record.

## Route (screen registration)

The route table is the runtime form of the spec's Screen Inventory (spec FR-020).

| Field | Type | Rules |
|---|---|---|
| `id` | `"home" \| "brief" \| "missions" \| "library" \| "import" \| "export" \| "models" \| "settings" \| "console"` | Unique; S1–S8 plus the preserved console. |
| `hash` | string (`"#/"`, `"#/brief"`, …) | Unique; empty/`#/` maps to `home`. |
| `titleKey` | `CatalogKey` | Localized nav label + screen title; never raw text. |
| `status` | `"shipped" \| "placeholder"` | `placeholder` renders the shared ComingSoon state; flips to `shipped` when the child spec's implementation merges. |
| `taxonomyScoped` | boolean | `true` for `missions`, `library` — these render under the active client context. |

**State transitions**: `placeholder → shipped` only (one-way, per child spec merge).
Unknown hash → synthetic `notFound` presentation (not a table entry — nothing can
navigate *to* it, it is a fallback rendering).

**Validation**: a test asserts the table contains exactly the inventory ids S1–S8 +
`console`, each with a distinct hash and an existing `titleKey` in both catalogs.

## Locale & Catalog

| Field | Type | Rules |
|---|---|---|
| `Locale` | `"en" \| "fr"` | Closed set for v1 (spec assumption). |
| `CatalogKey` | string-literal union defined in `catalog.ts` | Single source of key truth; keys are dot-namespaced (`nav.library`, `state.comingSoon.title`, `conn.unreachable`). |
| catalog | `Record<CatalogKey, string>` per locale | `en` is the fallback source of truth (spec FR-007); `{param}` placeholders must appear in both languages' strings for a given key. |

**Validation**: compile-time — `en.ts`/`fr.ts` typed as complete records (a missing key
fails `tsc`); runtime test — key sets deep-equal and no rendered output matches a raw
key pattern (SC-004).

## User Preferences (persisted)

Stored at `localStorage["agency-studio.prefs"]` as JSON.

| Field | Type | Rules |
|---|---|---|
| `locale` | `"en" \| "fr"` (optional) | Absent → derive from `navigator.language` (`fr*` → `fr`, else `en`). |
| `clientContext` | `{ client?: string; project?: string; campaign?: string }` (optional) | Names as registered by the Brick 6 taxonomy; a context naming entities that no longer exist degrades to "no context" silently. |

**Rules**: never contains secrets (spec FR-015); malformed JSON or wrong shape is
discarded wholesale and replaced with defaults (defensive read, same doctrine as the
Brick 6 registry readers); written only on explicit user change.

## Client Context (in-memory, shell-owned)

| Field | Type | Rules |
|---|---|---|
| `client` | string \| null | `null` = no context: taxonomy-scoped screens show all work, with unassigned work in a visible "unassigned" bucket (spec FR-013a). |
| `project` | string \| null | Only meaningful when `client` set. |
| `campaign` | string \| null | Only meaningful when `project` set. |

Hierarchical invariant: setting a shallower level clears deeper levels. Source data:
existing `GET /api/taxonomy` (Brick 6); the shell never mutates taxonomy — assignment
stays a per-mission action owned by existing/library surfaces.

## Connection State (in-memory)

| Field | Type | Rules |
|---|---|---|
| `reachable` | boolean | Starts `true` (optimistic); set `false` only on transport-level fetch failure, never on HTTP error statuses. |
| `retryTimer` | opaque | While unreachable, periodic lightweight retry against an existing endpoint; first success → `reachable: true`, banner clears, screens refetch. |

## Relationships

```text
Shell ──owns──> Route table (9 entries) ──titleKey──> Catalog (en, fr)
Shell ──owns──> ClientContext ──reads──> GET /api/taxonomy (Brick 6, unchanged)
Shell ──owns──> ConnectionState ──derives from──> existing api.ts fetches
Shell ──persists──> UserPreferences (localStorage; locale + clientContext echo)
Route "console" ──renders──> existing App.tsx (unmodified)
Route "models"  ──renders──> existing Capabilities.tsx (embedded)
```
