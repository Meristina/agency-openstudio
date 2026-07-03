---
name: tech-debt-balance
description: >-
  Classifies accumulated technical debt using Toyota's Muda/Muri/Mura taxonomy,
  surfaces executive-facing justification through DORA metrics (Forsgren, Humble,
  Kim — Accelerate, 2018), and ring-fences remediation budget as Scaling Work
  within the Reforge five-work-types model. Use when a team needs to make the
  cost of debt legible to cross-functional stakeholders, build a defensible
  business case for remediation, and protect that capacity from extraction into
  Feature Work sprints. Produces a classified debt register, DORA signal readout,
  VSM-based throughput cost, and a budget protection directive.
---

# Skill — Tech Debt Balance (Muda/Muri/Mura + DORA + Scaling Work)

Technical debt is not a monolithic concept — collapsing it into a single label
obscures distinct failure modes that require distinct remediation strategies.
This skill applies Toyota's three-waste taxonomy from the Toyota Production System
(TPS) — Muda (non-value-adding waste), Muri (unsustainable overload), and Mura
(uneven flow causing stop-start throughput degradation) — to classify debt in
terms legible to product, engineering, and finance stakeholders simultaneously.
DORA metrics from Forsgren, Humble, and Kim (Accelerate, 2018; State of DevOps
Report, 2024) provide the executive-facing signal layer: Change Failure Rate and
Lead Time for Changes are empirically validated lagging indicators of accumulated
debt burden, derived from research across more than 33,000 practitioners over seven
years. Value Stream Mapping (VSM) from the Lean Enterprise Institute — grounded in
Toyota TPS, Gene Kim's The Phoenix Project (2013), and Eliyahu Goldratt's Theory
of Constraints (The Goal, 1984) — quantifies debt cost in throughput terms using
Process Cycle Efficiency (PCE). The most operationally critical output is the
budget protection directive: debt remediation must be categorized as Scaling Work —
one of Casey Winters' five distinct product work types (Reforge) — and ring-fenced
from extraction into Feature Work or Growth Work sprints.

> **Doctrine:** Cite Toyota TPS for Muda/Muri/Mura. Cite Forsgren, Humble, Kim
> (Accelerate, 2018) and the State of DevOps Report (2024) for DORA metrics. Cite
> the Lean Enterprise Institute and Gene Kim (The Phoenix Project, 2013) for VSM
> and PCE. Cite Goldratt (The Goal, 1984) for Theory of Constraints. Cite Casey
> Winters and Fareed Mosavat (Reforge) for the five work types and the PMF Treadmill
> concept. Never cite "50% of features are never used," NPS as a sole growth driver,
> story points as productivity signals, or the 40% PMF Ellis threshold as a universal
> law. Never invent a quote, statistic, or benchmark — research every external fact
> and cite it. Unknown values → "unknown" or "[assumption — verify]".

## Procedure

1. **Classify debt by waste type (Muda/Muri/Mura).** For each item in the debt
   register — or for a free-text description of pain points — assign one of three
   Toyota TPS categories. Muda: work that consumes resources without producing
   customer value (e.g., dead code paths, redundant data pipelines, manual steps
   that could be automated). Muri: work that exceeds sustainable system or human
   capacity (e.g., on-call engineers firefighting incidents every week, services
   running above safe load thresholds with no headroom). Mura: uneven flow that
   creates stop-start throughput degradation (e.g., batch deployments that
   concentrate risk, manual release gates that queue work, test environments shared
   across teams with unpredictable availability). One debt item may carry multiple
   types; classify the dominant failure mode and note secondary effects. This
   taxonomy makes the remediation strategy visible: Muda → eliminate; Muri →
   redistribute or de-risk; Mura → smooth and automate flow.

2. **Map DORA metrics as executive lagging indicators.** Measure or estimate the
   team's current performance on the five DORA metrics: Deploy Frequency, Lead Time
   for Changes, Change Failure Rate, Mean Time to Restore (MTTR), and Rework Rate
   (added in the State of DevOps Report, 2024 as a fifth signal). Forsgren, Humble,
   and Kim (Accelerate, 2018) established that Change Failure Rate and Lead Time for
   Changes are the two metrics most predictive of accumulated debt burden — high CFR
   indicates fragility introduced by deferred quality work; high LTC indicates flow
   blockage caused by unresolved dependencies and manual gates. Map each classified
   debt item to the DORA metric it degrades. This translation makes debt cost legible
   to executives who do not read sprint backlogs: a 22% Change Failure Rate is a
   business risk statement, not an engineering complaint.

