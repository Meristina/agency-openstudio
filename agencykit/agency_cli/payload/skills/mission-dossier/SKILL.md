---
name: mission-dossier
description: >-
  Maintain the Mission Dossier — the single living-state artifact the commander
  carries from framing to delivery, so context, facts, decisions, and the
  to-verify trail survive every hand-off between officers and the Inspector can
  audit a real record. Use whenever running a multi-phase problem-solving mission:
  read the dossier into each phase's brief, write each phase's output back into it,
  and carry it across control-loop iterations. Not a problem-solving method itself —
  it is the shared memory + audit trail the whole army runs on.
---

# Mission Dossier — Field Manual

A multi-phase mission fails quietly when context leaks between steps: Phase 3
re-asks what Phase 1 already established, an assumption is silently treated as fact,
or the Inspector can't tell what was sourced. The Mission Dossier fixes this — one
living record, owned by the commander, read into every phase and written back after
every phase.

## The artifact (schema)

```
MISSION DOSSIER
  problem        : one-line statement (refined as you learn)
  sector         : detected context/domain
  baseline       : measured current state + when + source   (set in Phase 1)
  assumptions    : list — each tagged [confirmed | à vérifier]
  decisions      : per phase — what was chosen + the one-line why
  sources        : numbered; every cited fact points here
  open_to_verify : unresolved à-vérifier items (the live debt)
  hitl           : human go/no-go decision before Phase 4 (+ note)
  verdicts       : Inspector gate/final verdicts + required fixes
  iteration      : loop counter
```

## The rule — read in, write out (every phase)

1. **Read in.** Before a phase runs, assemble its brief *from the dossier*: the
   problem, the relevant prior decisions, the confirmed facts, and the open
   to-verify items it should resolve. Never re-ask what the dossier already holds.
2. **Write out.** After the phase returns, fold its output back: append the
   decision (+ why), new assumptions (tagged), new sources, and any new à-vérifier
   item. Resolve any open item the phase closed.

## Across the control loop

- The dossier is **carried, not reset**, between iterations. On a VETO / fix /
  Phase-5 miss, the re-entered phase reads the *updated* dossier (with the required
  fixes and new readings) — so each loop builds on the last.
- The `iteration` counter rises each loop; stop at `MAX_ITERS` and deliver with the
  `open_to_verify` and residual risk shown.

## Runtime

- **Claude:** the commander keeps the dossier in-context as this structured block,
  passing the relevant slice in each officer's brief and updating it on return.
- **OpenAI:** the dossier is a `dict` carried by the deterministic runner
  `openai/mission.py`, which serializes the relevant slice into each agent call and
  merges the result back.

## Guardrails
- One dossier per mission; the commander owns it — officers receive slices, they
  don't each keep a private copy.
- Every fact in the dossier is sourced or tagged `à vérifier`; `open_to_verify` is
  the live debt the Inspector checks before delivery.
- Carry it across iterations — never restart a loop from a blank state.
- Mirror the user's language in anything surfaced to them.
