# Phase 0 Research: The Specialist Army Plays

All Technical Context unknowns resolved. Each decision below was grounded by reading the
actual code and payload (2026-07-03): `cli_engine.py` (869 lines, mission loop at
648-869, dept execution at 780-797), payload inventory (10 commanders, 22 officer files,
126 soldier files, 13 `_shared-*` doctrines), studio call sites (`agency_studio/server.py`
1062/1287-1361), and the agencykit test architecture (`tests/test_engine.py` monkeypatches
`cli_engine._call`).

## D1 — Where escalation hooks into the mission loop

**Decision**: Branch inside the department execution loop (`cli_engine.py:780-797`). When
escalation is active for a department, replace the single `_call(exec_cmd, _dept_prompt(...))`
with `escalation.run_department(...)`, which returns `(dept_output, dept_trace)`. Routing,
synthesis, inspection, checkpoint, and cancel logic stay untouched.

**Rationale**: The dept loop is the only place "a department executes"; hooking there keeps
the veto loop (Art. IX) and resume invariants provably unchanged. Matches the clarified
chain: the *department* escalates internally; the mission-level phases are stable.

**Alternatives considered**: (a) Escalate inside `_dept_prompt` (prompt-only, no extra
calls) — rejected: specialists would not actually *run*, failing SC-001. (b) A wrapper
around `run_mission_cli` — rejected: cannot interleave per-department budget/cancel/
checkpoint correctly without duplicating the loop.

## D2 — Specialist roster: how officers/soldiers map to departments

**Decision**: Build the roster at mission time from payload frontmatter (stdlib text
parsing — the `_load` helper already strips YAML frontmatter, so parsing `name:` /
`description:` lines needs no YAML dependency), combined with a small curated
`DEPT_OFFICERS` mapping in `escalation.py` for the four armies that ship officer files
(marketing, product, solve, finance) — because description army-tags are inconsistent
(e.g. solve/finance officers carry no "of the X army" phrase). Soldiers form a shared pool
(126 files); they are presented to the selection call as a compact roster (name + first
sentence of description, truncated).

**Rationale**: Frontmatter is the payload's own metadata; a curated officer map is 4 short
tuples following the `departments.py` single-source-of-truth precedent, and it is
drift-guarded by a test that asserts every mapped file exists (same pattern as
`test_payload_agent_matches_source`).

**Alternatives considered**: (a) Pure description parsing — rejected: 11 of 22 officer
files carry no parsable army tag. (b) A committed generated index JSON — rejected: extra
artifact to keep in sync; the curated map + drift test is smaller. (c) Sending all 126
full soldier doctrines to the selector — rejected: prompt blow-up; compact roster suffices.

## D3 — Virtual officers for commander-only departments

**Decision**: comms, data, ops, people, tech ship no `officer-*.md` files; their phases
(e.g. comms O1 Corporate Comms … O6 Events) are declared inside the commander doctrine.
For these departments an "officer invocation" is the commander doctrine + a phase-scoping
directive ("Act strictly as phase O6 — Events …"), traced with a `virtual: true` marker
and the phase name (e.g. `comms/O6-events`).

**Rationale**: Satisfies SC-004 (comms fields ≥1 officer) without authoring new payload
files (forbidden by the spec's "payload is the source of the army" assumption — the
payload is a vendored snapshot that `agency sync` would overwrite).

**Alternatives considered**: (a) Author comms officer files — rejected (above). (b) Let
comms escalate commander+soldiers only — rejected: fails SC-004's "at least one officer".

## D4 — Selection mechanism ("the department's router")

**Decision**: One extra `_call` per escalated department — the **selection call** — on the
base command (`cmd`, like the agency router; never MCP-spliced). Prompt = the department
commander doctrine + the compact roster + the mission goal + prior dept outputs summary +
budget; required output = a JSON object `{officers: [...], soldiers: [...],
rationale: {...}}`. Parsing reuses the tolerant-extraction pattern of `_route_via_cli`
(find the JSON block, validate names against the roster, drop unknown names). Unparseable
or empty selection ⇒ fall back to condensed-doctrine-only for that department and record
`{"fallback": "selection-unparseable"}` in the trace (FR edge case).

