# Implementation Plan: S1 Home — The Enriched Entry Point (Brick 7 · Screen S1)

**Branch**: `015-s1-home` | **Date**: 2026-07-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/015-s1-home/spec.md`

## Summary

S1 **enriches the Home screen** — the studio's single entry point (`#/`) — from today's
bare intent→brief form into a real front door that does three jobs, one per prioritized
user story, all **additive** and all over **existing surfaces** (no new endpoint, no new
store):

1. **Start (P1)** — the existing question → guided-brief flow, preserved byte-for-byte
   (`navigate("#/brief?intent=…")` with the same optional-intent behavior), re-presented
   as a deliberate, welcoming entry rather than a stub.
2. **Resume (P2)** — surface the **unfinished brief** (the existing
   `loadBriefDraft()` / `studio.briefDraft.v1`) and up to **5** most-recent missions
   (existing `listMissions()`, global / all-contexts, most-recent-first). Selecting the
   draft reopens the guided brief where it was left; selecting a mission opens the right
   **existing** destination for its state — the live timeline (`#/missions`) if it is in
   progress (matching the persisted `followPointer.runId`), or its Library deliverable
   (`#/library?deliverable=<mission_id>`) if it is complete.
3. **Orient (P3)** — plain-language shortcuts to the studio's main areas
   (`#/library`, `#/import`, `#/models`) via `navigate`, plus a **read-only** label of the
   active default working context (from the existing `useClientContext()`), so users see
   what new work will be scoped to (editing stays in S8 Settings).

**Pure-frontend layer, no server change.** Unlike S8 (which added one honest read-only
endpoint for facts the frontend could not source), S1 needs **no** new backend: every
signal it shows already exists client-side or via an existing endpoint — the brief draft
(`localStorage`), recent missions (`GET /api/missions` via `listMissions()`), and the
active context (`useClientContext()`). This mirrors S4/S5/S7 (pure frontend over existing
endpoints). The job is a **presentation layer**: turn raw signals (a draft object, a
`MissionSummary[]`, a context selection) into plain-language, localized, WCAG 2.1 AA
operator content in a self-contained, additive Home rewrite that keeps the load-bearing
intent→brief flow identical.

The mission loop, routing engine, guided brief internals, mission timeline, library,
capability probing/selection-store, inspector veto loop, and the developer Console stay
byte-identical; the `agencykit/` subtree is untouched.

## Technical Context

**Language/Version**: TypeScript ~5.7 (frontend only). No Python change.

**Primary Dependencies**: React 19 + Vite 6 (pre-existing). **Zero new runtime
dependencies**, no new optional extra, no new endpoint.

**Storage**: **No new store.** S1 only **reads** existing state: the brief draft
(`studio.briefDraft.v1` via `loadBriefDraft`), the follow-pointer
(`agency.studio.followPointer.v1` via `followPointer.read()`), and the client-context
prefs (`agency-studio.prefs.clientContext` via `useClientContext()`). Recent missions
come from the existing `GET /api/missions` (`listMissions()`), read-only. Home writes
nothing except the intent it hands to the brief route (unchanged from today).

**Testing**: Vitest 3 + @testing-library/react + jsdom for the rewritten `Home` and a
pure `homeModel.ts` (fully offline — `listMissions` mocked via the existing `api.ts`
test-double pattern; `localStorage` exercised in jsdom; `navigate` asserted via
`window.location.hash`). No pytest (no server surface). Root offline suite stays green.

**Target Platform**: Desktop browser on the operator's machine, served by the local
stdlib server at `127.0.0.1` from `app/studio/dist`.

**Project Type**: Web application feature (one inventoried screen) — pure frontend module
over existing endpoints and existing client state.

**Performance Goals**: Home renders the start flow **immediately** (synchronous — no
data dependency, FR-007/FR-008), then loads recent missions in **one** cheap read
(`GET /api/missions`) that resolves in-band and fails soft (honest note, never a false
empty or a perpetual spinner). Draft and context reads are synchronous local reads.

**Constraints**: Constitution I–XI; umbrella cross-cutting rules (EN/FR catalogs;
design system + WCAG 2.1 AA — every control keyboard-operable and screen-reader
labelled; shared loading/empty/error states; tone of voice — no raw machine tokens as
operator content, so no raw `mission_id` shown, only plain goal/label + status).
Honesty (Principle III): recent work reflects the real `listMissions()` result — never
invented, never a false "delivered", never a false "no work" on failure (FR-008, FR-010);
the context label reflects the real `useClientContext()` value with a plain "no context"
state when unset. Start flow (Story 1) is **never** blocked by the availability of
recent work (Story 2). Security (Principle VI): served from `127.0.0.1`, no CORS `*`; S1
adds no endpoint, no user input beyond the existing free-text intent (already carried as
a URL-encoded query param exactly as today), no secret, no outbound of its own. Additive
(Principle X): Home is enriched, not re-architected — the intent→brief contract is
byte-identical; the guided brief, timeline, library, models, and Console are untouched.

