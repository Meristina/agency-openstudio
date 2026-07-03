---
name: cohort-analysis
description: >-
  Diagnoses product retention health by plotting D1/D7/D30/D90 cohort curves,
  reading the curve shape as a PMF signal, and identifying the AHA moment by
  comparing retained vs churned user behaviour in the first 7 days. Use when a
  team needs to know whether retention is improving, where the curve flattens
  (or fails to), and which activation behaviour to optimise next. Produces a
  retention curve diagnosis, AHA moment hypothesis, benchmark comparison, and a
  single highest-leverage intervention recommendation.
---

# Skill — Cohort Retention Analysis

Cohort retention analysis groups users by the period they first engaged with a
product, then tracks what fraction returns at each subsequent interval. The curve
shape — specifically whether it flattens to a horizontal asymptote — is the
strongest behavioural signal for product-market fit: a flattening curve means a
stable core of users find permanent value, while a curve that continues to decline
toward zero indicates no retained value at any scale (Reforge, Brian Balfour and
Casey Winters, 2017–2024; Amplitude North Star Playbook, John Cutler, 2019). The
method also provides the operational framework for AHA moment discovery — isolating
the specific action that differentiates users who retain from those who churn —
turning a vague activation hypothesis into a measurable behavioural threshold.
For product managers, cohort analysis converts a lagging outcome metric (revenue
churn) into a leading behavioural input metric: the fraction of new users who reach
the activation milestone within the first week.

> **Doctrine:** Cite Reforge (Balfour, Winters) for curve-shape PMF interpretation;
> cite Amplitude North Star Playbook (Cutler, 2019) for AHA moment methodology;
> cite Rachitsky & Timen for B2B/B2C benchmarks. Never cite the Ellis 40% PMF
> survey as a substitute for a behavioural retention signal — it measures declared
> preference, not repeat behaviour, and is therefore a weaker PMF signal than a
> horizontally flattening cohort curve or a DAU/MAU ratio above 50% (Reforge, 2022).
> Never invent a benchmark — look up the specific product category in Rachitsky
> & Timen's dataset. Unknown data → "unknown [assumption — verify]".

## Procedure

1. **Select the cohort window from the product's natural usage cycle.** Do not
   default to calendar weeks or months. Determine the frequency at which a healthy
   user is expected to return: daily (social/media), weekly (productivity/B2B SaaS),
   or monthly (insurance/tax/scheduling). The retention window must match this natural
   cycle — using a weekly window on a daily-use product artificially inflates retention;
   using a daily window on a weekly-use product artificially deflates it (Reforge,
   Balfour, 2019). Document the expected usage frequency before extracting any data.
   Confirm the window with a qualitative anchor — interview 3–5 retained users about
   how frequently they expect to use the product in a healthy week.

2. **Define and extract same-period cohorts.** Group users by the calendar period
   of their first meaningful action (first login, first core action, or first value
   moment — not app install). Each cohort is a row; each subsequent interval is a
   column. The denominator is cohort size at Day 0 (or Week 0); the numerator is
   the count of users who returned and completed any engagement event at each
   subsequent interval. Do not mix new-user cohorts with returning-user populations —
   this inflates apparent retention. Ensure the cohort extraction query filters on
   the same triggering event across all cohorts for comparability.

3. **Plot the retention curve and read its shape.** Render the retention curve with
   interval on the x-axis and retention rate on the y-axis. Apply three diagnostic
   reads: (a) Does the curve flatten to a horizontal asymptote at any interval?
   Flattening — even at a low absolute rate — is the primary PMF signal; a curve
   still declining at D90 is the primary early-warning signal for retention failure
   (Reforge, Balfour & Winters, 2024). (b) Where is the steepest drop? A D1 cliff
   indicates an onboarding failure before value delivery; a D7–D30 cliff indicates
   value was found but not sustained; a D30–D90 cliff indicates a habit was partially
   formed but broken. (c) Are more recent cohorts performing better or worse than
   older cohorts at the same interval? Improving cohort-over-cohort retention at
   the same interval is a leading indicator that product improvements are working.

