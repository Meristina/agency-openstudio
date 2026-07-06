# Feature Specification: Mission Timeline — Follow a Running Production, Live and in Human Terms (Brick 7 · Screen S3)

**Feature Branch**: `009-s3-mission-timeline`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "lance le cycle S3 Mission Timeline" — start the spec-kit cycle for screen S3 (Mission Timeline) of the Brick 7 magic-box inventory: follow a running mission live, in human terms — research → departments at work → synthesis → quality inspection, including fix loops, with cancel; owns human-language event mapping, live progress presentation, and cancel/error handling (per the authoritative screen inventory in `specs/007-magic-box/spec.md`).

## Scope

This spec covers the **Mission Timeline screen (S3)** only: the surface a non-technical
operator lands on the moment a production is launched (from the Guided Brief, S2) and
where they watch it run to completion. It turns the mission's live event stream into a
single, plain-language, at-a-glance story of what the agency is doing right now —
gathering facts, putting departments to work, drawing everything together, and letting
the quality inspector check it (including fix loops) — and lets the operator cancel a
run in progress or understand a run that ends in error. It replaces the current
`missions` coming-soon placeholder with the shipped experience.

It builds on the Brick 7 umbrella foundation (shell, navigation, EN/FR i18n, design
system, shared loading/empty/error states), on the S2 Guided Brief handoff (the launched
production session), and on the existing local mission service and its event stream —
which S3 only presents, never alters (umbrella FR-016; Constitution Principle X).

Out of scope here: capturing intent (S1) and building the brief (S2); browsing or
previewing finished deliverables (S4 Deliverable Library — S3 hands off to it at
completion but does not implement it); importing material (S5); export bundles (S6); the
capability/model panel (S7); settings (S8); and any change whatsoever to the mission
loop, routing, synthesis, asset rendering, the inspector veto loop, or the shape of the
events themselves (umbrella FR-016; Constitution Principles III, V, X). The existing
developer console and its raw event log remain untouched at their secondary location
(umbrella coexistence assumption); S3 is the operator-facing presentation, not a
replacement for the console.

## Clarifications

### Session 2026-07-06

- Q: After a full app reload/close while a production is still running, does the Mission Timeline live-re-attach to the in-flight run, or fall back to another path? → A: No live re-attach. In-app navigation still preserves live following (FR-015); only a full reload/close falls back — on return, when the interrupted run left a checkpoint, the screen offers to resume the production from that checkpoint via the existing resumable/checkpoint path (never pretending the live stream survived, never forcing a start-from-scratch when a checkpoint exists).
- Q: How much detail does the live timeline expose to the non-technical operator? → A: Curated high-level stages by default (gather facts → departments → synthesis → inspection), with an optional expand/drill-down to plain-language per-activity detail — not a raw per-event log (the developer console remains the raw view).
- Q: On a successful finish, before the Deliverable Library (S4) ships, where does the "view your deliverable" action lead? → A: To the existing local mission-detail/dossier view (including its PDF export) as the interim destination, swapped for the S4 library when it ships — so the operator reaches a real, usable deliverable at completion from day one.
- Q: Must v1 support following more than one production at the same time? → A: No — v1 follows a single active production at a time, matching the current single launch-session design; the Mission Run stays singular. Multi-run following can be added later without redesign.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Watch the production happen, in plain language (Priority: P1)

Immediately after launching a brief, the operator is on the Mission Timeline, watching
their production unfold as a living sequence of plain-language stages: the agency is
**gathering the facts it needs**, then **the right departments are doing the work**,
then it is **pulling everything together**, then **a quality check is verifying it** —
and if the check sends work back for fixing, the operator sees that a round of
improvements is under way, not a failure. Each stage shows whether it is coming up, in
progress, or finished. Nothing on the screen names a department kit, an engine, a
pipeline, a phase code, or a flag; the operator simply understands what is happening and
that it is progressing.

**Why this priority**: This is the screen's founding purpose and the reason S3 is on the
brick's critical path — between "I launched a production" (S2) and "here is my finished
deliverable" (S4), the operator must be able to see that the agency is working and trust
that it is going somewhere. Without a live, legible progress surface, a launched mission
is an opaque wait, which fails End-User Simplicity (Constitution VIII).

**Independent Test**: Feed the screen a recorded, representative sequence of mission
events (including a route, several departments, one or more synthesis/inspection
iterations with a fix loop, and completion) and verify it renders an ordered,
plain-language timeline whose stages transition coming-up → in-progress → done in step
with the stream — testable fully offline against a simulated event source, with no live
engine, network, or CLI.

