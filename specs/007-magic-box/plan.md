# Implementation Plan: The Magic Box — App Shell, Navigation, i18n & Screen Inventory (Brick 7 umbrella)

**Branch**: `007-magic-box` | **Date**: 2026-07-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-magic-box/spec.md`

## Summary

Brick 7's umbrella feature replaces the developer-console-first GUI with a
non-technical-user application foundation: a shell whose default landing surface is the
magic box home ("What do you want to produce?"), a persistent localized navigation over
the 8 inventoried screens, an EN/FR i18n scaffolding every child screen reuses, a shared
design system (tokens, components, shared states) with a WCAG 2.1 AA baseline, and a
shell-owned client-context selector backed by the Brick 6 taxonomy. Technically: a new
shell layer inside the existing React 19 + Vite app (`app/studio/`), a ~100-line
hash-based router, a custom typed i18n provider with static EN/FR catalogs (zero new npm
dependencies), CSS-custom-property design tokens, and localStorage persistence for
non-secret preferences. The existing console remains intact and reachable at a secondary
route; the Python stdlib server is not modified.

## Technical Context

**Language/Version**: TypeScript ~5.7 (frontend); Python 3.11+ (server — unchanged by this feature)

**Primary Dependencies**: React 19, Vite 6, react-markdown 9 (all pre-existing). **Zero new runtime or dev dependencies** — router and i18n are hand-rolled minimal modules.

**Storage**: Browser `localStorage` for non-secret preferences (language, last client context). No server-side storage changes; taxonomy and missions persist through existing Brick 6 registries.

**Testing**: Vitest 3 + @testing-library/react + jsdom for the frontend (existing setup); `pytest` root suite untouched and stays green (server not modified).

**Target Platform**: Desktop browser on the operator's own machine, served by the local stdlib server at `127.0.0.1` from `app/studio/dist` (existing static route, `path_inside()`-guarded).

**Project Type**: Web application frontend layer (shell) over an existing local HTTP/SSE server.

**Performance Goals**: Shell interactive on first paint of a local static bundle (sub-second on localhost); language switch and route change render without full page reload; no measurable regression to existing console flows.

**Constraints**: Constitution I–XI; additive delivery (console preserved at a secondary route, byte-identical server); offline test suites; no new npm dependencies (licensing surface stays frozen); WCAG 2.1 AA design-system baseline (spec FR-011a); interface-only i18n (spec FR-009a).

**Scale/Scope**: 8 inventoried screens (S1–S8) rendered as localized placeholders in this feature; 2 locales (EN/FR); ~1 shell layout, ~1 router, ~2 catalogs, ~6 shared UI states; child specs fill screen internals later.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — pure presentation layer; no reasoning path added or altered; no API calls of any kind beyond the existing local server.
- [x] **II. Engine neutrality**: PASS — the shell never talks to engines; it consumes the server's existing engine-neutral endpoints.
- [x] **III. No invented information**: PASS — mission semantics, citation, and inspector veto flow are untouched (FR-016); the shell only re-presents existing events.
- [x] **IV. Local-first & offline-by-default**: PASS — no new network behavior; the app is a local static bundle talking to 127.0.0.1; paid/cloud choices remain explicit opt-ins re-surfaced from Brick 4.
- [x] **V. Subprocess boundaries**: PASS — frontend-only change; `openmontage/`, `agencykit/`, and all subprocess boundaries untouched.
- [x] **VI. Security**: PASS — server not modified: bind, CORS posture, `path_inside()`, https-only outbound all byte-identical; FR-015 additionally forbids any secret-entry UI surface.
- [x] **VII. Offline tests**: PASS — the root `pytest` suite is unaffected (no Python changes); new Vitest tests (shell, router, i18n completeness, placeholders) run offline with mocked fetch, matching the existing frontend suite's conventions.
- [x] **VIII. End-user simplicity**: PASS — this brick is the enforcement of Principle VIII: single entry point, guided navigation, no terminal anywhere (FR-003).
- [x] **IX. License**: PASS — zero new components; nothing to add to `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — the existing console App is preserved intact and reachable at a secondary route; server and mission loop byte-identical. The one deliberate behavior change — the default landing surface becomes the magic box — is the brick's explicit, spec-clarified purpose (spec Clarifications Q1, FR-018), not an unjustified rewrite.
- [x] **XI. English everywhere**: PASS — repository artifacts in English; the FR catalog is an end-user-facing localization surface, which Principle XI explicitly permits.

**Post-Phase-1 re-check (2026-07-05)**: design artifacts (data-model, contracts,
quickstart) introduce no server changes, no new dependencies, no engine or mission-loop
surface — all gates hold as marked.

## Project Structure

### Documentation (this feature)

```text
specs/007-magic-box/
├── spec.md              # Umbrella spec (screen inventory S1–S8)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── routes.md        # Route map + navigation contract (shell ↔ screens)
│   └── i18n-catalog.md  # Catalog shape, key naming, fallback + completeness contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
app/studio/src/
├── main.tsx                    # Mounts <I18nProvider><Shell/></I18nProvider> (edited)
├── App.tsx                     # Existing console — preserved, rendered by the console route
├── shell/
│   ├── Shell.tsx               # App frame: topbar, nav, connection state, route outlet
│   ├── Nav.tsx                 # Persistent navigation (ARIA-patterned, localized)
│   ├── router.ts               # Minimal hash router: parse/subscribe/navigate + route table
│   ├── ClientContext.tsx       # Shell-owned client/project/campaign selector (Brick 6 API)
│   └── ConnectionBanner.tsx    # Plain-language reachability state + auto-recovery
├── i18n/
│   ├── I18nProvider.tsx        # Context provider: locale state, t(), persistence, fallback
│   ├── catalog.ts              # Typed key inventory (single source of key truth)
│   ├── en.ts                   # English catalog (fallback source of truth)
│   └── fr.ts                   # French catalog
├── ui/
│   ├── tokens.css              # Design tokens: color/type/spacing custom properties (AA contrast)
│   └── states.tsx              # Shared Loading / Empty / Error / ComingSoon / NotFound
├── screens/
│   ├── Home.tsx                # S1 seed: the magic box question routing into brief (placeholder-level)
│   ├── placeholders.tsx        # S2–S6, S8 localized ComingSoon screens
│   ├── Models.tsx              # S7: embeds existing <Capabilities/> in the shell
│   └── Console.tsx             # Secondary route hosting the preserved existing App
└── (existing components/, api.ts, types.ts … unchanged)

app/studio/src/__tests__ (co-located *.test.tsx as today):
├── shell/Shell.test.tsx        # Landing surface, nav reachability, a11y keyboard pass
├── shell/router.test.ts        # Route parse/fallback/not-found
├── i18n/i18n.test.tsx          # Switch, persistence, fallback, catalog completeness
└── screens/placeholders.test.tsx

tests/                          # Python suite — no changes (server untouched)
```

**Structure Decision**: single existing frontend project (`app/studio/`) gains three new
layers (`shell/`, `i18n/`, `ui/`, `screens/`); the current `App.tsx` console moves
behind a route unchanged. No backend directories are touched; the server keeps serving
`app/studio/dist` exactly as before.

## Complexity Tracking

> No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
