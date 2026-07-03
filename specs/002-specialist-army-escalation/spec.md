# Feature Specification: The Specialist Army Plays (Budget-Controlled Escalation)

**Feature Branch**: `002-specialist-army-escalation`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Brick 2 — the specialist army plays. Today the mission loop only loads each department's condensed doctrine (_shared-{dept}); the commanders, officers and soldiers snapshotted in the payload (177 agents, 110 skills) never participate. Wire a budget-controlled escalation inside a deployed department: condensed doctrine → the phase's officer → the method soldier (JTBD, STP, Pareto, PERT, etc.), where the department's router selects which officer(s) and soldier(s) to invoke. Keep per-department token cost bounded and measured, and trace every invoked officer and soldier in the mission dossier. Event work (comms-kit) and B2B 360 missions must become operational."

## Overview

Today a mission that deploys a department (product, marketing, solve, comms, …) reasons
only from that department's **condensed doctrine** (`_shared-{dept}`). The full specialist
army — the department's officers (one per phase) and the method soldiers (JTBD, STP,
Pareto, PERT, and the rest) snapshotted in the payload — is present on disk but never
participates in a mission. The result is generic: the mission never actually *runs* a
named method by a named specialist.

This feature makes the army play. Inside a deployed department, the mission escalates from
the condensed doctrine to the department's commander, from the commander to the phase's
officer, and from the officer to the specific method soldier the work calls for — with the
department's router choosing which specialists to invoke for this mission. Every escalation
is bounded by a per-department budget that is measured and reported, and every invoked
specialist is recorded in the mission dossier so the run is auditable. When this ships, a
real marketing mission — and event work (comms) and B2B 360 missions — stop being a single
doctrine prompt and become an actual chain of specialists doing named work.

## Clarifications

### Session 2026-07-03

- Q: When escalation ships, what does a normal mission do by default (no special flag)? →
  A: Escalation is ON by default for any deployed department that has an officer/soldier
  payload; "off" (byte-identical to today) is an explicit opt-out / budget-zero switch.
- Q: How is the per-department budget enforced and measured, given the brain is a
  subscription CLI subprocess (no billed tokens)? → A: Both axes — a hard cap on
  specialist-call count (the enforced bound) plus an estimated-token figure reported per
  department (advisory, for visibility).
- Q: Does the department commander participate in the escalation chain? → A: Yes — the
  chain is commander → officer → soldier: the department commander is invoked as the
  orchestrating layer above officers.
- Q: Which departments must be wired by this brick? → A: Generic — one department-agnostic
  escalation mechanism for any deployed department with a payload; marketing and comms
  (event) are the required end-to-end demonstrations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A marketing mission runs a named specialist, traced (Priority: P1)

An agency operator starts a marketing mission (e.g. "position and launch product X"). The
marketing department is deployed. Instead of answering from the condensed doctrine alone,
the department escalates: its commander takes the mission, the router picks the relevant
phase officer(s), each officer invokes the method soldier(s) its phase needs, and the work
is produced by those named specialists. When the mission finishes, the operator can see in the dossier exactly which
officer(s) and soldier(s) ran and what each contributed.

**Why this priority**: This is the definition of done for the whole brick — at least one
officer and one soldier actually invoked in a real marketing mission, both traced. Without
it, nothing else in the feature matters. It is the thinnest end-to-end slice that proves the
army plays.

**Independent Test**: Run one marketing mission end-to-end (offline, with the engine
boundary faked). Assert the returned dossier lists ≥1 named officer and ≥1 named soldier for
the marketing department, each with its contribution captured, and that the final
deliverable reflects that specialist work rather than only the condensed doctrine.

**Acceptance Scenarios**:

1. **Given** a marketing mission goal, **When** the mission runs to completion, **Then** the
   dossier records at least one invoked officer and at least one invoked soldier for the
   marketing department, each identified by name.
2. **Given** the same mission, **When** the operator inspects the trace, **Then** each
   recorded officer/soldier entry shows what it was asked to do and what it returned.
3. **Given** a department the router deems needs no escalation, **When** the mission runs,
   **Then** the department still completes from condensed doctrine and the dossier makes the
   "no escalation" decision explicit rather than silently omitting it.

---

### User Story 2 - Per-department cost stays bounded and is reported (Priority: P1)

An agency operator runs missions on a subscription and must not let one department balloon
into an unbounded chain of specialist calls. Each deployed department operates under a
budget; escalation stops when the budget is exhausted, and the mission reports how much each
department consumed against its budget.

**Why this priority**: Escalation without a bound is a runaway cost and latency risk that
would make the feature unusable in practice. Bounded-and-measured is a stated done-condition
and is co-critical with the trace, so it is also P1.

