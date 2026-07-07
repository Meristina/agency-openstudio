# Quickstart — S8 Settings (developer orientation)

**Goal**: replace the `#/settings` "coming soon" placeholder with a real, EN/FR, WCAG-AA Settings
screen — one home for language, default working context, a read-only System/About panel, and a
guarded reset — adding exactly one honest read-only server endpoint (`GET /api/system`).

## What you touch

**Backend (one small, read-only endpoint):**
- `agency_studio/server.py` — add `GET /api/system` → `_handle_system()` returning
  `{"version": __version__, "data_dir": str(rag.data_dir())}`. No user input, no secret.
- `tests/test_system_endpoint.py` — offline pytest for the endpoint (see
  `contracts/system-endpoint.md`).

**Frontend (the screen):**
- `app/studio/src/screens/settings/` — new module:
  - `SettingsScreen.tsx` (orchestrator; parallel load of `getSystemInfo` + `fetchCapabilities`;
    shared loading/error states; a11y landmarks)
  - `PreferencesSection.tsx` (language via `useI18n().setLocale`; default context via
    `useClientContext()` setters + clear)
  - `SystemStatusSection.tsx` (read-only: connection, version, data location, model summary +
    link to `#/models`)
  - `ResetSection.tsx` (confirm → `clearLocalPreferences` → done)
  - `settingsModel.ts` (pure: `PREFERENCE_KEYS`, `clearLocalPreferences`, `deriveSystemView`,
    `deriveModelSummary`)
  - co-located `*.test.ts(x)` files
- `app/studio/src/api.ts` — add `getSystemInfo()`; **reuse** `fetchCapabilities`.
- `app/studio/src/types.ts` — add `SystemInfo { version: string; dataDir: string }`.
- `app/studio/src/shell/Shell.tsx` — one line: route `settings` → `<SettingsScreen />`.
- `app/studio/src/shell/router.tsx` — `settings` status `placeholder → shipped`.
- `app/studio/src/screens/placeholders.tsx` — drop the `settings` entry.
- `app/studio/src/i18n/{catalog,en,fr}.ts` — add `settings.*` keys; remove
  `settings.comingSoon.*`; reuse `lang.*` / `context.*`.

## What you must NOT touch

- The Brick 4 server-side `SelectionStore` / `selections.json` (Reset must not touch it).
- `components/Capabilities.tsx` (developer Console) — byte-identical.
- The mission loop, routing engine, capability probing/aggregation, env>selection>default
  precedence, inspector veto loop, and the `agencykit/` subtree.
- Any existing endpoint response — `/api/system` is purely additive.

## Non-negotiables to keep green

- **No invented information**: version and data location come only from `/api/system`; connection
  state reflects the real probe; stale context is shown, not silently applied; no false "saved".
- **Security**: loopback bind (inherited), no CORS `*`, `/api/system` takes no user input and
  returns no secret; no API-key input anywhere in Settings.
- **Local-first**: no global network toggle; per-mission opt-in untouched.
- **Single source of truth**: Settings language/context use the same hooks as the top-bar
  controls — they can never drift (FR-002).
- **Offline tests**: Vitest (api mocked, `localStorage` in jsdom) + pytest (`/api/system`), all
  network-free.

## Verify locally

```bash
# Frontend module + pure model (offline)
cd app/studio && npm run test && npm run build

# Server endpoint + root offline suite
cd - && pytest tests/test_system_endpoint.py tests/
```

**Definition of done**: a non-technical user opens `#/settings`, changes language and default
context (reflected everywhere, no drift), sees the studio is connected + local-first with the
version and where their files live, jumps to model choice, and can reset local preferences to
defaults without losing any deliverable, mission, or model selection — all EN/FR and
keyboard-operable, with the offline suites green.
