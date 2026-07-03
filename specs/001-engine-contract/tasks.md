---

description: "Task list for the Engine contract (multi-CLI abstraction) — Brick 1"
---

# Tasks: The Engine Contract (Multi-CLI Abstraction)

**Input**: Design documents from `/specs/001-engine-contract/`

**Prerequisites**: plan.md, spec.md, research.md (D1–D8), data-model.md, contracts/engine-contract.md, quickstart.md

**Tests**: MANDATORY (Constitution Art. VII + FR-009). The new contract suite uses real fake binaries on a temp PATH; the existing monkeypatch suite must stay green.

**Organization**: Tasks grouped by user story. All code changes land in the `agencykit/` fork (plan.md Structure Decision); studio code and the root `tests/` suite are untouched.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 (byte-identical validated path), US2 (refusal guards), US3 (zero-change extension)

## Phase 1: Setup (Baseline)

**Purpose**: Record the green pre-change baseline that SC-001/SC-006 are measured against.

- [X] T001 Run both suites and record the baseline: `cd agencykit && pytest tests/ -q` and `pytest tests/ -q` at repo root; both must be green before any change. Capture the agencykit pass count in the PR description later.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The contract data structures every user story consumes. No behavior change yet — after this phase the module behaves identically (views carry the same values).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add the `EngineSpec` frozen dataclass to `agencykit/agency_cli/engines/cli_engine.py` with fields per data-model.md (name, run_cmd, route_cmd, web_search_headless, validated, run_timeout=900, route_timeout=60, kill_tree_on_cancel=True). Python 3.9-compatible annotations. Extend the module docstring's "Extension point" paragraph to name `EngineSpec`/`ENGINE_SPECS` instead of "add to ENGINES".
- [X] T003 Add `ENGINE_SPECS` registry (claude-code validated=True; codex, gemini validated=False; all web_search_headless=True; argv tuples byte-equal to the current `ENGINES`/`_ROUTE_CMD` literals), the `register_engine(spec)` helper, and rebuild `ENGINES` / `_ROUTE_CMD` as derived views (`{name: list(spec.run_cmd)}` / `{name: list(spec.route_cmd)}`) in `agencykit/agency_cli/engines/cli_engine.py` (research.md D1, D2).
- [X] T004 [P] Add `EngineNotValidated(RuntimeError)` with a docstring stating the Art. II rationale and the message contract (engine name, status, validated alternatives) in `agencykit/agency_cli/engines/cli_engine.py` (research.md D4).
- [X] T005 [P] Create the fake-binary test infrastructure in `agencykit/tests/test_engine_contract.py`: a fixture that writes an executable script (echo / sleep-then-echo / spawn-child-then-sleep variants) named after a given binary into `tmp_path` and prepends it to `PATH` via `monkeypatch.setenv` (research.md D7). Include a view-consistency test: `ENGINES`/`_ROUTE_CMD` values byte-equal `ENGINE_SPECS` argv for all three engines, and stay in sync after `register_engine`.

**Checkpoint**: `cd agencykit && pytest tests/ -q` fully green — the views guarantee no observable change yet.

---

## Phase 3: User Story 1 — Missions keep running exactly as today on the validated engine (Priority: P1) 🎯 MVP

**Goal**: `run_mission_cli` and `_route_via_cli` consume only the contract; every observable of the claude-code path is byte-identical (argv, prompts, timeouts, errors, cancel/kill-tree, veto loop).

**Independent Test**: full existing agencykit suite passes unmodified; contract tests prove run/route/cancel/kill-tree at the subprocess level with fake binaries.

### Tests for User Story 1 (MANDATORY — Constitution VII, offline) ⚠️

> Write these FIRST; they must pass against the CURRENT code (they pin behavior), then keep passing after T008–T009.

- [X] T006 [P] [US1] Add behavior-pinning contract tests in `agencykit/tests/test_engine_contract.py`: for EACH spec in `ENGINE_SPECS`, drive `_call(list(spec.run_cmd), prompt)` and `_call(list(spec.route_cmd), prompt)` against the echo fake binary (stdout returned verbatim); missing-binary path (`_call` on an absent binary → RuntimeError "not found on PATH"); timeout path (sleep fake + `timeout=1` → RuntimeError "timed out").
- [X] T007 [P] [US1] Add cancel/kill-tree contract tests in `agencykit/tests/test_engine_contract.py`: spawn-child fake binary + `should_cancel` flipping true → `MissionCancelled` raised AND both the fake's pid and its child's pid are gone (poll `os.kill(pid, 0)` until `ProcessLookupError`, bounded wait); assert no orphan after timeout kill too (SC-005).

