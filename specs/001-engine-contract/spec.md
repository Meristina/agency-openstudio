# Feature Specification: The Engine Contract (Multi-CLI Abstraction)

**Feature Branch**: `001-engine-contract`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Formalize the multi-CLI engine abstraction (Brick 1 of PLAN.md): an explicit Engine contract with research-grade execution, lightweight classification, declared capabilities (guaranteed headless web search as the constitutional precondition), timeout and kill-tree-on-cancel behavior, and a validated/unvalidated status. claude-code is the only validated v1 engine; unvalidated engines must refuse production missions. The mission loop consumes only the contract; adding an engine requires zero mission-loop changes. Claude-path behavior stays byte-identical; the veto loop never changes. Offline contract test suite with one fake engine binary per engine."

## Clarifications

### Session 2026-07-03

- Q: Can an engine ever hold "validated" status without declaring guaranteed
  headless web search? → A: No — coupled. Web search is a hard precondition of
  validation; a validated engine ALWAYS declares `web_search_headless`. FR-004 is a
  defense-in-depth runtime check that should never fire in production.
- Q: When an existing configuration (env var, saved setting) selects an unvalidated
  engine, what happens? → A: Hard refusal — the mission stops immediately with an
  actionable message; the system NEVER silently substitutes another engine.
- Q: Where does the offline contract test suite live? → A: In the `agencykit/`
  fork's own suite (run from its directory), next to the code being formalized;
  the studio's root `tests/` suite is untouched.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Missions keep running exactly as today on the validated engine (Priority: P1)

An agency operator launches a mission with the default (validated) engine. The mission
routes, executes departments, synthesizes, and passes inspection exactly as it did
before the contract existed: same prompts sent, same behavior on timeout and
cancellation, same deliverables. The operator cannot tell the refactor happened.

**Why this priority**: Constitution Art. X (additive over invasive) makes
byte-identical behavior on the validated path the non-negotiable baseline — if this
story fails, the feature is a regression regardless of what else works.

**Independent Test**: Run the full existing offline mission suite unmodified against
the refactored module; every test passes and the recorded subprocess invocations for
the validated engine are unchanged.

**Acceptance Scenarios**:

1. **Given** a mission configured for the validated engine, **When** it runs end to
   end, **Then** the sequence of engine invocations (commands, prompts, timeouts) is
   identical to the pre-contract behavior.
2. **Given** a running mission, **When** the operator cancels it while an engine call
   is in flight, **Then** the engine's entire process tree is terminated immediately,
   exactly as before.
3. **Given** the inspector issues a veto during a mission, **When** the veto loop
   reacts, **Then** its behavior is unchanged from the pre-contract implementation.

---

### User Story 2 - Unvalidated engines are refused before any production work starts (Priority: P2)

An operator (or a misconfigured environment) selects an engine that is registered but
has not passed end-to-end validation. The mission refuses to start production work and
tells the operator why, naming the engine's validation status and the validated
alternative(s).

**Why this priority**: Constitution Art. II makes this a constitutional guard — an
unvalidated engine running a production mission risks silently violating Art. III
(no invented information) if its headless web search is not actually guaranteed.

**Independent Test**: Select each registered-but-unvalidated engine for a production
mission; the mission is refused before any department work begins, with an
actionable message.

**Acceptance Scenarios**:

1. **Given** an engine registered as unvalidated, **When** a production mission is
   started with it, **Then** the mission refuses to run before any research or
   department work starts, and the refusal names the engine, its status, and the
   validated alternative.
2. **Given** an engine that does not declare guaranteed headless web search, **When**
   any research-grade work (department, synthesis, inspection) is requested from it,
   **Then** the request is refused — classification-only work does not require the
   web-search capability.
3. **Given** the validated engine, **When** a production mission is started,
   **Then** no refusal occurs and the mission proceeds normally.

---

### User Story 3 - An engine integrator adds a new engine without touching the mission loop (Priority: P3)

A contributor wants to add a new engine (e.g. opencode, planned for Brick 9). They
register one self-contained engine definition — its invocation recipe, declared
capabilities, and validation status — plus its contract tests. The mission loop, the
veto loop, and all existing engine definitions remain untouched.

**Why this priority**: This is the payoff of the contract — engine neutrality
(Constitution Art. II) is only real if extension requires zero changes to the
mission loop. It is P3 because it delivers future value, while P1/P2 protect
current behavior.

**Independent Test**: Add a fake "new engine" definition in a test; drive a mission
through the contract with it (validated flag set, in an offline harness) and verify
the mission loop code required no modification.

**Acceptance Scenarios**:

1. **Given** a new engine definition satisfying the contract, **When** it is
   registered, **Then** a mission can be driven by it with zero changes to the
   mission-loop module.
2. **Given** the new engine's definition, **When** its declared capabilities are
   inspected, **Then** they answer at minimum: guaranteed headless web search
   (yes/no), timeout behavior, and cancellation kill-tree behavior — plus the
   engine's validation status.

---

### Edge Cases

- **Missing binary**: the selected engine's executable is not installed → the
  operator gets a clear, actionable error naming the binary and how to install it,
  not a stack trace.
- **Timeout**: an engine call exceeds its time budget → the call fails with an
  explicit timeout error and no orphaned engine processes remain.
- **Cancellation mid-call**: a cancel arrives while an engine subprocess (and any
  children it spawned) is running → the whole process tree is terminated; nothing
  keeps running in the background.
- **Unknown engine name**: a mission references an engine that is not registered →
  refused immediately with the list of registered engines.
