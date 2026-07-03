# Implementation Plan: The Specialist Army Plays (Budget-Controlled Escalation)

**Branch**: `002-specialist-army-escalation` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-specialist-army-escalation/spec.md`

## Summary

Wire a budget-controlled specialist escalation into the department-execution phase of
`run_mission_cli` (`agencykit/agency_cli/engines/cli_engine.py:780-797`). Today each routed
department is one subprocess call built from the condensed doctrine (`_shared-{dept}`).
With escalation on (the product default, per clarification), a deployed department instead
runs a bounded chain: one **selection call** (the department router picks officers/soldiers
from a roster), then **commander → officer(s) → soldier(s)** invocations — each a separate
`_call` through the existing subprocess boundary, each traced into the dossier, all capped
by a hard per-department invocation budget with an advisory estimated-token figure. A new
`agencykit/agency_cli/escalation.py` module owns the roster index, selection parsing, and
the escalation loop; `cli_engine.py` grows one default-`None` parameter and a branch in the
department loop; `runner_bridge.run` resolves the product default (on, opt-out available);
the studio passes the option through its existing signature-introspection pattern. With
escalation off (`None` at the library boundary), every prompt and call is byte-identical to
today.

## Technical Context

**Language/Version**: Python 3.10+ (stdlib-only core, type hints)

**Primary Dependencies**: None at runtime (Constitution: zero core runtime deps). Dev: pytest.

**Storage**: Existing `~/.agency` store + `missions/<id>/` serialization via
`runner_bridge` — the dossier dict gains one additive `escalation` key; no new storage.

**Testing**: pytest, fully offline — `cli_engine._call` monkeypatched (existing pattern in
`agencykit/tests/test_engine.py`); no network, no CLI, no Node, no GPU.

**Target Platform**: macOS/Linux/Windows (same as agencykit today; no platform-specific code).

**Project Type**: Library (agencykit orchestration) + thin studio server passthrough.

**Performance Goals**: A department's escalation adds at most `budget` subprocess calls
(default cap: 6 — 1 selection + 1 commander + up to 2 officers + up to 2 soldiers).
Mission wall-time stays bounded by `(1 route + Σ per-dept (1 + budget) + MAX_ITERS ×
(synth + inspect)) × spec.run_timeout`.

**Constraints**: Escalation off ⇒ byte-identical prompts/calls (Principle X); veto-loop
inputs and logic untouched (Art. IX); router/inspector never see MCP tools or escalation
internals; per-mission network opt-in unchanged; comms/data/ops/people/tech have NO
officer agent files (commander-only doctrines) — the mechanism must field "virtual
officers" from the commander doctrine's declared phases.

**Scale/Scope**: 9 departments, 10 commanders / 22 officer files / 126 soldier files in
`agencykit/agency_cli/payload/agents/`; escalation index built once per mission from
frontmatter; selection prompt carries a compact roster (names + one-line summaries).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — every new call (selection, commander,
  officer, soldier) goes through the existing `_call` subprocess wrapper on the validated
  engine; no token-billed API anywhere.
- [x] **II. Engine neutrality**: PASS — escalation reads `ENGINE_SPECS` via the existing
  `ensure_production_engine` path; no engine-specific behavior outside the Engine contract;
  unvalidated engines are refused before escalation ever starts.
- [x] **III. No invented information**: PASS — officer/soldier doctrines all carry the
  research-and-cite mandate; escalation prompts keep the WebSearch/no-invention clause;
  inspector gate unchanged; graceful degradation records gaps instead of fabricating.
- [x] **IV. Local-first & offline-by-default**: PASS — no new network path; engine research
  remains the only network activity, unchanged; no cloud provider involved.
- [x] **V. Subprocess boundaries**: PASS — no `openmontage/` import; all specialist work via
  subprocess `_call`; `agencykit/` remains the only imported library (edits to `agencykit/`
  follow the Brick-1 precedent of in-repo evolution of our pinned fork).
- [x] **VI. Security**: PASS — no server-surface change beyond one optional request field
  passed through `agency_studio/server.py` (no new endpoint, no CORS/bind/path change; the
  field is validated as a bool + int, never an arbitrary path).
- [x] **VII. Offline tests**: PASS — new `test_escalation.py` + `test_engine.py` additions
  monkeypatch `_call`; byte-identical-off regression test; no network/CLI/Node/GPU.
- [x] **VIII. End-user simplicity**: PASS — escalation is on by default with sensible
  budget; the operator does nothing; opt-out is a single switch surfaced in the studio
  mission request (no terminal required).
- [x] **IX. License**: PASS — no new/reused external component; `docs/LICENSES.md` unchanged.
- [x] **X. Additive over invasive**: PASS WITH JUSTIFICATION — `run_mission_cli` gains a
  default-`None` `escalation` parameter (None ⇒ byte-identical, proven by regression test);
  the veto loop body is untouched. The product-level default-on lives in
  `runner_bridge.run` per the clarified decision — justified in Complexity Tracking.
- [x] **XI. English everywhere**: PASS — all new code/docs/commits in English. (Pre-existing
  note: vendored `payload/agents/commander-comms.md` contains French prose — vendored
  snapshot content, out of scope for this brick, flagged for the upstream sync.)

## Project Structure

### Documentation (this feature)

```text
specs/002-specialist-army-escalation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── escalation-api.md    # Library API contract (new param + module surface)
│   └── dossier-schema.md    # Additive dossier/checkpoint schema
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
agencykit/
├── agency_cli/
│   ├── escalation.py            # NEW — roster index, selection parsing, escalation loop
│   ├── engines/cli_engine.py    # dept-loop branch + escalation prompt builders + param
│   ├── runner_bridge.py         # product default-on resolution + opt-out plumbing
│   └── cli.py                   # --no-escalation / --escalation-budget flags
└── tests/
    ├── test_escalation.py       # NEW — index, selection, budget, degradation, trace
    └── test_engine.py           # byte-identical-off regression + loop integration

agency_studio/
└── server.py                    # optional `escalation` mission-request field passthrough

tests/
└── test_server.py               # studio passthrough + validation test
```

**Structure Decision**: Escalation is a sibling module of the engine
(`agency_cli/escalation.py`), not a change to the mission loop's shape — `cli_engine.py`
keeps route → execute → synthesize → inspect and only swaps the *inside* of one department
execution behind a default-`None` parameter, mirroring how `asset_clause` /
`persona_doctrine` / checkpoint hooks landed (the established additive pattern).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Product default-ON at `runner_bridge.run` (Principle X prefers default-off hooks) | Clarified decision (session 2026-07-03): the army must play out of the box; the brick's done-condition is a *real* mission invoking specialists without special flags | Pure opt-in (library default-None everywhere) was rejected in clarification: it makes the headline capability invisible by default; Principle X is still honored at the library boundary (`run_mission_cli(escalation=None)` ⇒ byte-identical, regression-tested) with an explicit user opt-out above it |
| Virtual officers for commander-only departments (comms, data, ops, people, tech) | Those armies ship no `officer-*.md` files — their phases live inside the commander doctrine; SC-004 requires comms to field ≥1 officer | Authoring new officer agent files was rejected: the payload is a vendored snapshot (sync would overwrite), and the spec's assumption "payload is the source of the army — this feature does not author new specialists" forbids it |
