# Phase 0 Research — S8 Settings

All Technical Context items are resolved; there are no open `NEEDS CLARIFICATION`. The spec was
authored with informed defaults, and the codebase investigation below fixes every remaining
design choice. Decisions are ordered by impact.

## D1 — How to source the System / About facts truthfully (the one impactful decision)

**Decision**: Add exactly **one** minimal, read-only server endpoint — `GET /api/system` →
`{ "version": <str>, "data_dir": <str> }` — and derive the rest of the System panel from signals
that already exist (reachability probe + `GET /api/capabilities`). S8 is therefore a frontend
presentation module **plus** one honest server fact-source, not a pure-frontend layer.

**Rationale**: FR-004 requires the panel to show the **application version** and the **local
data location**. Neither is truthfully knowable from the frontend:
- The web app's `package.json` version is `0.0.0` (an unmaintained placeholder); the maintained
  version lives server-side at `agency_studio/__init__.py::__version__`.
- The data directory is computed server-side by `agency_studio/rag.py::data_dir()`; the browser
  has no way to know the real filesystem location.

Principle III (No Invented Information — NON-NEGOTIABLE) forbids fabricating or guessing either
value. The authoritative, honest source is the server, so a tiny read-only endpoint is the
correct — and constitutionally required — way to satisfy FR-004. The endpoint takes no user
input, returns no secret, serves no user-named file (no `path_inside`/traversal surface), is
loopback-bound (inherited), stdlib JSON, and offline-testable — the same "small honest server
surface" shape S6 used.

**Alternatives considered**:
- *Pure frontend, scope statement only* (show "local, on this machine" but omit version/path) —
  rejected: silently drops two MUST fields of FR-004, and any attempt to show them from the
  frontend would invent them.
- *Inject the version at Vite build time* — rejected: still cannot know the data directory, and
  it forks a second version source that will drift from the server's `__version__`.
- *Reuse `GET /api/models` / `GET /api/capabilities` to carry version + path* — rejected:
  overloads a capability endpoint with unrelated system facts; a dedicated `/api/system` is
  clearer and keeps the capability contract byte-identical for S7.

## D2 — Language & default context: reuse the existing single sources of truth

**Decision**: Settings edits language via `useI18n().setLocale` and the default working context
via `useClientContext()` setters — the **same** hooks/state the top-bar `LanguageSwitch` and
`ClientContextSelector` already use. Settings builds **no** parallel preference state.

**Rationale**: FR-002 requires the Settings language control and the top-bar control to never
disagree. The only way to guarantee that is a single source of truth. `setLocale` persists
`PREFS_KEY` and re-renders the whole app; `ClientContext` persists `PREFS_KEY.clientContext` and
already contains stale-selection validation gated on the first taxonomy load (so a deleted
client/project/campaign is surfaced, not silently applied — satisfying the stale-context edge
case and FR-003). Reusing them means Settings inherits both behaviors for free.

**Alternatives considered**: a Settings-local prefs copy synced on change — rejected: two
sources of truth are exactly the drift FR-002 forbids.

## D3 — Reset scope: clear the studio's own local keys only, never server data

**Decision**: Reset removes exactly the four studio-owned `localStorage` keys and nothing else:
- `PREFS_KEY` = `agency-studio.prefs` (locale + clientContext)
- `PREFS_KEY.importAssociations` = `agency-studio.prefs.importAssociations`
- `BRIEF_DRAFT_KEY` = `studio.briefDraft.v1`
- `FOLLOW_POINTER_KEY` = `agency.studio.followPointer.v1`

It does **not** call `localStorage.clear()` (which could wipe unrelated same-origin data) and
does **not** touch any server resource — deliverables, missions, and the Brick 4 server-side
`SelectionStore` (`selections.json`) are provably untouched because Reset issues **no** network
call. A model selection is therefore preserved across a preferences reset (FR-006).

**Rationale**: FR-006 is explicit that resetting local preferences must not delete real work.
Enumerating the known keys is the additive, auditable way (Principle X) and lets a test assert
exactly which keys are cleared. The action is guarded by an explicit confirmation; dismissing it
changes nothing.

**Alternatives considered**: `localStorage.clear()` — rejected: over-broad, could remove data
owned by other tools on `127.0.0.1`. A server-side "reset preferences" endpoint — rejected:
there is no server-side preference store to reset (prefs are client-side); adding one is
needless surface.

## D4 — No global network toggle in Settings (preserve per-mission opt-in)

**Decision**: Settings surfaces at most an **informational** note that research/network is opt-in
per mission; it exposes **no control** that changes network behavior globally.

**Rationale**: Principle IV and the security invariant require network access only via explicit
per-mission opt-in. A global "always allow network" switch would weaken that guarantee. FR-007
encodes this: any network-related preference is a suggestion only, still confirmed per mission.
The simplest faithful implementation is to add no such control at all.

## D5 — Connection state without a new probe

**Decision**: The System panel reflects reachability using the **existing** probe semantics
(`ConnectionBanner` already polls `fetchTaxonomy` and distinguishes transport failure). On open,
the parallel `getSystemInfo` / `fetchCapabilities` reads themselves determine connected vs
offline; a transport failure renders an honest "offline / unknown" state while the purely local
Preferences and Reset controls keep working (FR-009). No new heartbeat endpoint is introduced.

**Rationale**: Reuse the shipped connection semantics; avoid a redundant polling surface.

## D6 — Appearance / theme deferred

**Decision**: No light/dark theme control in S8; the studio follows OS appearance.

**Rationale**: There is no existing theme system; adding one is net-new scope beyond "consolidate
existing preferences." Recorded as an out-of-scope assumption in the spec; a future spec can add
it as its own preference.

## Cross-cutting confirmations (from the codebase)

- **Route already exists**: `router.tsx` has `settings` (`#/settings`, `taxonomyScoped:false`)
  as `status:"placeholder"`. S8 flips it to `"shipped"` and adds the Shell dispatch line — no
  new route, no path/order change.
- **Shared states** (`ui/states.tsx`) provide `Loading` / `Empty` / `ErrorState`; the
  connection banner is app-wide in the Shell. S8 reuses them.
- **Catalog is a typed union** (`i18n/catalog.ts`); new keys are added to the union and to both
  `en.ts` / `fr.ts`. The `settings.comingSoon.*` pair is removed with the placeholder; `lang.*`
  and `context.*` keys are reused as-is.
- **api.ts pattern**: existing wrappers (`fetchCapabilities`, `getModelsStatus`, …) show the
  exact shape for the new `getSystemInfo` wrapper and its jsdom test double.
- **Server test collection**: root `pytest` collects `tests/`; the new `/api/system` handler
  gets an offline test there, monkeypatching nothing network-bound (it reads a version string
  and a path).