4. **Benchmark the curve against industry data.** Compare the measured retention
   rates against Lenny Rachitsky and Yuriy Timen's benchmarks from their study of
   500+ products: for B2B SaaS, top-quartile weekly active user retention is 77.9%;
   median is 61.4%; bottom-quartile is 44.6% (Rachitsky & Timen, "What is Good
   Retention", 2023). For B2C subscription products, D30 retention benchmarks differ
   materially by category — do not apply B2B benchmarks to consumer products without
   adjusting for category. Flag if the product is below the median for its category;
   this is the quantitative threshold that makes cohort improvement a strategic
   priority rather than an optional optimisation. Note that 60–70% of annual SaaS
   churn is estimated to occur within the first 90 days, making the D90 cohort
   window the primary early-warning instrument for retention failure
   [assumption — verify; Balfour, Reforge 2022 cites directionally consistent data].

5. **Run the AHA moment discovery analysis.** Using the Amplitude AHA moment
   methodology (Amplitude, 2020; Cutler, North Star Playbook, 2019): pull the
   behavioural event logs for two populations — users who were retained at D7 and
   users who churned before D7 — from the same cohort period. Compare the frequency
   and completion rate of every core action taken between Day 0 and Day 7 across
   both populations. The action (or action count threshold) with the largest
   statistically significant difference between the retained and churned populations
   is the candidate AHA moment. The AHA moment is not a feature — it is a specific
   behaviour executed at a specific frequency or depth within a specific time window
   (e.g., "invited 3+ collaborators within 7 days" or "completed first export within
   24 hours"). State the candidate AHA moment as a falsifiable hypothesis: "We
   believe users who [action] within [window] retain at [X]% vs [Y]% for those who
   do not; we will confirm this by [test method]."

6. **Diagnose the D90 window for early churn risk.** Segment the D90 retention view
   by acquisition channel, plan tier, and onboarding path if the data permits. Identify
   which segments have a D90 retention rate materially below the cohort median — these
   are the sub-populations driving aggregate churn. A segment-level diagnosis converts
   a portfolio-level retention problem (hard to act on) into a targeted intervention
   (specific to a channel or onboarding path). Apply the DAU/MAU diagnostic in
   parallel: a ratio above 50% combined with a horizontally flattening cohort curve
   constitutes a strong behavioural PMF signal; below 20% with a still-declining
   curve is a strong counter-signal (Reforge, 2022).

7. **Identify the single highest-leverage intervention.** The cohort analysis is a
   prioritisation input, not an end in itself. Translate the findings into one
   recommended intervention: the action most likely to increase the fraction of new
   users who reach the AHA moment within the natural usage window. Structure the
   recommendation as: target behaviour → current funnel completion rate → target
   completion rate → intervention hypothesis → leading metric to track. Do not
   recommend more than one primary intervention per analysis cycle — constraint forces
   prioritisation and enables clean measurement of impact.

8. **Establish the measurement cadence and hand off.** Define the cohort tracking
   frequency: new cohorts should be extracted at the natural usage window interval
   (weekly for weekly-use products). Set a statistical significance threshold before
   any A/B test on the activation intervention is called (Netflix ABlaze sequential
   testing methodology, Kohavi et al., "Trustworthy Online Controlled Experiments",
   2020, is the recommended statistical model). Hand off the AHA moment hypothesis
   to soldier-controlled-experiment (O6) for experimental design, and the retention
   curve diagnosis to the O6 officer for roadmap prioritisation context.

## Output format

```
COHORT RETENTION ANALYSIS — <product / context>
Context detected: <B2B/B2C · sector · stage · natural usage frequency>

COHORT WINDOW SELECTION
  Natural usage frequency:   [daily / weekly / monthly — with rationale]
  Windows analysed:          [D1 / D7 / D30 / D90 — list all available]
  Cohort definition:         [first event used to define Day 0]

RETENTION CURVE DIAGNOSIS
  D1 retention:   [X%] — [above / at / below] benchmark for category
  D7 retention:   [X%] — [above / at / below] benchmark for category
  D30 retention:  [X%] — [above / at / below] benchmark for category
  D90 retention:  [X%] — [above / at / below] benchmark for category
  Curve shape:    [flattening / still declining / not yet determinable]
  PMF signal:     [strong behavioural PMF / weak / counter-signal / insufficient data]
  Steepest drop:  [D0-D1 / D1-D7 / D7-D30 / D30-D90] → [diagnosis: onboarding / value / habit]
  Cohort trend:   [improving / flat / degrading] cohort-over-cohort at same interval

BENCHMARK COMPARISON
  Category:              [B2B SaaS / B2C subscription / marketplace / etc.]
  Benchmark source:      Rachitsky & Timen — 500+ products study (2023)
  Top-quartile weekly:   77.9% (B2B); [category-specific if different]
  Median weekly:         61.4% (B2B); [category-specific if different]
  Bottom-quartile:       44.6% (B2B); [category-specific if different]
  Product position:      [top / median / bottom quartile] → [priority: strategic / optimise / urgent]
  DAU/MAU ratio:         [X%] → [PMF-consistent / insufficient / counter-signal]

AHA MOMENT ANALYSIS
  Analysis population:   Retained at D7 (n=[N]) vs churned before D7 (n=[N]) — same cohort period
  Candidate AHA moment:  [specific action + frequency/depth threshold + time window]
  Retained rate:         [X%] of retained users completed this action in window
  Churned rate:          [X%] of churned users completed this action in window
  Delta:                 [difference — statistical significance: [p-value or "not yet tested"]]
  AHA hypothesis:        We believe users who [action] within [window] retain at [X]% vs [Y]%
                         for those who do not; confirmed by [planned test method]

D90 EARLY CHURN RISK
  Highest-churn segment: [acquisition channel / plan tier / onboarding path]
  Segment D90 rate:      [X%] vs cohort median [Y%]
  Estimated churn timing:[proportion of annual churn occurring within D90 — see SOURCES]
  Segment intervention:  [specific fix targeted at the highest-churn segment]

HIGHEST-LEVERAGE INTERVENTION
  Target behaviour:      [the AHA moment action to optimise]
  Current funnel rate:   [% of new users reaching the AHA moment today]
  Target rate:           [goal — with rationale]
  Intervention:          [specific product or onboarding change]
  Leading metric:        [metric to track weekly — not DAU/MAU, which lags]

SO-WHAT / NEXT STEPS
  - [Primary action: intervention to ship / test to run / data gap to close]
  - [Hand off to soldier-controlled-experiment (O6) for AHA moment A/B test design]
  - [Hand off to O6 officer with retention curve diagnosis for roadmap prioritisation]
  - [Next cohort review date and metric threshold that would trigger escalation]

SOURCES (every external fact cited; nothing invented)
  - Lenny Rachitsky & Yuriy Timen — "What is Good Retention" (2023) — B2B weekly
    retention benchmarks: top-quartile 77.9%, median 61.4%, bottom-quartile 44.6%
    https://www.lennysnewsletter.com/p/what-is-good-retention-updated
  - Reforge — Brian Balfour & Casey Winters — retention curve shape as PMF signal;
    curve-flattening methodology; D90 as early-warning window (2017–2024)
    https://www.reforge.com/blog/retention-engagement-growth
  - Amplitude — North Star Playbook (John Cutler, 2019) — AHA moment discovery
    methodology; comparing retained vs churned user behaviour D0–D7
    https://amplitude.com/north-star
  - Ron Kohavi, Diane Tang, Ya Xu — Trustworthy Online Controlled Experiments
    (Cambridge University Press, 2020) — sequential testing methodology for
    cohort-based A/B tests; statistical validity in retention experiments
```
