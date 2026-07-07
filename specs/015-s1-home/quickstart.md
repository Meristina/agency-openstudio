# Quickstart — S1 Home (developer orientation)

**What S1 is**: an **additive, pure-frontend** enrichment of the studio's entry point
(`#/`). Today's `screens/Home.tsx` is a single-file intent→brief form; S1 turns it into a
self-contained `screens/home/` module that also lets users **resume** work and **orient**
toward the studio — reusing existing surfaces, adding **no** endpoint and **no** store.

## Where the work lands

```
app/studio/src/screens/home/
  Home.tsx            # orchestrator (was screens/Home.tsx)
  StartSection.tsx    # question + intent + start  → #/brief?intent=…  (UNCHANGED behavior)
  ResumeSection.tsx   # unfinished brief + up-to-5 recent missions (fail-soft)
  ShortcutsSection.tsx# → #/library, #/import, #/models
  ContextLabel.tsx    # read-only active-context label (useClientContext)
  homeModel.ts        # PURE: recentMissionsView / hasResumableDraft / contextLabelView
  homeModel.test.ts   # pure-model tests (offline)
  Home.test.tsx       # screen tests (offline)
app/studio/src/shell/Shell.tsx   # import Home from screens/home (route already "shipped")
app/studio/src/i18n/{catalog,en,fr}.ts   # + home.* keys (EN/FR parity)
```

No change to `api.ts`, `types.ts`, the router table, any server file, or `agencykit/`.

## The five existing surfaces you reuse (do not re-create)

| Need | Reuse |
|---|---|
| Start / resume brief | `navigate("#/brief?intent=…")` / `navigate("#/brief")` |
| Detect unfinished brief | `loadBriefDraft()` — `screens/brief/briefDraft.ts` |
| Recent missions (≤5, global) | `listMissions()` — `api.ts` (no filter) |
| Is it the live run? | `followPointer.read()` — `screens/missions/followPointer.ts` |
| Active context (read-only) | `useClientContext()` — `shell/ClientContext.tsx` |

## Navigation cheatsheet (all existing routes)

- Start / resume brief → `#/brief` (`?intent=…` when starting with text)
- Open **in-progress** mission → `#/missions` (live timeline)
- Open **completed** mission → `#/library?deliverable=<mission_id>`
- See all recent work → `#/library` (full browsable list; `#/missions` is only the live/last run)
- Shortcuts → `#/library`, `#/import`, `#/models`

## Non-negotiables while building

- **Start flow never blocks on recent work.** Render Start synchronously; load
  `listMissions()` independently and **fail soft** — an honest "couldn't load recent work"
  note, never a false empty and never a perpetual spinner (FR-007/FR-008, Principle III).
- **No raw machine tokens.** Never render `mission_id` / `runId` / raw `verdict` — map to a
  plain label + a `home.recent.*` catalog status in the pure model (Principle VIII).
- **Byte-identical intent→brief.** The start action builds the exact same URL as today,
  including the empty-intent case (Principle X).
- **EN/FR parity.** Every new `home.*` key exists in both `en.ts` and `fr.ts`, typed in
  `catalog.ts` (Principle XI for the repo; EN/FR for the product surface).
- **No new endpoint, store, outbound network, or network toggle.** Reads only (VI, IV).

## Run the tests (offline)

```
cd app/studio
npm test            # Vitest: homeModel.test.ts + Home.test.tsx (jsdom, listMissions mocked)
npm run build       # type-check + Vite build
```

Root `pytest` is unaffected (no server surface). The root offline suite must stay green.

## Definition of done (per the spec)

- Intent→brief works exactly as before; empty intent still navigates.
- Unfinished brief and up-to-5 recent missions appear and resume/open by state.
- Empty (first-run) and load-failure states are calm and honest.
- Read-only context label reflects the active context (or a plain "no context").
- Shortcuts reach Library / Import / Models.
- EN + FR render with no missing/hard-coded strings; a11y/keyboard operable.
