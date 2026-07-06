# Phase 0 Research — S7 Capability & Model Panel

**Feature**: Capability & Model Panel (Brick 7 · Screen S7) · **Branch**: `013-s7-capability-panel` · **Date**: 2026-07-06

All Technical-Context unknowns were resolvable by codebase inspection — the Brick 4 backend and
the Brick 7 umbrella foundation already exist. No `NEEDS CLARIFICATION` remained after the spec
Clarifications session (2026-07-06). Decisions below are grounded in the actual source.

---

## D1 — Backend already complete: S7 is pure frontend

- **Decision**: Build S7 entirely in the frontend over the **existing** Brick 4 endpoints; add
  **no** server file, endpoint, persistence, or pytest change.
- **Rationale**: `GET /api/capabilities` (`agency_studio/server.py:854`, handler
  `_handle_capabilities` at `:1791`) returns a `CapabilityInventory` whose per-family
  `CapabilityFamilyView` already carries `selectable`, resolved `active`, `env_override`,
  `selected`, `selected_stale`, and `entries[]`; each `CapabilityEntry` already carries `label`,
  `cost` (`free`/`paid`/`free_paid`), `availability`, `reason`, `enablement`, `tier`, `note`,
  `default`, `key_env` (`app/studio/src/types.ts:263–304`). Selection persists via
  `PUT /api/capabilities/selection` (`server.py:918`) and
  `DELETE /api/capabilities/selection/{family}` (`server.py:934`), backed by `SelectionStore`
  (`agency_studio/capabilities.py:403`) under the env > selection > default resolution core
  (`capabilities.py:491`). **Every S7 FR maps to a field already emitted** — nothing new is
  needed server-side.
- **Alternatives considered**: (a) a bespoke S7 read/aggregation endpoint — rejected: it would
  duplicate `_handle_capabilities` and add surface for no gain; (b) client-side re-derivation of
  availability — rejected: probing is the server's job and already done. This mirrors **S4/S5**
  (pure frontend), and is *simpler* than **S6** (which needed a server bundler).

## D2 — Reuse the existing `api.ts` wrappers unchanged

- **Decision**: Consume `fetchCapabilities(refresh)`, `selectCapability(family, id)`, and
  `clearCapability(family)` (`app/studio/src/api.ts:287–306`) as-is; do **not** touch `api.ts`.
- **Rationale**: The three wrappers already cover load (+`?refresh=1` re-probe), set a standing
  default, and revert to default; `selectCapability` returns the updated `CapabilityFamilyView`
  and `clearCapability` tolerates `204`. Errors surface via the shared `errorText` helper, so the
  screen's error/retry handling matches the rest of the app.
- **Alternatives considered**: new typed wrappers — rejected: the existing ones are exactly the
  contract S7 needs and are already unit-covered (`capabilities-api.test.ts`).

## D3 — Replace the raw embed with a `screens/models/` module; keep the Console panel

- **Decision**: Create a self-contained `screens/models/` module (ModelsScreen + FamilyCard +
  ModelOption + pure `capabilityModel.ts`) and point the Shell's `models` route at it, replacing
  the thin `screens/Models.tsx` that renders `components/Capabilities.tsx` verbatim. Leave
  `components/Capabilities.tsx` **unchanged** for the developer Console (`App.tsx:14,574`).
- **Rationale**: `screens/Models.tsx` currently embeds the raw developer component (English-only,
  raw family codes, model ids in `<code>`, badges `FREE/PAID`/`API`, raw reasons
  `missing_binary`/`gateway_down`) under a localized title — a developer panel, not an operator
  surface. A dedicated module matches the established shipped-screen pattern (`screens/export/`,
  `screens/library/`, `screens/import/`) and isolates the plain-language transformation. Keeping
  the Console's raw panel honors the umbrella coexistence assumption and the Additive principle
  (byte-identical console).
- **Alternatives considered**: editing `components/Capabilities.tsx` in place — rejected: it is
  shared with the Console; localizing/plain-languaging it would change the developer panel
  (non-additive) and entangle two audiences in one component.

## D4 — Plain-language transformation lives in a pure `capabilityModel.ts`

- **Decision**: All raw→plain mapping is a **pure, catalog-key-driven** model:
  family code → `{nameKey, descriptionKey}`; `cost` → plain cost label; `availability` + `reason`
  + `enablement` → plain status + enablement hint; per-family **display kind** (`chooser` when
  `selectable`, else `readonly`); `active`/`selected`/`env_override`/`selected_stale` →
  `activeChoice`, `isEnvOverridden`, `isStale`. Components render the model; they hold no mapping
  logic.
