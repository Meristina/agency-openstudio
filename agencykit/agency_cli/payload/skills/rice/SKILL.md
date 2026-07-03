---
name: rice
description: >-
  Scores and sequences a prioritization backlog using the RICE formula (Reach ×
  Impact × Confidence / Effort) with four calibration enrichments: ODI opportunity
  score replaces subjective Confidence; behavioral data gates inflate Confidence
  claims; a strategic alignment multiplier discounts off-strategy Impact; and
  Cost-of-Delay sequencing corrects for time-sensitivity. Use when ranking competing
  initiatives, auditing an existing roadmap, or enforcing ownership accountability
  before committing engineering capacity. Produces a scored, sequenced RICE ledger
  with a strategic verdict and explicit assumption flags.
---

# Skill — RICE Scoring with ODI Confidence Calibration and CoD Sequencing

RICE (Reach × Impact × Confidence / Effort) is a quantitative prioritization formula
introduced by Sean McElvey at Intercom (2016). It converts four variables into a
single comparable score across initiatives: Reach (how many users affected per period),
Impact (magnitude of effect on the target metric), Confidence (how certain the team is
in the estimates), and Effort (person-months of work). The formula's practical virtue is
that it makes hidden assumptions visible and forces teams to argue about numbers rather
than advocacy. Its known weakness is that Confidence is typically set by gut feel,
Impact is subject to optimism bias, and the formula is blind to time-sensitivity —
meaning a low-urgency item can score above a crisis-level item simply by having a larger
user base. These weaknesses are corrected by four enrichments: (1) Tony Ulwick's
Outcome-Driven Innovation opportunity score calibrates Confidence against empirical
evidence of job-to-be-done underservice; (2) NielsenIQ BASES methodology deflates
Confidence claims not corroborated by behavioral data; (3) McKinsey/BCG strategic
alignment doctrine discounts Impact for items not laddering to the current strategic
objective; and (4) SAFe Cost-of-Delay sequencing promotes high-urgency items above
higher-scoring RICE items when delay cost is material.

> **Doctrine:** RICE scores are hypotheses about future value, not facts. Confidence
> inputs derived from surveys or declared intent must be corroborated with behavioral
> data (cohort retention curves, usage frequency) before being treated as valid — this
> is the NielsenIQ BASES deflation principle. ODI opportunity scores above 10 signal an
> under-served job; below 5 signal an over-served one — use this as a directional
> calibration input, not a mechanical multiplier. Never cite "50% of features are never
> used" — this figure is untraceable. Never use NPS as the sole proxy for Impact.
> Amazon's single-threaded owner (STL) doctrine applies before scoring: any initiative
> without a 100%-dedicated named owner is removed from the ranked list regardless of
> RICE score — no formula compensates for diffuse ownership. Research every external fact
> and cite it; invent nothing.

## Procedure

1. **Context and ownership gate.** Before scoring anything, document: product name,
   stage (pre-PMF, growth, mature), B2B or B2C, planning horizon, and the current
   primary strategic objective (the one OKR or North Star metric the organization is
   committed to this period). Then apply the Amazon single-threaded leader audit: for
   each initiative, confirm a named, 100%-dedicated owner. Initiatives with no STL are
   flagged BLOCKED and removed from the ranked list. No RICE score is computed for them
   (Colin Bryar & Bill Carr, Working Backwards: Insights, Stories, and Secrets from
   Inside Amazon, 2021).

2. **Candidate enumeration and scoping.** List every candidate initiative in scope.
   Each must be described as a specific, shippable outcome — not a vague theme or
   project name. Confirm the unit of Reach (weekly active users, monthly paying accounts,
   daily sessions) and make it consistent across all candidates. Inconsistent Reach units
   are the most common RICE corruption — flag and standardise before proceeding.

