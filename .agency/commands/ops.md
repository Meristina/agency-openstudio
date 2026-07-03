---
description: Deploy the ops-kit commander on this mission (process, PMO, procurement B2G, EU compliance, risk)
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.ops — Ops Department (commander_ops)

**Constitution check:** `.agency/memory/constitution.md` (Art. I sourcing, Art. II
ethics, Art. IV sovereignty, Art. VI routing, Art. VII pipeline, Art. X scope).
`$MISSION` = `$ARGUMENTS`.

## Do

1. **Read in**: `$MISSION/dossier.md` — goal, context, framing assumptions, and all
   upstream `dept_outputs` (finance outputs if present — ops evaluates operational
   viability and regulatory fit, not commercial strategy).
   Also read `agents/_shared-ops.md` for this department's shared operating doctrine.
   If `AK_JURISDICTION` is set (eu/us/fr), read `agents/_shared-{AK_JURISDICTION}.md`
   for the applicable regulatory framework (NIS2/AI Act/DORA/CSRD for EU; NIST/SOC2 for US;
   ANSSI/CCP for FR) and pass it as context in step 3.

2. **Guard**: if `ops` is not in the dossier's `route`, do not proceed — note the
   misroute in the dossier and stop. If ops-kit is not installed, record the gap
   (`dept_outputs.ops: not_installed`) and stop — never fabricate its output (Art. I).

3. **Delegate to the `commander_ops` subagent** (Agent tool — runs elite grade):
   pass the goal **and** the accumulated `dept_outputs` as context (Art. VII). Let the
   ops commander run its **full internal lifecycle under its own doctrine** (Art. IV):
   process optimisation, PMO, procurement B2G, EU regulatory compliance (NIS2, AI Act,
   DORA ICT), risk mapping, lean/VSM, BCP — whatever the department's constitution
   prescribes. Do **not** reach inside its sequencing, short-circuit its quality gates,
   or rewrite its deliverable.

4. **Capture**: record the full ops deliverable into `dept_outputs.ops` in the dossier.

5. **Write out** — update `$MISSION/dossier.md`:
   - Append `dept_outputs.ops` with the full deliverable.
   - Append key ops decisions and sources to Decisions + Sources sections.
   - Flag any regulatory compliance items (NIS2, AI Act, DORA) under Open to verify.

## Done when
`$MISSION/dossier.md` has `dept_outputs.ops` with the full ops deliverable, and the
ops commander's own internal gates passed (Art. IV + Art. IX).
Mirror the user's language.
