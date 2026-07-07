# Contract — Settings Screen Model (frontend)

The frontend contract for the `screens/settings/` module: which sources of truth it reads/writes,
what the pure `settingsModel.ts` derives, the reset key-set, and the catalog keys. No secret is
ever entered, displayed, persisted, or transmitted anywhere in Settings.

## Sections → sources of truth

| Section | Reads | Writes (single source of truth) | Never does |
|---|---|---|---|
| **Preferences** | `useI18n().locale`; `useClientContext()` client/project/campaign + taxonomy | `useI18n().setLocale` (persists `PREFS_KEY`); `useClientContext()` setters (persist `PREFS_KEY.clientContext`) | Keep a parallel prefs copy; write any key directly |
| **System / About** | `getSystemInfo()` (`GET /api/system`); `fetchCapabilities()` (`GET /api/capabilities`, reused); reachability | — (read-only) | Duplicate the model chooser; fabricate version/path |
| **Reset** | — | `clearLocalPreferences(localStorage)` | Call `localStorage.clear()`; issue any network call; touch server data or `SelectionStore` |

## `settingsModel.ts` (pure, unit-tested)

- `PREFERENCE_KEYS: readonly string[]` — exactly:
  `["agency-studio.prefs", "agency-studio.prefs.importAssociations", "studio.briefDraft.v1", "agency.studio.followPointer.v1"]`.
  (Sourced from `PREFS_KEY`, the import `associationStore` key, `BRIEF_DRAFT_KEY`,
  `FOLLOW_POINTER_KEY` — imported, not re-hardcoded, so the list can't drift.)
- `clearLocalPreferences(storage: Storage): void` — removes each `PREFERENCE_KEYS` entry; leaves
  every other key intact; no-op-safe if a key is absent or storage is unavailable.
- `deriveSystemView(info: SystemInfo | null, capabilities: CapabilityInventory | null, reachable: boolean): SystemStatusView`
  — maps to `{ connection, version, dataLocation, modelSummary }` per data-model §3;
  `connection` = `"unknown"` before load, `"offline"` on transport failure, else `"connected"`.
- `deriveModelSummary(capabilities: CapabilityInventory): Array<{ familyKey: CatalogKey; choiceLabel: string }>`
  — selectable families only; the selected/active model rendered in plain language (reuse S7's
  family-name catalog keys). Read-only.

All outputs are catalog-key driven. The only literal string rendered is `dataLocation` (the
user's own path, intentionally literal so they can find/back up their files).

## Honesty & accessibility rules

- **Single source of truth** (FR-002): the language `<select>` in Settings and the top-bar
  `LanguageSwitch` both call `setLocale`; changing one updates the other in the same render.
- **Stale context** (FR-003): a default context pointing at a deleted node is shown as stale via
  the provider's existing validation and offered for clear/reselect — never silently applied.
- **Honest confirmation** (FR-010): every change reflects the true resulting state; no false
  "saved".
- **Offline degrade** (FR-009): on transport failure the System panel shows offline/unknown while
  Preferences and Reset keep working.
- **No global network toggle** (FR-007): Settings shows at most an informational per-mission note;
  it adds no control that changes network behavior globally.
- **WCAG 2.1 AA** (FR-008): every control keyboard-operable and screen-reader labelled; sections
  use proper landmarks/headings; EN/FR parity for every string.

## Wiring

- `router.tsx`: `settings` route `status: "placeholder" → "shipped"` (no path/order change).
- `Shell.tsx`: add `if (match.route.id === "settings") return <SettingsScreen />;` (replaces the
  `PlaceholderScreen` fall-through for `settings`).
- `placeholders.tsx`: drop the `settings` entry; remove the two `settings.comingSoon.*` catalog
  keys from `catalog.ts` / `en.ts` / `fr.ts`.

## New catalog keys (EN/FR, indicative)

`settings.title`, `settings.section.preferences`, `settings.section.system`,
`settings.section.reset`, `settings.system.connected`, `settings.system.offline`,
`settings.system.unknown`, `settings.system.version`, `settings.system.dataLocation`,
`settings.system.localFirst`, `settings.system.modelSummary`, `settings.system.modelLink`,
`settings.reset.title`, `settings.reset.body`, `settings.reset.confirm`, `settings.reset.cancel`,
`settings.reset.done`, `settings.network.perMissionNote`. Reuse existing `lang.*` and `context.*`
keys for the language and default-context controls.
