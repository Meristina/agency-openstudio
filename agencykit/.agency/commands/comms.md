---
description: Deploy the comms-kit commander on this mission (communications domain only)
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.comms — Comms Department (commander_comms)

**Constitution check:** `.agency/memory/constitution.md` (Art. I sourcing, Art. II
ethics, Art. IV sovereignty, Art. VI routing, Art. VII pipeline, Art. X scope).
`$MISSION` = `$ARGUMENTS`.

## Do

1. **Read in**: `$MISSION/dossier.md` — goal, context, framing assumptions, and all
   upstream `dept_outputs` (product, marketing, finance outputs if present — comms builds
   on the strategy and narrative already established, does not re-derive them).
   Also read `agents/_shared-comms.md` for this department's shared operating doctrine.
   If `AK_JURISDICTION` is set (eu/us/fr), read `agents/_shared-{AK_JURISDICTION}.md`
   and pass it as regulatory/legal context when delegating in step 3.

2. **Guard**: if `comms` is not in the dossier's `route`, do not proceed — note the
   misroute in the dossier and stop. If comms-kit is not installed, record the gap
   (`dept_outputs.comms: not_installed`) and stop — never fabricate its output (Art. I).

3. **Delegate to the `commander_comms` subagent** (Agent tool — runs elite grade):
   pass the goal **and** the accumulated `dept_outputs` as context (Art. VII). Let the
   comms commander run its **full internal lifecycle under its own doctrine** (Art. IV):
   corporate communications, PR/media, crisis management, public affairs, ESG/CSRD,
   events — whatever the department's constitution prescribes. Do **not** reach inside
   its sequencing, short-circuit its quality gates, or rewrite its deliverable.

4. **Capture**: record the full comms deliverable into `dept_outputs.comms` in the
   dossier.

5. **Write out** — update `$MISSION/dossier.md`:
   - Append `dept_outputs.comms` with the full deliverable.
   - Append key comms decisions and sources to Decisions + Sources sections.
   - Flag any regulatory items (droit de la presse, CSRD, lobbying registry) under
     Open to verify.

## Done when
`$MISSION/dossier.md` has `dept_outputs.comms` with the full comms deliverable, and the
comms commander's own internal gates passed (Art. IV + Art. IX).
Mirror the user's language.
