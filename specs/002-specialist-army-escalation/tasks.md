# Tasks: The Specialist Army Plays (Budget-Controlled Escalation)

**Input**: Design documents from `/specs/002-specialist-army-escalation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Per Constitution Principle VII, every code change ships offline tests (no
network, no CLI, no Node, no GPU — `cli_engine._call` monkeypatched / injected). Test
tasks are written FIRST within each story and must fail before implementation.

**Organization**: Tasks grouped by user story (spec.md priorities: US1 P1, US2 P1, US3 P2).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 — traceability to spec.md

## Path Conventions

Vendored-library + studio layout (per plan.md): `agencykit/agency_cli/` (library code),
`agencykit/tests/` (library suite, run from `agencykit/`), `agency_studio/` (studio
server), `tests/` (studio suite, run from repo root).

---

## Phase 1: Setup

**Purpose**: Skeletons so every later task has a home; no behavior yet.

- [X] T001 Create `agencykit/agency_cli/escalation.py` module skeleton: module docstring
      (chain, budget, additive contract), frozen `EscalationConfig` dataclass
      (`enabled: bool = True`, `budget: int = 6`), `__all__`
- [X] T002 [P] Create `agencykit/tests/test_escalation.py` skeleton: scripted-call
      recorder fixture (a fake `call(cmd, prompt, ...)` that records `(cmd, prompt)` and
      pops queued outputs), payload-path fixture pointing at
      `agencykit/agency_cli/payload/agents/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The Principle X safety net, the roster, and the loop wiring every story needs.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Byte-identical-off regression test in `agencykit/tests/test_engine.py`:
      monkeypatch `_call`, run `run_mission_cli` on a fixed goal, capture the full
      `(cmd, prompt)` sequence as the golden baseline; assert the same capture with
      `escalation=None` (after T008) is identical — the SC-003 gate
- [X] T004 Frontmatter `AgentRef` parser in `agencykit/agency_cli/escalation.py`
      (stdlib text parsing: `name:`, first sentence of `description:` truncated ≤ 200
      chars) + unit tests in `agencykit/tests/test_escalation.py` (well-formed, malformed
      ⇒ skipped, multi-line `>-` descriptions)
- [X] T005 [P] Curated `DEPT_OFFICERS` map in `agencykit/agency_cli/escalation.py`
      (marketing 6, product 5, solve 5, finance 6 — per research.md D2; commander name
      exceptions: product ⇒ `commander-product`, solve ⇒ `commander-problem-solving`)
- [X] T006 [P] Drift-guard test in `agencykit/tests/test_escalation.py`: every
      `DEPT_OFFICERS` entry and every `commander-{dept}` resolves to an existing payload
      file (same spirit as `test_payload_agent_matches_source`)
- [X] T007 `build_roster()` in `agencykit/agency_cli/escalation.py`: commanders, officers
      (from `DEPT_OFFICERS`), virtual officers (parse the commander doctrine's numbered
      phase list for officer-less depts — comms O1–O6 per research.md D3), compact soldier
      pool (126 files) + tests in `agencykit/tests/test_escalation.py` (marketing has file
      officers, comms yields virtual phases, unreadable file skipped)
- [X] T008 Wire the `escalation: Optional[EscalationConfig] = None` parameter into
      `run_mission_cli` in `agencykit/agency_cli/engines/cli_engine.py`: dept-loop branch
      (`escalation.run_department(...)` when active for a dept, existing single `_call`
      otherwise), `None` / `enabled=False` / `budget <= 0` ⇒ exact current path; T003
      golden test must stay green

**Checkpoint**: Foundation ready — roster builds, off-path proven byte-identical.

---

## Phase 3: User Story 1 — A marketing mission runs a named specialist, traced (P1) 🎯 MVP

**Goal**: A mission whose department escalates commander → officer → soldier, every
invocation traced by name in the dossier (SC-001).

**Independent Test**: Offline `run_mission_cli` with scripted `_call` outputs (selection
JSON, then specialist outputs) returns a dossier whose `escalation.marketing` trace lists
≥1 named officer and ≥1 named soldier with task + output; the marketing dept output
contains the labeled specialist sections.

### Tests for User Story 1 (write first — must fail) ⚠️

- [X] T009 [P] [US1] Happy-path integration test in `agencykit/tests/test_escalation.py`:
      scripted selection (`officer-2-strategy` + `soldier-stp`) then specialist outputs;
      assert trace roles/names/order, `task` + `output` per invocation, dossier
      `escalation` key present only for the escalated dept
