# Implementation Plan: Capability & Model Panel — See What This Machine Can Produce and Choose Models (Brick 7 · Screen S7)

**Branch**: `013-s7-capability-panel` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/013-s7-capability-panel/spec.md`

## Summary

S7 replaces the **raw developer capability embed** currently rendered on the `#/models` route
with a real, non-technical, EN/FR-localized **operator surface**: *see what this machine can
produce* (images, video, voice/narration, transcription, understanding, search/memory, plus
production tools and integrations) and *choose which model each capability uses* — local/free
by default, cloud/paid an explicit opt-in, keys environment-only, no secrets on screen.

Per the spec Clarifications (2026-07-06): S7 surfaces **all inventoried families read-through**
(the model **chooser** renders only on the **7 selectable model families**; the **2
non-selectable** families — production tools, integrations/connectors — appear as **read-only**
availability status with a plain "how to enable it" hint); and a model pick is framed as the
capability's **standing default, applied on the next production** (saved and used next run — no
claim of a live hot-swap of an already-warm model, mirroring the honest env-override framing).

Unlike S6 (which added a small server surface), **S7 is a pure frontend layer over the
existing Brick 4 endpoints** — exactly like S4 and S5. The backend already ships everything S7
needs: `GET /api/capabilities` returns each family's `selectable` flag, resolved `active`
model, `env_override` (the var name currently overriding, or null), stored `selected` +
`selected_stale`, and per-entry `cost` / `availability` / `reason` / `enablement` / `default` /
`key_env`; `PUT /api/capabilities/selection` and `DELETE /api/capabilities/selection/{family}`
persist a per-family standing default via the existing server-side `SelectionStore` under the
env > selection > default precedence. The existing `api.ts` wrappers
(`fetchCapabilities(refresh)`, `selectCapability(family, id)`, `clearCapability(family)`) are
reused **as-is**. **No server file changes, no new endpoint, no new persistence, no pytest
change.**

The whole job is a **presentation transformation** in the frontend: turn the raw inventory
(raw family codes like `image`/`stt`/`tts`, raw model ids, raw badges `FREE/PAID`/`API`, raw
reasons `missing_binary`/`gateway_down`, English-only strings) into plain-language, localized,
accessible operator content — routed through a pure model (`capabilityModel.ts`) that maps
family→name/description, cost→plain label, availability+reason+enablement→plain status, and
computes per-family display (chooser vs read-only), env-override honesty, stale-selection
handling, and the key-name-only enablement hint (never a key value). The developer **Console**
keeps the raw `components/Capabilities.tsx` verbatim (coexistence); S7 is a separate,
self-contained `screens/models/` module. Byte-identical with the screen unused; the mission
loop, capability probing/aggregation, selection-store shape, and env>selection>default
precedence are untouched.

## Technical Context

**Language/Version**: TypeScript ~5.7 (frontend only). **No Python / server change.**

**Primary Dependencies**: React 19, Vite 6 (frontend, pre-existing). **Zero new runtime
dependencies.** No new optional extra. The screen consumes only the **existing** Brick 4
capability endpoints via the **existing** `api.ts` wrappers.

**Storage**: None added. A model choice persists as a per-family **standing default** via the
**existing** server-side `SelectionStore` (`selections.json` under the RAG data dir), owned by
Brick 4 — S7 adds **no** new store and does **not** change the selection-store shape or the
env > selection > default precedence (FR-006). Capability availability is read-only from the
existing probing.

**Testing**: Vitest 3 + @testing-library/react + jsdom for the new `screens/models/` module —
fully offline, `fetchCapabilities`/`selectCapability`/`clearCapability` mocked via the existing
`api.ts` test-double pattern (the current `screens/Models.test.tsx` already demonstrates it).
**No pytest change** (no server surface added); the root offline suite stays byte-identical and
green.

**Target Platform**: Desktop browser on the operator's machine, served by the local stdlib
server at `127.0.0.1` from `app/studio/dist`.

**Project Type**: Web application feature (one inventoried screen) — **pure frontend**, no
server-side surface.

**Performance Goals**: The panel loads the inventory on open (existing probe, same cost as the
current embed) and renders all ~9 families within one frame at local single-user volume.
Re-check (re-probe) is an explicit user action with the shared loading state and honest
progress — never a frozen or blank panel. Choosing/reverting a model is a single existing
`PUT`/`DELETE` round-trip re-reading the inventory, reflected immediately.

