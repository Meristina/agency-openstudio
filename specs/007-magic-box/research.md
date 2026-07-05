# Phase 0 Research — Brick 7 umbrella (app shell, navigation, i18n, screen inventory)

All Technical Context unknowns resolved. Each decision below records what was chosen,
why, and what was rejected.

## R1. Routing mechanism

- **Decision**: A minimal hash-based router (`app/studio/src/shell/router.ts`, ~100
  lines): parse `location.hash` against a static route table (S1–S8 + console +
  not-found), a subscribe hook (`useRoute()`), and a `navigate()` helper. Deep links
  like `#/library` work; unknown hashes resolve to the localized NotFound state.
- **Rationale**: 9 static routes need no dynamic matching, nested layouts, or data
  loaders. Hash routing requires zero server configuration — the stdlib server keeps
  serving `index.html` and static assets exactly as today (no history-API fallback
  route needed, so `server.py` stays byte-identical, Constitution VI/X). Zero new
  dependencies keeps the license ledger frozen (Constitution IX).
- **Alternatives considered**:
  - *react-router v7* — rejected: a large dependency for 9 flat routes; history-mode
    default would demand a server fallback handler (invasive to `server.py`).
  - *Keep the current in-memory `tab` state* — rejected: not deep-linkable, no
    not-found semantics, and child screens (library items, mission views) will need
    addressable locations.

## R2. i18n mechanism

- **Decision**: A hand-rolled typed i18n module: `catalog.ts` declares the key
  inventory as a TypeScript type; `en.ts` and `fr.ts` export `Record<CatalogKey,
  string>` catalogs; `I18nProvider.tsx` holds the active locale in React context,
  exposes `t(key, params?)` with `{param}` interpolation, falls back to `en` for any
  missing key, persists the choice to `localStorage`, and initializes from
  `navigator.language` (fr* → FR, otherwise EN).
- **Rationale**: Typing catalogs against one key inventory makes completeness a
  compile-time property, and a trivial Vitest test (`Object.keys(en)` deep-equals
  `Object.keys(fr)`) satisfies spec FR-007/SC-004 mechanically. Two locales and flat
  interpolation need none of ICU plural machinery. Zero new dependencies
  (Constitution IX/X); react-markdown-rendered mission content is data, not chrome,
  and is out of i18n scope per spec FR-009a.
- **Alternatives considered**:
  - *react-i18next* — rejected: two runtime deps (i18next + binding), runtime key
    typing is opt-in and looser than a native typed record, and its
    suspense/namespace machinery is unearned at 2 locales × ~1–200 keys.
  - *react-intl (FormatJS)* — rejected: heavier still; ICU features unneeded.
  - *Per-component string constants* — rejected: exactly the hardcoding FR-006 bans.

## R3. Rollout mechanics (magic box default, console preserved)

- **Decision**: `main.tsx` mounts the new `Shell`; the default route (`#/` or empty
  hash) renders S1 Home. The entire existing console `App.tsx` is preserved
  unmodified and rendered by a `#/console` route (`screens/Console.tsx` is a thin
  wrapper). No server change: `/` continues to serve the built bundle.
- **Rationale**: Implements clarification Q1 (magic box default immediately, console
  fully functional at a secondary location) with the smallest possible blast radius:
  the console keeps its own tabs, state, and tests; regressions are structurally
  impossible on the Python side because `server.py` is untouched (SC-009).
- **Alternatives considered**:
  - *Second Vite entry/bundle for the new app* — rejected: two bundles complicate the
    stdlib static route and double build/test surface.
  - *Console as default, magic box opt-in* — rejected by clarification Q1.

## R4. Design tokens & WCAG 2.1 AA enforcement

- **Decision**: CSS custom properties in `ui/tokens.css` (palette with AA-verified
  contrast pairs, type scale, spacing, focus ring), consumed by shell and shared
  states; interactive patterns follow the ARIA Authoring Practices already used by
  the console's tablist (roving tabindex). AA verification: (a) contrast pairs chosen
  at token definition time (documented in the token file), (b) Vitest +
  testing-library assertions that every interactive element is reachable by keyboard
  and exposes an accessible name — written as reusable test helpers child screens
  repeat.
