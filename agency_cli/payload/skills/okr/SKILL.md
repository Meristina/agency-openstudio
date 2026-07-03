---
name: okr
description: >-
  Guides product and strategy teams through writing, calibrating, and reviewing
  Objectives and Key Results using Grove's original design intent. Use when
  setting quarterly or annual goals, auditing existing OKRs for failure modes,
  or distinguishing OKRs from KPIs. Produces a labeled OKR block with a 0.6–0.7
  attainment target, explicit failure-mode audit, and cited sources.
---

# Skill — Objectives and Key Results (OKR)

OKR is a goal-setting framework originated by Andrew Grove at Intel in the 1970s,
formalized in his book High Output Management (1983), and introduced to Google by
John Doerr in 1999 as documented in Measure What Matters (2018). The method pairs
an Objective — a qualitative, inspirational statement of direction — with Key Results,
which are quantitative, time-bound measures of progress toward that objective. Its
defining design principle, frequently violated in practice, is the decoupling of OKR
attainment scores from compensation and performance reviews; when that coupling exists,
rational sandbagging becomes the dominant equilibrium and the framework collapses into
a negotiation game. The 0.6–0.7 attainment norm is not a consolation prize — a score
of 1.0 is a diagnostic signal that the objective was set too conservatively.

> **Doctrine:** Cite Grove (1983) for the MBO-to-OKR lineage and the compensation-decoupling
> principle. Cite Doerr (2018) for the 0.6–0.7 scoring norm and the four failure modes.
> Cite Google OKR practice for structural implementation patterns. Never cite "50% of
> features are never used," NPS as a sole growth driver, or story points as productivity
> signals. Never invent a quote, statistic, or benchmark — research every external fact
> and cite it. Label every output block explicitly as OKR (not KPI) and state the
> 0.6–0.7 norm as a design target, not a post-hoc interpretation.

## Procedure

1. **Establish context and scope.** Identify the team level (company, department, squad,
   individual), the planning horizon (annual, quarterly), and the business stage. Clarify
   whether the request is to write new OKRs, audit existing ones, or convert from another
   goal-setting format. Confirm the parent objective one level up so lower-level OKRs
   can be evaluated for cascading conformity — the third canonical failure mode.

2. **Separate OKRs from KPIs.** Before writing a single line, audit the user's existing
   goal vocabulary for conflation. OKRs are hypothesis-driven improvement targets where
   60–70% attainment signals appropriate ambition (Doerr, 2018). KPIs are operational
   health indicators that must remain within a defined range — uptime, support SLA,
   error rate. A KPI that drops is not a failed OKR; it is an operational alert.
   Conflating the two causes teams to sandbag rationally and causes executives to misread
   partial attainment as failure. Label every output as OKR or KPI explicitly.

3. **Write the Objective.** Draft a qualitative, motivating statement that describes
   the desired state at period end. It should pass the "pub test" — could it appear on
   a company all-hands slide without embarrassment? An objective is not a task list or
   a project name. It names the direction, not the work. Grove's formulation: the
   objective answers "Where do I want to go?" (High Output Management, 1983).

4. **Write Key Results.** For each Objective, draft 2–5 Key Results. Each KR must be
   quantitative, falsifiable, and outcome-oriented — it measures the result of work, not
   the work itself. Tactical OKRs that describe activities ("ship feature X") rather than
   outcomes ("increase 30-day retention from 42% to 55%") are the second canonical failure
   mode (Doerr, 2018). Apply the HEART framework as an input structure where appropriate:
   HEART dimensions (Happiness, Engagement, Adoption, Retention, Task Success) map to
   Objectives; specific signals and measures map to Key Results (Rodden, Hutchinson, Fu —
   Google, 2010).

5. **Calibrate for 0.6–0.7 attainment.** Review each Key Result against the scoring norm.
   If a KR is set such that the team is confident of hitting 1.0 under normal execution,
   the target is too conservative — recalibrate upward. A stretch target means accepting
   that full attainment is unlikely; the design intent is to shift the effort distribution,
   not to manufacture a failure. Doerr (2018) describes a 0.6–0.7 average score as healthy;
   consistent 1.0 scores are a signal to investigate sandbagging.

