---
description: Deploy the people-kit commander on this mission (org design, talent, L&D, performance, culture)
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.people — People Department (commander_people)

**Constitution check:** `.agency/memory/constitution.md` (Art. I sourcing, Art. II
ethics, Art. IV sovereignty, Art. VI routing, Art. VII pipeline, Art. X scope).
`$MISSION` = `$ARGUMENTS`.

## Do

1. **Read in**: `$MISSION/dossier.md` — goal, context, framing assumptions, and all
   upstream `dept_outputs` (product and tech outputs if present — people org design
   follows the product and tech architecture decisions, not the reverse).
   Also read `agents/_shared-people.md` for this department's shared operating doctrine.
   If `AK_JURISDICTION` is set (eu/us/fr), read `agents/_shared-{AK_JURISDICTION}.md`
   for the applicable employment law context (EU Directives/pay transparency for EU;
   NLRA/FLSA/EEOC for US; Code du travail/CSE for FR) and pass it as context in step 3.

2. **Guard**: if `people` is not in the dossier's `route`, do not proceed — note the
   misroute in the dossier and stop. If people-kit is not installed, record the gap
   (`dept_outputs.people: not_installed`) and stop — never fabricate its output (Art. I).

3. **Delegate to the `commander_people` subagent** (Agent tool — runs elite grade):
   pass the goal **and** the accumulated `dept_outputs` as context (Art. VII). Let the
   people commander run its **full internal lifecycle under its own doctrine** (Art. IV):
   org design, talent acquisition, L&D, performance & compensation, pay equity, DEI,
   culture, people analytics — whatever the department's constitution prescribes. Do
   **not** reach inside its sequencing, short-circuit its quality gates, or rewrite its
   deliverable.

4. **Capture**: record the full people deliverable into `dept_outputs.people` in the
   dossier.

5. **Write out** — update `$MISSION/dossier.md`:
   - Append `dept_outputs.people` with the full deliverable.
   - Append key people decisions and sources to Decisions + Sources sections.
   - Flag any labour law, pay equity, or DEI compliance items under Open to verify.

## Done when
`$MISSION/dossier.md` has `dept_outputs.people` with the full people deliverable, and
the people commander's own internal gates passed (Art. IV + Art. IX).
Mirror the user's language.
