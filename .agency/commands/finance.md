---
description: Deploy the finance-kit commander on this mission (business case, pricing, commercial pipeline, reporting)
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.finance — Finance Department (commander_finance)

**Constitution check:** `.agency/memory/constitution.md` (Art. I sourcing, Art. IV
sovereignty, Art. VI routing, Art. VII pipeline, Art. X scope).
`$MISSION` = `$ARGUMENTS`.

## Do

1. **Read in**: `$MISSION/dossier.md` — goal, context, framing assumptions, and all
   upstream `dept_outputs` (product, marketing, and solve outputs if present — finance
   evaluates the upstream strategy financially, it does not re-derive it).
   Also read `agents/_shared-finance.md` for this department's shared operating doctrine.

2. **Guard**: if `finance` is not in the dossier's `route`, do not proceed — note the
   misroute in the dossier and stop. If finance-kit is not installed, record the gap
   (`dept_outputs.finance: not_installed`) and stop — never fabricate its output (Art. I).

3. **Delegate to the `commander_finance` subagent** (Agent tool — runs elite grade):
   pass the goal **and** the accumulated `dept_outputs` as context (Art. VII). Let the
   finance commander run its **full internal lifecycle under its own doctrine** (Art. IV):
   business case, financial modelling, pricing strategy, commercial pipeline, account
   management, and financial reporting — whatever the department's constitution prescribes.
   Do **not** reach inside its sequencing, short-circuit its quality gates, or rewrite
   its deliverable.

4. **Capture**: record the full finance deliverable into `dept_outputs.finance` in the
   dossier.

5. **Write out** — update `$MISSION/dossier.md`:
   - Append `dept_outputs.finance` with the full deliverable.
   - Append key finance decisions and sources to Decisions + Sources sections.
   - Flag any regulatory or compliance items (droit commercial, délais de paiement,
     reporting obligations) under Open to verify.

## Done when
`$MISSION/dossier.md` has `dept_outputs.finance` with the full finance deliverable, and
the finance commander's own internal gates passed (Art. IV + Art. IX).
Mirror the user's language.