3. **Run a Value Stream Map (VSM) to quantify throughput cost.** Trace the end-to-end
   delivery flow from customer request to production. Identify all value-adding steps
   (steps that directly transform the work toward the customer outcome) and all
   non-value-adding wait steps (queue time, handoff delays, environment wait, manual
   approval gates). Calculate Process Cycle Efficiency: PCE = total value-adding time
   / total lead time. The Lean Enterprise Institute's benchmark finding in software
   delivery is that PCE is typically below 15%, meaning more than 85% of total lead
   time is non-value-adding wait. Each non-value-adding step should be traced to a
   Muda, Muri, or Mura debt item. This step converts debt from a code-quality
   conversation into a throughput and cost conversation — the language of the CFO.

4. **Identify the constraint (Theory of Constraints).** Following Goldratt (The Goal,
   1984), find the single bottleneck that most limits throughput. In software delivery
   this is typically a shared environment, a manual approval gate, a central
   infrastructure team, or a monolith with high merge conflict rate. Debt remediation
   should be sequenced to unblock the constraint first — improving non-constraint steps
   before the constraint is resolved does not increase system throughput. Name the
   constraint explicitly in the output.

5. **Build the executive business case.** Translate VSM waste and DORA degradation
   into business terms: estimated engineering time lost per sprint to rework (from
   Rework Rate), estimated revenue or feature velocity impact from Lead Time for
   Changes exceeding elite thresholds (Forsgren et al., Accelerate, 2018 define elite
   as LTC under one hour), and incident cost from MTTR. If the team is in the "low"
   or "medium" DORA performance band, cite the Accelerate research: elite performers
   deploy 208x more frequently, recover from incidents 2,604x faster, and have
   a change failure rate 7x lower than low performers. Use these multipliers as
   directional evidence, not precise predictions for this team.

6. **Categorize remediation as Scaling Work and ring-fence the budget.** Apply the
   Reforge five-work-types model (Casey Winters, Reforge): Feature Work (new
   customer-facing capabilities), Growth Work (acquisition, activation, retention
   experiments), Scaling Work (infrastructure, reliability, and quality work required
   to maintain PMF at higher volume or complexity), Innovation Work (exploratory bets),
   and PMF Work (repositioning or market pivot). Debt remediation is Scaling Work by
   definition — it is not optional maintenance, it is the mechanism that prevents
   PMF decay as the system scales. Apply Doctrine #4: the O3 budget must include an
   explicit Scaling Work ring-fence. Winters and Mosavat (Reforge) define the PMF
   Treadmill as the dynamic where teams must continuously invest in Scaling Work to
   maintain their current PMF level — without it, the product degrades in quality and
   speed relative to customer expectations even as the feature set grows. The Chegg
   2024 case is the canonical public example: the company's failure to invest
   sufficiently in AI-era Scaling Work caused PMF erosion that was visible in
   subscriber churn before it was visible in revenue. Define a specific percentage of
   sprint capacity as non-negotiable Scaling Work allocation — typically 20–30%
   depending on current debt load — and protect it from extraction.

7. **Prioritize debt items for remediation.** Rank items using three criteria: (a)
   constraint leverage — does remediating this item unblock the identified throughput
   constraint? (b) DORA impact — does it directly reduce Change Failure Rate or Lead
   Time for Changes? (c) Muri risk — does it address an overload condition creating
   burnout or outage risk? Items scoring high on all three criteria are the first
   allocation target within the Scaling Work budget. Label each item with its
   classification, priority tier, estimated effort, and expected DORA metric impact.

8. **Produce the output block and cite all sources.** Format the output using the
   template below. Every DORA metric cited must reference its source. Every Toyota
   TPS category must be traceable to a concrete team artifact. Every budget
   recommendation must reference the Reforge five-work-types model. End with a
   SOURCES section citing every external fact; nothing in the block may be invented.

## Output format

