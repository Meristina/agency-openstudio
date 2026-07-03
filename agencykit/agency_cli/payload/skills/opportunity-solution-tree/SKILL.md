---
name: opportunity-solution-tree
description: >-
  Builds a four-level Opportunity Solution Tree (OST) for a product team: desired outcome →
  opportunity nodes → solution leaves → assumption tests. Use it when a team needs to move
  from a business metric to a prioritised, testable set of experiments without jumping to
  solutions prematurely. Produces a structured tree with hypothesis taxonomy and a ranked
  test escalation ladder.
---

# Skill — Opportunity Solution Tree

The Opportunity Solution Tree is a visual problem-structuring method developed by Teresa Torres
(Product Talk, *Continuous Discovery Habits*, 2021) to align product teams around a single
desired outcome and systematically surface the user opportunities that, if addressed, would
move that outcome. The tree enforces a strict four-level hierarchy — desired outcome,
opportunities, solutions, assumption tests — that prevents the most common product failure mode:
jumping to solutions before validating the problem. Unlike backlog-driven planning, OST
is outcome-first and structurally prevents teams from prioritising a solution before naming the
specific opportunity it addresses and the outcome metric that opportunity would move.

> **Doctrine:** Cite Torres directly for OST mechanics; cite Tony Ulwick (Strategyn) and Bob
> Moesta (The ReWired Group) for upstream JTBD and ODI work that feeds the opportunity nodes.
> Never cite "50% of features are never used" as a motivating statistic without a primary source.
> Never treat NPS as a desired outcome — it is a lagging satisfaction indicator, not an input
> metric. The OST desired outcome must be a business metric used as a directional compass, not
> a fixed numeric target; treating it as a hard target corrupts prioritisation.
> Research every external fact; flag anything unverified as [assumption — verify].

## Procedure
1. **Confirm the JTBD→ODI→OST pipeline entry point.** OST is the third stage of a mandatory
   sequential pipeline (Torres, 2021; Ulwick, *JTBD Theory*, Strategyn). Before building the
   tree, verify that JTBD timeline interviews (Moesta/The ReWired Group — 4-forces diagram:
   push, pull, anxiety, habit) and ODI outcome statements (Ulwick — format: direction + metric
   + object + context; opportunity score = importance + max(importance − satisfaction, 0)) have
   been completed. If they have not, flag the gap; OST opportunity nodes sourced from team
   assumptions rather than user discovery are structurally invalid.

2. **Define the desired outcome (Level 1).** Identify a single business metric that the team
   is responsible for moving directionally — e.g. weekly active retention, trial-to-paid
   conversion rate, or time-to-value for new users. Per Torres (2021): the desired outcome is
   a direction, not a target. Record the metric name, current baseline, and how it is measured.
   Flag any outcome that is an output metric (revenue, NPS) rather than an input metric as a
   risk; the team should own a metric they can influence through product behaviour, not a
   lagging financial result.

3. **Map opportunity nodes from user discovery (Level 2).** Populate the second level
   exclusively from user research — interviews, contextual observation, diary studies, or ODI
   outcome statements. Each opportunity node must describe a specific gap between what users
   need and what the current product delivers. Format: "[User segment] struggles to [verb +
   object] when [context]." Do not allow team-invented opportunities; if research is
   insufficient, stop and prescribe a discovery sprint before proceeding. Per Torres (2021),
   the minimum viable discovery cadence is one user interview per week per team, enabled by
   automated recruitment pipelines (Calendly, Respondent).

4. **Sub-divide opportunities into sub-opportunities (Level 2, depth).** Large opportunity
   nodes must be broken into more specific child nodes until each leaf is actionable — narrow
   enough that a single solution could plausibly address it. Use the MECE principle
   (McKinsey/BCG): child nodes must be mutually exclusive and collectively exhaustive under
   their parent. Identify which sub-opportunity, if addressed, would most move the desired
   outcome; this is the target opportunity for the current discovery cycle.

