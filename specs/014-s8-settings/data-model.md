# Phase 1 Data Model — S8 Settings

S8 introduces **no new persisted entity**. It reuses the existing client-side preference store
and reads one new server fact-source. The "entities" below are (a) the existing preference state
Settings edits and (b) ephemeral view-models the pure `settingsModel.ts` derives for display.
Nothing here defines a new database, table, or file format beyond what already ships.

## 1. Studio Preference (existing, client-side — edited by S8)

The user-scoped preferences that Settings reads and writes, all persisted in the browser's
`localStorage`. Settings owns **no** copy of these — it edits the canonical state through the
existing hooks/helpers.

| Preference | Storage key | Owner (single source of truth) | Default |
|---|---|---|---|
| Interface language | `agency-studio.prefs` (`.locale`) | `useI18n().setLocale` / `writePrefs` | OS language → `fr` if `fr*`, else `en` |
| Default working context | `agency-studio.prefs` (`.clientContext`) | `useClientContext()` setters | none (unassigned) |
| Import associations | `agency-studio.prefs.importAssociations` | import `associationStore` | `{}` |
| Brief draft | `studio.briefDraft.v1` | `briefDraft` helpers | none |
| Follow-pointer | `agency.studio.followPointer.v1` | `followPointer` helpers | on |

- **Validation / state transitions**: language is one of `"en" | "fr"`. Default working context
  is validated by the `ClientContext` provider against the loaded taxonomy — a value pointing at
  a deleted client/project/campaign is surfaced as **stale** (shown, offered for clear/reselect),
  never silently applied (FR-003, stale-context edge case).
- **Reset (FR-006)**: `clearLocalPreferences(storage)` removes exactly the five keys above (four
  distinct key strings) and nothing else — no `localStorage.clear()`, no server call. After
  reset, language and context fall back to their defaults; import associations, brief draft, and
  follow-pointer return to their defaults. Server deliverables, missions, and the Brick 4
  `SelectionStore` are untouched.

## 2. SystemInfo (new — server fact, read-only)

The honest system facts the frontend cannot invent, delivered by `GET /api/system`.

| Field | Type | Source | Notes |
|---|---|---|---|
| `version` | string | `agency_studio.__version__` | The studio version to display verbatim |
| `dataDir` (`data_dir`) | string | `str(agency_studio.rag.data_dir())` | Absolute path of the studio's **primary local data folder** (documents, settings, knowledge, model-selection preferences) — shown so the user can find/back up these files. Not a claim that every produced deliverable lives here |

- **No secret, no user input**: the endpoint reads two server-computed values; it accepts no
  query/body and serves no user-named file. See `contracts/system-endpoint.md`.
- Frontend `types.ts`: `interface SystemInfo { version: string; dataDir: string }` (mapped from
  the JSON `data_dir`).

## 3. System Status view (ephemeral — derived by `settingsModel.ts`)

A pure, non-persisted view-model assembled for the System / About section. Not stored anywhere.

| Field | Type | Derived from | Meaning |
|---|---|---|---|
| `connection` | `"connected" \| "offline" \| "unknown"` | success/transport-failure of the system + capabilities reads | Honest reachability of the local server |
| `version` | string | `SystemInfo.version` | Displayed as-is |
| `dataLocation` | string | `SystemInfo.dataDir` | Displayed as-is (the one legitimately literal path), under a label naming it the primary documents/settings folder — never "all your files" |
| `modelSummary` | `Array<{ familyKey: CatalogKey; choiceLabel: string }>` | `CapabilityInventory` (S7's `GET /api/capabilities`) | Per selectable family, the selected/active model in plain language |

- `connection` is `unknown` before the first read resolves, `offline` on a transport failure
  (local Preferences/Reset still work), `connected` once system/capabilities load.
- `modelSummary` is **read-only** here; changing a model is a link-out to `#/models` (S7).
- All labels are catalog-key driven; no raw family code or model id is rendered as operator
  content (the `dataLocation` path is the single intentional literal, and it is the user's own).

## 4. Studio Preference section state (ephemeral UI)

The Preferences section holds no persistent state of its own — it renders the current
`useI18n()` locale and `useClientContext()` selection and calls their setters. Any change is a
synchronous write to the canonical store, reflected immediately across the app (including the
top-bar controls), with an honest confirmation and no false "saved" if a write did not occur
(FR-010).
