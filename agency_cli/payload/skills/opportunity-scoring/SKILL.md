---
name: opportunity-scoring
description: >-
  Scores and ranks customer outcome statements using Tony Ulwick's Outcome-Driven
  Innovation (ODI) opportunity formula — importance + max(importance − satisfaction, 0)
  — to surface under-served and over-served outcomes. In B2B contexts, applies the AIM
  Institute multi-role disaggregation standard (economic buyer, technical evaluator, end
  user, procurement). Use when you have a validated set of outcome statements and need a
  defensible, citation-grounded prioritisation map. Produces a ranked opportunity matrix,
  a serving-level heat map, and next-step prescriptions tied to behavioral corroboration.
---

# Skill — ODI Opportunity Scoring

Outcome-Driven Innovation (ODI) opportunity scoring is Tony Ulwick's quantitative method
for translating customer outcome statements into a ranked investment map. Built on 300+
client engagements at Strategyn, the method treats each outcome statement — written in the
four-part syntax of direction + metric + object + context (e.g., "minimize the time needed
to identify at-risk accounts") — as an independent unit of customer need. Respondents rate
each statement on importance (1–10) and satisfaction with current solutions (1–10). The
opportunity score is importance + max(importance − satisfaction, 0): scores above 10 signal
under-served outcomes (prioritise); scores below 5 signal over-served ones (deprioritise
or harvest). The formula intentionally weights importance above satisfaction — an important
but poorly served need represents a larger market opportunity than a moderately important
but well-served one. The result is a prioritisation surface built on customer language, not
on internal feature opinions or satisfaction surveys alone.

> **Doctrine:** Any opportunity score built exclusively on declared preference (survey responses)
> is a hypothesis, not a finding. Behavioral corroboration — cohort retention curves that
> flatten, DAU/MAU above 50%, PQL activation signals (Reforge; OpenView Partners, Blake Bartlett)
> — is required before treating scores above 10 as confirmed investment priorities (Doctrine #3).
> Never cite "50% of features are never used" — untraceable. Never treat a single-respondent
> score in B2B as valid (AIM Institute prohibition). Research every external fact; invent nothing.

## Procedure

1. **Confirm upstream inputs.** Verify that a validated JTBD has been defined and that 50–150
   outcome statements have been elicited using the ODI four-part syntax: direction + metric +
   object + context (Ulwick, "Jobs to Be Done: Theory to Practice," Idea Bite Press, 2016;
   Strategyn, 300+ client engagements). If the outcome statement set is missing or uses
   feature-centric language ("users want a dashboard"), stop and refer to soldier-odi-outcome-mapping
   (O3) to close the elicitation gap. Opportunity scoring on malformed inputs produces a
   malformed priority list — the pipeline is sequential and non-substitutable.

2. **Segment respondents by role (B2B gate).** In B2B contexts, apply the AIM Institute
   New Product Blueprinting standard: disaggregate scoring by buying role — economic buyer,
   technical evaluator, end user, and procurement. Each role has distinct outcome criteria;
   aggregating them masks role-level under-service patterns that drive deal loss (AIM
   Institute, "New Product Blueprinting," Dan Adams, 2008). Single-respondent scoring per
   account is prohibited; minimum 3 respondents per role per segment. In B2C, segment by
   primary user archetype, usage frequency tier, or cohort maturity stage.

3. **Collect importance and satisfaction ratings.** For each outcome statement, survey
   validated respondents on two dimensions: importance (1 = not at all important, 10 =
   extremely important) and satisfaction with current solutions (1 = not at all satisfied,
   10 = extremely satisfied). Use independent scales — do not anchor satisfaction responses
   to a named competitor to avoid priming bias. Minimum viable sample: 30 respondents per
   segment; 100+ preferred for statistical stability on multi-role B2B programmes.

4. **Compute opportunity scores.** For each outcome statement, apply the Ulwick opportunity
   formula: Opportunity = Importance + max(Importance − Satisfaction, 0). Record both
   components alongside the composite score. Under-served threshold: score > 10 (prioritise —
   important and poorly served). Over-served threshold: score < 5 (deprioritise — either
   unimportant or already well served). The 5–10 band is a watch zone: monitor for drift
   but do not mobilise investment without behavioral corroboration.

5. **Disaggregate and cross-tab by role and segment.** Produce role-level opportunity matrices
   (economic buyer, technical evaluator, end user, procurement in B2B; segment tiers in B2C).
   Identify divergence patterns: an outcome that scores > 10 for end users but < 7 for economic
   buyers signals a value-communication gap, not necessarily a product gap. An outcome that
   scores > 10 across all roles is a consensus priority — highest investment confidence.
   Flag any segment where role-level scores conflict materially and prescribe qualitative
   follow-up.

6. **Overlay behavioral corroboration signals.** Treat declared-preference scores as hypotheses
   (Doctrine #3). For each under-served outcome (score > 10), identify the behavioral signal
   that would corroborate or refute it: cohort retention curves that flatten horizontally
   (most resistant to falsification; Casey Winters & Fareed Mosavat, Reforge), DAU/MAU ratio
   above 50%, the power-user curve, organic referral growth without paid amplification, or
   PQL activation milestones (users reaching activation events express revealed preference
   3–5× more predictive than declared intent; Blake Bartlett, OpenView Partners, PLG thesis,
   2016). PQL-to-paid conversion benchmarks: 25–30% vs. MQL-to-paid 5–10% (OpenView
   Partners, PLG Benchmarks [assumption — verify current year figures]). Log each behavioral
   signal as confirmed, pending, or absent.

7. **Produce the ranked opportunity matrix and serving heat map.** Output: (a) a ranked list
   of all outcome statements by opportunity score, annotated with under-served / watch-zone /
   over-served classification, role-level breakdown, and behavioral corroboration status;
   (b) a serving heat map plotting importance on the y-axis and satisfaction on the x-axis
   with opportunity score as bubble size; (c) a role-level divergence table for B2B contexts.
   Every score must carry the survey date — classifications older than 12 months require
   re-survey before investment decisions are made.

8. **Prescribe next steps and hand-offs.** For confirmed under-served outcomes with behavioral
   corroboration: escalate to soldier-opportunity-solution-tree (O3) to map solution options.
   For under-served outcomes lacking behavioral corroboration: design the cheapest test that
   could falsify the declared-preference signal (activation experiment, fake door, usage log
   analysis). For over-served outcomes: flag as harvest or sunset candidates; hand to
   soldier-rice or soldier-tech-debt-balance for scoping. Name owners and deadlines for
   every prescription.

## Output format

```
ODI OPPORTUNITY SCORING — <product / context>
Survey date: <YYYY-MM-DD>   |   Next re-survey due: <YYYY-MM-DD>
Context detected: <B2B/B2C · sector · stage>
Respondent roles: <economic buyer | technical evaluator | end user | procurement / B2C tiers>

RANKED OPPORTUNITY MATRIX
  Rank | Outcome Statement                               | Imp  | Sat  | Score | Zone       | Behav. signal
  -----|--------------------------------------------------|------|------|-------|------------|---------------
  1    | minimize the time to [verb + object] when [ctx]  | 8.4  | 3.1  | 14.7  | UNDER-SERVED | pending
  2    | reduce the risk of [verb + object] in [ctx]      | 7.9  | 4.0  | 11.8  | UNDER-SERVED | confirmed
  n    | increase the confidence in [object] during [ctx] | 5.1  | 8.2  | 5.1   | OVER-SERVED  | n/a

ROLE-LEVEL DIVERGENCE TABLE (B2B)
  Outcome Statement              | Econ. Buyer | Tech. Eval. | End User | Procurement | Flag
  -------------------------------|-------------|-------------|----------|-------------|------
  <outcome 1>                    | 13.2        | 11.8        | 14.1     | 7.4         | Econ. gap
  <outcome 2>                    | 9.1         | 9.4         | 9.0      | 8.7         | Watch zone

BEHAVIORAL CORROBORATION STATUS
  Under-served outcomes confirmed by behavior: <list with signal type>
  Under-served outcomes hypothesis-only (no behavioral signal): <list — prescribe test>
  Behavioral signals used: <retention curve / DAU-MAU / power-user / PQL activation / referral>

SERVING HEAT MAP
  [Importance × Satisfaction plot — bubble = opportunity score]
  Under-served cluster (score >10): <outcome labels>
  Watch zone (5–10): <outcome labels>
  Over-served cluster (score <5): <outcome labels — harvest / sunset candidates>

SO-WHAT / NEXT STEPS
  - <Under-served outcome, confirmed: escalate to soldier-opportunity-solution-tree>
  - <Under-served outcome, unconfirmed: run [specific behavioral test], owner, deadline>
  - <Over-served outcome: flag for harvest, hand to soldier-tech-debt-balance>
  - <B2B role divergence: schedule qualitative follow-up with [role], owner, deadline>
  - <Re-survey trigger: date or competitive event>

SOURCES (every external fact cited; nothing invented)
  - Tony Ulwick, "Jobs to Be Done: Theory to Practice," Idea Bite Press, 2016
    https://strategyn.com [300+ client engagements documented on Strategyn.com]
  - Dan Adams, "New Product Blueprinting," AIM Institute, 2008
    https://aiminstitute.com [B2B multi-role scoring standard; single-respondent prohibition]
  - Casey Winters & Fareed Mosavat, "The PMF Treadmill," Reforge
    https://www.reforge.com [behavioral PMF signals; retention curve flatness criterion]
  - Blake Bartlett, OpenView Partners, PLG thesis, 2016
    https://openviewpartners.com [PQL 3-5x predictive advantage; PQL conversion 25-30%
    vs MQL 5-10% — [assumption — verify current year benchmark figures]]
```
