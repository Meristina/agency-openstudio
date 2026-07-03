# Data Model: The Specialist Army Plays

All structures are plain stdlib types (dataclasses / dicts) — zero runtime dependencies.
Everything here is **additive**: absent when escalation is off, so the off-path dossier,
events, and checkpoints are byte-identical to today.

## EscalationConfig (input)

The single knob threaded `runner_bridge.run` → `run_mission_cli` → `escalation.run_department`.

| Field | Type | Default | Rules |
|---|---|---|---|
| `enabled` | `bool` | `True` | `False` ⇒ department runs exactly as today |
| `budget` | `int` | `6` | Hard cap on escalation subprocess calls per department; `<= 0` ⇒ treated as disabled (FR-006) |

Library boundary: `run_mission_cli(escalation: Optional[EscalationConfig] = None)` —
`None` ⇒ OFF (byte-identical). Product boundary: `runner_bridge.run` constructs the
default (ON) unless the caller opts out. Studio request field:
`{"escalation": {"enabled": bool, "budget": int}}`, types validated, unknown keys rejected.

## SpecialistRoster (derived, per mission)

Built once per mission from `payload/agents/` frontmatter + the curated `DEPT_OFFICERS`
map. Never persisted.

| Field | Type | Notes |
|---|---|---|
| `commanders` | `dict[dept, AgentRef]` | `commander-{dept}.md` (product ⇒ `commander-product`, solve ⇒ `commander-problem-solving`) |
| `officers` | `dict[dept, list[AgentRef]]` | From `DEPT_OFFICERS` (marketing, product, solve, finance); `[]` for commander-only depts |
| `virtual_officers` | `dict[dept, list[PhaseRef]]` | Parsed from the commander doctrine's numbered phase list (comms O1–O6, …) when `officers[dept]` is empty |
| `soldiers` | `list[AgentRef]` | Shared pool (126); compact form only (name + first description sentence) |

**AgentRef**: `{name: str, file: Path, summary: str}` — `name` from frontmatter, `summary`
= first sentence of `description`, truncated ≤ 200 chars.

**PhaseRef**: `{name: str, directive: str, virtual: True}` — e.g.
`{"name": "comms/O6-events", "directive": "O6 Events — stratégie événementielle…"}`.

**Validation**: every `DEPT_OFFICERS` entry must resolve to an existing file (drift-guard
test); a selection naming an unknown specialist is dropped at parse time (never invented).

## Selection (engine output, parsed)

Returned by the selection call as a JSON object; parsed with the tolerant
`_route_via_cli`-style extraction; validated against the roster.

```json
{
  "officers": ["officer-2-strategy", "comms/O6-events"],
  "soldiers": ["soldier-stp", "soldier-positioning"],
  "rationale": {
    "officer-2-strategy": "goal is a positioning decision",
    "soldier-stp": "segment→target→position is the asked method"
  }
}
```

Rules: names not in the roster are dropped; empty/unparseable result ⇒
`{"fallback": "selection-unparseable"}` and doctrine-only execution (FR edge case);
rationale is required per selected name (FR-012) — a missing rationale gets
`"(no rationale returned)"` recorded rather than blocking.

## InvocationRecord (per specialist call)

One entry per escalation subprocess call, appended in execution order.

| Field | Type | Notes |
|---|---|---|
| `role` | `"selection" \| "commander" \| "officer" \| "soldier"` | |
| `name` | `str` | Agent name or virtual phase name |
| `virtual` | `bool` | Only present (True) for virtual officers |
| `task` | `str` | The scoped task given (truncated ≤ 2000 chars in the trace; full text lives in the prompt) |
| `output` | `str` | The returned deliverable (full — departments are sovereign, Art. IV) |
| `est_tokens` | `int` | chars/4 heuristic over (prompt + output), advisory |
| `skipped` | `str?` | `"budget-exhausted"` / `"missing-file"` / `"call-failed"` — mutually exclusive with `output` |

## DeptEscalationTrace (per department, in the dossier)

```json
{
  "budget": 6,
  "consumed": 5,
  "est_tokens": 41230,
  "selection": { "...": "the parsed Selection object or its fallback marker" },
  "invocations": [ "InvocationRecord, execution order" ],
  "no_escalation": "reason string — only when the dept ran doctrine-only"
}
```

Invariants (tested): `consumed == len([i for i in invocations if not i.skipped])`;
`consumed <= budget` (SC-002); `est_tokens == sum(i.est_tokens)`; a department with
`enabled=False`/budget 0 has NO trace entry at all (byte-identical off, SC-003).

## Dossier extension (additive)

```python
dossier = {
    # ... existing keys unchanged (goal, route, dept_outputs, verdicts, iteration, ...)
    "escalation": { "<dept>": DeptEscalationTrace },   # ONLY present when escalation ran
}
```

## Checkpoint extension (additive, version stays 1)

The `"dept"` snapshot gains an optional `escalation` key holding traces of **completed**
departments only. `_validate_resume_state` defaults a missing key to `{}` (old snapshots
resume unchanged). A crash mid-escalation re-runs the department from scratch — the
existing "dept not in dept_outputs ⇒ re-run" invariant is untouched.

## Event extension (additive)

`_emit` gains escalation events, same observational contract (swallow-exceptions):

```python
{"phase": "escalation", "dept": d, "step": "selection|commander|officer|soldier",
 "name": n, "status": "start|done|skipped"}
```

## State transitions (one escalated department)

```
doctrine-ready ─▶ selecting ─▶ commanding ─▶ officer(s) ─▶ soldier(s) ─▶ assembled
      │               │ unparseable ⇒ doctrine-only (fallback recorded)
      │               └ budget hit at ANY arrow ⇒ skip-remaining, assemble what exists
      └ escalation off/zero ⇒ doctrine-only (no trace at all)
Cancel at any boundary ⇒ MissionCancelled (no dossier — existing contract)
```
