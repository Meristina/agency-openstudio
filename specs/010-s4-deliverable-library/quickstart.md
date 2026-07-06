# Quickstart — Deliverable Library (S4)

How to build, run, and verify S4 as a frontend-only, server-untouched feature.

## What ships

A new `screens/library/` module that turns the `#/library` coming-soon placeholder into
the operator-facing Deliverable Library: finished productions grouped by client → project →
campaign (+ unassigned), searchable, outcome-filterable, previewable in place, with the
three non-destructive actions (open · download PDF · file/refile). **No backend changes,
no new dependencies.**

## Prerequisites

- Existing studio dev setup (Node + the app under `app/studio/`).
- Some saved missions to browse. Either use an existing store, or produce a couple via the
  Guided Brief (S2) so `GET /api/missions` returns dossiers — including one attached to a
  client and one left unassigned, and ideally one that ended in error (needs-attention).

## Build & test (offline)

```bash
cd app/studio
npm install            # no new deps expected in the lockfile diff
npm run test           # Vitest — new screens/library/*.test.* must pass
npm run build          # tsc + vite build; app/studio/dist is what the server serves
```

Root Python suite (must stay green, server untouched):

```bash
cd ../..               # repo root
pytest -q              # unchanged; S4 touches no Python
```

## Run

```bash
# from repo root — the existing local server serves app/studio/dist at 127.0.0.1
python -m agency_studio --path /path/to/a/workspace     # or the project's usual launch
# open the studio, click "Library" (plain-language nav), or go to #/library
```

## Manual verification (maps to acceptance scenarios)

1. **Browse grouped (US1)**: open Library → deliverables appear grouped client → project →
   campaign; an unassigned one sits on the **unassigned** shelf; no mission ids / kit names
   / paths anywhere.
2. **Scope by client context (US1-AC3)**: set the shell client-context selector → Library
   narrows to that client; clear it → full library returns.
3. **Open full detail (US1-AC4)**: click a card → the existing dossier detail
   (`MissionDetail`) opens with sources/decisions/assets.
4. **First-run empty (US1-AC5)**: with an empty store, Library shows the friendly empty
   state with a "start producing" way forward — not a blank screen.
5. **Search + outcome filter (US2)**: type part of a title/client → list narrows as typed;
   apply the needs-attention filter → only troubled runs remain; a no-match query shows the
   nothing-found state; clear restores the grouped view.
6. **Preview (US3-AC1)**: trigger a card's preview → inline summary (headline, outcome, key
   sources/decisions, media thumbnails) appears without navigating away; a text-only
   deliverable shows no broken media.
7. **PDF (US3-AC2)**: download PDF → progress then download; on a build without the `[pdf]`
   extra, a plain-language hint appears and the rest stays usable.
8. **File / refile (US3-AC3/AC4)**: file an unassigned deliverable under a client → it moves
   shelves immediately; move it again / return to unassigned → reflected immediately;
   filing again reverses it.
9. **No delete (clarify)**: confirm there is **no** delete/remove control on any deliverable.
10. **i18n + a11y (SC-004/SC-005)**: switch EN↔FR → all Library chrome follows immediately;
    browse/search/preview/actions are fully keyboard-operable with visible focus.
11. **S3 hand-off (FR-017/SC-007)**: finish a production in the S3 Mission Timeline and click
    "view your deliverable" → you land on the Library (`#/library?deliverable=<id>`) with that
    finished deliverable opened — not the developer console.

## Guardrails (must hold)

- `git diff` touches **only** `app/studio/src/**` (new `screens/library/`, five integration
  edits in `router.ts` / `Shell.tsx` / `placeholders.tsx` / `i18n/*` / `screens/missions/TerminalPanel.tsx`).
  **No** files under `agency_studio/`, `agencykit/`, or `openmontage/`.
- `components/TaxonomyBrowser.tsx` (dev console) is **byte-identical**.
- No new entry in `package.json` dependencies; no new persisted field; no new endpoint.
