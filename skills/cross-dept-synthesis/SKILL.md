---
name: cross-dept-synthesis
description: >-
  Combine the outputs of multiple deployed departments (solve, product, marketing, finance,
  comms, data, ops, people, tech) into a single coherent cross-department deliverable —
  one agency voice, not a stack of reports. Resolves overlaps, surfaces contradictions, traces every cross-department
  claim to its source department, and flags open decisions for the human. Used by the
  agency commander in Phase 2 (Synthesize) of every multi-department mission.
---

# Cross-Department Synthesis — Field Manual

Three individually correct department deliverables can still contradict each other,
leave handoffs orphaned, or read as three separate documents stapled together.
Cross-department synthesis is the agency's Phase 2 task: combining `dept_outputs`
into one coherent deliverable that speaks with a single agency voice.

## When to use

Run after **all routed departments have completed** and their deliverables are recorded
in `dept_outputs`. Synthesis is a Phase 2 task — it does not run mid-execution between
departments; it runs once, after the last department finishes.

## Step 1 — Inventory the outputs

Read the full dossier: goal, route, all `dept_outputs`. For each deployed department,
identify:
- The **core claim** (strategy, positioning, decision, solution, plan — the load-bearing
  output of that department).
- The **key assumptions** it made that downstream departments may have acted on.
- The **metrics and targets** it set.
- The **constraints** it declared.

## Step 2 — Map overlaps

Find every topic that more than one department touched. Common overlap zones:
- **Target customer** — product defined the ICP; marketing positioned to whom?
- **Value proposition** — product named the core job; marketing named the message?
- **Metrics** — product set the North Star; marketing set campaign KPIs?
- **Timeline / constraints** — product set a deadline; solve's plan lands when?
- **Market / competitive facts** — product cited a TAM; marketing cited the same market?

For each overlap: do the departments agree? If yes, merge into one claim and cite both
source departments. If they use different numbers for the same fact, flag it as a
conflict (do not average or silently pick one — see Step 3).

## Step 3 — Surface contradictions

A contradiction is any case where two departments make **incompatible claims** about the
same thing. Name both sides explicitly; never bury a contradiction in a synthesis.

Common contradiction types:
- **Strategic misalignment** — product builds for one customer; marketing positions to
  another. State both positions; flag as requiring reconciliation.
- **Metric mismatch** — marketing's campaign KPI does not ladder up to the product North
  Star, or contradicts a guardrail. Name the mismatch; name which metric is authoritative
  or that it must be resolved.
- **Conflicting facts** — two departments cite different figures for the same data point.
  Flag the conflict; do not fabricate a single "correct" number (Art. I).
- **Cross-constraint contradiction** — a constraint set by one department (pricing model,
  privacy stance, timeline, budget ceiling) is violated by another's plan. Name both the
  constraint and the violation; name which department declared the constraint and which
  one broke it.

Contradictions go into the deliverable's **Surfaced tensions** section — they are either
resolved with explicit reasoning or escalated as **open decisions for the human**.

## Step 4 — Trace handoffs

Trace the full chain: **discover → position → deliver**. For each stage:
- Is there an output that nothing downstream consumed? → **Orphaned output** — flag it.
- Is there an input that nothing upstream produced? → **Orphaned input / gap** — flag it.

Common handoff gaps:
- A positioning with no campaign to carry it (marketing deliverable, no execution plan).
- A spec with no delivery plan (product deliverable, no solve implementation path).
- A North Star with no instrumentation plan.
- A solve action plan whose owners or resources were never established by upstream.

## Step 5 — Draft the synthesis

Write the combined deliverable with these sections:

**Executive summary (1 paragraph)**
One agency voice. What was decided, what was produced, what is the recommended next step.
Every claim is traceable to a source department (cite inline: "per the product department…",
"marketing's analysis shows…", "the solve department recommends…").

**Department contributions**
One section per deployed department: what it produced and the key decisions it made.
Blank / "not routed" / "not installed" for absent departments — disclosed, not hidden.

**Reconciled overlaps**
Where two or more departments touched the same topic and agreed — merged claim, both
departments cited as sources.

**Surfaced tensions**
Where departments disagreed or set conflicting constraints. Each tension names both sides
with the original claims quoted. Each is either resolved (reasoning shown) or escalated.

**Open decisions for the human**
Anything requiring human authority before real-world execution — budget, launch date,
legal sign-off, architectural trade-off, unresolved strategic tension. The agency hands
the decision-ready package; the human acts. (Art. X)

**Gaps and not-installed departments**
Any department that was routed but not installed, or any handoff that has no owner.

## Step 6 — Write out

Record the synthesis in `$MISSION/dossier.md` → `synthesis`. Fill the corresponding
sections of `$MISSION/deliverable.md`. Then hand to `/agency.inspect` (FINAL mode).

## Guardrails

- **One voice, not a stack.** The deliverable reads as the agency speaking — not as
  "product says X, then marketing says Y, then solve says Z." Integrate; don't staple.
- **Both sides on every contradiction.** A finding that names only one department's
  position is incomplete. Always cite the other side.
- **Source every shared fact.** A fact cited in two departments must be identical and
  double-cited. A discrepancy between two citations of the same data point is a conflict,
  not a synthesis (Art. I).
- **Escalate, don't resolve by fiat.** If a contradiction requires a strategic call the
  agency cannot make from the evidence, escalate it as an open decision — do not pick
  a side and present it as consensus.
- **Disclose all gaps.** A missing department or orphaned handoff is always named
  explicitly. Silent omission is not allowed (Art. I).
- Mirror the user's language (Art. III).