5. **Generate solution leaves against the target opportunity (Level 3).** Map product ideas
   1-to-many onto the selected opportunity node. Each solution must address the same
   opportunity — solutions that address different opportunities belong on different branches.
   Generate a minimum of three solutions per opportunity before evaluating any of them, to
   avoid premature convergence. Do not score or rank solutions before this step is complete.

6. **Identify and classify assumptions using Torres's hypothesis taxonomy (Level 4 prep).**
   For each solution, list the riskiest underlying assumptions. Classify each assumption into
   one of the four types defined by Torres (2021): desirability (do users want this?),
   viability (can the business sustain this?), feasibility (can the team build this?), and
   usability (can users operate this without friction?). Rank assumptions by risk: the riskiest
   assumption is the one that, if false, would invalidate the entire solution.

7. **Design assumption tests on the test escalation ladder (Level 4).** Select the cheapest
   experiment that could falsify the riskiest assumption. Use the escalation ladder defined
   in Torres (2021) and continuous discovery practice: fake door (measure intent before
   building) → smoke test (landing page / waitlist) → concierge (manual service delivery) →
   Wizard of Oz (automated front-end, manual back-end) → data mining (analyse existing
   behavioural data). Never over-invest in a test when a cheaper test can answer the same
   question.

8. **Enforce the continuous discovery rhythm and produce the tree artefact.** Output the
   complete OST as a structured document. Record the current discovery cadence: is the team
   running at minimum one interview per week? If not, flag it as the priority fix before any
   assumption test is designed. The quarterly research sprint is not a substitute for
   continuous discovery (Torres, 2021). End with a SO-WHAT section naming the single
   next experiment and its owner.

## Output format
```
OPPORTUNITY SOLUTION TREE — <product / context>
Context detected: <B2B/B2C · sector · stage>

DESIRED OUTCOME (Level 1)
  Metric:          <metric name>
  Baseline:        <current value>
  Measurement:     <how it is measured>
  Direction:       <increase / decrease / stabilise>
  Metric type:     <input metric / output metric — flag output metrics>

OPPORTUNITY NODES (Level 2)
  Root opportunities (from user discovery only):
    [O1] <gap statement — "[Segment] struggles to [verb + object] when [context]">
      └── [O1a] <sub-opportunity>
      └── [O1b] <sub-opportunity>
    [O2] <gap statement>
      └── [O2a] <sub-opportunity>
  Target opportunity this cycle: <O-code + rationale>

SOLUTION LEAVES (Level 3 — mapped to target opportunity)
  [S1] <solution idea>
  [S2] <solution idea>
  [S3] <solution idea>
  (minimum 3 before evaluation)

ASSUMPTION TESTS (Level 4)
  Top assumption for [S1]:
    Type:        <desirability / viability / feasibility / usability>
    Hypothesis:  <if [action], then [outcome], because [mechanism]>
    Test:        <fake door / smoke test / concierge / Wizard of Oz / data mining>
    Cost:        <time + effort estimate>
    Success criterion: <measurable threshold>
  Top assumption for [S2]:
    [same structure]

DISCOVERY RHYTHM AUDIT
  Current cadence:   <interviews/week/team>
  Recruitment pipe:  <automated (Calendly/Respondent) / manual / none>
  Status:            <on-standard / below-standard (flag)>
  Anti-pattern flag: <quarterly sprint / no recruitment pipeline / team-invented opportunities>

SO-WHAT / NEXT STEPS
  - Run <test type> for <solution> by <date / sprint> — owner: <role>
  - If test invalidates <assumption>, pivot to <alternative solution or sub-opportunity>
  - Next interview scheduled: <date or "not scheduled — fix this first">

SOURCES (every external fact cited; nothing invented)
  - Teresa Torres, Continuous Discovery Habits, Product Talk (2021) — https://www.producttalk.org
  - Tony Ulwick, Jobs to Be Done: Theory to Practice, Strategyn (2016) — https://strategyn.com
  - Bob Moesta, The ReWired Group — 4-forces diagram (push/pull/anxiety/habit) [assumption — verify URL]
```
