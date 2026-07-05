# Contract — Route map & navigation (shell ↔ screens)

The shell exposes this contract to every child screen spec. A child spec implements a
screen by replacing the placeholder component behind its route id; it must not add
routes outside the spec's Screen Inventory (spec FR-020) without amending the umbrella.

## Route table (authoritative runtime form of the Screen Inventory)

| Inventory | Route id | Hash | Default component (this feature) | Taxonomy-scoped |
|---|---|---|---|---|
| S1 | `home` | `#/` (and empty hash) | `screens/Home` — magic box question, hands off to `#/brief` | no |
| S2 | `brief` | `#/brief` | ComingSoon placeholder | no (reads context if set) |
| S3 | `missions` | `#/missions` | ComingSoon placeholder | yes |
| S4 | `library` | `#/library` | ComingSoon placeholder | yes |
| S5 | `import` | `#/import` | ComingSoon placeholder | no |
| S6 | `export` | `#/export` | ComingSoon placeholder | no |
| S7 | `models` | `#/models` | `screens/Models` — embeds existing `Capabilities` | no |
| S8 | `settings` | `#/settings` | ComingSoon placeholder (language switch lives in shell chrome regardless) | no |
| — | `console` | `#/console` | `screens/Console` — the preserved pre-Brick-7 `App.tsx`, unmodified | no |

Unknown hash → NotFound shared state (localized, link home). It is a rendering
fallback, not a route entry.

## Navigation guarantees (what child screens may rely on)

1. **Reachability**: every route above is reachable from the persistent nav in ≤ 2
   interactions from anywhere (SC-002); the nav marks the active route
   (`aria-current="page"`).
2. **Intent hand-off**: `home` navigates to `brief` carrying the user's typed intent
   (query encoded in the hash fragment's search part, e.g. `#/brief?intent=…`);
   the brief child spec owns interpreting it.
3. **Locale**: every screen renders inside `I18nProvider`; `useI18n().t` is available
   and re-renders on locale change without unmount (screen state survives a language
   switch).
4. **Client context**: taxonomy-scoped screens receive the active
   `{client, project, campaign}` from shell context; `null` client means "all work,
   unassigned bucket visible" (FR-013a).
5. **Connection**: transport-level unreachability is shell-owned (banner + retry);
   screens only handle their own HTTP-level errors with the shared Error state.
6. **No terminal**: a screen requiring env vars for optional power features must
   explain them in prose, never require them (FR-003) or accept secrets (FR-015).

## Accessibility contract (design-system baseline, FR-011a)

- All interactive elements keyboard-operable and exposing an accessible name; focus
  visible via the shared focus-ring token; nav follows the ARIA pattern already used
  by the console tablist (roving tabindex, arrow keys).
- Shared test helpers (shipped with the shell tests) encode these checks; child
  screens reuse them.
