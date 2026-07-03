---
name: mission-dossier
description: >-
  Maintain the Cross-Department Mission Dossier — the single living-state artifact
  the agency commander carries from framing to delivery, so goal, route, department
  outputs, synthesis, and the open-to-verify trail survive every hand-off between
  departments and the Inspector can audit a real record. Use whenever running a
  multi-department agency mission: read the dossier into each phase's brief, write
  each phase's output back into it, and carry it across control-loop iterations.
  Not an orchestration method itself — it is the shared memory and audit trail the
  whole agency runs on.
---

# Agency Mission Dossier — Field Manual

A multi-department mission fails quietly when context leaks between stages: the
marketing department re-derives what the product department already established, an
assumption from routing is silently treated as fact, or the Inspector can't tell which
claim came from which department. The Agency Mission Dossier fixes this — one living
record, owned by the commander, read into every phase and written back after every
phase.

## The artifact (schema)

```
AGENCY MISSION DOSSIER
  goal           : one-line mission goal (from $ARGUMENTS, refined in /agency.frame)
  context        : detected sector · stage · constraints  (set in /agency.frame)
  route          : ordered dept list + per-dept rationale  (set in /agency.frame)
  direction_check: GO | REDIRECT | ADJUST + note  (Art. VIII)
  dept_outputs   : one entry per deployed department, full deliverable, versioned
    .product     : full product deliverable or "not_installed" or "not_routed"
    .marketing   : full marketing deliverable or "not_installed" or "not_routed"
    .solve       : full solve deliverable or "not_installed" or "not_routed"
    .finance     : full finance deliverable or "not_installed" or "not_routed"
    .comms       : full comms deliverable or "not_installed" or "not_routed"
    .data        : full data deliverable or "not_installed" or "not_routed"
    .ops         : full ops deliverable or "not_installed" or "not_routed"
    .people      : full people deliverable or "not_installed" or "not_routed"
    .tech        : full tech deliverable or "not_installed" or "not_routed"
  synthesis      : combined cross-department deliverable (one agency voice)
  assumptions    : list — each tagged [ASSUMPTION] | confirmed | à vérifier
  decisions      : per phase — what was chosen + the one-line why
  sources        : numbered; every factual claim cites a real source (Art. I)
  open_to_verify : unresolved items (the live debt the Inspector checks)
  verdicts       : Inspector PASS / PASS WITH FIXES / VETO + required fixes
  iteration      : control-loop counter
```

## The rule — read in, write out (every phase)

1. **Read in.** Before a phase runs, assemble its brief *from the dossier*: the goal,
   the routing decision, the relevant upstream `dept_outputs`, confirmed facts, and the
   open-to-verify items it should resolve. Never re-ask what the dossier already holds.
   Never pass a department its own prior output as the sole context — pass the
   accumulated dossier slice so it sees upstream work.

2. **Write out.** After the phase returns, fold its output back:
   - Append the department deliverable to the relevant `dept_outputs.<dept>` entry.
   - Append decisions (+ why) and new sources to Decisions and Sources.
   - Tag new assumptions `[ASSUMPTION]`; add unresolved items to Open to verify.
   - Record the Inspector verdict in Verdicts.

## Across the control loop

- The dossier is **carried, not reset**, between iterations. On a VETO or
  PASS-WITH-FIXES, the re-entered department reads the updated dossier (with the
  required fixes and the Inspector's findings) — so each loop builds on the last.
- The `iteration` counter rises each loop; stop at `MAX_ITERS = 3` and deliver with
  `open_to_verify` and residual risk explicitly stated.
- On REDIRECT during the direction check, update `route` in the dossier and reclassify
  — do not restart from a blank state.

## Department sovereignty (Art. IV)

Each department receives a **slice** of the dossier (its input context), not
write-access to the whole document. The commander owns the dossier; departments append
their deliverable through the `/agency.<dept>` command, which writes `dept_outputs.<dept>`
and nothing else. A department does not see another department's internal working notes
— only its final deliverable as recorded in `dept_outputs`.

## Runtime

- **Claude (slash commands):** the commander keeps the dossier as `$MISSION/dossier.md`
  on disk, passing the relevant slice in each department command's brief and updating
  the file on return.
- **Headless engine (`agency run`):** the dossier `dict` is built by
  `agency_cli/engines/cli_engine.run_mission_cli`, which drives the chosen CLI engine
  (Claude Code / Codex / Gemini) through route → execute → synthesize → inspect,
  carrying `dept_outputs` forward between phases. No SDK and no API key — each engine
  CLI uses its own authenticated session.

## Guardrails

- One dossier per mission; the commander owns it — departments receive slices, not a
  private copy.
- Every fact in the dossier is sourced or tagged `à vérifier`; `open_to_verify` is the
  live debt the Inspector checks before delivery (Art. I + Art. IX).
- A department listed as `not_installed` or `not_routed` must appear explicitly in the
  dossier — gaps are disclosed, never silently ignored.
- Carry the dossier across iterations — never restart a loop from a blank state.
- Mirror the user's language in anything surfaced to them (Art. III).
