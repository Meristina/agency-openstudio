---
description: "Task list for Brick 9 — Real Multi-CLI"
---

# Tasks: Real Multi-CLI — Validate codex, Replace gemini with antigravity, Add opencode, Publish Compatibility Matrix

**Input**: Design documents from `/specs/017-multi-cli-engines/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/engine-registry.md, research-cli.md

**Tests**: Per Constitution VII, every code change ships offline tests (fake binaries on a temp PATH; no network/CLI/Node). The **live-test tasks** (codex/antigravity/opencode validation) are NOT part of the offline suite — they are the out-of-band evidence (FR-015/016) that gates each `validated=True` flip, recorded in a report.

**Organization**: Grouped by user story. The `ENGINE_SPECS` registry edits are Foundational because the matrix (US2) and every contract test depend on the final roster shape, and they all edit one file.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: different files, no dependency on incomplete tasks → parallelizable
- **[Story]**: US1 / US2 / US3
- All source paths are inside the `agencykit/` fork unless noted.

---

## Phase 1: Setup (Baseline)

**Purpose**: Confirm a green starting point so every later change is a measurable delta.

- [X] T001 Establish the offline baseline: from `agencykit/`, run `pip install -e ".[dev]"` then `pytest tests/ -q`; record the pass count (e.g. "N passed") to compare against at the end. Baseline: `236 passed, 1 skipped`.

**Checkpoint**: Suite green; baseline captured.

---

## Phase 2: Foundational (Engine registry roster — BLOCKS all stories)

**Purpose**: Bring `ENGINE_SPECS` to its final Brick-9 shape. All edits are in the single file `agencykit/agency_cli/engines/cli_engine.py`, so they are **sequential (not [P])**. `cli.py:_engine_choices` and `scaffolder.py:_engine_binaries` derive from this dict, so the CLI `--engine` list and `agency check` update automatically.

**⚠️ CRITICAL**: No user story work begins until this phase is complete.

- [X] T002 Fix the `codex` `EngineSpec` in `agencykit/agency_cli/engines/cli_engine.py`: `run_cmd = ("codex", "--search", "exec", "--color", "never", "--sandbox", "read-only", "--skip-git-repo-check", "--")` and `route_cmd = ("codex", "exec", "--color", "never", "--sandbox", "read-only", "--skip-git-repo-check", "--")` (global `--search` before `exec` on run only; route carries `exec` but no `--search`; `--skip-git-repo-check` allows non-git CWD). Keep `validated=False` for now. (Ref: research.md D1)
- [X] T003 In the same file, add the `antigravity` `EngineSpec` (`name="antigravity"`, `run_cmd=("agy", "--print")`, `route_cmd=("agy", "--print")`, `web_search_headless=False`, `validated=False`) and **remove the `gemini` `EngineSpec`** entirely. (Ref: research.md D2)
- [X] T004 In the same file, add the `opencode` `EngineSpec` (`name="opencode"`, `run_cmd=("opencode", "run")`, `route_cmd=("opencode", "run")`, `web_search_headless=False`, `validated=False`). (Ref: research.md D3)
- [X] T005 Update the module docstring's "Registered engines" block in `agencykit/agency_cli/engines/cli_engine.py` to the new roster (claude-code / codex / antigravity / opencode; drop gemini; note antigravity & opencode web search is config-gated & unproven).

**Checkpoint**: Registry is `{claude-code, codex, antigravity, opencode}`; gemini gone; codex argv well-formed. (Existing `test_call_run_and_route_commands_return_stdout_for_each_spec` now exercises all four via fake binaries.)

---

## Phase 3: User Story 1 — Second production engine: codex (Priority: P1) 🎯 MVP

**Goal**: `claude-code` + `codex` both drive the mission loop identically; codex produces a comparable, source-verified dossier — the constitutional "two engines" bar.

**Independent Test**: `agency run --engine codex "<goal>"` completes with a dossier of the same shape as a claude-code run and cited, resolvable sources.

### Tests for User Story 1 (offline) ⚠️

- [X] T006 [US1] Add a regression test in `agencykit/tests/test_engine_contract.py` that locks the codex argv fix: assert `ENGINE_SPECS["codex"].route_cmd` contains `"exec"` and NOT `"--search"`, and `run_cmd` contains `"--search"` positioned before `"exec"`. (Turns the D1 fix into a permanent guard.)

### Implementation for User Story 1

- [X] T007 [US1] Live-validate codex (out-of-band): run the representative mission `agency run --engine codex --min-sources 3 --resolve-sources "<representative goal>"` (temporarily flipping `validated=True` on a work branch to exercise it); capture dossier shape, per-department cited-source counts, and resolved-URL results into the Brick-9 live-test report (see T018). (Ref: quickstart.md §3)
- [X] T008 [US1] If codex PASSed the live-test: set `ENGINE_SPECS["codex"].validated=True` in `agencykit/agency_cli/engines/cli_engine.py` (its `web_search_headless` is already `True`, so the invariant holds). If it FAILED: leave it refused, document the failure in the report, and flag that the brick's minimum bar is unmet.
- [X] T009 [US1] Confirm the invariant tests pass with codex validated (`test_validated_specs_declare_headless_web_search`, `test_engine_spec_rejects_validated_without_headless_web_search`) and add an explicit assertion in `agencykit/tests/test_engine_contract.py` that `"codex"` is in the validated set.

**Checkpoint**: Two validated engines (claude-code + codex). MVP complete.

---

## Phase 4: User Story 2 — Compatibility matrix (Priority: P2)

**Goal**: One README table shows every engine's capabilities and validation status; a test keeps it honest against the registry.

**Independent Test**: Read the matrix in `agencykit/README.md`; run the consistency test — it fails if the matrix drifts from `ENGINE_SPECS`.

### Implementation for User Story 2

- [X] T010 [US2] Replace the 3-column engine table in `agencykit/README.md` (~line 79) with the engines × capabilities matrix: columns **Engine (`--engine`) · Run / Route · Headless web search (+ config note) · MCP `--mcp-config` · Kill-tree on cancel · Validation status**. Show config-gated search honestly (`✅ via OPENCODE_ENABLE_EXA`, `⚠️ tool-driven (unproven)`), never a bare ✓. Also update the `--engine gemini` usage examples elsewhere in this README (~lines 100, 125–126, 167) to codex/antigravity. (Ref: data-model.md matrix schema)
- [X] T011 [P] [US2] Add a matrix-vs-registry consistency test in `agencykit/tests/test_engine_contract.py`: parse the README matrix rows and assert each engine name + validation status equals `ENGINE_SPECS`, exactly one row per registered engine (no missing/extra), and no `validated` row shows a non-affirmative headless-web-search cell. (Ref: contracts C7, FR-011)
- [X] T012 [P] [US2] Update root `README.md` engine mentions (~line 15 pillar row "Multi-engine: claude-code / codex / gemini"; ~lines 27–28 comment) to the current roster and link to the `agencykit/README.md` matrix.
- [X] T013 [P] [US2] Reconcile `agencykit/CLAUDE.md` — the `ENGINE_SPECS` example block and prose references (codex/gemini → codex/antigravity/opencode; note config-gated search).

**Checkpoint**: Matrix published and guarded by an offline test; docs consistent across surfaces.

---

## Phase 5: User Story 3 — Register antigravity & opencode candidates (Priority: P3)

**Goal**: antigravity (`agy`) and opencode (`opencode run`) appear as unvalidated candidates, refused for production; the removed `gemini` name errors cleanly; each candidate is put through live validation and flipped only on proof.

**Independent Test**: `--engine antigravity` / `--engine opencode` are refused with the not-validated message; `--engine gemini` is an unknown-engine error.

### Tests for User Story 3 (offline) ⚠️

- [X] T014 [US3] Update the refusal test in `agencykit/tests/test_engine_contract.py` to parametrize over the registry's unvalidated set derived at runtime (`[n for n, s in ENGINE_SPECS.items() if not s.validated]`) instead of the hardcoded `["codex", "gemini"]`; assert `EngineNotValidated` names the engine, "NOT validated", and "claude-code". Also grep the whole `agencykit/tests/` suite for other `"gemini"` references and update/remove them. (Ref: contracts C3)
- [X] T015 [US3] Add an unknown-engine test in `agencykit/tests/test_engine_contract.py`: `run_mission_cli(engine="gemini")` raises `ValueError` whose message contains "Unknown engine", lists the current registered engines, and never substitutes another engine. (Ref: contracts C4, FR-005)

### Implementation for User Story 3

- [X] T016 [US3] Live-validate antigravity (out-of-band): run the representative mission via `agy --print` (add `--dangerously-skip-permissions` if tool approval blocks headless search); record the outcome in the Brick-9 report. Flip `antigravity` `validated=True` AND `web_search_headless=True` in `cli_engine.py` **only if** genuine headless web search with resolvable sources is proven; otherwise keep it refused and document the limitation. (Ref: research.md D4/D5)
- [X] T017 [US3] Live-validate opencode (out-of-band): run the representative mission with `OPENCODE_ENABLE_EXA=1` via `opencode run`; record the outcome. Flip `opencode` `validated=True` AND `web_search_headless=True` **only if** proven; otherwise keep it refused and document. (Ref: research.md D4/D5)

**Checkpoint**: Both candidates registered/refused; gemini errors cleanly; any candidate that passed its live-test is validated.

---

## Phase 6: Polish & Cross-Cutting

- [X] T018 Author the Brick-9 multi-CLI live-test report at `docs/legacy/brick9-multi-cli-live-test.md`, consolidating the codex / antigravity / opencode outcomes (per-engine: goal, PASS/FAIL + reason, dossier shape, per-department source counts, resolved URLs, config used, flip decision) — the FR-016 artifact.
- [X] T019 [P] Reconcile the `agency init --agent` harness choices in `agencykit/agency_cli/cli.py` (~line 232 `"claude | codex | cursor | copilot | gemini | opencode"`): drop `gemini`, add `antigravity` (this scaffolder list is separate from `ENGINE_SPECS`).
- [X] T020 Run the full offline suite from `agencykit/` (`pytest tests/ -q`) green — including the new matrix-consistency test — and confirm the pass count moved up from the T001 baseline by the number of added tests. Final: `239 passed, 1 skipped` (net +3; codex promotion removes one dynamic unvalidated-engine refusal case).
- [X] T021 [P] Run the quickstart.md validation: `agency check` shows the correct roster, `agency run --help` `--engine` choices are `{claude-code, codex, antigravity, opencode}`, and `--engine gemini` is rejected.

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (P1)** → no deps.
- **Foundational (P2)** → after Setup; **BLOCKS all user stories** (registry shape drives matrix + all tests). Internally sequential (T002→T003→T004→T005, one file).
- **US1 (P3)** → after Foundational. MVP.
- **US2 (P4)** → after Foundational (matrix must reflect the final roster; independent of US1's live flip except that the matrix's codex validation cell reflects US1's outcome — write it after T008, or write "validated" once T008 lands).
- **US3 (P5)** → after Foundational. Independent of US1/US2 for its offline tests; its live flips (T016/T017) are independent of codex.
- **Polish (P6)** → after the stories whose outcomes it records (T018 needs T007/T016/T017; T020 needs all test tasks).

### Critical cross-task notes

- T011 (matrix consistency test) can be *authored* in parallel but only *passes* after T010 writes the matrix — keep T010 before T011 in execution.
- T008 (codex flip) changes what T014's runtime-derived refusal set contains — T014 derives it dynamically, so order is not brittle, but run T014 after the Foundational + US1 flips have settled.
- Live-test tasks (T007, T016, T017) require the real CLIs authenticated and cost real subprocess + network; they are the only non-offline tasks and never gate the offline suite.

### Parallel opportunities

- Phase 6: T019 ∥ T021 (different files).
- US2: after T010, tasks T011 (test file) ∥ T012 (root README) ∥ T013 (agencykit/CLAUDE.md) are all different files.
- Within Foundational and within the shared test file, tasks are sequential (same file).

---

## Parallel Example: User Story 2

```bash
# After T010 (matrix written), these touch different files and can run together:
Task: "T011 matrix-vs-registry consistency test in agencykit/tests/test_engine_contract.py"
Task: "T012 update root README.md engine mentions + link to matrix"
Task: "T013 reconcile agencykit/CLAUDE.md engine references"
```

---

## Implementation Strategy

### MVP first (US1)

1. Phase 1 (baseline) → Phase 2 (registry roster, incl. the codex argv fix) → Phase 3 (codex offline guard + live-validate + flip).
2. **STOP and VALIDATE**: run a mission on codex; confirm comparable dossier + verified sources. Two validated engines = the brick's minimum bar met.

### Incremental delivery

1. Setup + Foundational → roster in final shape, suite green.
2. US1 (codex) → MVP: second production engine.
3. US2 (matrix) → operator-legible capabilities, test-guarded.
4. US3 (antigravity/opencode) → candidates registered/refused; live-validate & flip any that pass.
5. Polish → live-test report, scaffolder list, quickstart validation.

### Notes

- [P] = different files, no incomplete-task dependency.
- The three `validated=True` flips (T008, T016, T017) are evidence-gated: no flip without a passing live-test recorded in T018's report. A candidate that fails stays refused — that is a valid brick outcome (only claude-code + codex are required).
- The `claude-code` path, prompts, and the inspector veto loop are never edited (FR-007/012); verify by the existing loop tests re-passing unchanged.
