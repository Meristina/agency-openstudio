# Quickstart — Brick 7 umbrella (shell, navigation, i18n)

## Prerequisites

- Node 20+ and npm (frontend build/tests only — the Python suite needs neither).
- Python 3.11+ for the studio server (unchanged by this feature).

## Build & run

```bash
# macOS / Linux
cd app/studio
npm install
npm run build          # tsc -b && vite build → app/studio/dist
cd ../..
agency-studio          # stdlib server → serves the built shell at http://127.0.0.1:8765/
```

```powershell
# Windows (PowerShell)
cd app\studio
npm install
npm run build
cd ..\..
agency-studio
```

Opening the studio now lands on the **magic box home** ("What do you want to
produce?"). The pre-existing developer console is at **`#/console`**, unchanged.

## What to try

1. **Single entry**: load `/` → the question is the first surface; type an intent →
   you are handed to `#/brief` (placeholder until S2's spec ships) with the intent
   carried along.
2. **Navigation**: every inventoried area (home, brief, missions, library, import,
   export, models, settings, console) is reachable from the persistent nav; unbuilt
   areas show a localized "coming soon" with a way home; an unknown hash (e.g.
   `#/nope`) shows the not-found state.
3. **EN/FR**: switch language from the shell chrome — all visible text follows
   immediately without losing your place; reload → the choice persists.
4. **Client context**: pick a client in the shell selector (taxonomy from Brick 6);
   taxonomy-scoped areas scope to it; with no selection, unassigned work stays
   visible in its own bucket.
5. **Models**: `#/models` shows the Brick 4 capability & model panel inside the
   shell.
6. **Connection**: stop the Python server → a plain-language banner appears; restart
   it → the banner clears by itself.

## Tests

```bash
# Frontend (shell, router, i18n completeness, placeholders, a11y helpers)
cd app/studio && npm test && npm run typecheck

# Python — must stay untouched and green (no server changes in this feature)
pytest
```

Both suites run fully offline (fetch mocked in Vitest; no network, no CLI agents).
