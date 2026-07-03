# Research: The Engine Contract

**Feature**: 001-engine-contract | **Date**: 2026-07-03

No NEEDS CLARIFICATION markers remained after `/speckit-clarify` (3 decisions
recorded in the spec). This document records the design decisions that resolve the
plan's Technical Context constraints, each grounded in the current code
(`agencykit/agency_cli/engines/cli_engine.py` @ fork state, `agencykit/tests/`).

## D1 — Contract representation: frozen dataclass in `cli_engine.py`

**Decision**: An `EngineSpec` frozen `dataclasses.dataclass` defined in
`cli_engine.py`, with an `ENGINE_SPECS: dict[str, EngineSpec]` registry in the same
module. No new module, no abstract base class, no `typing.Protocol`.

**Rationale**:
- PLAN.md Brick 1 words it as "formalize the `ENGINES` dict … into an explicit
  Engine contract" — the contract is data (argv recipes + declared capabilities +
  status), not polymorphic behavior. All engines share one execution path
  (`_call`); what differs per engine is pure configuration. A dataclass says
  exactly that; a class hierarchy would imply per-engine code that doesn't exist.
- Same-module placement keeps every existing import path
  (`from agency_cli.engines.cli_engine import run_mission_cli, MissionCancelled`)
  and monkeypatch seam (`cli_engine._call` — stubbed by every engine test and
  wrapped by studio `knowledge.py:455`) untouched.
- `frozen=True` prevents accidental mutation of shared specs (mirrors the existing
  "`_with_mcp` returns a NEW list; the shared ENGINES entry is never mutated"
  discipline). Tests replace whole registry entries via `monkeypatch.setitem`
  instead of mutating fields.

**Alternatives considered**:
- *Abstract `Engine` class per engine* — rejected: invents per-engine subclasses
  with no behavioral difference to encode; bigger diff; breaks the monkeypatch
  seam story.
- *Separate `engines/contract.py` module* — rejected: splits one cohesive concept
  across files inside a vendored subtree where diff size matters; nothing imports
  the contract without also importing the engine runner.
- *TypedDict / plain dicts* — rejected: no invariant enforcement (a typo'd
  capability key would silently read as absent), no frozen semantics.

## D2 — Backward compatibility: `ENGINES` / `_ROUTE_CMD` become derived views

**Decision**: `ENGINE_SPECS` is the single source of truth. `ENGINES` and
`_ROUTE_CMD` remain module-level dicts, rebuilt from `ENGINE_SPECS` at module load
(`{name: spec.run_cmd}` / `{name: spec.route_cmd}`).

**Rationale**: verified external readers that must keep working unchanged:
- `agency_cli/cli.py:_engine_choices()` — `list(ENGINES)` feeds `--engine` choices.
- `tests/test_engine.py:16-17` — asserts the three names are in both dicts.
- `tests/test_engine.py:685` — reads `ENGINES["codex"]` argv content.
- `agencykit/CLAUDE.md` documents both dicts as the wiring surface.

The mission loop itself stops reading the view dicts and reads `ENGINE_SPECS`
directly; the views exist for external readers. A helper `register_engine(spec)`
(used by the contract suite and Brick 9) inserts into `ENGINE_SPECS` and refreshes
both views so the three structures can never drift.

**Alternatives considered**:
- *Keep dicts primary, derive specs* — rejected: two dicts can't carry capabilities
  or validation status; the new data has to live somewhere, and then THAT becomes
  the source of truth anyway.
- *Delete the dicts, migrate readers* — rejected: touches `cli.py`, tests, and
  agencykit's own docs for zero functional gain; maximally invasive in a subtree.

## D3 — Guard ordering: validation → web-search → binary

**Decision**: `run_mission_cli` checks, in order: (1) unknown engine →
`ValueError` (existing message, unchanged); (2) `spec.validated` →
`EngineNotValidated` naming engine, status, and validated alternatives;
(3) `spec.web_search_headless` → `EngineNotValidated`-family refusal for
research-grade work (defense-in-depth — per the spec clarification, a validated
engine always declares web search, so this can only fire on a inconsistent
registry); (4) missing binary → existing `RuntimeError` (message unchanged).

**Rationale**: refusing before the binary check avoids the absurd sequence
"install gemini" → user installs gemini → "gemini is refused as unvalidated". The
guards are pure attribute checks — no subprocess is spawned before all four pass,
satisfying FR-003's "before any department work".

**Consequence (accepted, tracked in plan Complexity Tracking)**: the existing
`test_run_mission_cli_raises_clear_error_when_binary_missing` uses
`engine="gemini"` incidentally; with guard (2) first it now hits the refusal. The
test's intent is the missing-binary path, so it switches to `engine="claude-code"`
(1 line), and new tests assert the codex/gemini refusals explicitly. SC-001 in the
spec is annotated accordingly.

**Alternatives considered**:
- *Binary check first (fully preserves existing tests)* — rejected for the UX
  absurdity above; also makes the refusal dependent on installation state, which
  FR-003 does not want.
- *Refusal inside `_route_via_cli`* — rejected: routing is classification-only and
  constitutionally allowed without web search; the production-mission guard belongs
  to the mission entry point, not the route helper.