**Constraints**: Constitution I–XI; umbrella cross-cutting rules (EN/FR catalogs; design system
+ WCAG 2.1 AA — keyboard-operable read-status / choose-model / revert-to-default and
screen-reader labels; shared loading/empty/error/connection states; tone of voice — zero
machinery terms, no raw model id / family code / MIME type / file path as operator content).
Security & privacy: **no secret ever entered, displayed, persisted, or transmitted** — the
`key_env` field is used only to show the **name** of the environment variable to set (FR-013's
one permitted technical token), never its value, and no key input is rendered (the existing
`Models.test` no-secret assertion is preserved and strengthened). Honesty: an `env_override` in
force is shown as the environment deciding, not the stored selection (FR-007); a `selected_stale`
choice is surfaced plainly (FR-012). Additive: the developer Console's raw capability panel
stays byte-identical; the `agencykit/` subtree is untouched (not even called — S7 reads/writes
only via the studio's own capability endpoints).

**Scale/Scope**: 1 screen; **0 new endpoints, 0 server files, 0 pytest changes**; a new
self-contained `screens/models/` frontend module (Screen + per-family card + capability row +
a pure `capabilityModel.ts`) replacing the thin `screens/Models.tsx` raw embed; the router
`models` route already `shipped` + `taxonomyScoped:false` (**no router change**); ~40–55 new
EN/FR catalog keys (plain-language family names/descriptions, cost/availability statuses,
enablement hints, chooser/revert labels, empty/error/override/stale states); ~3–4 Vitest files.
Mission loop, routing, synthesis, asset rendering, inspector veto loop, capability
probing/aggregation, selection-store shape, env>selection>default precedence, developer console:
**untouched**.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — S7 adds no reasoning path; it reads the
  passive capability inventory and writes a model-selection preference. No engine call, no API
  call, no mission-loop touch; the marginal cost is zero.
- [x] **II. Engine neutrality**: PASS — the panel presents whatever the registries/probes
  report; it assumes no specific engine and adds no engine-specific behavior. The Engine
  contract and production-engine guard are untouched.
- [x] **III. No invented information**: PASS — every status, cost, availability, and enablement
  hint is derived from the studio's existing probing; S7 fabricates nothing and states honestly
  what is not available and what an env override or stale selection actually means (FR-007,
  FR-012). The inspector veto loop is untouched.
- [x] **IV. Local-first & offline-by-default**: PASS — local/free is the presented default;
  cloud/paid is explicitly marked opt-in and never the default (FR-004). Reading the inventory
  and choosing a model add **no** outbound network beyond the studio's existing local probing;
  selecting a paid provider records a **preference only** and sends nothing (FR-009). Non-Mac
  not regressed (pure presentation over the platform-neutral inventory).
- [x] **V. Subprocess boundaries**: PASS — no `openmontage/` import; the `agencykit/` subtree is
  **not** edited or even called (S7 talks only to the studio's own capability endpoints).
  Vendored subtrees unchanged.
- [x] **VI. Security**: PASS — served from `127.0.0.1`, no CORS `*`; **no API key or secret is
  ever accepted, displayed, persisted, or transmitted** — `key_env` yields only the variable
  **name** as an enablement hint, never a value, and no key input field exists (FR-010, FR-017);
  https-only-outbound is n/a (no S7 outbound). No new served path (no `path_inside` surface
  added — S7 adds no endpoint).
- [x] **VII. Offline tests**: PASS — the new module is covered by Vitest with the api wrappers
  mocked (no network, no CLI, no Node beyond jsdom, no GPU); the pure `capabilityModel.ts` is
  unit-tested directly. No server test needed (no server change); the root offline suite is
  byte-identical.
- [x] **VIII. End-user simplicity**: PASS — S7 *is* the "what can this machine make, and pick my
  model, without a terminal" promise: plain-language capability names/descriptions, plain
  availability/cost, friendly "not available — how to enable it" and empty/error states, a
  one-click chooser + revert-to-default, honest env-override/stale messaging — never a raw model
  id / family code / MIME / path (FR-002, FR-013, SC-001/004).
- [x] **IX. License**: PASS — frontend-only change using existing React/Vite; no new third-party
  component; nothing to add to `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — a thin raw embed becomes a proper shipped screen (the
  umbrella's designed lifecycle); the developer Console's raw `Capabilities` panel and every
  capability endpoint stay byte-identical; no mission loop / probing / selection-store / veto-loop
  change; the env>selection>default precedence is inherited unchanged. Behavior is byte-identical
  with the screen unused.
- [x] **XI. English everywhere**: PASS — code/docs/commits in English; operator-facing strings
  live only in the EN/FR end-user catalogs (explicitly permitted).

**Post-Phase-1 re-check (2026-07-06)**: design artifacts (research, data-model, contracts,
quickstart) confirm S7 is a pure frontend presentation layer over the **existing** Brick 4
endpoints — **no** server file, endpoint, persistence, or pytest change; the developer console
and the `agencykit/` subtree are untouched; every FR maps to a field the backend **already**
emits (`selectable`, `active`, `env_override`, `selected`/`selected_stale`, `cost`,
`availability`, `reason`, `enablement`, `key_env`); `key_env` is rendered as a variable **name**
only (never a value) and no secret input exists. All gates hold as marked.

## Project Structure

### Documentation (this feature)

```text
specs/013-s7-capability-panel/
├── spec.md              # Feature spec (clarified 2026-07-06)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── capability-endpoints.md   # The EXISTING Brick 4 contract S7 consumes read-only (no change):
│   │                             #   GET /api/capabilities, PUT + DELETE /api/capabilities/selection — shapes, precedence, key_env rule
│   └── capability-panel-model.md # Frontend contract: plain-language family map, cost/availability/status derivation,
│                                 #   selectable→chooser vs read-only, env-override & stale honesty, key-name-only hint, catalog keys
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
app/studio/src/
├── screens/
│   └── models/                       # NEW self-contained module (replaces the thin screens/Models.tsx raw embed)
│       ├── ModelsScreen.tsx          # Screen: loads the inventory (fetchCapabilities), renders every family in plain
│       │                             #   language; re-check control (refresh); shared loading / error(retry) states;
│       │                             #   machine-level (ignores client context); a11y/keyboard operable
│       ├── FamilyCard.tsx            # One capability family: plain name + description + availability status; for a
│       │                             #   SELECTABLE family renders the model chooser + revert-to-default + env-override /
│       │                             #   stale-selection honesty; for a NON-SELECTABLE family renders read-only status only
│       ├── ModelOption.tsx           # One option row: plain label, free/local vs paid/cloud marker, availability, default
│       │                             #   badge, key-configured / "set $VAR to enable" hint (NAME only, never a value)
│       └── capabilityModel.ts        # PURE model over CapabilityInventory: family→{name,description}, cost→plain label,
│                                     #   availability+reason+enablement→plain status, per-family display kind
│                                     #   (chooser|readonly), activeChoice + isEnvOverridden + isStale, enablementHint
│                                     #   (env-var NAME only) — all catalog-key driven, no raw id/code as operator content
├── screens/
│   └── Models.tsx                    # REPLACED: now renders <ModelsScreen /> (thin wrapper kept for the Shell import),
│                                     #   or deleted with Shell importing screens/models/ModelsScreen directly
├── components/
│   └── Capabilities.tsx              # UNCHANGED — still used by the developer Console (App.tsx); coexistence
├── i18n/
│   ├── catalog.ts                    # + models.* typed CatalogKeys (family names/descriptions, cost/availability
│   │                                 #   statuses, chooser/revert labels, env-override & stale notes, enablement hint,
│   │                                 #   recheck, empty/error states) — models.title reused
│   ├── en.ts                         # + EN strings (fallback source of truth)
│   └── fr.ts                         # + FR strings (parity)
└── api.ts                            # UNCHANGED — existing fetchCapabilities / selectCapability / clearCapability reused

Co-located tests (existing convention):
├── screens/models/capabilityModel.test.ts   # Pure model: family→plain name/description for all 9 families; cost/availability
│                                             #   →plain status; selectable→chooser vs non-selectable→readonly; env-override
│                                             #   honesty; stale-selection; enablement hint = env-var NAME only (never key value)
├── screens/models/ModelsScreen.test.tsx      # Load + render all families in plain language; re-check; error(retry); empty
│                                             #   (no options) state; machine-level (client context ignored); a11y/keyboard
└── screens/models/FamilyCard.test.tsx        # Selectable: choose an available option → selectCapability; revert → clearCapability;
                                              #   unavailable option not selectable; paid/cloud opt-in records preference (no key
                                              #   field, no send); env-override shown as in force; stale selection surfaced;
                                              #   NON-selectable family shows read-only status with no chooser
# (screens/Models.test.tsx is rewritten/relocated for the new plain-language surface; the current
#  raw-embed assertions — raw "Seedance (cloud)" label, no-secret — are preserved/strengthened.)
```

**Structure Decision**: one new self-contained frontend module `screens/models/` inside the
existing app, consuming the umbrella's shell/i18n/design-system layers and the **existing**
Brick 4 capability endpoints via the **existing** `api.ts` wrappers (reused unchanged). It
replaces the thin `screens/Models.tsx` raw-`Capabilities` embed with a plain-language,
localized, WCAG 2.1 AA operator surface driven by a pure `capabilityModel.ts`. **No server
file, endpoint, persistence, or pytest change** — every FR maps to a field the backend already
emits. The developer Console's raw `components/Capabilities.tsx`, the mission loop, the
capability probing/aggregation, the selection-store shape, and the env>selection>default
precedence are left byte-identical. The `models` route is already `shipped` +
`taxonomyScoped:false`, so no router change is required.

## Complexity Tracking

> No constitution violations — table intentionally empty. S7 is a pure frontend presentation
> transformation over the existing Brick 4 endpoints: no server surface, no new dependency, no
> new persistence, no change to probing / selection-store / precedence / veto loop, and no
> secret ever handled (env-var name shown, never a value).

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
