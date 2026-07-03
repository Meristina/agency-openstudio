# Implementation Plan: The Engine Contract (Multi-CLI Abstraction)

**Branch**: `001-engine-contract` | **Date**: 2026-07-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-engine-contract/spec.md`

## Summary

Formalize the implicit two-dict engine convention (`ENGINES` / `_ROUTE_CMD` in
`agencykit/agency_cli/engines/cli_engine.py`) into an explicit, declarative Engine
contract: one `EngineSpec` per engine carrying its run command, route command,
capability declaration (`web_search_headless`, timeouts, kill-tree-on-cancel) and
validation status. `run_mission_cli` consumes only the spec; two new guards enforce
Constitution Art. II (unvalidated engines refuse production missions; engines
without guaranteed headless web search refuse research-grade work). The claude-code
path stays byte-identical (Art. X); the veto loop is untouched; a new offline
contract suite drives real fake binaries through run/route/cancel/kill-tree/
missing-binary paths (Art. VII).

## Technical Context

**Language/Version**: Python 3.9+ (stdlib only — `dataclasses`, `subprocess`, `shutil`; no new dependencies)

**Primary Dependencies**: none (agency-kit has zero runtime dependencies; this feature adds none)

**Storage**: N/A (registry is in-code; no persistence changes)

**Testing**: pytest, fully offline — existing suite monkeypatches `cli_engine._call`; the new
contract suite uses real fake binaries on a temp `PATH` (no network, no real CLI, no Node, no GPU)

**Target Platform**: macOS + Linux (kill-tree uses POSIX process groups — a pre-existing
constraint of `_signal_tree`, unchanged by this feature; Windows parity is Brick 5 territory)

**Project Type**: library — the `agencykit/` vendored fork (studio's orchestration brain);
change lands in the fork per its rules of engagement

**Performance Goals**: contract suite completes in < 60 s offline (SC-004); no runtime
overhead on the mission loop (guards are O(1) dict/attribute checks before any subprocess)

**Constraints**: byte-identical claude-code path (argv, prompts, timeouts, error messages);
`cli_engine._call` must remain the monkeypatch seam (studio `knowledge.py` wraps it; every
existing engine test stubs it); `ENGINES` / `_ROUTE_CMD` must remain importable views
(`cli.py:_engine_choices` and `tests/test_engine.py:16-17` read them)

**Scale/Scope**: 3 registered engines today (claude-code validated; codex, gemini
unvalidated); contract must admit Brick 9 engines (opencode) with zero mission-loop changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — no reasoning path changes; the
  contract still drives CLI subprocesses only; no token-billed API anywhere.
- [x] **II. Engine neutrality**: PASS — this feature IS the Art. II enforcement:
  capability-declared specs, validated/unvalidated status, production refusal,
  web-search precondition guard.
- [x] **III. No invented information**: PASS — router/department/synthesis/inspector
  prompts and the inspector veto are byte-identical; web-search-enabled run commands
  unchanged.
- [x] **IV. Local-first & offline-by-default**: PASS — no network behavior changes;
  no new cloud/paid paths; per-mission opt-in flags untouched.
- [x] **V. Subprocess boundaries**: PASS — engines remain subprocess-driven via
  `_call`; no `openmontage/` involvement; change lands in `agencykit/` (the one
  permitted imported library) inside the fork, per subtree rules.
- [x] **VI. Security**: PASS — no server surface, no CORS, no served paths, no keys
  touched.
- [x] **VII. Offline tests**: PASS — new contract suite is fully offline (fake
  binaries on a temp PATH); existing monkeypatched suite unchanged in approach.
- [x] **VIII. End-user simplicity**: PASS — refusal messages are actionable (engine,
  status, validated alternative, fix); no new user-facing complexity.
- [x] **IX. License**: PASS — no third-party code reused; all new code original,
  AGPL-3.0 in the combined work.
- [x] **X. Additive over invasive**: PASS with one justified deviation — see
  Complexity Tracking: the Art. II refusal deliberately changes behavior for
  unvalidated engines (codex/gemini production runs stop working). Constitutionally
  mandated (Art. II), spec-clarified (hard refusal, no silent fallback). The claude
  path and the veto loop are byte-identical.
- [x] **XI. English everywhere**: PASS — all code, docs, and messages in English.

**Post-Phase-1 re-check**: all gates still PASS. The design keeps `_call` as the
seam, `ENGINES`/`_ROUTE_CMD` as derived views, and adds only default-inert code
paths for the validated engine.

## Project Structure

### Documentation (this feature)

```text
specs/001-engine-contract/
├── plan.md              # This file
├── research.md          # Phase 0 output — design decisions & rationale
├── data-model.md        # Phase 1 output — EngineSpec, registry, states
├── quickstart.md        # Phase 1 output — how to add/validate an engine
├── contracts/
│   └── engine-contract.md   # Phase 1 output — the library API contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
agencykit/
├── agency_cli/
│   ├── engines/
│   │   └── cli_engine.py    # EngineSpec + ENGINE_SPECS registry + guards land here;
│   │                        # ENGINES/_ROUTE_CMD become derived views; _call, prompts,
│   │                        # veto loop, MissionCancelled unchanged
│   └── cli.py               # unchanged (reads ENGINES via _engine_choices — still works)
└── tests/
    ├── test_engine.py           # existing suite — unchanged except the one gemini-labeled
    │                            # missing-binary test (see research.md D3)
    └── test_engine_contract.py  # NEW offline contract suite (fake binaries, per engine)
```

**Structure Decision**: single-module change inside the `agencykit/` fork. The
contract lives in `cli_engine.py` itself (not a new module) to keep the diff
minimal, preserve every existing import path and monkeypatch seam, and respect the
subtree's rules of engagement. Studio code (`agency_studio/`) is untouched.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Art. X letter: unvalidated engines (codex/gemini) lose the ability to run production missions — a behavior change, not byte-identical for those paths | Constitution Art. II explicitly mandates: "an unvalidated engine MUST NOT run a production mission"; spec FR-003 + Clarification (2026-07-03) chose hard refusal over silent fallback | Keeping codex/gemini runnable would satisfy Art. X's letter but violate Art. II outright; a runtime bypass flag was explicitly ruled out in the spec's Assumptions |
| SC-001 letter: one existing test (`test_run_mission_cli_raises_clear_error_when_binary_missing`) uses `engine="gemini"` incidentally and intersects the new refusal guard | The test's intent is the missing-binary path; gemini was an arbitrary choice there. The refusal guard fires first (by design — research.md D3), so the test switches to `engine="claude-code"` (1-line change) and a new test asserts the gemini refusal | Ordering the binary check before the validation guard would keep that test green but produce absurd UX: "install gemini" → user installs it → "gemini is refused" |