## D4 — Refusal exception: `EngineNotValidated(RuntimeError)`

**Decision**: a new exception class `EngineNotValidated` subclassing
`RuntimeError`, raised by guard (2) and (3).

**Rationale**: every existing caller (`runner_bridge.run`, studio server, CLI)
already handles `RuntimeError` from `run_mission_cli` (missing binary, timeout,
non-zero exit) by surfacing the message — so refusals flow through existing error
paths with zero caller changes, while tests and future callers (Brick 4's
capabilities endpoint) can catch the specific type. Message format (self-contained —
no host-repo article/brick numbers baked into the fork-level message, since the fork
ships its own constitution with a different Art. II):
`engine 'codex' is registered but NOT validated for production missions. Validated
engine(s): claude-code. Select a validated engine, or validate this one end-to-end
before use — no other engine is substituted for the one you chose.`

**Alternatives considered**: bare `RuntimeError` (loses type-level testability);
`ValueError` (existing `ValueError` on unknown engine means "you typo'd the name",
a different failure class than "known but not allowed").

## D5 — Timeouts move into the spec, values unchanged

**Decision**: `EngineSpec.run_timeout = 900` and `EngineSpec.route_timeout = 60`;
`run_mission_cli` passes `spec.run_timeout` to `_call` for department/synthesis/
inspection calls, `_route_via_cli` passes `spec.route_timeout`. `_call`'s own
default stays `900` (unused by the mission loop after this, but preserved for
direct callers and the studio's `knowledge.py` wrapper).

**Rationale**: FR-001 requires the capability declaration to state the time
budget; the current values (900 in `_call`'s signature, 60 hard-coded at the
route call site, `cli_engine.py:239`) are preserved byte-for-byte per the spec
Assumption ("the contract declares them, it does not change them").

## D6 — Route fallback semantics preserved

**Decision**: `_route_via_cli` resolves
`ENGINE_SPECS.get(engine, ENGINE_SPECS["claude-code"]).route_cmd`, mirroring the
current `_ROUTE_CMD.get(engine, _ROUTE_CMD["claude-code"])` silent fallback.

**Rationale**: unreachable from the mission loop (unknown engines fail guard (1)
first), but `_route_via_cli` is importable directly; preserving the fallback keeps
any direct caller byte-identical (Art. X). Tightening it is not required by any FR.

## D7 — Fake engine binaries: temp-PATH executables, not monkeypatches

**Decision**: the new `tests/test_engine_contract.py` creates one tiny executable
script per engine name (`claude`, `codex`, `gemini`) in a `tmp_path` directory,
prepends it to `PATH` via `monkeypatch.setenv`, and drives `_call` /
`_route_via_cli` / `run_mission_cli` for real — no `_call` stubbing. Scripts:
echo canned output (run/route paths), sleep-then-echo (timeout/cancel paths), and
spawn-a-child-then-sleep (kill-tree path, asserting both PIDs die).

**Rationale**: FR-009 asks the contract suite to prove subprocess-level behavior
(cancel, kill-tree, missing binary) — exactly the layer monkeypatching `_call`
bypasses. Local scripts satisfy Art. VII: no network, no real engine CLI, no
Node, no GPU; runtime well under SC-004's 60 s (sleeps are ≤ ~2 s each). The
existing `test_engine.py` keeps its monkeypatch style — the two suites test
complementary layers.

**Alternatives considered**: extending the monkeypatch suite (cannot exercise
kill-tree or process groups); a shared fixture binary parameterized by env vars
(more coupling, no benefit over per-test scripts).

## D8 — CLI and caller surfaces: minimal, review-driven changes

**Decision** (revised): the initial implementation left `cli.py`,
`runner_bridge.py`, `scaffolder.py`, and `agency_studio/` untouched. A follow-up
review surfaced caller-side gaps that the bare guard created, so this stack makes
four small, targeted changes and leaves `cli.py` as-is:

- `scaffolder.py` (`agency check`): report health on a VALIDATED engine on PATH,
  not any registered engine — an unvalidated engine no longer reads as "runnable".
- `batch_runner.py`: pre-flight the engine once (`ensure_production_engine`) so an
  unvalidated `--engine` refuses the whole queue up front instead of failing every
  goal and burning retry counters.
- `agency_studio/server.py`: on resume, let an explicit body engine override the
  pinned one (escape hatch for a checkpoint pinned to a now-unvalidated engine),
  and pre-flight the engine BEFORE opening the SSE stream so a refusal is a clean
  JSON 4xx rather than a mid-stream `phase:"error"` frame.
- `runner_bridge.py`: docstring only — document that codex/gemini are refused.

**Rationale**: `--engine` choices still come from `ENGINES` (D2 view) — an
unvalidated engine stays selectable and returns the actionable `EngineNotValidated`
message, which is better UX than argparse rejecting it as unknown. The refusal is a
shared helper (`ensure_production_engine`, D4) so the mission loop, the batch
pre-flight, and the studio pre-flight enforce it identically. Exposing validation
status in the studio GUI's model panel remains Brick 4's capabilities endpoint.