- **Rationale**: A pure model is directly unit-testable offline (no DOM, no network), keeps
  raw-identifier suppression (FR-013) in one auditable place, and matches S4/S6's
  `libraryModel.ts`/`exportModel.ts` precedent.
- **Alternatives considered**: inline mapping in JSX — rejected: untestable in isolation and
  scatters the "no raw id/code" invariant.

## D5 — Secret safety: env-var **name** only, never a value, never an input

- **Decision**: For a paid/cloud entry, show whether its key is configured (derived from the
  entry's `availability`/`reason`) and, when not, the **name** of `key_env` as an enablement hint
  ("set `$AGENCY_STUDIO_VIDEO_API_KEY`") — never the value, and never a key input field.
- **Rationale**: Constitution VI + umbrella FR-015 keep keys environment-only; observation 7307
  explicitly flags `key_env` must not be exposed as a value. The existing `Models.test` already
  asserts no `key|secret` label and no textbox — S7 preserves and strengthens this (FR-010).
- **Alternatives considered**: a "configure key" affordance in-app — rejected: it would breach
  the env-only invariant; enabling a key is a deliberate environment action outside the studio.

## D6 — Honesty for env override and stale selection

- **Decision**: When `env_override` is non-null, present the environment as **currently
  deciding** that family (the stored `selected` is retained but not in force); when
  `selected_stale` is true (chosen model no longer available), plainly note the prior choice is
  unavailable and what is in force (`active`) instead, and let the operator pick again or revert.
- **Rationale**: These map 1:1 to `CapabilityFamilyView.env_override` and `selected_stale`,
  which Brick 4 already computes; surfacing them honestly satisfies FR-007/FR-012 and Principle
  III (no invented state). The raw component already shows `overridden by $VAR` / `stale
  selection` badges — S7 restates them in plain, localized language.
- **Alternatives considered**: hiding the override / showing the stored pick as active —
  rejected: dishonest; the operator would think their choice is in force when it is not.

## D7 — Selection effect = standing default on next production (no live hot-swap)

- **Decision**: Frame a model pick as the capability's **standing default, applied on the next
  production**; the screen confirms the choice is saved and used next run, and does not claim an
  already-warm/resident model is hot-swapped.
- **Rationale**: The server applies a selection by invalidating the lazy singletons bound to that
  family (`_invalidate_selection_consumers`, `server.py:1818`) so the new model is picked up on
  **next use** — there is no mid-flight swap of a warm model. Spec Clarification Q2 locks this
  honest framing (mirrors the env-override honesty). Acceptance wording is "becomes the standing
  default and persists," not "instantly active."
- **Alternatives considered**: "now active" immediacy — rejected: overclaims a live swap the
  backend does not perform.

## D8 — Machine-level, not taxonomy-scoped; no router change

- **Decision**: The panel reflects what *this machine* can produce, independent of the active
  client/project/campaign; it does **not** consume the shell's `useClientContext()` selector.
  The `models` route stays `status:"shipped"`, `taxonomyScoped:false` — **no router change**.
- **Rationale**: Models a machine can run are a machine property, not a client's; the route is
  already correctly non-scoped (`app/studio/src/shell/router.ts:22`). FR-015/SC-007.
- **Alternatives considered**: per-client model profiles — rejected: out of scope; the backend
  has one machine-level selection store, not per-taxonomy.

## D9 — Testing strategy (offline, no server change)

- **Decision**: Vitest + @testing-library/react + jsdom with the three `api.ts` wrappers mocked
  (per the existing `screens/Models.test.tsx` / `capabilities-api.test.ts` pattern); the pure
  `capabilityModel.ts` unit-tested directly. **No pytest change** (no server surface).
- **Rationale**: Constitution VII (offline, no network/CLI/Node-beyond-jsdom/GPU). The transform
  and every honesty/secret/selectable branch are deterministic over a mocked inventory.
- **Alternatives considered**: an integration test hitting the live endpoint — rejected: the
  endpoints are already covered by Brick 4's server tests; S7 adds only presentation.

---

**Outcome**: All unknowns resolved; zero `NEEDS CLARIFICATION` remain. S7 is a pure,
additive frontend presentation layer over the existing Brick 4 capability endpoints, with no
server, persistence, dependency, or precedence change and no secret ever handled.