**Acceptance Scenarios**:

1. **Given** a production has just been launched from the Guided Brief, **When** the operator is routed to the Mission Timeline, **Then** they immediately see the production identified in plain language and a timeline that begins showing activity as the first events arrive — they never see a blank or purely technical screen.
2. **Given** the mission emits its stream of events, **When** each event arrives, **Then** the corresponding human-language stage updates its state (coming up → in progress → done) live, in order, without the operator taking any action and without a manual refresh.
3. **Given** the quality inspection sends work back for improvement (a fix loop), **When** the subsequent iteration runs, **Then** the operator sees, in plain language, that the work is being revised and re-checked — presented as normal quality assurance, not as an error.
4. **Given** any moment of the run, **When** the operator looks at the timeline, **Then** they can tell what has finished, what is happening now, and that more is to come — without needing to interpret any internal term (no department key, engine name, pipeline, phase code, or flag appears in any language).
5. **Given** the mission runs through optional early steps (e.g. it consults sources, prior material, or connected knowledge before the departments start), **When** those steps occur, **Then** they are shown as plain-language preparatory activity when present and simply omitted when absent — the timeline never shows an empty slot for a step that did not run.
6. **Given** the whole surface, **When** its wording is reviewed, **Then** every stage label, status, helper text, and message is rendered in the interface language (EN/FR) from the umbrella catalogs, with no hardcoded or raw-key text.

---

### User Story 2 - Stop a run that shouldn't continue (Priority: P2)

At any point while the production is running, the operator can **stop it** with one
clearly labeled action. Because stopping throws away in-progress work, the action asks
for a brief confirmation in plain language; once confirmed, the run halts promptly and
the timeline settles into an unambiguous "stopped" state that makes clear the production
did not finish and nothing was saved as a deliverable. The operator is never stranded on
a screen that keeps spinning after they asked it to stop.

**Why this priority**: Cancel is explicitly part of S3's mandate in the screen inventory,
and the ability to stop a run the operator no longer wants (wrong brief, changed mind,
runaway) is basic control over their own machine. It ranks below US1 because there must
first be a run to watch before stopping it matters.

**Independent Test**: Drive a simulated running mission, invoke stop, confirm, and verify
the underlying cancel path is exercised, the stream is torn down, and the timeline
resolves to the stopped state with no lingering "in progress" stage — all offline against
the simulated service.

**Acceptance Scenarios**:

1. **Given** a production is running, **When** the operator chooses to stop it, **Then** they are asked to confirm in plain language (because in-progress work will be lost), and only an explicit confirmation actually stops the run.
2. **Given** the operator confirms the stop, **When** the request is issued, **Then** the run is asked to halt through the existing local cancel path and the timeline promptly settles into a clear "stopped, not finished, nothing saved" state.
3. **Given** the operator decides against stopping, **When** they dismiss the confirmation, **Then** the run continues undisturbed and the timeline keeps updating.
4. **Given** a run that has already finished, failed, or been stopped, **When** the operator looks for the stop action, **Then** it is no longer offered — a settled run cannot be stopped again.
5. **Given** the operator navigates away or the confirmation is racing a run that is finishing on its own, **When** either resolves first, **Then** the outcome is consistent (a run that finished shows finished; a run that was stopped shows stopped) — the operator never sees two contradictory outcomes.

---

### User Story 3 - Understand a run that ends — success or error (Priority: P3)

When the production finishes, the timeline resolves into a clear terminal state. On
**success**, the operator sees a plain-language completion summary — the production is
done and its quality verdict — with a clear way forward to the finished deliverable (its
home in the library once S4 ships, or the existing mission-detail view until then). On **error**,
the operator sees a plain-language explanation that something went wrong and the
production did not complete, with a sensible next step (retry or go back to the brief),
and, when the mission left recoverable work behind, the honest option to resume rather
than start over. No terminal state ever dead-ends on a spinner or a raw technical dump.

**Why this priority**: A production the operator cannot tell has succeeded or failed is
useless; the terminal states are what connect S3 to the rest of the journey (S4). It
ranks below live progress and cancel because it concerns the end of the run, which only
matters once the run and its controls exist.

**Independent Test**: Replay a simulated stream that terminates in (a) success with a
deliverable reference and (b) an error, and verify each resolves to the matching
plain-language terminal state with the correct forward action — offline, no live service.

**Acceptance Scenarios**:

1. **Given** a production completes successfully, **When** the terminal state renders, **Then** the operator sees a plain-language "finished" summary including the quality verdict, and a clear action leading to the finished deliverable (the library once S4 ships, the existing mission-detail view — including its PDF export — until then).
2. **Given** a production ends in error, **When** the terminal state renders, **Then** the operator sees a plain-language explanation that it did not complete and a sensible next step, with no raw stack trace, phase code, or engine error surfaced as-is.
3. **Given** an errored run left recoverable work behind, **When** the terminal state renders, **Then** the operator is honestly offered the option to resume the production from where it stopped, using the existing resume path, instead of only being able to restart.
4. **Given** any terminal state (finished, stopped, or error), **When** the operator views it, **Then** the launched production remains identifiable and the operator has at least one clear way forward — the screen is never a dead end.

---

### User Story 4 - Reach and re-open the timeline from anywhere (Priority: P4)

The Mission Timeline is not only reached by launching a brief — it is a first-class
destination the operator can open from the application's navigation while a production is
running, to check on it after wandering off to another screen. Opening the timeline with
a production active shows that production live; opening it with no production active
shows a calm, plain-language empty state that points the operator to start one (the
Guided Brief). The operator is never shown a broken or developer-facing page in either
case.

**Why this priority**: The umbrella guarantees every inventoried screen is reachable in
at most two interactions and renders either its experience or a localized placeholder
(umbrella SC-002, SC-005); S3 must honor that as a navigable destination. It ranks below
the core watch/stop/resolve stories because those define the screen's value, while this
defines its reachability.

**Independent Test**: With a production active in the session, navigate to the timeline
from the shell and verify it shows the live run; with no production active, navigate to
it and verify the localized empty state with a route to the Guided Brief — both offline.

**Acceptance Scenarios**:

1. **Given** a production is being followed in the current app session, **When** the operator navigates to another screen and back to the Mission Timeline, **Then** the same production is still shown with its current progress (the session is not lost by in-app navigation).
2. **Given** no production is active, **When** the operator opens the Mission Timeline from navigation, **Then** they see a plain-language empty state explaining there is nothing running and offering to start a production (the Guided Brief) — never a blank, broken, or technical page.
3. **Given** the operator is on the timeline of a finished, stopped, or errored production, **When** they choose to start another, **Then** they are routed to begin a new brief, and the just-ended production's outcome remains consultable until they do.

---

### User Story 5 - Honest about what "live following" can and cannot survive (Priority: P5)