### Implementation for User Story 1

- [X] T008 [US1] Switch `run_mission_cli` in `agencykit/agency_cli/engines/cli_engine.py` to resolve `spec = ENGINE_SPECS.get(engine)` (guard 1: `None` → the EXISTING `ValueError` message, byte-identical), use `spec.run_cmd` for `cmd`, and pass `timeout=spec.run_timeout` to every department/synthesis/inspection `_call`. No new guards in this task. Keep `_with_mcp`, the binary check, and the veto loop line-for-line untouched.
- [X] T009 [US1] Switch `_route_via_cli` in `agencykit/agency_cli/engines/cli_engine.py` to `spec = ENGINE_SPECS.get(engine, ENGINE_SPECS["claude-code"])`, using `spec.route_cmd` and `timeout=spec.route_timeout` — preserving the silent claude-code fallback for direct callers (research.md D6).
- [X] T010 [US1] Verify byte-identity: `cd agencykit && pytest tests/ -q` — 100% green with ZERO modifications to `tests/test_engine.py` at this point (the gemini-labeled test still passes because no refusal guard exists yet). Also run the studio suite at repo root: `pytest tests/ -q` green (SC-001, SC-006).

**Checkpoint**: US1 delivers a working refactor with no behavior change — safe to merge alone (MVP).

---

## Phase 4: User Story 2 — Unvalidated engines are refused before any production work starts (Priority: P2)

**Goal**: Art. II guards: unvalidated engines and (defense-in-depth) engines without headless web search are refused with actionable messages; no silent engine substitution.

**Independent Test**: production mission on codex/gemini refused before any subprocess spawns; claude-code unaffected.

### Tests for User Story 2 (MANDATORY — Constitution VII, offline) ⚠️

- [X] T011 [P] [US2] Add refusal-matrix tests in `agencykit/tests/test_engine_contract.py`: `run_mission_cli(goal, engine="codex")` and `engine="gemini"` raise `EngineNotValidated` whose message names the engine, the unvalidated status, and `claude-code` — WITHOUT the fake binary being invoked (assert via a fake that records invocations, or absent PATH entry); `engine="claude-code"` proceeds past the guards (with `_call` monkeypatched); registry invariant: every spec with `validated=True` has `web_search_headless=True` (FR-002/003, SC-002).
- [X] T012 [P] [US2] Add defense-in-depth test in `agencykit/tests/test_engine_contract.py`: `monkeypatch.setitem(ENGINE_SPECS, "broken", EngineSpec(..., validated=True, web_search_headless=False))` → `run_mission_cli` refuses research-grade work with an `EngineNotValidated`-family error naming the missing capability (FR-004, guard 3).

### Implementation for User Story 2