- [X] T010 [P] [US1] Assembly test in `agencykit/tests/test_escalation.py`: department
      output = commander brief + labeled officer/soldier sections in execution order
      (deterministic, no extra assembly call — count the `_call` invocations)
- [X] T011 [P] [US1] Explicit no-escalation test in `agencykit/tests/test_escalation.py`:
      router selects nothing ⇒ dept runs doctrine-only and the trace records
      `finalized_by: "doctrine-fallback"` with `fallback_reason:
      "router-selected-none"`, keeping the selection invocation (US1 scenario 3 —
      never silent)

### Implementation for User Story 1

- [X] T012 [US1] Selection call in `agencykit/agency_cli/escalation.py`: prompt builder
      (commander doctrine + compact roster + goal + prior-outputs summary + budget),
      tolerant JSON extraction (the `_route_via_cli` pattern), roster-name validation
      (unknown names dropped); runs on the base `cmd` (never MCP-spliced)
- [X] T013 [US1] Specialist prompt builders in `agencykit/agency_cli/escalation.py`:
      commander / officer / soldier prompts embedding each doctrine (frontmatter stripped),
      the WebSearch/no-invention clause, and `asset_clause` / `context_clause` /
      `persona_doctrine[dept]` exactly as `_dept_prompt` threads them
- [X] T014 [US1] `run_department()` chain execution in
      `agencykit/agency_cli/escalation.py`: selection → commander → officers → soldiers
      via the injected `call`, `InvocationRecord` accumulation, deterministic assembly,
      cancel-checked between calls (`MissionCancelled` propagates); returns
      `(dept_output, DeptEscalationTrace)`
- [X] T015 [US1] Dossier wiring in `agencykit/agency_cli/engines/cli_engine.py`: collect
      per-dept traces, attach `dossier["escalation"]` ONLY when ≥1 dept escalated
      (absent ⇒ byte-identical dossier)

**Checkpoint**: MVP — the army demonstrably plays, offline, traced.

---

## Phase 4: User Story 2 — Per-department cost stays bounded and is reported (P1)

**Goal**: Hard invocation cap enforced with graceful degradation; budget/consumed/
est_tokens reported per department; off/zero identical to today; product default-on with
explicit opt-out everywhere (CLI + studio).

**Independent Test**: Offline mission with `budget=3` and a selection of 4+ specialists:
escalation halts at the cap with explicit skips, dept output stays coherent, trace reports
`consumed <= budget` and `est_tokens`; `budget=0` reproduces the T003 golden capture.

### Tests for User Story 2 (write first — must fail) ⚠️

- [X] T016 [P] [US2] Budget-exhaustion test in `agencykit/tests/test_escalation.py`:
      budget=3, selection of 2 officers + 2 soldiers ⇒ later specialists recorded as
      `{"skipped": "budget-exhausted"}`, `consumed <= budget`, dept output coherent
      (SC-002, US2 scenario 1)
- [X] T017 [P] [US2] Off-equivalence test in `agencykit/tests/test_escalation.py`:
      `EscalationConfig(enabled=False)` and `budget=0` both reproduce the T003 golden
      `(cmd, prompt)` capture and a dossier with NO `escalation` key (FR-006)
- [X] T018 [P] [US2] Token-accounting test in `agencykit/tests/test_escalation.py`:
      every invocation carries `est_tokens` (chars/4 over prompt+output), dept
      `est_tokens == sum(invocations)`, `consumed == len(non-skipped invocations)`
- [X] T019 [P] [US2] runner_bridge resolution tests in `agencykit/tests/test_cli.py`:
      default ⇒ `EscalationConfig()` passed down; `escalation=False` / dict opt-out ⇒
      `None` passed down; junk types ⇒ `ValueError`

### Implementation for User Story 2

- [X] T020 [US2] Budget enforcement in `agencykit/agency_cli/escalation.py`: decrement
      before each call, skip-remaining with explicit reasons at exhaustion, mid-phase
      exhaustion closes out cleanly (the skipped reasons ARE the partial-escalation
      record); tiny-budget hybrid case sets `finalized_by: "doctrine-fallback"` when
      nothing assemblable ran (assert in the T016 test)
- [X] T021 [US2] `est_tokens` accounting in `agencykit/agency_cli/escalation.py`:
      per-invocation chars/4 heuristic + per-dept totals in the trace
