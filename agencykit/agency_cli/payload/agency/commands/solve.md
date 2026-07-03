---
description: Deploy the solve-kit commander on this mission (problem-solving domain only)
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.solve — Solve Department (commander_problem_solving)

**Constitution check:** `.agency/memory/constitution.md` (Art. I sourcing, Art. IV
sovereignty, Art. VI routing, Art. VII pipeline, Art. X scope).
`$MISSION` = `$ARGUMENTS`.

## Do

1. **Read in**: `$MISSION/dossier.md` — goal, context, framing assumptions, and all
   upstream `dept_outputs` (`dept_outputs.product` and `dept_outputs.marketing` if
   present — solve applies decision intelligence to the combined picture, not to the
   raw brief alone once upstream departments have run).
   Also read `agents/_shared-solve.md` for this department's shared operating doctrine.

2. **Guard**: if `solve` is not in the dossier's `route`, do not proceed — note the
   misroute in the dossier and stop. If solve-kit is not installed, record the gap
   (`dept_outputs.solve: not_installed`) and stop — never fabricate its output (Art. I).

3. **Delegate to the `commander_problem_solving` subagent** (Agent tool — runs elite grade):
   pass the goal **and** the accumulated `dept_outputs` as context (Art. VII). Let the
   solve commander run its **full internal lifecycle under its own doctrine** (Art. IV):
   problem framing, root-cause analysis, solution design, decision intelligence —
   whatever the department's constitution prescribes. Do **not** reach inside its
   sequencing, short-circuit its quality gates, or rewrite its deliverable.

4. **Capture**: record the full solve deliverable into `dept_outputs.solve` in the
   dossier.

5. **Write out** — update `$MISSION/dossier.md`:
   - Append `dept_outputs.solve` with the full deliverable.
   - Append key solve decisions and sources to Decisions + Sources sections.
   - Flag any `[ASSUMPTION]` or `à vérifier` items from the solve deliverable under
     Open to verify.

## Done when
`$MISSION/dossier.md` has `dept_outputs.solve` with the full solve deliverable, and the
solve commander's own internal gates passed (Art. IV + Art. IX).
Mirror the user's language.