The operator gets an honest, plain-language account of the connection between the app and
the running production. While the app is following a run, a dropped connection to the
local service is surfaced calmly (consistent with the shell's connection state), not as a
crash. And the operator is not misled into thinking a run survives things it cannot: if
following the run depends on the app session staying open, the screen does not pretend
otherwise — it sets the expectation truthfully and, wherever the underlying service can
reconnect or reload state, uses it.

**Why this priority**: End-User Simplicity (Constitution VIII) and the "no invented
information" spirit (Constitution III) extend to the interface's own honesty about its
limits; a timeline that silently loses a run, or implies durability it doesn't have,
betrays the operator's trust. It ships last because it hardens the edges of the core
stories rather than introducing new capability.

**Independent Test**: Simulate a mid-run loss of the local service and verify the timeline
surfaces a calm, localized connection-lost state without discarding what was already
shown or crashing; verify the screen's stated expectations about following match its
actual behavior (no claim of durability the run does not have).

**Acceptance Scenarios**:

1. **Given** a run is being followed, **When** the connection to the local service is lost mid-run, **Then** the timeline surfaces a calm, plain-language connection-lost state (consistent with the shell), keeps what was already shown, and does not present a raw error or a frozen spinner.
2. **Given** the way following works has a real limit (e.g. it depends on the app session staying open), **When** the operator is following a run, **Then** the interface sets that expectation truthfully rather than implying a durability it does not have.
3. **Given** the operator returns after a full app reload/close and the interrupted run left a checkpoint, **When** the timeline reopens, **Then** it offers to resume the production from that checkpoint (via the existing resume path) rather than forcing the operator to start over — and where no checkpoint exists, the honest terminal/empty state applies.

---

### Edge Cases

- **Events arrive faster than the eye**: a burst of events (many departments finishing at once) still resolves to a correct, ordered final timeline; no stage is dropped, duplicated, or shown out of order.
- **Unknown or newly-added event kind**: an event whose kind the screen does not specifically map is either folded into the nearest human stage or safely ignored — it never crashes the timeline or leaks a raw phase code to the operator.
- **Optional preparatory steps absent**: a plain research/strategy run with no sources, prior material, connected knowledge, or asset rendering shows only the stages that actually occurred — no empty placeholders for steps that never ran.
- **Fix loop repeats several times**: multiple inspection→revision rounds are shown as successive quality rounds, legibly numbered in human terms, without the timeline growing incomprehensible.
- **Stop pressed at the very last moment**: a stop that races a run finishing on its own resolves to exactly one outcome (finished or stopped), never both, and never a stuck in-progress stage (US2 scenario 5).
- **Terminal reached with zero deliverable**: a successful run that produced no previewable artifact still resolves to a clear "finished" state with its verdict and a forward path, not an error.
- **Interface language switched mid-run**: the timeline re-renders every stage, status, and message in the new language with the run's progress intact (umbrella guarantee), and keeps updating.
- **Direct navigation to the timeline with no active run**: renders the localized empty state (US4 scenario 2), never a broken page — mirroring the umbrella's placeholder guarantee for not-yet-active surfaces.
- **App reload / close while a run is in progress**: the screen behaves per its truthfully-stated following model (US5) — it does not silently claim the run continued if it did not, and it does not fabricate progress; on return it offers checkpoint-resume when a checkpoint exists (US5 scenario 3), otherwise the honest terminal/empty state.
- **Error payload carries technical detail**: any raw message from the service is presented through a plain-language wrapper; the operator sees an understandable explanation, and technical detail is never surfaced verbatim as the primary message.

## Requirements *(mandatory)*

### Functional Requirements

**Live progress presentation**

- **FR-001**: The Mission Timeline MUST present a launched production's live event stream as an ordered sequence of plain-language stages covering, at minimum, gathering facts / preparation, departments at work, drawing everything together (synthesis), and quality inspection including fix loops — updating each stage's state (upcoming → in progress → done) as events arrive, with no manual refresh. These curated high-level stages are the default view; per-activity detail MUST be reachable through an optional, plain-language drill-down (expand) and MUST never be required to understand that the production is progressing.
- **FR-002**: The screen MUST map the mission's existing event kinds to human-language stages without changing, reordering, or dropping the underlying events; it presents the stream, and MUST NOT alter mission-loop, routing, synthesis, asset, or inspector behavior (umbrella FR-016; Constitution Principles III, V, X).
- **FR-003**: Optional/best-effort activities that only occur on some runs (e.g. source consultation, prior-material retrieval, connected-knowledge lookup, asset rendering) MUST be shown as plain-language activity only when they actually occur, and omitted entirely — with no empty placeholder — when they do not.
- **FR-004**: A quality inspection that returns work for improvement (a fix loop) MUST be presented as a normal quality round in progress — legibly indicating that revision and re-checking are happening — never as an error or a stall; repeated rounds MUST remain legible.
- **FR-005**: No surface of the timeline may display internal machinery terminology in any language — no department key, engine name, pipeline name, phase/status code, flag, or environment variable; all stage and status wording MUST be plain production language per the umbrella tone-of-voice rules.
- **FR-006**: A burst of events MUST resolve to a correct, ordered, de-duplicated timeline; an unrecognized event kind MUST be safely folded or ignored without crashing the view or leaking a raw code (graceful over strict).

**Cancel / stop**

- **FR-007**: While a production is running, the screen MUST offer a single, clearly labeled stop action; because stopping discards in-progress work, activating it MUST require an explicit plain-language confirmation before the run is actually stopped.
- **FR-008**: On confirmed stop, the screen MUST request cancellation through the existing local cancel path (the mission's cancel endpoint / session cancel), tear down the live stream, and settle the timeline into an unambiguous "stopped — did not finish, nothing saved as a deliverable" state.
- **FR-009**: The stop action MUST NOT be offered once a run is settled (finished, errored, or already stopped), MUST be protected against double activation, and MUST resolve consistently when it races a run that is finishing on its own — the operator never sees two contradictory outcomes or a stuck in-progress stage.

**Terminal states & handoff**

- **FR-010**: On successful completion, the screen MUST show a plain-language completion summary including the mission's quality verdict, and MUST provide a clear forward action to the finished deliverable — routing to the Deliverable Library (S4) once it ships, and, until then, to the existing local mission-detail/dossier view (including its PDF export) so the operator always reaches a real, usable deliverable rather than a placeholder.
- **FR-011**: On error, the screen MUST show a plain-language explanation that the production did not complete plus a sensible next step (retry / return to brief), and MUST NOT surface a raw stack trace, phase code, or engine error as the primary message; any technical detail is wrapped, never shown verbatim as the main text.
- **FR-012**: When an errored run left recoverable work behind, the screen MUST honestly offer to resume it from where it stopped using the existing resume path, instead of only allowing a restart; when no recoverable work exists, only restart/return options are offered.
- **FR-013**: Every terminal state (finished, stopped, error) MUST keep the launched production identifiable and MUST present at least one clear way forward — the screen is never a dead end or an endless spinner.

**Reachability & session**

- **FR-014**: The Mission Timeline MUST be a first-class navigable destination in the shell (replacing the current `missions` coming-soon placeholder), reachable per the umbrella's navigation guarantees, and MUST render the live run when one is active in the session or a plain-language empty state — pointing to the Guided Brief — when none is.
- **FR-015**: Following a production MUST survive in-app navigation between screens within the same session (returning to the timeline shows the same run at its current progress); the launch handoff from S2 MUST land the operator on this screen following the just-launched run. The timeline follows a single active production at a time (v1); a settled run remains consultable until a new production is launched.

**Honesty about following**

- **FR-016**: A connection loss to the local service while following a run MUST be surfaced as a calm, plain-language state consistent with the shell's connection indicator — preserving what was already shown, never a raw error or a frozen spinner.
- **FR-017**: The screen MUST truthfully represent the limits of live following (dependence on the app session) rather than implying durability it does not have. Specifically, after a full app reload/close the timeline MUST NOT claim the live stream survived; instead, when the interrupted run left a checkpoint, it MUST offer to resume the production from that checkpoint via the existing resumable path, and MUST fall back to the honest terminal/empty state only when no checkpoint exists — never fabricating progress and never forcing a start-from-scratch when resumption is possible.

**Security & secrets**

- **FR-018**: No surface of the Mission Timeline may accept, display, or persist API keys or other secrets (umbrella FR-015; Constitution Principle VI); where a run's activity might reference a provider, the timeline describes it in plain language without exposing credentials or key-environment details.

**Foundation compliance**

- **FR-019**: The screen MUST be built on the umbrella foundations — shell navigation, i18n mechanism, design-system components and shared loading/empty/error/connection states, and WCAG 2.1 AA accessibility (full keyboard operability, screen-reader labels including live-region announcement of stage changes, AA contrast, visible focus) — re-inventing none of them.
- **FR-020**: All timeline text — stage labels, statuses, confirmations, terminal summaries, error and empty states — MUST come from the umbrella EN/FR locale catalogs (no hardcoded strings, complete and keyed identically in both languages, English as fallback source of truth).
- **FR-021**: All Mission Timeline behavior — event-to-stage mapping, live updates, fix-loop presentation, cancel/confirm, terminal-state resolution, resume offer, empty and connection-lost states — MUST be covered by automated tests that run fully offline (no network, no CLI agents, no live services), driven by a simulated event source and a simulated cancel/launch boundary.

### Key Entities

- **Mission Run (followed)**: The single production currently or most-recently followed in the session — its identity for the operator, its live status (launching, running, stopped, finished, errored), its ordered event history, and its quality verdict on completion. Exactly one production is followed at a time in v1. Owned by the launch session handed over from S2; S3 observes it, and can request its cancellation, but does not own the mission itself.
- **Timeline Stage**: One human-language step in the presented story of the run (preparation / gathering facts, departments at work, drawing together, quality inspection, optional activities). Carries a localized label, a state (upcoming, in progress, done, skipped), and — for quality inspection — its round/iteration in human terms. Stages are the default curated view; each may expose optional plain-language per-activity detail on drill-down. Derived by folding the raw event stream; never a verbatim event.
- **Event Stream**: The existing, unchanged sequence of mission events the run emits (the contract S3 consumes read-only). Its order is the contract; S3 maps it, and MUST NOT change it.
- **Terminal Outcome**: The settled end of a run — finished (with verdict and a forward path to the deliverable), stopped (cancelled, nothing saved), or error (with a plain-language explanation and, when applicable, a resume option). Exactly one outcome per run.
- **Forward Action**: The clear next step offered from any timeline state — go to the finished deliverable (library/placeholder), start another production (Guided Brief), retry, or resume — ensuring the screen is never a dead end.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A non-technical test user, watching a launched production on the Mission Timeline, can correctly describe in their own words what the agency is doing at three sampled moments of the run (e.g. "it's gathering facts", "the work is being checked and improved") without using or needing any internal term — 3 out of 3.
- **SC-002**: 100% of a representative event stream (route, multiple departments, at least one fix loop, optional preparatory steps present and absent, completion) is reflected in the rendered timeline in correct order, with zero raw phase codes, engine names, department keys, or flags appearing in either language — verified by automated inspection.
- **SC-003**: From a running production, an operator can stop it in at most two interactions (act + confirm), and in 100% of test runs the timeline settles into the "stopped" state with the cancel path exercised and no lingering in-progress stage.
- **SC-004**: 100% of terminal outcomes (finished, stopped, error) resolve to a plain-language state with at least one clear forward action and zero dead-ends or infinite spinners — verified across the simulated success, cancel, and error streams.
- **SC-005**: The full timeline is operable with the keyboard alone and passes the umbrella's WCAG 2.1 AA checks on every state, including screen-reader announcement of stage changes; 100% of timeline strings resolve from the EN and FR catalogs with zero missing keys or raw-key leaks.
- **SC-006**: Following a run survives in-app navigation in 100% of test cases (leave the timeline, return, same run at current progress), and a mid-run connection loss produces a calm connection-lost state — never a crash or a raw error — in 100% of simulated drops.
- **SC-007**: The offline test suite — existing plus new Mission Timeline coverage — passes with no network, no CLI agents, and no live services, and all pre-existing studio functionality (including the developer console's raw timeline) remains behaviorally unchanged (additive delivery, zero regressions).
- **SC-008**: With S3 shipped, an operator can perform the middle of the brick's exit journey — launch a brief (S2) and follow the mission to a clear outcome — end-to-end through the application, unassisted, connecting S2's launch to S4's deliverable.

## Assumptions

- **Presentation-only over the existing stream**: S3 consumes the mission's existing event contract (the stream already emitted by the local mission service and already folded into a structured, technology-neutral progress model) and re-presents it for a non-technical audience; it adds no new event kinds, no new mission semantics, and no outbound network behavior (umbrella FR-016; Constitution Principles III, V, X). The developer console's raw timeline stays as-is at its secondary location.
- **Curated human stages with optional drill-down (clarified 2026-07-06)**: the operator sees a small, legible set of plain-language stages by default (preparation → departments → synthesis → inspection, with optional activities shown when they occur), and can expand any stage for plain-language per-activity detail — but never the full raw per-event engineering log (the developer console remains the raw view). This matches the umbrella's one-line description of S3 while giving curious users depth.
- **Live following is app-session-bound, with checkpoint-resume on reload (clarified 2026-07-06)**: following a run relies on the launch session established at S2 handoff (a single live stream held in the running application). In-app navigation preserves it; a full app reload/close does NOT live-re-attach to a still-running mission (that would require new server-side run-registry/reconnect semantics S3 does not add — FR-016). Instead, on return the screen offers to resume the production from its last checkpoint via the mission service's existing resumable path when a checkpoint exists (FR-017, US5), and falls back to the honest terminal/empty state otherwise. A durable live-reconnect capability can be added later without restructuring this screen.
- **Single active run in v1 (clarified 2026-07-06)**: the timeline follows one production at a time, matching the current single launch-session design; the Mission Run entity stays singular. Following several concurrent runs (with a run switcher) is a later additive enhancement — the backend run registry already permits it — and does not require restructuring S3.
- **Terminal success handoff targets the existing mission-detail view until S4 (clarified 2026-07-06)**: on success, the forward path targets the Deliverable Library (S4) once it ships; until then it routes to the existing local mission-detail/dossier view (including its PDF export) so the operator reaches a real, usable deliverable at completion from day one, swapped for the S4 library when it lands without restructuring S3.
- **Resume reuses the existing mechanism**: the resume-on-error offer surfaces the mission service's existing resumable-checkpoint capability (the recoverability signal already carried on an error outcome); S3 presents and triggers it but does not implement new resumption logic.
- **Cancel reuses the existing path**: stopping a run uses the existing explicit cancel endpoint / session cancel already in place; S3 wraps it in a plain-language confirmation and consistent terminal state, adding no new cancellation semantics.
- **Sourcing/inspection honesty is upstream**: the "no invented information" guarantee and the inspector's veto (Constitution III) are enforced by the mission loop and Brick 3; S3 only reports the inspection's progress and verdict in human terms — it neither performs nor weakens verification.
- **Desktop-first, EN/FR only**: as set by the umbrella — desktop/laptop browser and two interface locales; the timeline's live region and stage rendering target that context.
