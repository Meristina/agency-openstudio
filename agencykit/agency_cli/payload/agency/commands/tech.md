---
description: Deploy the tech-kit commander on this mission (architecture, DevOps, security, engineering excellence)
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.tech — Tech Department (commander_tech)

**Constitution check:** `.agency/memory/constitution.md` (Art. I sourcing, Art. II
ethics, Art. IV sovereignty, Art. VI routing, Art. VII pipeline, Art. X scope).
`$MISSION` = `$ARGUMENTS`.

## Do

1. **Read in**: `$MISSION/dossier.md` — goal, context, framing assumptions, and all
   upstream `dept_outputs` (product spec if present — tech architecture serves the
   product requirements, not the other way around).
   Also read `agents/_shared-tech.md` for this department's shared operating doctrine.
   If `AK_JURISDICTION` is set (eu/us/fr), read `agents/_shared-{AK_JURISDICTION}.md`
   for the applicable security/data-residency requirements (NIS2/GDPR/AI Act for EU;
   NIST CSF/SOC2/SEC cyber for US; ANSSI/SecNumCloud for FR) and pass it as context in step 3.

2. **Guard**: if `tech` is not in the dossier's `route`, do not proceed — note the
   misroute in the dossier and stop. If tech-kit is not installed, record the gap
   (`dept_outputs.tech: not_installed`) and stop — never fabricate its output (Art. I).

3. **Delegate to the `commander_tech` subagent** (Agent tool — runs elite grade):
   pass the goal **and** the accumulated `dept_outputs` as context (Art. VII). Let the
   tech commander run its **full internal lifecycle under its own doctrine** (Art. IV):
   software architecture (C4, ADR), DevOps/IaC, security (OWASP, SOC2, zero trust,
   threat modeling), engineering excellence, build-vs-buy, DORA metrics, FinOps —
   whatever the department's constitution prescribes. Do **not** reach inside its
   sequencing, short-circuit its quality gates, or rewrite its deliverable.

4. **Capture**: record the full tech deliverable into `dept_outputs.tech` in the dossier.

5. **Write out** — update `$MISSION/dossier.md`:
   - Append `dept_outputs.tech` with the full deliverable.
   - Append key tech decisions and sources to Decisions + Sources sections.
   - Flag any security, compliance (SOC2, cloud), or architecture risk items under
     Open to verify.

## Done when
`$MISSION/dossier.md` has `dept_outputs.tech` with the full tech deliverable, and the
tech commander's own internal gates passed (Art. IV + Art. IX).
Mirror the user's language.
