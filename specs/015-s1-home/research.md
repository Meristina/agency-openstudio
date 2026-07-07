# Phase 0 Research — S1 Home

All Technical Context items are resolved; there are no open `NEEDS CLARIFICATION`. The
spec was authored with informed defaults and clarified in one session (four decisions).
The codebase investigation below fixes every remaining design choice and records one
planning reconciliation. Decisions are ordered by impact.

## D1 — Pure frontend, or does S1 need a server change?

**Decision**: **Pure frontend, no new endpoint, no new store.** Every signal Home shows
already exists client-side or via an existing read-only endpoint:

- **Unfinished brief** → `loadBriefDraft()` reading `studio.briefDraft.v1` (existing
  `screens/brief/briefDraft.ts`), which stores the answers + `stepIndex` needed to resume.
- **Recent missions** → the existing `listMissions()` (`GET /api/missions` →
  `MissionSummary[]`, `api.ts`), read-only.
- **Active default working context** → the existing `useClientContext()`
  (`shell/ClientContext.tsx`), backed by `agency-studio.prefs.clientContext`.
- **Navigation** → the existing `navigate()` (`shell/router.tsx`).

**Rationale**: S8 legitimately added one endpoint because the frontend could not
truthfully source the version or data path (Principle III). S1 has **no** such gap —
nothing it displays is unknowable to the frontend — so adding a backend surface would
violate Additive-over-invasive (X) and the zero-dependency-core spirit for no benefit.
This mirrors S4/S5/S7: a presentation layer over existing endpoints and existing client
state.

**Alternatives considered**:
- *A new `GET /api/home` aggregation endpoint* — rejected: pure duplication of
  `GET /api/missions` plus client-only state the server doesn't hold (the brief draft and
  context live in the browser); adds surface for zero honesty or capability gain.
- *A new client-side "recent work" store* — rejected: the mission list is already the
  source of truth; a second store would drift and risk a false view (III).

## D2 — Where does selecting a recent mission go? (planning reconciliation of the Q2 clarification)

**Decision**: **Route by state, to the two existing destinations.** An **in-progress**
mission (the live/last run, identified by the persisted `followPointer.runId`) opens the
mission timeline (`#/missions`); a **completed** mission opens its delivered work in the
Library, focused on that mission (`#/library?deliverable=<mission_id>`, the existing
Library search param). S1 introduces **no** new per-mission view.

**Rationale**: The clarify session (Q2) recorded a preference for "one shared
timeline/dossier destination for both states." Planning investigation found that
destination **does not exist** and cannot be reused:

- `#/missions` (`screens/missions/MissionTimeline.tsx`) renders the **live** mission
  session (`missionSession.snapshot()`) plus a resume pointer (`followPointer`), i.e. the
  currently-running or just-finished run — **not** an arbitrary past mission by id. There
  is no timeline-by-id route.
- Completed missions' delivered work lives in the **Library**
  (`screens/library/DeliverableLibrary.tsx`), which lists `listMissions()` and already
  accepts `?deliverable=<mission_id>` to focus one.

Building a new per-mission dossier-by-id view to honor Q2 literally would be an
**invasive** change well beyond "enrich Home" (new route + new mission-rendering surface),
contradicting Principle X and the S1 scope. The reconciled behavior — in-progress → live
timeline, completed → Library deliverable — is exactly the **original** FR-005 split, is
purely additive, reuses existing surfaces, and was confirmed with the user during
planning. The spec's Clarifications and FR-005 were updated to record this.

**Alternatives considered**:
- *Always open the Library (both states)* — rejected: an in-progress mission loses its
  live timeline (the one view that shows progress), degrading the resume value of Story 2.
- *Build a per-mission dossier route* — rejected: out of scope, invasive (X).

## D3 — Recent-work scope and cardinality

**Decision**: **Global, all-contexts, most-recent-first, capped at 5**, with a "see all"
link to the **Library** (`#/library`) — the full browsable list of work — for more. Home
calls `listMissions()` with **no** filter. (`#/missions` shows only the live/last run, not
a browsable list, so it is **not** the "see all" target — see D2.)

**Rationale**: Clarify Q1/Q3. A "resume what I was doing" front door must not hide the
user's actual last work behind the active context (which primarily scopes *new* work);
global most-recent is the honest, simplest read and matches the mental model. Five is a
calm glance, not the full list; the "see all" link (to the Library, which lists every
mission) preserves discoverability without turning Home into a list view. Ordering uses the list's existing order (the API
already returns most-recent-first); if a tie/label is missing, the pure model falls back
to a sensible plain label (never a raw id).

**Alternatives considered**:
- *Scope to the active context* — rejected (Q1): hides a mission run under another
  context until the user switches, surprising a non-technical user (VIII) and risking a
  "where did my mission go" moment.
- *Show all missions inline* — rejected: duplicates the Missions/Library screens and
  bloats the front door (VIII).

## D4 — Honest degradation: empty, first-run, and load failure

**Decision**: The **start flow renders synchronously and unconditionally** (no data
dependency). The resume/recent region loads `listMissions()` independently and:
- **no draft + no missions** → a calm empty state that points back to starting new work
  (never a blank panel, dead control, or spinner);
- **`listMissions()` fails** (server unreachable) → the start flow is fully usable and an
  honest, non-alarming "couldn't load recent work" note is shown — **never** a false "no
  recent work" and **never** a perpetual spinner.

**Rationale**: FR-007/FR-008 and Principle III (no false state) + VIII (never broken for a
non-technical user). Decoupling the start flow from the recent-work fetch guarantees Story
1 is never blocked by Story 2, and the honest failure note keeps "no invented information"
true even in the empty/error case (an empty list because the fetch failed is *not* the
same claim as "you have no work").

**Alternatives considered**:
- *Block Home render until missions load* — rejected: a slow/offline server would stall
  the entire entry point (VIII, FR-008).
- *Show an empty recent list on fetch failure* — rejected: that is a false "no work"
  claim (III).

## D5 — No raw machine tokens as operator content

**Decision**: The pure `homeModel.ts` maps each `MissionSummary` to a plain **label**
(its human goal, trimmed/truncated) and a **catalog-keyed status** (in progress /
delivered / needs attention), never surfacing a raw `mission_id`, `runId`, or verdict
token to the user; the `mission_id` is used only internally to build the navigation
target. The context label is rendered from `context.*` catalog keys with a plain "no
context" state when unset.

**Rationale**: Umbrella tone-of-voice + Principle VIII (no raw machine tokens as
operator content), consistent with how the timeline/library humanize mission data. Keeping
the mapping in a **pure** model makes it fully offline-testable (VII) and keeps the
orchestrator thin.

**Alternatives considered**:
- *Render `verdict` / ids directly* — rejected: leaks machine tokens to a non-technical
  user (VIII) and couples copy to backend strings.

## Resolved unknowns

| Item | Resolution |
|---|---|
| New endpoint? | **No** — pure frontend over existing `GET /api/missions` + client state (D1) |
| New store? | **No** — reads existing draft/pointer/context/missions (D1) |
| Open a recent mission | **By state** — in-progress → `#/missions`; completed → `#/library?deliverable=<id>` (D2) |
| Recent scope / count | **Global, most-recent-first, ≤5** + see-all link (D3) |
| Empty / failure behavior | Start flow always renders; honest empty + honest load-error, no false empty/spinner (D4) |
| Operator content | Plain label + catalog status; no raw id/verdict shown (D5) |
| Testing | Vitest offline (`listMissions` mocked, `localStorage`/`navigate` in jsdom); no pytest (no server) |
