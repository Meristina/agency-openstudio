---
description: Deploy the marketing-kit commander on this mission (marketing domain only)
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.marketing — Marketing Department (commander_marketing)

**Constitution check:** `.agency/memory/constitution.md` (Art. I sourcing, Art. II
ethics, Art. IV sovereignty, Art. VI routing, Art. VII pipeline, Art. X scope).
`$MISSION` = `$ARGUMENTS`.

## Do

1. **Read in**: `$MISSION/dossier.md` — goal, context, framing assumptions, and all
   upstream `dept_outputs` (especially `dept_outputs.product` if present — marketing
   builds on product's truth, it does not re-derive the product strategy).
   Also read `agents/_shared-marketing.md` for this department's shared operating doctrine.

2. **Guard**: if `marketing` is not in the dossier's `route`, do not proceed — note the
   misroute in the dossier and stop. If marketing-kit is not installed, record the gap
   (`dept_outputs.marketing: not_installed`) and stop — never fabricate its output (Art. I).

3. **Delegate to the `commander_marketing` subagent** (Agent tool — runs elite grade):
   pass the goal **and** the accumulated `dept_outputs` as context (Art. VII). Let the
   marketing commander run its **full internal lifecycle under its own doctrine** (Art. IV):
   research, positioning, content, campaigns, analytics — whatever the department's
   constitution prescribes. Do **not** reach inside its sequencing, short-circuit its
   quality gates, or rewrite its deliverable.
   **Dark-pattern guard (Art. II):** do not instruct the marketing commander toward dark
   patterns (forced continuity, confirm-shaming, hidden costs, manufactured urgency,
   fake social proof). If its output contains such patterns, flag them and send it back.

4. **Capture**: record the full marketing deliverable into `dept_outputs.marketing` in
   the dossier.

5. **Write out** — update `$MISSION/dossier.md`:
   - Append `dept_outputs.marketing` with the full deliverable.
   - Append key marketing decisions and sources to Decisions + Sources sections.

## Done when
`$MISSION/dossier.md` has `dept_outputs.marketing` with the full marketing deliverable,
and the marketing commander's own internal gates passed (Art. IV + Art. IX).
Mirror the user's language.