- **Rationale**: Tokens make AA contrast a one-place property instead of a per-screen
  audit (spec FR-011a); accessible-name/keyboard tests encode the testable half of AA
  without adding an audit dependency. Zero new dependencies.
- **Alternatives considered**:
  - *axe-core / vitest-axe automated audits* — deferred, not rejected: axe-core is
    MPL-2.0 (AGPL-compatible) and could be added later by a child spec if manual
    helpers prove insufficient; not taken now to keep this brick dependency-free.
  - *A component library (Radix, MUI…)* — rejected: large dependency and design
    surface; the app needs ~10 primitives, all buildable on the existing css.

## R5. Preferences persistence

- **Decision**: `localStorage` under a single namespaced key (`agency-studio.prefs`):
  `{ locale, clientContext }`. Read once at boot, written on change; malformed or
  absent storage falls back to defaults (browser-language locale, no client context).
- **Rationale**: Preferences are per-browser, non-secret, and needed before the first
  server round-trip (locale). Keeping them client-side means zero server surface and
  no new persistence to guard (Constitution VI). Matches Jan/AnythingLLM local-first
  convention.
- **Alternatives considered**:
  - *Server-side prefs endpoint + registry file* — rejected: adds an API and file
    format for data the server never needs; violates smallest-surface instinct.
  - *Cookies* — rejected: sent on every request for no reason; localStorage is the
    established SPA mechanism.

## R6. Connection state (service reachability)

- **Decision**: The shell derives reachability from the API calls it already makes
  (taxonomy fetch at boot + any screen fetch): a shared fetch wrapper flags
  network-level failures (TypeError / fetch rejection, not HTTP error codes) into a
  `ConnectionBanner` with a localized plain-language message and a periodic retry;
  first success clears it. No new health endpoint.
- **Rationale**: Reuses existing endpoints, so the server stays untouched; HTTP-level
  errors (404/500) stay screen-local errors, while only transport failure means "the
  studio isn't reachable" (spec FR-005). Periodic retry gives the automatic recovery
  the spec requires.
- **Alternatives considered**:
  - *New `/api/health` endpoint* — rejected: server change for information the
    existing calls already reveal.
  - *SSE keepalive probe* — rejected: heavier lifecycle for the same signal.

## R7. Client-context selector data source

- **Decision**: Reuse the existing Brick 6 taxonomy API (`fetchTaxonomy()` in
  `app/studio/src/api.ts` → `GET /api/taxonomy`) as the sole source for the shell's
  client-context selector; the selection itself lives in shell state + preferences
  (R5). "Unassigned" is a client-side presentation of missions without taxonomy
  fields (already supported by the Brick 6 data model), per clarification Q3.
- **Rationale**: The taxonomy contract shipped and was reviewed in Brick 6
  (`specs/006-clients-projects/contracts/taxonomy-api.md`); the shell adds no new
  server semantics, only a persistent, shell-level presentation of the same data.
- **Alternatives considered**:
  - *New "active context" server endpoint* — rejected: the active context is a UI
    lens, not shared server state.

## R8. Placeholder screens for S2–S6, S8

- **Decision**: One parameterized `ComingSoon` shared state (localized title +
  body + back-home action), instantiated per inventoried route from the route table;
  S1 (Home) ships as a real-but-minimal magic box surface (the question + a
  navigation hand-off), S7 (Models) embeds the existing `<Capabilities/>` component.
- **Rationale**: Spec US5/FR-004 requires localized graceful placeholders; deriving
  them from the route table guarantees no inventoried route can lack one. S7 is an
  embed rather than a rebuild because the Brick 4 panel already exists and its child
  spec owns deeper localization.
- **Alternatives considered**:
  - *Skip placeholders, hide unbuilt nav entries* — rejected: the spec's promise is a
    navigable whole application from day one; hidden areas break SC-002/SC-005.