**Independent Test**: Run a mission with a deliberately small department budget and assert
that (a) escalation halts at or before the budget, (b) the department still returns a
coherent result via graceful degradation, and (c) the dossier reports consumed-vs-budget per
department.

**Acceptance Scenarios**:

1. **Given** a department budget, **When** escalation would exceed it, **Then** the
   department stops escalating and completes with what it has, without error.
2. **Given** any completed mission, **When** the operator reads the dossier, **Then** each
   deployed department shows its budget and how much of it was consumed.
3. **Given** a budget of zero (or escalation disabled), **When** the mission runs, **Then**
   the department behaves exactly as it does today — condensed doctrine only, no officer or
   soldier invoked — and the pre-existing behavior is unchanged.

---

### User Story 3 - The router selects the right specialists for the mission (Priority: P2)

Different missions need different specialists: a positioning mission needs STP and
positioning soldiers; an event mission (comms) needs its own officers and methods; a
diagnostic mission needs Pareto and root-cause soldiers. The department's router reads the
mission and selects which officer(s) and soldier(s) to invoke, so the army fielded matches
the work rather than running every specialist every time.

**Why this priority**: Selection is what keeps escalation both relevant and affordable, and
it is what makes comms/event and B2B 360 missions genuinely operational rather than
marketing-only. It builds on US1/US2 (which prove *that* the army can play and stay bounded)
so it is P2.

**Independent Test**: Run two missions with clearly different goals through the same
department and assert the router selects a different, goal-appropriate set of soldiers for
each, recorded in the dossier with a one-line rationale per selection.

**Acceptance Scenarios**:

1. **Given** two missions with different goals in the same department, **When** each runs,
   **Then** the router selects a goal-appropriate set of officers/soldiers for each, and the
   two sets differ where the goals differ.
2. **Given** a comms/event mission, **When** it runs, **Then** the comms department fields
   its own officers and soldiers and produces an operational event deliverable.
3. **Given** any selection, **When** it is recorded, **Then** each chosen officer/soldier
   carries a short rationale for why it was fielded.

---

### Edge Cases

- **Missing/renamed specialist**: The router selects a soldier whose payload file is absent
  or renamed. The department must degrade gracefully (skip it, note the gap in the dossier)
  rather than crash the mission.
- **Budget exhausted mid-phase**: The budget runs out after an officer starts but before its
  soldier returns. The department must close out cleanly and record a partial-escalation note
  rather than emit a truncated or fabricated result.
- **Router returns nothing / unparseable selection**: The department falls back to
  condensed-doctrine-only behavior and records the fallback.
- **Cancellation during escalation**: A mission cancelled mid-escalation must honor the
  existing kill-tree/abort contract and yield no dossier (consistent with the inspector/veto
  invariant that an aborted mission produces no verdict).
- **Inspector veto after specialist work**: A vetoed deliverable re-enters the existing veto
  loop unchanged — specialist escalation must not alter how the veto loop behaves.
- **No specialists needed**: A trivial goal for which the router justifiably fields no
  officer/soldier still completes and records the empty selection explicitly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Within a deployed department, the system MUST be able to escalate beyond the
  condensed doctrine through the full specialist chain — the department's commander as the
  orchestrating layer, the phase's officer(s) below it, and the relevant method soldier(s)
  below each officer — all drawn from the specialist payload.
- **FR-002**: The department's router MUST select which officer(s) and soldier(s) to invoke
  for a given mission, based on the mission goal, rather than invoking a fixed or exhaustive
  set every time.
- **FR-003**: Every invoked specialist — commander, officer, or soldier — MUST be recorded in
  the mission dossier, identified by name, with the task it was given and the output it
  returned.
- **FR-004**: Each deployed department MUST operate under a bounded budget enforced as a
  hard cap on the number of specialist invocations (commander, officers, soldiers);
  escalation MUST stop when the cap is reached, and the department MUST still return a
  coherent result via graceful degradation.
- **FR-005**: The system MUST measure and report, per deployed department in the dossier,
  the invocation budget allotted, the invocations consumed, and an advisory estimated-token
  figure for the department's escalation work.
- **FR-006**: Escalation MUST be on by default for any deployed department that has a
  specialist payload, with an explicit opt-out (escalation disabled or budget zero). When
  opted out, department behavior MUST be identical to the pre-feature behavior (condensed
  doctrine only, no specialist invoked) — existing behavior stays byte-identical with the
  option off.
- **FR-007**: The system MUST degrade gracefully when a selected specialist is missing,
  renamed, or fails — skipping it and noting the gap in the dossier — without aborting the
  mission.