```
TECH DEBT BALANCE — <product / context>
Context detected: <B2B/B2C · sector · stage>
Team DORA band: <Elite / High / Medium / Low — or "not yet measured">

DEBT CLASSIFICATION (Muda / Muri / Mura)
  [D1] <Debt item name>
    Type: <Muda | Muri | Mura | Muda+Mura (dominant: ...)>
    Description: <What it is, where it lives>
    DORA signal degraded: <CFR | LTC | Deploy Freq | MTTR | Rework Rate>
    Remediation strategy: <Eliminate (Muda) | De-risk / redistribute (Muri) | Smooth flow (Mura)>
    Priority tier: <1 — constraint / 2 — DORA-critical / 3 — backlog>

  [D2] ...
  [D3] ...

DORA SIGNAL READOUT
  Deploy Frequency:        <current value or "unknown"> — Elite benchmark: on-demand (Accelerate, 2018)
  Lead Time for Changes:   <current value or "unknown"> — Elite benchmark: <1 hour (Accelerate, 2018)
  Change Failure Rate:     <current value or "unknown"> — Elite benchmark: 0–15% (Accelerate, 2018)
  Mean Time to Restore:    <current value or "unknown"> — Elite benchmark: <1 hour (Accelerate, 2018)
  Rework Rate:             <current value or "unknown"> — Added as 5th metric (State of DevOps, 2024)
  Overall band:            <Elite / High / Medium / Low>
  Key signal: <Which metric is the strongest indicator of debt burden for this team>

VALUE STREAM MAP (VSM)
  Total lead time (end-to-end): <N days/hours>
  Value-adding time:            <N days/hours>
  Process Cycle Efficiency:     <PCE% — LEI benchmark: <15% typical in software delivery>
  Identified constraint:        <Step or system that is the primary throughput bottleneck>
  Top 3 wait steps (Muda):      <Step, estimated wait, debt item it maps to>

EXECUTIVE BUSINESS CASE
  Engineering time lost to rework per sprint: <N hours or "unknown">
  Estimated feature velocity impact from LTC:  <qualitative or quantitative estimate>
  Incident cost from MTTR:                     <estimate or "unknown">
  Elite-vs-current gap (Accelerate, 2018):    <Deploy 208x more frequently / MTTR 2,604x faster — directional>

BUDGET PROTECTION DIRECTIVE (Reforge — Scaling Work)
  Work type classification: Scaling Work (not Feature Work, not Growth Work)
  Rationale: PMF Treadmill — without Scaling Work investment, PMF erodes as volume and
             complexity scale (Winters & Mosavat, Reforge). Chegg 2024: canonical
             case of PMF degradation from Scaling Work underinvestment.
  Recommended Scaling Work allocation: <20–30% of sprint capacity — adjust by debt load>
  Ring-fence mechanism: <Sprint quota | Separate track | Rolling budget — specify>
  Extraction guard: <Who has authority to override the ring-fence and under what conditions>

SO-WHAT / NEXT STEPS
  - <Highest-priority debt item: why it is the constraint and what unblocking it unlocks>
  - <DORA measurement gaps to close before next planning cycle>
  - <Scaling Work budget proposal for next sprint / quarter>
  - <Handoff if strategy or roadmap realignment needed: O3 Prioritization officer>

SOURCES (every external fact cited; nothing invented)
  - Toyota Motor Corporation. Toyota Production System — Muda, Muri, Mura taxonomy.
    https://global.toyota/en/company/vision-and-philosophy/production-system/ [assumption — verify URL currency]
  - Forsgren, N., Humble, J., & Kim, G. Accelerate: The Science of Lean Software and
    DevOps. IT Revolution Press, 2018.
  - DORA / Google Cloud. State of DevOps Report 2024.
    https://dora.dev/research/2024/dora-report/
  - Lean Enterprise Institute. Value Stream Mapping.
    https://www.lean.org/explore-lean/what-is-value-stream-mapping/
  - Kim, G., Behr, K., & Spafford, G. The Phoenix Project. IT Revolution Press, 2013.
  - Goldratt, E. M., & Cox, J. The Goal: A Process of Ongoing Improvement.
    North River Press, 1984.
  - Winters, C., & Mosavat, F. "The Five Types of Product Work." Reforge.
    https://www.reforge.com/blog/five-types-of-product-work [assumption — verify URL currency]
  - [Additional sources as needed — author, title, year, URL or [assumption — verify]]
```