**Scale/Scope**: 1 screen (Home enriched in place); a new self-contained
`screens/home/` module (orchestrator `Home.tsx` + small presentational parts + a pure
`homeModel.ts`); **no** new `api.ts` wrapper (reuses `listMissions`), **no** new
`types.ts` interface (reuses `MissionSummary`); reuses `loadBriefDraft`,
`followPointer.read`, `useClientContext`, `navigate`; ~15–20 new EN/FR catalog keys
(section titles, resume/recent labels + statuses, empty/failed-to-load notes, shortcut
labels, context-label copy) reusing existing `nav.*`, `context.*`, `brief.draft.*`,
`state.*` keys where they fit; ~2–3 Vitest files. Mission loop, routing engine, guided
brief, timeline, library, capability probing/selection-store/precedence, inspector veto
loop, developer console, and the `agencykit/` subtree: **untouched**. No backend, no
pytest.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — S1 adds no reasoning path. Home
  reads local state and one existing read-only list endpoint and navigates. No engine
  call, no token-billed API, no mission-loop touch; marginal cost zero.
- [x] **II. Engine neutrality**: PASS — no engine-specific behavior; Home presents entry,
  resumption, and orientation. The Engine contract and production guard are untouched.
- [x] **III. No invented information**: PASS — recent work is exactly what
  `listMissions()` returns (never fabricated); status labels reflect the real
  `verdict`/`delivered`/in-progress signal; the context label reflects the real
  `useClientContext()` value; on load failure Home shows an honest note, never a false
  "no work" or a perpetual spinner (FR-008, FR-010). The inspector veto loop is untouched.
- [x] **IV. Local-first & offline-by-default**: PASS — Home reads local state and the
  studio's own local `GET /api/missions`; it adds **no** outbound network of its own and
  **no** network toggle, so the per-mission opt-in is preserved exactly. Non-Mac not
  regressed (platform-neutral).
- [x] **V. Subprocess boundaries**: PASS — no `openmontage/` import; the `agencykit/`
  subtree is not edited or called (Home talks only to the studio's own endpoint and
  client state). Vendored subtrees unchanged.
- [x] **VI. Security**: PASS — served from `127.0.0.1`, no CORS `*`. S1 adds no endpoint
  and no new user-input surface: the only input is the existing free-text intent, still
  passed to `#/brief` as a URL-encoded query param exactly as today (no new traversal or
  injection surface); no secret, no key, nothing persisted or logged.
- [x] **VII. Offline tests**: PASS — the rewritten Home and pure `homeModel` are covered
  by Vitest with `listMissions` mocked and `localStorage`/`navigate` exercised in jsdom
  (no network, no CLI, no Node beyond jsdom, no GPU). No server surface → no pytest. Root
  offline suite stays green.
- [x] **VIII. End-user simplicity**: PASS — S1 *is* the "single entry point" principle
  made whole: one plain question to start, one-click resume of what you were doing, plain
  shortcuts to the rest, no terminal, no raw machine tokens (no `mission_id` shown — only
  a plain goal/label + status).