**Rationale**: "The department's router selects" (clarified) with zero new dependencies;
mirrors the proven `_route_via_cli` contract; the selection consumes 1 unit of the same
budget it allocates, so the bound covers it.

**Alternatives considered**: (a) Keyword-based offline selection (like
`keyword_classify`) — kept only as the *validation* layer (names must exist in roster),
not the selector: methods like JTBD-vs-STP need semantic reading of the goal. (b) Let the
commander call decide inline — rejected: conflates orchestration output with selection
JSON; harder to parse and test.

## D5 — Budget semantics and default

**Decision**: `EscalationConfig(budget=6, enabled=True)`. Budget = hard cap on
**escalation subprocess calls per department**, counting: the selection call (1), the
commander call (1), each officer call, each soldier call. Decremented before each call;
when 0 remain, remaining selected specialists are skipped and recorded as
`{"skipped": "budget-exhausted"}`. The department is then finalized by the commander-call
output already in hand (or, if even the commander never ran, by the condensed-doctrine
call — which is *outside* the escalation budget, preserving "the department still returns
a coherent result"). Advisory token estimate = `ceil(len(prompt + output) / 4)` summed per
department, reported as `est_tokens` (documented as a chars/4 heuristic, never enforced).

**Rationale**: Clarified decision (hard call-cap enforced, tokens advisory). Default 6
fits the clarified chain (1 selection + 1 commander + 2 officers + 2 soldiers) while
keeping worst-case added wall-time ≈ 6 × run_timeout per department.

**Alternatives considered**: enforcing on estimated tokens — rejected in clarification
(true tokens unobservable across a subscription CLI; estimates make SC-002 unverifiable).

## D6 — Where "default on" lives (Principle X reconciliation)

**Decision**: Three layers. (1) `run_mission_cli(escalation: Optional[EscalationConfig] =
None)` — `None` ⇒ escalation OFF, byte-identical to today (library stays additive,
regression-tested). (2) `runner_bridge.run` resolves the product default: unless the
caller passes an explicit opt-out (`escalation=False` / budget 0), it constructs
`EscalationConfig()` (ON) for departments that have a payload. (3) Surfaces: `agency run
--no-escalation / --escalation-budget N`; studio mission request gains an optional
`escalation: {enabled: bool, budget: int}` field (validated types, default on), passed via
the existing `inspect.signature(runner_bridge.run).parameters` introspection so an older
agencykit degrades gracefully.

**Rationale**: Honors both the clarified default-ON and Principle X's byte-identical-off:
the byte-identity guarantee attaches to the library switch, the product default to the
wrapper — exactly how a user actually opts out. Justified in plan.md Complexity Tracking.

**Alternatives considered**: default-ON inside `run_mission_cli` itself — rejected: breaks
the additive contract every prior hook established at that signature and would change
standalone-agencykit test expectations wholesale.

## D7 — Escalation flow inside one department

**Decision** (per escalated department, all via existing `_call`, cancel-checked between
calls, `_emit` events at each step):

```text
1. selection  (base cmd)      → {officers, soldiers, rationale} | fallback
2. commander  (exec_cmd)      → department brief: phase directives per selected officer
3. per officer (exec_cmd)     → phase deliverable (officer doctrine, or virtual-officer
                                 directive for commander-only depts; sees commander brief)
4. per soldier (exec_cmd)     → method deliverable (soldier doctrine; sees its officer's
                                 phase deliverable)
5. department output = commander-led assembly: the commander call's brief + officer/soldier
   deliverables concatenated in chain order under labeled headers (deterministic assembly,
   no extra "assembly" subprocess call — budget is spent on specialists, not glue)
```

Officer/soldier prompts embed each specialist's own doctrine file (frontmatter stripped by
`_load`'s pattern), the WebSearch/no-invention clause, plus `asset_clause` /
`context_clause` / `persona_doctrine[dept]` exactly as `_dept_prompt` does today — the
inspector/router never see any of it (Art. IX inputs unchanged).

**Rationale**: Matches the clarified commander → officer → soldier chain; deterministic
assembly keeps the budget for real specialist work and keeps output reproducible.

**Alternatives considered**: a final commander "assemble" call — rejected: +1 budget unit
for glue, and a second commander call risks re-summarizing (Art. IV sovereignty: outputs
pass forward unchanged).

## D8 — Dossier, events, and checkpoint additions (all additive)

**Decision**: Dossier gains `escalation: {dept: DeptEscalationTrace}` (schema in
data-model.md) — present only when escalation ran (absent ⇒ byte-identical dossier).
`_emit` events gain `{"phase": "escalation", "dept": ..., "step": "selection|commander|
officer|soldier", "name": ..., "status": ...}`. The `"dept"` checkpoint snapshot gains an
optional `escalation` key (traces of *completed* departments only); `_validate_resume_state`
treats a missing key as `{}` — old snapshots resume fine, and a crash mid-escalation
re-runs that department from scratch (dept not yet in `dept_outputs` ⇒ existing invariant
holds unchanged).

**Rationale**: The dossier is the audit surface (spec assumption); checkpoint versioning
stays at 1 because the addition is optional-with-default — the documented invariants in
`_checkpoint`'s docstring are preserved verbatim.

**Alternatives considered**: bumping checkpoint `version` to 2 — rejected: nothing breaks
for old snapshots; a version bump would force resume-path branching for no behavioral need.

## D9 — Test plan (offline, Principle VII)

**Decision**: `agencykit/tests/test_escalation.py` (new) + `test_engine.py` additions,
all monkeypatching `cli_engine._call` (existing fixture pattern):

- Byte-identical-off: with `escalation=None`, capture every `(cmd, prompt)` and assert
  equality with a pre-feature golden run (same monkeypatch, same inputs).
- Happy path: scripted `_call` returning selection JSON then specialist outputs; assert
  dossier trace names, order, budget accounting, `est_tokens` present.
- Budget exhaustion: budget=3 with 2 officers + 2 soldiers selected ⇒ skips recorded,
  consumed ≤ budget, department output still coherent.
- Budget zero / disabled: identical to off (FR-006).
- Selection unparseable ⇒ doctrine-only fallback recorded (edge case).
- Missing specialist file ⇒ skipped + gap recorded, mission completes (FR-007/SC-006).
- Virtual officers: comms selection yields phase-officers with `virtual: true` (SC-004).
- Veto loop unchanged: escalation on, inspector returns VETO then PASS — assert identical
  iteration behavior and inspector prompt as the off case (SC-008).
- Cancel mid-escalation ⇒ `MissionCancelled`, no dossier (edge case).
- Roster drift guard: every `DEPT_OFFICERS` entry resolves to an existing payload file.
- Studio: `tests/test_server.py` — `escalation` request field validated and passed through
  only when `runner_bridge.run` accepts it (signature-introspection degradation path).

**Rationale**: Exactly the suite SC-001…SC-008 demand, in the house style (no network, no
CLI, no Node, no GPU).

## D10 — Marketing / comms / B2B-360 demonstrations

**Decision**: The three demos (SC-001, SC-004) are validated twice: (a) offline, as
scripted-`_call` integration tests (the merge gate), and (b) live, as a manual validation
run on the validated `claude-code` engine recorded in the PR description (same discipline
as Brick 1's engine validation). B2B 360 = a goal routing marketing + product + comms in
one mission.

**Rationale**: Principle VII makes offline the only merge gate; the live run proves the
"real mission" wording of the brick's done-condition without becoming a flaky CI step.