- **Stale configuration**: a pre-existing configuration selects a registered but
  unvalidated engine → hard refusal with an actionable message; the mission never
  falls back to another engine silently.
- **Classification vs research**: classification (routing) work is allowed on an
  engine without web search; research-grade work is not (see US2, scenario 2).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define an explicit Engine contract that every engine
  satisfies, covering: (a) research-grade execution used for department, synthesis,
  and inspection work — where headless web search is REQUIRED; (b) lightweight
  classification used for routing — where web search is NOT required; (c) declared
  capabilities, at minimum guaranteed headless web search (yes/no), the time budget
  applied to calls, and cancellation kill-tree behavior; and (d) a validation
  status: validated or unvalidated.
- **FR-002**: The engine registry MUST declare claude-code as the only validated v1
  engine; codex and gemini MUST remain registered and be marked unvalidated.
- **FR-003**: An unvalidated engine MUST refuse to run a production mission
  (Constitution Art. II). The refusal MUST occur before any department work starts
  and MUST name the engine, its status, and the validated alternative(s). The
  system MUST NOT silently substitute a different engine for the one configured —
  the refusal is a hard stop until the operator changes the configuration.
- **FR-004**: An engine that does not declare guaranteed headless web search MUST be
  refused for research-grade execution (Constitution Art. II precondition);
  classification-only use remains permitted. Validated status REQUIRES the
  web-search declaration (see Clarifications), so this check is defense-in-depth:
  in production it can only fire if the registry is inconsistent, and the suite
  MUST cover it anyway.
- **FR-005**: The mission loop MUST consume engines only through the contract.
  Adding a new engine MUST require exactly one new engine definition and its tests,
  with zero changes to the mission-loop module.
- **FR-006**: Behavior on the claude-code path MUST remain byte-identical
  (Constitution Art. X): same subprocess invocations, same prompts, same timeout
  values, same cancellation semantics, same outputs. The inspector veto loop MUST
  NOT change behavior.
- **FR-007**: Cancelling a mission while an engine call is in flight MUST terminate
  the engine's entire process tree (no orphaned children), preserving today's
  semantics.
- **FR-008**: A missing engine binary and an unknown engine name MUST each produce a
  clear, actionable error before any work starts.
- **FR-009**: An offline contract test suite MUST exercise every registered engine
  against the contract using one fake engine binary per engine — covering
  research-grade execution, classification, cancellation, kill-tree, and
  missing-binary paths — with no network, no real CLI, no Node, and no GPU
  (Constitution Art. VII). The suite lives in the `agencykit/` fork's own test
  suite (see Clarifications); the studio's root suite is not modified.

### Key Entities

- **Engine**: a CLI agent that can drive the agency; defined by an invocation
  recipe, declared capabilities, and a validation status.
- **Engine contract**: the promise every engine makes — research-grade execution,
  classification, capability declaration, timeout and cancellation semantics.
- **Capability declaration**: the engine's self-description; at minimum guaranteed
  headless web search, time budget, kill-tree-on-cancel.
- **Validation status**: validated (may run production missions) or unvalidated
  (registered, refused for production); changed only by an explicit human decision
  after end-to-end validation. An engine cannot be validated without declaring
  guaranteed headless web search.
- **Engine registry**: the single place engines are registered; the only place an
  integrator touches to add an engine (besides its tests).
- **Fake engine binary**: an offline stand-in executable used by the contract suite
  to exercise an engine definition without the real CLI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the existing offline test suite passes unmodified after the
  refactor, and the recorded engine invocations for the validated engine are
  identical to the pre-contract baseline. (Sole exception: a test that incidentally
  used an unvalidated engine to exercise an unrelated path is retargeted to the
  validated engine — the old permissive behavior it relied on is exactly what
  FR-003 removes; see plan.md Complexity Tracking.)
- **SC-002**: A production mission attempted on each unvalidated engine is refused
  in 100% of attempts, before any department work begins, with a message naming the
  engine, its status, and a validated alternative.
- **SC-003**: Adding a new engine definition (demonstrated with a fake engine in the
  suite) requires changes to exactly one registry location plus new tests — zero
  lines changed in the mission-loop module.
- **SC-004**: The contract test suite runs green on a machine with no network access,
  no engine CLI installed, no Node, and no GPU, in under 60 seconds.
- **SC-005**: After a mid-call cancellation, zero engine processes (parent or child)
  remain alive.
- **SC-006**: The inspector veto loop's observable behavior is unchanged across the
  refactor (its existing tests pass unmodified).

## Assumptions

- "Production mission" means any real mission run through the mission loop; the
  offline test harness (fake binaries, monkeypatched boundaries) is not a production
  mission, which is how unvalidated and future engines get exercised and validated.
- Promoting an engine from unvalidated to validated is an explicit human decision
  recorded in the registry (per the constitution's governance), made after
  end-to-end validation — planned for Brick 9 for codex/gemini/opencode; no runtime
  bypass flag is in scope for this feature.
- The current engine module (`agencykit/agency_cli/engines/cli_engine.py`, with its
  `ENGINES` and `_ROUTE_CMD` convention dicts and the `run_mission_cli` mission
  loop) is the surface being formalized; `agencykit/` is the studio fork vendored as
  a subtree, so this change lands in the fork under its rules of engagement.
- Existing timeout values (the current per-call defaults) are preserved as-is; the
  contract declares them, it does not change them.
- Engine identifiers keep their current names (claude-code, codex, gemini) so
  existing configurations keep working.
