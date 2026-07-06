# Implementation Plan: Guided Brief — From Intent to a Launch-Ready Production (Brick 7 · Screen S2)

**Branch**: `008-s2-guided-brief` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-s2-guided-brief/spec.md`

## Summary

S2 replaces the `#/brief` placeholder with the Guided Brief screen: a deterministic,
curated question flow (per deliverable type — research / strategy / video —
parameterized by sector/domain) that turns the intent carried from the magic box home
into a complete brief, shows it on a single editable review, and launches it through
the **existing** `POST /api/mission` endpoint. Technically: a new `screens/brief/`
module in the React 19 + Vite app (`app/studio/`) — question-set data modules, a flow
engine component, a review component, a brief→mission composer, and a localStorage
draft store — plus new `brief.*` keys in the EN/FR catalogs. Zero server changes, zero
new dependencies: the brief composes a structured goal text and reuses the existing
flags (`web_search` on by default per clarification), taxonomy fields, and the
server's pre-SSE 409 capability-blocker contract. A small module-scoped mission
session keeps the launched SSE stream alive across navigation until S3 ships its
timeline.

## Technical Context

**Language/Version**: TypeScript ~5.7 (frontend only); Python 3.11+ server **unchanged**.

**Primary Dependencies**: React 19, Vite 6 (pre-existing). **Zero new runtime or dev dependencies** — question sets are typed data modules, the flow engine is plain React, drafts use `localStorage`.

**Storage**: Browser `localStorage` for the single brief draft (non-secret, local-only, versioned key) — same pattern as the umbrella's language/client-context persistence. No server-side storage changes.

**Testing**: Vitest 3 + @testing-library/react + jsdom (existing setup), fetch mocked; root `pytest` suite untouched and stays green (server not modified).

**Target Platform**: Desktop browser on the operator's machine, served by the local stdlib server at `127.0.0.1` from `app/studio/dist` (existing static route).

**Project Type**: Web application frontend feature (one inventoried screen) over the existing local HTTP/SSE server.

**Performance Goals**: Step transitions and review render instantly (pure local state); launch feedback within one SSE frame (the server announces the run id first); no regression to shell or console flows.

**Constraints**: Constitution I–XI; umbrella cross-cutting rules (i18n catalogs, design system + WCAG 2.1 AA, shared states, tone of voice); additive delivery — server byte-identical, `assets` default corrected only inside the new brief path (the console keeps its behavior); spec clarifications: curated deterministic question sets, three v1 deliverable types, no expert knobs, `web_search` default-on.

**Scale/Scope**: 1 screen, 3 question sets (research / strategy / video), ~1 curated sector list, 2 locales (~60–90 new catalog keys), 1 draft store, 1 composer, 1 mission session module, ~6 test files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — no reasoning path added; the brief is deterministic UI data; launching delegates to the existing mission loop (CLI engine subprocess).
- [x] **II. Engine neutrality**: PASS — the brief never names an engine; it omits `engine` semantics beyond the existing API default, and the server's `ensure_production_engine` guard is untouched.
- [x] **III. No invented information**: PASS — the brief transmits the operator's answers verbatim (composer adds structure, not content); mission internet research is **on by default** (spec FR-012a) so deliverables stay sourced; citation/inspector flow untouched.
- [x] **IV. Local-first & offline-by-default**: PASS — local/free defaults everywhere; the only off-machine options (cloud video model) surface as explicit, labeled opt-ins read from the Brick 4 inventory; engine research is the constitutionally exempt default (Principle IV wording: "offline apart from the engine's own research").
- [x] **V. Subprocess boundaries**: PASS — frontend-only; no `openmontage/` import, no subtree edits.
- [x] **VI. Security**: PASS — server byte-identical (bind/CORS/`path_inside()`/https-only unchanged); no secret-entry surface anywhere in the flow (spec FR-014); drafts store answers only.
- [x] **VII. Offline tests**: PASS — all new behavior covered by Vitest with mocked fetch (flow, composer, draft store, blockers, launch failure); no network, no CLI, no live server. Root pytest suite unaffected.
- [x] **VIII. End-user simplicity**: PASS — this screen *is* the guided-brief promise: plain-language questions, defaults/skip everywhere, no terminal, no machinery terms (tone-of-voice + wording audit SC-007).
- [x] **IX. License**: PASS — zero new components; nothing to add to `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — a placeholder route becomes a shipped screen (the umbrella's designed lifecycle); server, mission loop, veto loop, console untouched. No behavior change outside the new screen.
- [x] **XI. English everywhere**: PASS — code/docs/commits in English; FR strings live only in the end-user catalog (explicitly permitted).

**Post-Phase-1 re-check (2026-07-06)**: design artifacts (data model, contracts,
quickstart) confirm zero server changes, zero new dependencies, no engine or
mission-loop surface, composer transmits answers verbatim — all gates hold as marked.

## Project Structure

### Documentation (this feature)

```text
specs/008-s2-guided-brief/
├── spec.md              # Feature spec (clarified 2026-07-06)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── brief-mission-mapping.md   # Brief → POST /api/mission body (the launch contract)
│   └── question-set.md            # Question-set data shape + catalog-key contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
app/studio/src/
├── screens/
│   ├── brief/
│   │   ├── GuidedBrief.tsx      # Screen: reads ?intent=, drives flow → review → launch states
│   │   ├── FlowStep.tsx         # One question step: prompt, input/choices, default/skip, back/next
│   │   ├── Review.tsx           # Single editable summary of every answer + effective options
│   │   ├── questionSets.ts      # Curated typed question sets (research/strategy/video) + sector list
│   │   ├── briefDraft.ts        # Single localStorage draft: load/save/discard, versioned key
│   │   ├── composeMission.ts    # Brief → structured goal text + flags/taxonomy fields (verbatim answers)
│   │   └── missionSession.ts    # Module-scoped launched-run session (SSE kept alive across navigation)
│   └── placeholders.tsx         # S2 entry removed (S3–S6, S8 remain)
├── shell/router.ts              # `brief` route status: "placeholder" → "shipped"
├── i18n/
│   ├── catalog.ts               # + brief.* typed keys (questions, choices, review, errors, states)
│   ├── en.ts                    # + EN strings (fallback source of truth)
│   └── fr.ts                    # + FR strings
└── api.ts                       # One additive tweak: runMission gains an optional `assets` opt
                                 #   (absent ⇒ today's `true`, so console callers stay byte-identical;
                                 #   the brief passes it per question set — see contracts/brief-mission-mapping.md)

Co-located tests (existing convention):
├── screens/brief/GuidedBrief.test.tsx   # Intent handoff, flow completion per type, a11y/keyboard pass
├── screens/brief/Review.test.tsx        # Completeness of summary, edit-and-return, launch failure keeps brief
├── screens/brief/questionSets.test.ts   # Set shape, per-type relevance, catalog-key completeness
├── screens/brief/briefDraft.test.ts     # Persist/resume/discard, restart survival, single-draft rule
├── screens/brief/composeMission.test.ts # Verbatim answers, default flags (web_search on, paid off), taxonomy fields
└── screens/brief/missionSession.test.ts # Session survives unmount; cancel path; double-launch guard

tests/                                   # Python suite — no changes (server untouched)
```

**Structure Decision**: one new self-contained module `screens/brief/` inside the
existing frontend project, consuming the umbrella's shell/i18n/design-system layers
and the existing `api.ts` client. The only edits outside the module are the four
declared integration points: the router status flip, the catalog additions, the
placeholder-list removal, and the additive optional `assets` opt on `runMission`.
No backend directories are touched.

## Complexity Tracking

> No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
