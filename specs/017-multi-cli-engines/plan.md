# Implementation Plan: Real Multi-CLI — Validate codex, Replace gemini with antigravity, Add opencode, Publish Compatibility Matrix

**Branch**: `017-multi-cli-engines` | **Date**: 2026-07-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-multi-cli-engines/spec.md`

## Summary

Turn the single-engine reality (`claude-code` validated; `codex`/`gemini` refused) into a real multi-engine roster driven by the Brick 1 Engine contract, with zero mission-loop changes. Concretely: (1) **fix and validate `codex`** — its current `route_cmd` is malformed (no `exec` subcommand, exec-only `--color` used at the top level → hangs headless), so the registry entry is corrected and codex is put through end-to-end live validation; (2) **replace the deprecated `gemini` slot** (Gemini CLI → Antigravity CLI upstream; consumer `gemini` stopped serving 2026-06-18, binary absent) with a new **`antigravity`** engine (binary `agy --print`); (3) **register `opencode`** (binary `opencode run`); and (4) **publish an engines × capabilities compatibility matrix** in `agencykit/README.md` (the authoritative engine surface) with the root `README.md` pointing to it. Every add/validate is one `EngineSpec` edit plus its offline contract tests; the veto loop, prompts, and the `claude-code` path stay byte-identical. Per the Session 2026-07-07 clarifications, all three candidates are put through live validation and each flips to `validated=True` only on its own passing live-test; the minimum bar to close the brick is `claude-code` + `codex`.

## Technical Context

**Language/Version**: Python 3.9+ (stdlib only — `dataclasses`, `subprocess`, `shutil`, `signal`; no new dependencies)

**Primary Dependencies**: none (agency-kit has zero runtime dependencies; this feature adds none). External artifacts are the engine CLIs themselves, driven across the subprocess boundary: `claude` (Claude Code 2.1.x), `codex` (Codex CLI 0.142.x), `agy` (Antigravity CLI 1.0.x), `opencode` (1.17.x).

**Storage**: N/A (registry is in-code `ENGINE_SPECS`; no persistence changes)

**Testing**: pytest, fully offline — existing suite monkeypatches `cli_engine._call`; the contract suite (`test_engine_contract.py`) spawns real *fake* binaries on a temp `PATH` (no network, no real CLI, no Node, no GPU). Real-CLI validation is a separate live-test report, not required for the offline suite to pass.

**Target Platform**: macOS + Linux (kill-tree uses POSIX process groups via `_signal_tree`; the subprocess tests are `@requires_posix`, unchanged by this feature).

**Project Type**: library — the `agencykit/` vendored fork (the studio's orchestration brain). All code changes land inside the fork per its rules of engagement; the studio server/GUI are untouched.

**Performance Goals**: no runtime overhead on the mission loop (registry lookup is O(1); guards are attribute checks before any subprocess). Offline contract suite stays fast (< 60 s), consistent with SC-005.

**Constraints**: byte-identical `claude-code` path (argv, prompts, timeouts, messages); the veto loop and `_short_verdict` logic untouched (Art. X / spec FR-007, FR-012); `cli_engine._call` remains the monkeypatch seam; `ENGINES` / `_ROUTE_CMD` stay live in-place views (`cli.py:_engine_choices`, `scaffolder.py:_engine_binaries`, and `tests/` read them); flipping any engine to `validated=True` is gated on a passing live-test report (spec FR-001/016).

**Scale/Scope**: 3 registered engines today (claude-code validated; codex, gemini unvalidated) → 4 after this brick (claude-code, codex, antigravity, opencode; gemini removed). One `EngineSpec` edit + contract tests per engine; two README surfaces + one internal `CLAUDE.md` updated; one live-test report authored.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — every engine is a subscription CLI driven via `_call`; no token-billed API path is introduced. Registering more CLI engines reinforces this principle.
- [x] **II. Engine neutrality**: PASS — this feature *is* Art. II in action: capability-declared specs, validated/unvalidated status, production refusal, and the headless-web-search precondition. Adding an engine remains one `EngineSpec` + contract tests with zero mission-loop changes.
- [x] **III. No invented information**: PASS — router/department/synthesis/inspector prompts and the inspector veto are byte-identical; an engine only becomes validated after a live-test proves it genuinely searches the web (spec FR-006/008/016). No engine that can fabricate is promoted.
- [x] **IV. Local-first & offline-by-default**: PASS — no network behavior changes; opencode's Exa search is an explicit, env-keyed opt-in (`OPENCODE_ENABLE_EXA`), exactly the "explicit, opt-in, env-keyed" shape Art. IV mandates; no silent cloud default. `claude-code` stays the default engine.
- [x] **V. Subprocess boundaries**: PASS — engines are driven only via `_call`; **opencode uses `run` (one-shot subprocess), never `serve` (a long-lived HTTP server)** — deliberately keeping the subprocess-prompt→stdout shape. No `openmontage/` import; the change lands in `agencykit/` (the one permitted imported library) inside the fork.
- [x] **VI. Security**: PASS — no server surface touched; because opencode `serve` is *not* used, no new bind/CORS surface is introduced; outbound engine research is the CLI's own HTTPS; API keys/sessions stay engine-owned and env-only (agency-kit never sees a key). The `--sandbox read-only` posture is kept for codex.
- [x] **VII. Offline tests**: PASS — new per-engine contract tests use fake binaries on a temp `PATH`, mirroring `test_engine_contract.py`; the suite stays green with no CLI/network/Node. Live validation is out-of-band.
- [x] **VIII. End-user simplicity**: PASS — engine selection remains a power-user `--engine` override; the default (`claude-code`) is unchanged. Refusal messages stay actionable (engine, reason, validated alternative); the README matrix makes capabilities legible without reading code.
- [x] **IX. License**: PASS — no third-party code reused; all new code original (AGPL-3.0 in the combined work). No new entry needed in `docs/LICENSES.md` (the engine CLIs are external tools invoked over subprocess, not vendored code).
- [x] **X. Additive over invasive**: PASS with one justified deviation — see Complexity Tracking. Adding `antigravity`/`opencode` and fixing/validating `codex` are additive (codex was already refused, so no production behavior regresses). **Removing the `gemini` slot is the single non-additive edit**, mandated by upstream deprecation. The `claude-code` path and the veto loop are byte-identical.
- [x] **XI. English everywhere**: PASS — all code, docs, commit messages, and the live-test report in English.

## Project Structure

### Documentation (this feature)

```text
specs/017-multi-cli-engines/
├── plan.md              # This file
├── spec.md              # Feature spec (clarified)
├── research-cli.md      # Verified CLI invocations (authored during specify)
├── research.md          # Phase 0 output — consolidated decisions
├── data-model.md        # Phase 1 output — EngineSpec rows, matrix + report schemas
├── quickstart.md        # Phase 1 output — run offline suite / live validation / add an engine
├── contracts/
│   └── engine-registry.md   # The registry contract: argv, capabilities, refusal, matrix invariant
└── checklists/
    └── requirements.md  # Spec quality checklist (from specify)