- **FR-008**: The escalation mechanism MUST be department-agnostic — one mechanism serving
  any deployed department that has a specialist payload. Comms/event missions and B2B 360
  missions MUST be operational end-to-end as the required demonstrations: the relevant
  department fields its own specialists and produces a domain-appropriate deliverable.
- **FR-009**: The inspector veto loop MUST behave identically with escalation on or off; a
  vetoed deliverable re-enters the same loop and specialist work does not change veto
  semantics.
- **FR-010**: All escalation reasoning (officer and soldier work, router selection) MUST run
  through the CLI-agent subprocess boundary; no reasoning path may use a token-billed API and
  no in-process import of the video/production subtree may be introduced.
- **FR-011**: A mission MUST NOT touch the network except through the existing explicit
  per-mission opt-in; escalation MUST NOT introduce any new implicit network access.
- **FR-012**: Each router selection MUST carry a short rationale (why this officer/soldier
  was fielded) recorded alongside the selection in the dossier.
- **FR-013**: The full behavior MUST be exercisable by the offline test suite with no network,
  no installed CLI agent, no Node, and no GPU — every subprocess and network boundary faked.

### Key Entities

- **Department escalation**: The act, within one deployed department, of going from condensed
  doctrine → commander → officer(s) → soldier(s); has an invocation budget, a consumed count,
  an advisory token estimate, a selected specialist set, and a trace of what each specialist
  did.
- **Commander**: The department's top-level orchestrating specialist; when escalation runs,
  it receives the mission for its department and directs which phases (officers) engage.
- **Officer**: A phase-level specialist of a department (e.g. discovery, strategy, delivery);
  when invoked, receives a scoped task and delegates to method soldiers.
- **Soldier**: A method-level specialist (JTBD, STP, Pareto, PERT, …); when invoked, performs
  one named method and returns its result.
- **Router selection**: The router's decision of which officer(s)/soldier(s) to field for a
  mission, each with a rationale.
- **Department budget**: The hard cap on specialist invocations a single deployed department
  may consume via escalation; paired with the measured consumed count and an advisory
  estimated-token figure.
- **Escalation trace (in the dossier)**: The audit record — per department — of budget,
  consumed, selection with rationales, and each invoked specialist's task and output.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A real marketing mission run end-to-end invokes at least one named officer and
  at least one named soldier, both visible in the dossier trace. *(the brick's headline
  done-condition)*
- **SC-002**: For every deployed department in a completed mission, the dossier reports the
  invocation budget, the invocations consumed, and an advisory estimated-token figure — and
  consumed invocations never exceed the budget.
- **SC-003**: With escalation disabled (or budget zero), the mission's department behavior and
  final deliverable are unchanged from the pre-feature baseline — verifiable as identical
  output on the same input.
- **SC-004**: A comms/event mission and a B2B 360 mission each complete end-to-end with their
  department fielding at least one officer and one soldier and producing a domain-appropriate
  deliverable.
- **SC-005**: Two missions with materially different goals in the same department produce
  materially different specialist selections, each with a recorded rationale.
- **SC-006**: When a selected specialist is missing or fails, the mission still completes and
  the dossier records the gap — no crash, no fabricated substitute.
- **SC-007**: The offline test suite covering the above stays green with no network, no CLI
  agent, no Node, and no GPU.
- **SC-008**: The inspector veto loop produces the same verdicts on the same deliverables with
  escalation on as with it off — no behavioral drift in the trust anchor.

## Assumptions

- **Budget unit (clarified 2026-07-03)**: The enforced bound is a hard cap on specialist
  invocations per department; an estimated-token figure is reported alongside it as advisory
  visibility (true tokens are not observable across a subscription CLI subprocess). The
  default cap value and any user override are a planning/config detail.
- **Default-on, explicit opt-out (clarified 2026-07-03)**: Escalation is on by default for
  any deployed department with a specialist payload. Principle X is honored through the
  opt-out: with escalation disabled or budget zero, existing missions stay byte-identical to
  today's behavior.
- **Router reuse**: Selection reuses the existing agency routing doctrine/mechanism rather
  than introducing a separate router product; the new part is intra-department
  officer/soldier selection, not re-deciding which departments deploy.
- **Payload is the source of the army**: Officers and soldiers come from the existing
  specialist payload snapshot; this feature wires them in and does not author new specialists.
- **Dossier is the audit surface**: The existing mission dossier is where the escalation trace
  and budget report live; no separate reporting artifact is introduced.
- **Subprocess & network invariants inherited**: All engine reasoning stays behind the CLI
  subprocess boundary and the existing per-mission network opt-in; this feature adds no new
  boundary or network path.
- **Engine**: `claude` is the validated engine used to demonstrate the done-conditions;
  engine neutrality is preserved but end-to-end proof is on the validated engine.