3. **ODI opportunity score as Confidence calibration.** For each initiative, assess
   whether a relevant Opportunity Score is available from an ODI study (Ulwick,
   Strategyn — drawn from 300+ client engagements). An opportunity score above 10
   indicates an under-served job-to-be-done: increase the Confidence input toward the
   upper end of the plausible range. A score below 5 indicates an over-served job:
   suppress Confidence, because the market has already competed away the differentiation
   value. Where no ODI score exists, label the Confidence input [assumption — verify]
   and apply a conservative default of 50% (Tony Ulwick, Outcome-Driven Innovation,
   Strategyn whitepaper, 2002; Anthony Ulwick, Jobs to Be Done: Theory to Practice,
   IDEA BITE Press, 2016).

4. **Behavioral data corroboration gate.** Before accepting any Confidence score above
   70%, require corroboration from behavioral data: cohort retention curves (do users
   return after first exposure to the relevant job step?) and usage frequency data
   (is the underlying job performed with the frequency implied by the Reach estimate?).
   This gate applies the NielsenIQ BASES deflation principle: declared purchase intent
   and survey-stated importance systematically overstate actual behavior, calibrated
   against empirical benchmarks from 300,000+ concept tests and 500,000+ volume
   forecasts (NielsenIQ, BASES Methodology Overview). Any Confidence input not
   corroborated by behavioral data must be flagged as [assumption — verify] and capped
   at 70% unless behavioral evidence is supplied.

5. **Strategic alignment multiplier on Impact.** Score each initiative against the
   current primary strategic objective: Fully aligned (multiplier 1.0), Partially
   aligned (0.7), Off-strategy (0.4). Apply the multiplier to the Impact variable
   before computing the RICE score. This operationalises McKinsey and BCG strategic
   portfolio doctrine: investment that does not ladder to the current committed objective
   should be discounted even when its isolated value is high, preventing the matrix from
   optimizing for tractability rather than strategic direction (McKinsey & Company,
   strategy portfolio guidance; BCG, strategic prioritization frameworks). Document the
   strategic rationale for each multiplier assignment explicitly.

6. **Effort estimation and Cost-of-Delay sequencing.** Estimate Effort in person-months
   using the team's own historical velocity — not story points or abstract complexity
   scores. Then compute Cost-of-Delay for each initiative: the value lost per week or
   month of delay (expressed in the same currency as the target metric — revenue,
   activated users, retained cohort share). Items with high CoD and short duration
   (CD3 = Cost-of-Delay / Duration) are promoted above higher-RICE-scoring items that
   carry lower urgency. This correction applies the SAFe Lean Portfolio Management
   weighted shortest job first (WSJF) logic, which formalises CoD sequencing for
   portfolio-level decisions (Scaled Agile Framework, Lean Portfolio Management; Don
   Reinertsen, Principles of Product Development Flow, Celeritas Publishing, 2009).

7. **RICE score computation and ranked ledger.** Compute RICE = (Reach × Impact ×
   Confidence) / Effort for each initiative, where Impact already carries the strategic
   alignment multiplier. Sort candidates descending by RICE score. Then apply the CoD
   sequencing overlay: where CD3 rank materially differs from RICE rank, document the
   override and the reason. Produce the final sequenced ledger with both RICE score and
   CoD-adjusted position clearly shown.

8. **Assumption audit and residual risk.** For every Confidence input flagged
   [assumption — verify], specify the cheapest validation test available (analytics
   pull, one-week prototype, five user interviews) and assign an owner and deadline.
   Identify the single assumption whose failure would most change the top item's rank.
   Document residual risks: ownership stability (STL commitment), behavioral data gaps,
   and strategic objective continuity.

## Output format

