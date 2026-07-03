---
description: Deploy the product-kit commander on this mission (product domain only)
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.product — Product Department (commander_product)

**Constitution check:** `.agency/memory/constitution.md` (Art. I sourcing, Art. IV
sovereignty, Art. VI routing, Art. VII pipeline, Art. X scope).
`$MISSION` = `$ARGUMENTS`.

## Do

1. **Read in**: `$MISSION/dossier.md` — goal, context, framing assumptions, and any
   upstream `dept_outputs` already present (carry forward, do not reset).
   Also read `agents/_shared-product.md` for this department's shared operating doctrine.

2. **Guard**: if `product` is not in the dossier's `route`, do not proceed — note the
   misroute in the dossier and stop. If product-kit is not installed, record the gap
   (`dept_outputs.product: not_installed`) and stop — never fabricate its output (Art. I).

3. **Delegate to the `commander_product` subagent** (Agent tool — runs elite grade):
   pass the goal **and** the accumulated `dept_outputs` as context (Art. VII). Let the
   product commander run its **full internal lifecycle under its own doctrine** (Art. IV):
   discovery, strategy, prioritisation, spec, delivery, measurement — whatever the
   department's constitution prescribes. Do **not** reach inside its sequencing,
   short-circuit its quality gates, or rewrite its deliverable.

4. **Capture**: record the full product deliverable into `dept_outputs.product` in the
   dossier. Include the product commander's summary, key decisions, and sources.

5. **Write out** — update `$MISSION/dossier.md`:
   - Append `dept_outputs.product` with the full deliverable.
   - Append key product decisions and sources to Decisions + Sources sections.

## Done when
`$MISSION/dossier.md` has `dept_outputs.product` with the full product deliverable, and
the product commander's own internal gates passed (Art. IV + Art. IX).
Mirror the user's language.
