# Quickstart: Guided Brief (S2)

## Where the work lives

- Feature module: `app/studio/src/screens/brief/` (new — see [plan.md](./plan.md) structure)
- Integration edits only in: `app/studio/src/shell/router.ts` (status flip),
  `app/studio/src/i18n/{catalog,en,fr}.ts` (`brief.*` keys),
  `app/studio/src/screens/placeholders.tsx` (remove S2 entry),
  `app/studio/src/api.ts` (`runMission` gains an optional `assets` opt — absent ⇒ today's `true`)
- Server: **no changes** (`agency_studio/` untouched)

## Develop

```bash
cd app/studio
npm install            # existing deps only — this feature adds none
npm run dev            # Vite dev server; open http://localhost:5173/#/brief?intent=hello
```

Against the real local service (taxonomy, capabilities, launch):

```bash
agency-studio                    # serves app/studio/dist on 127.0.0.1:8765 (agency_studio/cli.py)
cd app/studio && npm run build   # rebuild the bundle the server serves
```

## Test (offline — Constitution VII)

```bash
cd app/studio
npx vitest run src/screens/brief          # feature suite (mocked fetch, jsdom)
npx vitest run                            # full frontend suite
npm run build                             # type-check + bundle
cd ../.. && python -m pytest              # root suite — must stay green (no server change)
```

Key assertions the suite must carry (from spec SC):
- default-launch body: `web_search === true`, zero paid/off-machine flags (SC-004)
- EN/FR completeness of the `brief.*` namespace; no machinery terms (SC-005/SC-007)
- draft survives reload; failed launch preserves the brief (SC-006)
- keyboard-only completion via the shared a11y helpers (`src/testing/a11y.tsx`) (SC-005)

## Manual smoke (5 min)

1. Home → type an intent → "Start" → arrives on `#/brief` with the intent pre-filled.
2. Pick *research* → accept every default → review lists intent, type, language,
   research-on, "at least 3 sources", unassigned → Launch → run id confirmation.
3. Pick *video* on a machine without a video backend → blocker panel appears at the
   review with a link to Models — launch not attempted.
4. Mid-flow, reload the page → resume-or-discard prompt; resume restores the step.
5. Switch FR/EN mid-flow → all wording flips, answers intact, deliverable-language
   choice unchanged.