```
RICE SCORING — <product / context>
Scoring date: <YYYY-MM-DD>   |   Planning horizon: <quarter / half-year>
Context detected: <B2B/B2C · sector · stage>
Primary strategic objective: <OKR or North Star metric in scope this period>

STL OWNERSHIP GATE
  Blocked (no dedicated owner): <list of initiatives removed, or "none">
  Confirmed STL owners: <initiative → owner name>

RICE LEDGER
  Rank | Initiative          | Reach | Impact | Align× | Conf% | Effort | RICE  | CoD/wk | CD3   | Final seq.
  -----|---------------------|-------|--------|--------|-------|--------|-------|--------|-------|----------
  1    | <initiative name>   | 4200  | 3      | 1.0    | 70%   | 1.5    | 5880  | $12K   | 8000  | 1
  2    | <initiative name>   | 8000  | 2      | 0.7    | 50%   | 2.0    | 2800  | $40K   | 20000 | 2 (CoD↑)
  n    | <initiative name>   | ...   | ...    | ...    | ...   | ...    | ...   | ...    | ...   | n
  Note: Impact carries strategic alignment multiplier (1.0 / 0.7 / 0.4). Conf% capped at
  70% without behavioral corroboration.

ODI CONFIDENCE CALIBRATION
  Initiative             | ODI Score | Signal          | Conf% adjustment
  -----------------------|-----------|-----------------|------------------
  <initiative>           | 11.2      | Under-served ↑  | Raised to 80%
  <initiative>           | 4.1       | Over-served ↓   | Capped at 40%
  <initiative>           | N/A       | No ODI data     | [assumption — verify], default 50%

BEHAVIORAL CORROBORATION STATUS
  Initiative             | Cohort retention | Usage freq. | Conf% gate status
  -----------------------|------------------|-------------|--------------------
  <initiative>           | Available        | Available   | PASS — Conf% accepted
  <initiative>           | Not available    | Not available | FAIL — Conf% capped at 70% [assumption — verify]

COST-OF-DELAY SEQUENCING OVERRIDES
  Initiative             | RICE rank | CoD/wk | CD3    | CoD-adjusted rank | Override rationale
  -----------------------|-----------|--------|--------|-------------------|--------------------------
  <initiative>           | 3         | $40K   | 20000  | 2                 | High CoD, short duration — time-sensitive

ASSUMPTION AUDIT
  - <initiative>: Confidence flagged — validation test: <method>, owner: <name>, deadline: <date>
  - <initiative>: Reach estimated — validate with analytics pull by <date>
  Rank-breaking assumption: <the single assumption whose failure would most change rank 1>

SO-WHAT / NEXT STEPS
  - Ship <initiative> first: RICE rank 1, CoD-adjusted rank 1, STL confirmed.
  - Promote <initiative> ahead of rank 3: CoD override justified by $40K/wk delay cost.
  - Block <initiative> until STL assigned — do not begin sizing or scoping.
  - Validate Confidence on <initiative> via <behavioral test> by <date> before committing sprint capacity.
  - Re-run ODI opportunity scoring on <initiative> — no current score, Confidence is [assumption].

SOURCES (every external fact cited; nothing invented)
  - Sean McElvey (Intercom), "RICE: Simple Prioritization for Product Managers," Intercom Blog, 2016
    — https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/
  - Tony Ulwick, "Outcome-Driven Innovation," Strategyn whitepaper, 2002
    — https://strategyn.com/outcome-driven-innovation-process/
  - Anthony Ulwick, Jobs to Be Done: Theory to Practice, IDEA BITE Press, 2016
  - NielsenIQ, BASES Methodology Overview — 300,000+ concept tests, 500,000+ volume forecasts
    — https://nielseniq.com/global/en/solutions/bases/ [assumption — verify specific publication year]
  - Colin Bryar & Bill Carr, Working Backwards: Insights, Stories, and Secrets from Inside Amazon,
    St. Martin's Press, 2021
  - Scaled Agile Framework, "Lean Portfolio Management — Weighted Shortest Job First (WSJF)"
    — https://scaledagileframework.com/wsjf/
  - Don Reinertsen, Principles of Product Development Flow: Second Generation Lean Product
    Development, Celeritas Publishing, 2009
  - McKinsey & Company, strategic portfolio prioritization guidance [assumption — verify specific
    report title and year]
```