- [x] **IX. License**: PASS — frontend uses existing React/Vite; no new third-party
  component; nothing to add to `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — the intent→brief contract is byte-identical;
  resume/recent/orient are new **additive** regions that degrade to today's behavior when
  empty or on failure (FR-007). No new route, no per-mission view; the guided brief,
  timeline, library, models, probing, selection-store, and veto loop are byte-identical.
- [x] **XI. English everywhere**: PASS — code/docs/commits in English; operator-facing
  strings live only in the EN/FR end-user catalogs (explicitly permitted).

**Post-Phase-1 re-check (2026-07-07)**: the design artifacts (research, data-model,
contracts, quickstart) confirm the footprint above — a pure-frontend enrichment reusing
`listMissions` / `loadBriefDraft` / `followPointer` / `useClientContext` / `navigate`,
zero new endpoint, zero new store, the intent→brief contract byte-identical, and mission
opening routed to the two **existing** destinations by state. All gates hold as marked.

## Project Structure

### Documentation (this feature)

```text
specs/015-s1-home/
├── spec.md              # Feature spec (clarified; planning reconciliation of FR-005 recorded)
├── plan.md              # This file
├── research.md          # Phase 0 output — pure-frontend decision, mission-open-by-state, recent-scope, honesty/degrade
├── data-model.md        # Phase 1 output — read-only view-models (Home view, recent-mission item, context label)
├── quickstart.md        # Phase 1 output — developer orientation
├── contracts/
│   └── home-screen-model.md   # Frontend contract: region map, existing sources of truth, recent-item derivation,
│                              #   mission-open routing by state, empty/error rules, catalog keys
├── checklists/
│   └── requirements.md  # Spec quality checklist (all pass)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
app/studio/src/
├── screens/
│   └── home/                        # NEW self-contained module (replaces the single-file Home.tsx)
│       ├── Home.tsx                 # Orchestrator: start form (unchanged intent→brief) + resume region + recent list
│       │                            #   + shortcuts + read-only context label; loads recent missions once, fails soft;
│       │                            #   a11y landmarks; start flow renders synchronously, never blocked by recent load
│       ├── StartSection.tsx         # The existing question + intent textarea + start button; submit builds the SAME
│       │                            #   `#/brief?intent=…` URL as today (byte-identical behavior)
│       ├── ResumeSection.tsx        # Unfinished-brief affordance (loadBriefDraft → resume #/brief) + up-to-5 recent
│       │                            #   missions (plain label + status → open by state); calm empty state; honest
│       │                            #   "couldn't load recent work" note on failure; "see all" link → #/library (full list)
│       ├── ShortcutsSection.tsx     # Plain-language shortcuts → #/library, #/import, #/models (navigate)
│       ├── ContextLabel.tsx         # READ-ONLY active-context label from useClientContext(); "no context" when unset;
│       │                            #   never edits (points to S8 Settings for changes)
│       └── homeModel.ts             # PURE: recentMissionsView(MissionSummary[]) → up-to-5 {label, statusKey, target}
│                                    #   (target = #/missions if in-progress else #/library?deliverable=<id>);
│                                    #   hasResumableDraft(draft); contextLabelView(context) → {text|noneKey};
│                                    #   all catalog-key driven, no raw mission_id / verdict token as operator content
├── shell/
│   └── Shell.tsx                    # +0/1 line: route id "home" → <Home /> from screens/home (import path only;
│                                    #   route already "shipped", no status/order change)
├── i18n/
│   ├── catalog.ts                   # + home.* typed CatalogKeys (home.resume.title/draft/recentTitle/openMission,
│   │                                #   home.recent.inProgress/delivered/failedVerdict, home.recent.empty,
│   │                                #   home.recent.loadError, home.recent.seeAll, home.shortcuts.title/library/import/
│   │                                #   models, home.context.scopedTo/none). Reuse nav.*, context.*, brief.draft.*, state.*
│   ├── en.ts                        # + EN strings (fallback source of truth)
│   └── fr.ts                        # + FR strings (parity)
└── (api.ts / types.ts unchanged)    # reuses listMissions() + MissionSummary; NO new wrapper, NO new interface

Co-located frontend tests (existing convention):
├── screens/home/homeModel.test.ts   # Pure: recentMissionsView caps at 5, most-recent-first, maps in-progress vs
│                                     #   delivered → correct target (#/missions vs #/library?deliverable=<id>), never
│                                     #   emits a raw mission_id/verdict as label; hasResumableDraft true/false;
│                                     #   contextLabelView with/without a set context
└── screens/home/Home.test.tsx       # Start flow: intent → #/brief?intent=… byte-identical (incl. empty intent still
                                      #   navigates); resume draft → #/brief; recent list renders + opens by state;
                                      #   empty state (no draft, no missions) is calm not broken; listMissions failure
                                      #   → start flow still works + honest note (no false empty, no perpetual spinner);
                                      #   EN/FR render; a11y/keyboard
```

**Structure Decision**: one new self-contained frontend module `screens/home/` inside the
existing app (replacing the current single-file `screens/Home.tsx`), consuming the
umbrella's shell/i18n/design-system layers and the **existing single sources of truth**
(`loadBriefDraft`, `followPointer.read`, `useClientContext`, `listMissions`, `navigate`)
so nothing drifts and no new store or endpoint is introduced. The `home` route is already
`shipped`; only the Shell's import target changes. The load-bearing intent→brief flow is
preserved byte-for-byte; the guided brief, mission timeline, library, models panel,
capability probing/selection-store/precedence, inspector veto loop, developer console, and
the `agencykit/` subtree are left byte-identical.

## Complexity Tracking

> No constitution violations — table intentionally empty. S1 is a pure-frontend,
> additive enrichment of an existing screen: no new endpoint (I, IX; every fact already
> exists client-side or via an existing read-only endpoint), no new store (X — reads
> existing state), no new outbound network or toggle (IV, VI), offline-tested (VII), and
> the intent→brief contract plus all downstream screens stay byte-identical (X). The one
> planning reconciliation (open a recent mission via the two **existing** destinations by
> state, rather than a new per-mission dossier route) is the *additive* choice —
> explicitly to avoid an invasive new route.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