```

### Source Code (repository root)

```text
agencykit/                                   # the vendored orchestration brain (edits land here)
├── agency_cli/
│   ├── engines/
│   │   └── cli_engine.py                    # ENGINE_SPECS: fix codex route; add antigravity, opencode; remove gemini
│   ├── cli.py                               # --engine choices derive from ENGINES (auto-updates; no manual edit)
│   └── scaffolder.py                        # `agency check` derives from ENGINE_SPECS (auto-updates); --agent init list reconciled
├── tests/
│   └── test_engine_contract.py             # per-engine contract tests: run/route parse, refusal, matrix-vs-registry consistency
├── README.md                                # AUTHORITATIVE compatibility matrix (engines × capabilities)
└── CLAUDE.md                                # internal doc: engine wiring references reconciled (codex/gemini → codex/antigravity/opencode)

README.md                                    # root: engine mentions updated to point at the matrix
docs/legacy/                                 # live-test report lands alongside the archived reports (Brick-9 multi-CLI live test)
```

**Structure Decision**: Library change confined to the `agencykit/` fork. `ENGINE_SPECS` in `agency_cli/engines/cli_engine.py` is the single source of truth; `cli.py:_engine_choices` and `scaffolder.py:_engine_binaries` already derive from it, so the CLI `--engine` list and `agency check` update with **zero** manual edits. Manual doc surfaces are exactly three: `agencykit/README.md` (the matrix), root `README.md` (engine mentions), and `agencykit/CLAUDE.md` (internal wiring notes). The offline contract suite gains per-engine cases; the live-test report is authored separately and gates the `validated=True` flips.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Non-additive removal of the `gemini` engine slot** (Art. X: changes behavior — `--engine gemini` becomes an unknown-engine error) | Google transitioned Gemini CLI → Antigravity CLI; consumer `gemini` stopped serving requests 2026-06-18 and the binary is absent from the environment. A registered engine that can never run is a live lie in the registry, the `agency check` output, and the compatibility matrix. | Keeping the `gemini` slot (even `validated=False`) was rejected: it would always fail at mission time with a confusing "not validated" message instead of the truthful "this engine no longer exists — use antigravity", and it would force the matrix to publish a dead row. Replacing it with `antigravity` is the honest, minimal change. Owner-approved (Session 2026-07-07). |