- [X] T013 [US2] Add guards 2 and 3 to `run_mission_cli` in `agencykit/agency_cli/engines/cli_engine.py`, between the existing unknown-engine `ValueError` and the `shutil.which` binary check (research.md D3 ordering): guard 2 raises `EngineNotValidated` per the contracts/engine-contract.md message contract; guard 3 raises the web-search refusal. Update the `run_mission_cli` docstring to document both guards and the no-silent-substitution rule.
- [X] T014 [US2] Retarget `test_run_mission_cli_raises_clear_error_when_binary_missing` from `engine="gemini"` to `engine="claude-code"` in `agencykit/tests/test_engine.py` (1-line change; plan.md Complexity Tracking row 2 — the test's intent is the missing-binary path, now reachable only on a validated engine).
- [X] T015 [US2] Run `cd agencykit && pytest tests/ -q` — green; confirm the ONLY modified existing test is T014's (SC-001 annotated exception).

**Checkpoint**: US1 + US2 together enforce Art. II while the validated path stays untouched.

---

## Phase 5: User Story 3 — An engine integrator adds a new engine without touching the mission loop (Priority: P3)

**Goal**: prove the extension contract — one `EngineSpec` + tests, zero mission-loop changes.

**Independent Test**: a fake "newengine" registered in a test drives a full mission end-to-end offline.

### Tests for User Story 3 (MANDATORY — Constitution VII, offline) ⚠️

- [X] T016 [US3] Add the extension proof test in `agencykit/tests/test_engine_contract.py`: build `EngineSpec(name="fake-engine", validated=True, web_search_headless=True, run_cmd=(<fake binary>,...), route_cmd=(...))`, call `register_engine`, then run a FULL `run_mission_cli` mission against fake binaries that answer route (JSON array) and run (canned deliverable with a PASS verdict and a source URL) — assert a complete dossier (route, dept_outputs, delivered, verdicts, sources) with zero changes to any module code, and that `"fake-engine"` appears in the `ENGINES` view (FR-005, SC-003; use `monkeypatch` so the registry is restored).

### Implementation for User Story 3

- [X] T017 [US3] Confirm `register_engine` + views + guards make T016 pass with no production-code edits beyond Phases 2–4; if any edit IS needed, it is a contract bug — fix it in `agencykit/agency_cli/engines/cli_engine.py` and note it in the PR (the mission-loop module must show zero US3-motivated diff lines).

**Checkpoint**: All three stories independently verifiable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: docs drift, timing budget, final gates.

- [X] T018 [P] Update `agencykit/CLAUDE.md` "Engine wiring" section: `ENGINE_SPECS` is the single source of truth (capabilities + validation status), `ENGINES`/`_ROUTE_CMD` are derived views, adding an engine = one `EngineSpec` + contract tests (only if it guarantees headless web search), codex/gemini are registered-unvalidated and refuse production missions.
- [X] T019 [P] Check `agencykit/docs/ARCHITECTURE.md` for `ENGINES`-wiring claims and update the same way (docs-guard Rule 6: grep for `ENGINES` / `_ROUTE_CMD` across agencykit docs; update every stale mention).
- [X] T020 Time the contract suite: `cd agencykit && pytest tests/test_engine_contract.py -q --durations=5` — total < 60 s offline (SC-004); if over, shrink the sleep-based tests' waits.
- [X] T021 Final gate: `cd agencykit && pytest tests/ -q` AND root `pytest tests/ -q` both green; run the guard gate (guard-skills + /code-review) before commit per repo hooks.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (P1)**: none.
- **Foundational (P2)**: after Setup — BLOCKS all stories.
- **US1 (P3)**: after Foundational.
- **US2 (P4)**: after US1 (guards insert into the spec-resolving `run_mission_cli` that T008 produces).
- **US3 (P5)**: after US2 (the extension proof exercises guards + registry together).
- **Polish (P6)**: after US3.

This feature is intentionally sequential at the phase level (single module); parallelism lives within phases.

### Within Each Phase

- T004 ∥ T005 (different files) after T003.
- T006 ∥ T007 (independent test groups in the new file) before T008–T009.
- T011 ∥ T012 before T013.
- T018 ∥ T019 (different docs files).

## Parallel Example: Phase 2

```bash
# After T002+T003 land in cli_engine.py:
Task: "T004 EngineNotValidated exception in agencykit/agency_cli/engines/cli_engine.py"
Task: "T005 fake-binary fixture in agencykit/tests/test_engine_contract.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 → Phase 2 → Phase 3 (US1).
2. **STOP and VALIDATE**: both suites green, zero test modifications — a pure, mergeable refactor.

### Incremental Delivery

1. US1 = contract consumed, behavior frozen (MVP).
2. US2 = Art. II guards live (the one documented test retarget).
3. US3 = extension proof (test-only phase).
4. Polish = docs drift + timing + final gates.
5. Single PR squash-merged to `main` per repo conventions, or per-story checkpoints if review prefers.

## Notes

- Every code task edits `agencykit/agency_cli/engines/cli_engine.py` or `agencykit/tests/` — nothing else (plan.md Structure Decision; Constitution Art. V subtree rules).
- `_call`'s signature, semantics, and messages are untouchable (studio `knowledge.py` wraps it; the whole existing suite stubs it).
- Fake binaries must be created with `chmod +x` and a proper shebang; keep sleeps ≤ 2 s so SC-004's 60 s budget holds with margin.
- Commit after each phase checkpoint (Conventional Commits, e.g. `feat(agencykit): engine contract — spec registry (brick 1, phase 2)`).