6. **Audit for the four failure modes.** Run the complete checklist: (1) Too many OKRs —
   more than 3–5 Objectives per level dilutes focus; prune ruthlessly. (2) Tactical OKRs —
   any KR that is an activity, milestone, or output rather than an outcome must be rewritten.
   (3) Cascading conformity — lower-level OKRs that merely restate the level above add no
   signal; they must be rewritten to describe the team's specific contribution. (4)
   Compensation coupling — if the OKRs are linked to bonuses or performance ratings,
   flag this explicitly as a structural defect (Grove, 1983; Doerr, 2018).

7. **Define confidence and check-in cadence.** Assign a starting confidence score (0.0–1.0)
   to each Key Result at the beginning of the period. Establish a weekly or biweekly
   check-in rhythm where teams update scores and surface blockers. Score movement — not
   just the final score — is the primary management signal. A KR that moves from 0.3 to
   0.8 over a quarter tells a different story than one that sits at 0.8 throughout.

8. **Produce the output block and cite all sources.** Format the result using the output
   template below. Label each item as OKR or KPI. State the 0.6–0.7 norm explicitly in
   the calibration field. End with a SOURCES section that cites every external fact;
   nothing in the block may be invented or uncited.

## Output format

```
OKR BLOCK — <product / context>
Context detected: <B2B/B2C · sector · stage>
Planning horizon: <Q[N] YYYY | Annual YYYY>
Team level: <Company | Department | Squad | Individual>

INSTRUMENT CLASSIFICATION
  Type: OKR  [not KPI — see calibration norm below]
  Attainment norm: 0.6–0.7 target; 1.0 = objective was too conservative (Doerr, 2018)
  Compensation coupling: <Decoupled [recommended] | Coupled [structural defect — flag]>

OBJECTIVE
  [O1] <Qualitative, inspirational statement of direction>

KEY RESULTS
  [KR1] <Quantitative outcome — baseline → target>   Starting confidence: 0._
  [KR2] <Quantitative outcome — baseline → target>   Starting confidence: 0._
  [KR3] <Quantitative outcome — baseline → target>   Starting confidence: 0._
  [KR4] (optional) <Quantitative outcome>            Starting confidence: 0._
  [KR5] (optional) <Quantitative outcome>            Starting confidence: 0._

FAILURE MODE AUDIT
  (1) Volume: <N Objectives at this level — [OK / PRUNE: reason]>
  (2) Tactical KRs: <Any activity-not-outcome KRs? [None found / Flag: KRn reason]>
  (3) Cascading conformity: <Do KRs merely restate parent? [No / Flag: reason]>
  (4) Compensation coupling: <[Decoupled / Coupled — structural defect]>

OKR vs KPI DISTINCTION
  OKRs (this block): hypothesis-driven improvement targets; 60–70% attainment = healthy
  KPIs (separate): operational health indicators that must stay in range
  Items reclassified as KPI: <None | list items moved>

HEART MAPPING (if applicable — Rodden et al., Google 2010)
  Happiness →  <Objective or KR]>
  Engagement → <Objective or KR>
  Adoption →   <Objective or KR>
  Retention →  <Objective or KR>
  Task Success → <Objective or KR>

CHECK-IN CADENCE
  Frequency: <Weekly / Biweekly>
  Score update owner: <Role>
  Escalation trigger: <KR confidence drops below 0.3 for 2+ consecutive check-ins>

SO-WHAT / NEXT STEPS
  - <Key risk or dependency to resolve before period start>
  - <Recommended first check-in action>
  - <Handoff if strategy realignment needed: O2 Strategy & Direction officer>

SOURCES (every external fact cited; nothing invented)
  - Grove, Andrew. High Output Management. Random House, 1983.
  - Doerr, John. Measure What Matters. Portfolio/Penguin, 2018.
  - Rodden, K., Hutchinson, H., & Fu, X. "Measuring the User Experience on a Large Scale:
    User-Centered Metrics for Web Applications." Google, CHI 2010.
    https://research.google/pubs/pub36299/
  - [Additional sources as needed — author, title, year, URL or [assumption — verify]]
```
