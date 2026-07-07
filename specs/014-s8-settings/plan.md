# Implementation Plan: S8 Settings — One Home for Studio Preferences (Brick 7 · Screen S8)

**Branch**: `014-s8-settings` | **Date**: 2026-07-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/014-s8-settings/spec.md`

## Summary

S8 is the **final child spec of Brick 7**. It replaces the `#/settings` **"coming soon"
placeholder** (`screens/placeholders.tsx` + `ComingSoon`) with a real, non-technical, EN/FR
Settings screen: one calm home for the preferences that shape every other screen. Three
sections, one per prioritized user story:

1. **Preferences (P1)** — interface **language** (EN/FR) and the **default working context**
   (client / project / campaign), edited through the studio's **existing** single sources of
   truth so the two controls can never drift: language reuses `useI18n().setLocale` (the same
   hook the top-bar `LanguageSwitch` calls, persisting `PREFS_KEY`), and context reuses
   `useClientContext()` setters (the same state the top-bar `ClientContextSelector` drives,
   persisting `PREFS_KEY.clientContext`, with the provider's existing stale-selection validation).
2. **System / About (P2)** — a **read-only** panel: connection state (the existing reachability
   probe), the studio **version**, the **local data location**, and a **model-selection
   summary** with a link to the S7 `#/models` panel (Settings never duplicates that UI).
3. **Reset (P3)** — a guarded action that clears the studio's **own local preference keys**
   (`PREFS_KEY`, `PREFS_KEY.importAssociations`, `BRIEF_DRAFT_KEY`, `FOLLOW_POINTER_KEY`) back to
   defaults, behind an explicit confirmation, and **never** touches server-side deliverables,
   missions, or the persisted model `SelectionStore`.

**One honest server addition, not a pure-frontend layer.** Unlike S4/S5/S7 (pure frontend over
existing endpoints), S8 adds **one minimal read-only endpoint** — `GET /api/system` →
`{ "version", "data_dir" }`. This is deliberate and required by Principle III (no invented
information): FR-004 mandates showing the **application version** and the **local data
location**, and the frontend cannot truthfully source either — the web `package.json` version is
an unmaintained `0.0.0` placeholder, and the data directory is known only server-side via
`rag.data_dir()`. Inventing or guessing them would violate the non-negotiable "no invented
information" rule; the honest source is the server. The endpoint is additive, loopback-only,
carries no secret and no user input (so no `path_inside` / traversal surface), returns stdlib
JSON, and is offline-testable — mirroring the small honest server surface S6 added. Everything
else S8 needs already exists: reachability (the `ConnectionBanner` probe pattern), the
model-selection summary (`GET /api/capabilities`, reused read-only via `fetchCapabilities`), and
all preference persistence (the existing `localStorage` prefs).

The rest of the job is a **presentation layer** in the frontend: a self-contained
`screens/settings/` module (orchestrator + three section components + a pure `settingsModel.ts`)
that turns raw signals (a `data_dir` path, a capability inventory, a reachability boolean) into
plain-language, localized, WCAG 2.1 AA operator content, and flips the `settings` route from
`placeholder` to `shipped` with a one-line Shell wiring change. The mission loop, routing logic,
synthesis, inspector veto loop, capability probing/selection-store, and the developer Console
stay byte-identical; the `agencykit/` subtree is untouched.

## Technical Context

**Language/Version**: TypeScript ~5.7 (frontend) + Python 3 stdlib (one new server handler).

**Primary Dependencies**: React 19 + Vite 6 (frontend, pre-existing); Python **stdlib only** for
the new endpoint (`http.server` handler + `json`). **Zero new runtime dependencies**, no new
optional extra.

**Storage**: **No new store.** Preferences persist in the **existing** browser `localStorage`
prefs (`PREFS_KEY` and siblings) via the existing `writePrefs` / `ClientContext` / `followPointer`
/ `briefDraft` helpers. The model choice remains owned by Brick 4's server-side `SelectionStore`
(Settings only **reads** a summary and links out; Reset does **not** touch it). The new
`/api/system` endpoint reads `agency_studio.__version__` and `rag.data_dir()` — it writes nothing.

**Testing**: Vitest 3 + @testing-library/react + jsdom for the new `screens/settings/` module and
`settingsModel.ts` (fully offline — `getSystemInfo` / `fetchCapabilities` mocked via the existing
`api.ts` test-double pattern; `localStorage` exercised in jsdom). **pytest** for the new
`/api/system` handler (offline, no network) alongside the existing server tests. Root offline
suite stays green.

**Target Platform**: Desktop browser on the operator's machine, served by the local stdlib
server at `127.0.0.1` from `app/studio/dist`.

**Project Type**: Web application feature (one inventoried screen) — frontend module + one
minimal read-only server endpoint.

**Performance Goals**: Settings opens with two cheap reads in parallel (`GET /api/system`,
reused `GET /api/capabilities`) and renders within one frame at local single-user volume.
Changing a preference is a synchronous `localStorage` write reflected immediately. Reset is a
synchronous clear + confirmation. Connection state degrades to offline/unknown without blocking
the local controls.

**Constraints**: Constitution I–XI; umbrella cross-cutting rules (EN/FR catalogs; design system
+ WCAG 2.1 AA — every control keyboard-operable and screen-reader labelled; shared
loading/empty/error/connection states; tone of voice — no raw machine tokens as operator
content). Honesty (Principle III): version and data location come from the server, never
invented; connection state reflects the real probe; a stale default context is surfaced plainly
(reusing the provider's existing validation), never silently applied; a preference change gives
an honest confirmation and never a false "saved". Security (Principle VI): served from
`127.0.0.1`, no CORS `*`; `/api/system` takes **no user input** and returns only the studio
version + the local user's own data path over loopback — **no secret, no traversal surface**;
no API key is ever entered, displayed, persisted, or transmitted; Settings adds **no** global
network toggle, so the per-mission network opt-in (Principle IV) is untouched. Additive
(Principle X): the placeholder becomes a shipped screen (the umbrella's designed lifecycle); the
new endpoint is default-safe and read-only; the developer Console, mission loop, probing,
selection-store, and `agencykit/` subtree are byte-identical.

**Scale/Scope**: 1 screen (placeholder → shipped); **1 new read-only endpoint** (`GET
/api/system`) + its handler + 1 pytest; a new self-contained `screens/settings/` frontend module
(orchestrator + 3 sections + pure `settingsModel.ts`); 1 new `api.ts` wrapper (`getSystemInfo`)
+ 1 `types.ts` interface (`SystemInfo`); a one-line Shell dispatch change + flip the router
`settings` route to `shipped`; drop the `settings` placeholder entry (and its two
`settings.comingSoon.*` catalog keys); ~25–35 new EN/FR catalog keys (section titles, system
labels/statuses, reset copy, per-mission-network note) reusing existing `lang.*` / `context.*`
keys; ~4–5 Vitest files. Mission loop, routing engine, synthesis, asset rendering, inspector
veto loop, capability probing/selection-store/precedence, developer console: **untouched**.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — S8 adds no reasoning path. The new endpoint
  reads a version string and a directory path; the screen reads/writes local preferences. No
  engine call, no token-billed API, no mission-loop touch; marginal cost zero.
- [x] **II. Engine neutrality**: PASS — no engine-specific behavior; the panel presents
  preferences and platform-neutral system facts. The Engine contract and production guard are
  untouched.
- [x] **III. No invented information**: PASS — this principle is the **reason** S8 adds
  `/api/system`: version and data location are read from the authoritative server
  (`__version__`, `rag.data_dir()`), never fabricated by the frontend. Connection state reflects
  the real probe; a stale default context is shown plainly, not silently applied; a preference
  change confirms the true resulting state (no false "saved"). The inspector veto loop is
  untouched.
- [x] **IV. Local-first & offline-by-default**: PASS — every preference is local; the System
  panel affirms the local-first, on-this-machine reality. Settings adds **no** global network
  control and **no** outbound network of its own — the per-mission network opt-in is preserved
  exactly (FR-007). Non-Mac not regressed (platform-neutral).
- [x] **V. Subprocess boundaries**: PASS — no `openmontage/` import; the `agencykit/` subtree is
  not edited or called (S8 talks only to the studio's own endpoints). Vendored subtrees
  unchanged.
- [x] **VI. Security**: PASS — served from `127.0.0.1`, no CORS `*`. `GET /api/system` takes
  **no user input** (no traversal / `path_inside` surface — it serves no user-named file) and
  returns only the studio version and the local user's own data directory over loopback: **no
  secret, no key, nothing persisted or logged that wasn't already**. No API-key input exists
  anywhere in Settings; https-only-outbound is n/a (no S8 outbound).
- [x] **VII. Offline tests**: PASS — the frontend module and pure model are covered by Vitest
  with `getSystemInfo` / `fetchCapabilities` mocked and `localStorage` in jsdom (no network, no
  CLI, no Node beyond jsdom, no GPU); the new `/api/system` handler is covered by an offline
  pytest. Root offline suite stays green.
- [x] **VIII. End-user simplicity**: PASS — S8 *is* "one place for my settings, in plain
  language, no terminal": pick language and default context, see at a glance that the studio is
  connected and local-first, find where your files live, jump to model choice, and reset to
  defaults safely. No raw machine tokens as operator content (the `data_dir` path is the one
  legitimately literal, user-useful value — for finding/backing up their own files).
- [x] **IX. License**: PASS — frontend uses existing React/Vite; the endpoint is stdlib-only. No
  new third-party component; nothing to add to `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — the designed placeholder→shipped lifecycle; the new
  endpoint is read-only and default-safe (adding it changes no existing response); Reset clears
  only the studio's own local keys and never server data or the `SelectionStore`; the developer
  Console, mission loop, probing, selection-store, precedence, and veto loop are byte-identical.
- [x] **XI. English everywhere**: PASS — code/docs/commits in English; operator-facing strings
  live only in the EN/FR end-user catalogs (explicitly permitted).

**Post-Phase-1 re-check (2026-07-07)**: the design artifacts (research, data-model, contracts,
quickstart) confirm the footprint above — exactly one new read-only, no-input, no-secret
endpoint (`GET /api/system`) plus a self-contained frontend module reusing the existing
`setLocale` / `ClientContext` / prefs helpers as single sources of truth; Reset scoped to the
four enumerated studio local keys with server data and `SelectionStore` provably untouched; no
global network toggle added. All gates hold as marked.

## Project Structure

### Documentation (this feature)

```text
specs/014-s8-settings/
├── spec.md              # Feature spec (informed-default scope; no clarification markers)
├── plan.md              # This file
├── research.md          # Phase 0 output — the /api/system decision, reuse-vs-new, reset-scope, honesty
├── data-model.md        # Phase 1 output — Studio Preference + System Status view-models (ephemeral)
├── quickstart.md        # Phase 1 output — developer orientation
├── contracts/
│   ├── system-endpoint.md      # NEW server contract: GET /api/system → {version, data_dir}; shape, no-input, no-secret rules
│   └── settings-screen-model.md# Frontend contract: section map, sources of truth (setLocale/ClientContext/prefs),
│                               #   system view-model derivation, reset key-set, catalog keys
├── checklists/
│   └── requirements.md  # Spec quality checklist (all pass)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
app/studio/src/
├── screens/
│   └── settings/                     # NEW self-contained module (replaces the settings ComingSoon placeholder)
│       ├── SettingsScreen.tsx        # Orchestrator: three sections; parallel load of system info + capability summary;
│       │                             #   shared loading/error(retry) states; a11y landmarks; machine-level (client
│       │                             #   context edited here IS the app-wide context — same provider)
│       ├── PreferencesSection.tsx    # Language (reuse useI18n().setLocale) + default working context (reuse
│       │                             #   useClientContext() setters + clear); stale-context note surfaced via provider
│       ├── SystemStatusSection.tsx   # READ-ONLY: connection state (probe), version + data location (getSystemInfo),
│       │                             #   model-selection summary + link to #/models; honest offline/unknown degrade
│       ├── ResetSection.tsx          # Guarded reset: confirm → clear the studio's own local pref keys → success note;
│       │                             #   explicitly does NOT delete server deliverables / missions / SelectionStore
│       └── settingsModel.ts          # PURE: known-preference-key list + clearLocalPreferences(storage); systemView
│                                     #   derivation (connected|offline|unknown; version; dataLocation); modelSummary
│                                     #   from CapabilityInventory (selectable families → selected/active label) — all
│                                     #   catalog-key driven, no raw family code / model id as operator content
├── shell/
│   ├── Shell.tsx                     # +1 line: route id "settings" → <SettingsScreen /> (replaces PlaceholderScreen)
│   └── router.tsx                    # settings route status "placeholder" → "shipped" (no path/order change)
├── screens/
│   └── placeholders.tsx              # Drop the `settings` entry (copy map becomes empty; component returns null path
│                                     #   stays valid for any future placeholder) — and its test updated
├── i18n/
│   ├── catalog.ts                    # + settings.* typed CatalogKeys (section titles; system.connected/offline/unknown,
│   │                                 #   system.version, system.dataLocation, system.localFirst note, system.modelSummary
│   │                                 #   + link label; reset.title/body/confirm/cancel/done; network.perMissionNote).
│   │                                 #   Reuse lang.* and context.* keys. Remove settings.comingSoon.* (placeholder gone).
│   ├── en.ts                         # + EN strings (fallback source of truth); remove the two comingSoon strings
│   └── fr.ts                         # + FR strings (parity); remove the two comingSoon strings
├── api.ts                            # + getSystemInfo(): GET /api/system → SystemInfo; existing fetchCapabilities reused
└── types.ts                          # + SystemInfo { version: string; dataDir: string }

agency_studio/
└── server.py                         # + GET /api/system route → _handle_system(): JSON {version: __version__,
                                      #   data_dir: str(rag.data_dir())}; read-only, no user input, loopback (inherited)

tests/
└── test_system_endpoint.py           # NEW offline pytest: /api/system returns version + data_dir JSON; 200; no secret;
                                      #   GET-only (no write path); shape stable

Co-located frontend tests (existing convention):
├── screens/settings/settingsModel.test.ts        # Pure: clearLocalPreferences removes exactly the 4 studio keys and
│                                                  #   leaves unrelated keys; systemView derives connected/offline/unknown +
│                                                  #   version + dataLocation; modelSummary from a CapabilityInventory
├── screens/settings/SettingsScreen.test.tsx      # Load + render three sections; parallel fetch; error(retry); offline
│                                                  #   degrade (local controls still work); a11y/keyboard
├── screens/settings/PreferencesSection.test.tsx  # Change language → setLocale persists + top-bar stays in sync (single
│                                                  #   source of truth); set/clear default context → ClientContext persists;
│                                                  #   stale context surfaced
└── screens/settings/ResetSection.test.tsx        # Confirm → local pref keys cleared to defaults; dismiss → nothing changes;
                                                   #   asserts server-side data / SelectionStore untouched (no such call made)
```

**Structure Decision**: one new self-contained frontend module `screens/settings/` inside the
existing app, consuming the umbrella's shell/i18n/design-system layers and — crucially — the
**existing single sources of truth** (`useI18n().setLocale`, `useClientContext()`, the
`localStorage` prefs) so a preference edited in Settings is byte-for-byte the same state the
top-bar controls drive (no drift, FR-002). It replaces the `settings` `ComingSoon` placeholder
and flips the route `placeholder → shipped` with a one-line Shell dispatch change. The **only**
backend change is one minimal, read-only, no-input `GET /api/system` endpoint that supplies the
two facts the frontend cannot truthfully invent (version + data location), satisfying FR-004
without violating Principle III. The developer Console, mission loop, capability
probing/selection-store/precedence, inspector veto loop, and the `agencykit/` subtree are left
byte-identical.

## Complexity Tracking

> No constitution violations — table intentionally empty. S8's one server addition
> (`GET /api/system`) is **not** a violation of any principle: it is additive and read-only
> (Principle X), stdlib-only (I, IX), loopback with no user input and no secret (VI), offline
> tested (VII), and is *required by* Principle III (no invented information) precisely because
> the frontend cannot truthfully source the version or data location. Reset is scoped to the
> studio's own local keys and provably leaves server data and the `SelectionStore` untouched.
> No change to probing / selection-store / precedence / mission loop / veto loop.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
