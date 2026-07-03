---
description: Deploy the data-kit commander on this mission (data strategy, engineering, analytics, ML/LLMOps)
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.data — Data Department (commander_data)

**Constitution check:** `.agency/memory/constitution.md` (Art. I sourcing, Art. IV
sovereignty, Art. VI routing, Art. VII pipeline, Art. X scope).
`$MISSION` = `$ARGUMENTS`.

## Do

1. **Read in**: `$MISSION/dossier.md` — goal, context, framing assumptions, and all
   upstream `dept_outputs` (product spec if present — data engineering builds on what
   the product requires, tech architecture if present).
   Also read `agents/_shared-data.md` for this department's shared operating doctrine.
   If `AK_JURISDICTION` is set (eu/us/fr), read `agents/_shared-{AK_JURISDICTION}.md`
   for the applicable privacy-engineering and data-residency constraints (GDPR/CCPA/RGPD)
   and pass it as context in step 3.

2. **Guard**: if `data` is not in the dossier's `route`, do not proceed — note the
   misroute in the dossier and stop. If data-kit is not installed, record the gap
   (`dept_outputs.data: not_installed`) and stop — never fabricate its output (Art. I).

3. **Delegate to the `commander_data` subagent** (Agent tool — runs elite grade):
   pass the goal **and** the accumulated `dept_outputs` as context (Art. VII). Let the
   data commander run its **full internal lifecycle under its own doctrine** (Art. IV):
   data strategy, engineering pipelines, analytics/BI, ML/LLMOps, data quality, data
   products — whatever the department's constitution prescribes. Do **not** reach inside
   its sequencing, short-circuit its quality gates, or rewrite its deliverable.

4. **Capture**: record the full data deliverable into `dept_outputs.data` in the dossier.

5. **Write out** — update `$MISSION/dossier.md`:
   - Append `dept_outputs.data` with the full deliverable.
   - Append key data decisions and sources to Decisions + Sources sections.
   - Flag any data governance or privacy items under Open to verify.

## Done when
`$MISSION/dossier.md` has `dept_outputs.data` with the full data deliverable, and the
data commander's own internal gates passed (Art. IV + Art. IX).
Mirror the user's language.