- [X] T022 [US2] Product default-on resolution in `agencykit/agency_cli/runner_bridge.py`:
      `escalation=None` ⇒ `EscalationConfig()`; `False`/disabled/0 ⇒ pass `None`;
      dict coercion with type checks (`ValueError` on junk); thread through `resume()` too
- [X] T023 [US2] CLI flags in `agencykit/agency_cli/cli.py`: `--no-escalation` /
      `--escalation-budget N` on `run`, `batch run`, `resume` (`0 ≡ --no-escalation`) +
      dispatch tests in `agencykit/tests/test_cli.py`
- [X] T024 [US2] Studio passthrough in `agency_studio/server.py`: optional
      `escalation: {enabled, budget}` mission-request field, strict type validation
      (400 on junk), forwarded only if `runner_bridge.run` accepts it (existing
      `inspect.signature` pattern at the run call site)
- [X] T025 [US2] Studio passthrough tests in `tests/test_server.py`: field validated,
      forwarded when supported, silently dropped for an older agencykit signature,
      no new endpoint/bind/CORS surface

**Checkpoint**: Bounded, measured, reported; opt-out proven identical to today.

---

## Phase 5: User Story 3 — The router selects the right specialists (P2)

**Goal**: Goal-appropriate selection with rationale; graceful fallback and gap handling;
comms/event (virtual officers) and B2B 360 operational (SC-004, SC-005, SC-006).

**Independent Test**: Two offline missions with different goals through marketing produce
different scripted selections, each with a recorded rationale; a comms mission fields
virtual phase-officers; a B2B-360 mission (marketing + product + comms) carries one trace
per department.

### Tests for User Story 3 (write first — must fail) ⚠️

- [X] T026 [P] [US3] Selection-differs test in `agencykit/tests/test_escalation.py`: two
      goals ⇒ different selections, each selected name carrying a rationale (SC-005,
      FR-012; missing rationale ⇒ `"(no rationale returned)"` recorded)
- [X] T027 [P] [US3] Fallback test in `agencykit/tests/test_escalation.py`: unparseable /
      empty selection output ⇒ doctrine-only execution with `selection` recorded as the
      `{"fallback": "selection-unparseable"}` marker, `finalized_by:
      "doctrine-fallback"`, `fallback_reason: "selection-unparseable"` (edge case)
- [X] T028 [P] [US3] Missing-specialist test in `agencykit/tests/test_escalation.py`:
      selected soldier's file absent ⇒ `{"skipped": "missing-file"}`, mission completes,
      no fabricated substitute (FR-007, SC-006)
- [X] T029 [P] [US3] Comms virtual-officer test in `agencykit/tests/test_escalation.py`:
      comms selection yields phase-officers (`comms/O6-events`-style names) invoked with
      the commander doctrine + phase directive, traced `virtual: true` (SC-004)
- [X] T030 [P] [US3] B2B-360 integration test in `agencykit/tests/test_escalation.py`:
      route `["marketing", "product", "comms"]`, one `DeptEscalationTrace` per dept,
      budgets independent per dept

### Implementation for User Story 3

- [X] T031 [US3] Rationale capture in `agencykit/agency_cli/escalation.py`: per-name
      rationale from the selection JSON, default string when absent
- [X] T032 [US3] Fallback path in `agencykit/agency_cli/escalation.py`: unparseable/empty
      selection ⇒ condensed-doctrine call + explicit trace record (no crash, no retry-spend)
- [X] T033 [US3] Graceful specialist-failure handling in
      `agencykit/agency_cli/escalation.py`: missing file ⇒ skip+record; `_call` failure on
      a specialist ⇒ `{"skipped": "call-failed"}` + continue (only `MissionCancelled`
      propagates)
- [X] T034 [US3] Virtual-officer invocation in `agencykit/agency_cli/escalation.py`:
      phase-scoping directive prompt over the commander doctrine for officer-less depts,
      `virtual: true` in the record

**Checkpoint**: All three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T035 [P] Escalation `_emit` events in `agencykit/agency_cli/escalation.py`
      (`{"phase": "escalation", "dept", "step", "name", "status"}`) + event-sequence
      assertions added to the T009 happy-path test
- [X] T036 Checkpoint/resume additions in `agencykit/agency_cli/engines/cli_engine.py`:
      optional `escalation` key on `"dept"` snapshots (completed depts only),
      `_validate_resume_state` defaults it to `{}`; resume tests in
      `agencykit/tests/test_engine.py` (old snapshot resumes; crash mid-escalation
      re-runs the dept from scratch)
- [X] T037 [P] Veto-loop-invariance test in `agencykit/tests/test_engine.py`: escalation
      on, inspector VETO → PASS sequence ⇒ iteration behavior and inspector prompt
      identical to the off case (SC-008, FR-009)
- [X] T038 [P] Cancel-mid-escalation test in `agencykit/tests/test_escalation.py`:
      `should_cancel` flips true between specialist calls ⇒ `MissionCancelled`, no dossier
      (edge case, Art. IX)
- [X] T039 [P] Update `agencykit/CLAUDE.md` (mission-loop diagram + escalation section,
      key-files table row for `escalation.py`) and `docs/` if the studio surface is
      documented there
- [X] T040 Full offline gate: `cd agencykit && pytest tests/ -q` and `pytest tests/ -q`
      (repo root) both green (SC-007)
- [ ] T041 Live validation on `claude-code` (per research.md D10): one marketing mission
      (SC-001), one comms/event mission (SC-004), one B2B-360 mission — dossier traces
      captured and recorded in the PR description
- [X] T042 Walk `specs/002-specialist-army-escalation/quickstart.md` end-to-end and fix
      any drift between it and the shipped CLI/studio surfaces

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none — start immediately
- **Foundational (Phase 2)**: after Setup — BLOCKS all user stories; T003 before T008
  (the golden capture must predate the wiring); T004 → T007; T005 → T006/T007
- **US1 (Phase 3)**: after Foundational — no dependency on other stories
- **US2 (Phase 4)**: after Foundational — enforcement lands inside `run_department`
  (T014), so T020/T021 depend on T014; the surfaces (T022–T025) only need T008
- **US3 (Phase 5)**: after Foundational — refines T012/T014 paths; T029/T034 also need
  T007's virtual-officer roster
- **Polish (Phase 6)**: after all desired stories; T040 before T041; T041 → T042

### User Story Dependencies

- **US1 (P1)**: independent — the MVP
- **US2 (P1)**: independently testable (budget knobs exercised through the same
  `run_department` entry); integrates with US1's chain
- **US3 (P2)**: independently testable (selection/fallback paths); builds on US1's
  selection call

### Within Each User Story

- Tests first (fail-first per Constitution VII), then implementation
- `escalation.py` internals before `cli_engine.py` wiring
- Library surfaces before studio surfaces

### Parallel Opportunities

- T002 ∥ T001; T005/T006 ∥ T004
- All test-first tasks within a story are [P] (same file but disjoint test functions —
  parallelize by writing, serialize the commit)
- After Phase 2: US1, US2-surfaces (T022–T025), and US3 tests can proceed in parallel
  streams; T035/T037/T038/T039 are mutually parallel in Polish

---

## Parallel Example: User Story 1

```bash
# Write the three failing tests together:
Task: "T009 happy-path trace test in agencykit/tests/test_escalation.py"
Task: "T010 assembly determinism test in agencykit/tests/test_escalation.py"
Task: "T011 explicit no-escalation test in agencykit/tests/test_escalation.py"

# Then implement bottom-up:
Task: "T012 selection call" → "T013 prompt builders" → "T014 run_department" → "T015 dossier wiring"
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Phase 1 + Phase 2 (T001–T008) — the byte-identical safety net is non-negotiable
2. Phase 3 (T009–T015) — the army plays, traced
3. **STOP & VALIDATE**: offline suite green; optional early live marketing run
4. Then US2 (the P1 co-requisite for merging the brick), then US3, then Polish

### Incremental Delivery

- Foundation → US1 (MVP demo) → US2 (bounded + surfaces) → US3 (selection quality +
  comms/B2B demos) → Polish (events, resume, invariance proofs, docs, live validation)
- The brick's done-condition (PLAN.md) needs US1 + US2 + T040/T041 at minimum; US3
  completes SC-004/SC-005

---

## Notes

- Every escalation call goes through the injected `call` (= `cli_engine._call`) — never a
  new subprocess path, never an API (Constitution I/V)
- The T003 golden capture is the Principle X proof — never weaken it to "similar"
- Commit after each task or logical group (Conventional Commits)
- 42 tasks: Setup 2 · Foundational 6 · US1 7 · US2 10 · US3 9 · Polish 8
