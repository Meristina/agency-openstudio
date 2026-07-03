---
name: product-market-fit
description: >-
  Diagnoses whether a product has achieved product-market fit and whether it is maintaining
  it over time, using behavioural signals (cohort retention flattening, DAU/MAU, organic CAC)
  weighted over declared preference surveys (Sean Ellis 40% test, NPS). Produces a structured
  PMF verdict with a mandatory re-evaluation cadence, a Five Forces structural gate, and an
  explicit categorisation of roadmap work by Casey Winters' five types. Use when a team needs
  to determine readiness to scale, diagnose retention decline, or stress-test a PMF claim.
---

# Skill — Product-Market Fit Diagnosis

Product-market fit (PMF) is the degree to which a product satisfies a strong market demand —
first popularised as a term by Marc Andreessen (2007) and operationalised as a diagnostic
framework by Sean Ellis (40% survey, 2010) and extended by Andy Rachleff, Hiten Shah, and
the Reforge ecosystem. The method matters because most premature scaling failures trace to
teams believing they have PMF when they have only survey signal, not behavioural confirmation.
The seminal structural contribution from Casey Winters and Fareed Mosavat (PMF Treadmill,
Reforge) is that PMF is never a milestone: consumer expectations compound upward over time,
so a product that met the bar in 2020 can lose it by 2024 without shipping a single bad
feature, simply because the competitive reference class improved (Chegg 2024: 90% valuation
decline, 500,000 subscribers lost in 10 months). This skill produces a verdict-bearing
diagnosis with a mandated re-evaluation trigger, not a one-time pass/fail stamp.

> **Doctrine:** Weight behavioural signals (cohort retention curve shape, DAU/MAU ratio,
> organic CAC trajectory) more heavily than declared preference (Ellis 40% survey, NPS).
> Behavioural signals are harder to falsify. When citing the Ellis 40% survey, apply its
> two scope constraints: minimum 100 responses, respondents must be active users from the
> last 14 days — applying it to any registered user base produces an inflated signal.
> Cite Casey Winters & Fareed Mosavat (PMF Treadmill, Reforge) for the dynamic threshold
> doctrine. Cite Lenny Rachitsky & Yuriy Timen (500+ products study) for benchmarks.
> Run Michael Porter's Five Forces as a mandatory upstream gate: authentic PMF in a
> structurally unattractive market is a strategic trap, not a launch signal.
> Never invent a quote, statistic, or benchmark — research every external fact and cite it.

## Procedure

1. **Frame product context and stage.** Identify product type (B2B SaaS / B2C consumer /
   marketplace / platform), business model, growth stage (pre-PMF / PMF / scaling / mature),
   primary user segment, and geography. Determine whether this is a first PMF diagnosis or a
   treadmill re-evaluation for a product that previously had PMF. The stage and model shape
   which behavioural thresholds are applicable and which work type (per Winters' five types)
   should dominate the roadmap.

2. **Run the Porter Five Forces structural gate.** Before interpreting any PMF signal, assess
   structural market attractiveness across all five forces: competitive rivalry, buyer bargaining
   power, supplier bargaining power, threat of new entrants, and threat of substitutes. Score
   each Low / Medium / High with a one-sentence rationale and produce a structural verdict
   (Attractive / Borderline / Unattractive). A product with authentic PMF in a structurally
   Unattractive market is a strategic trap that will erode even real retention gains over time;
   surface this explicitly before proceeding. Cite Michael Porter (Competitive Strategy, 1980).

3. **Collect and weight behavioural signals.** Gather and assess the three primary behavioural
   PMF indicators, treating them as harder to falsify than survey data. First, cohort retention
   curve shape: a curve that flattens horizontally — meaning a stable percentage of users
   continues to engage indefinitely — is the most structurally significant signal of PMF
   (Lenny Rachitsky & Yuriy Timen, 500+ products study). A curve that continues to decline
   to zero indicates no PMF regardless of survey scores. Second, DAU/MAU ratio: for
   daily-habit products, a ratio above 50% is the threshold associated with strong PMF;
   WhatsApp and Facebook historically exceeded this; most products sit at 10-20%
   [assumption — verify against sector]. Third, organic CAC trajectory: PMF is evidenced
   when word-of-mouth and organic channels grow without paid stimulus — declining blended CAC
   in the presence of organic growth is a confirmatory signal.

4. **Apply the Sean Ellis 40% survey with scope constraints.** Administer the survey question
   ("How would you feel if you could no longer use this product?" with options including
   "Very disappointed") only to users who have been active in the last 14 days, with a minimum
   of 100 qualifying responses. A result of 40% or above "Very disappointed" is a leading
   indicator of declared preference and correlates with PMF across Ellis's dataset. This is
   a leading indicator, not behavioural confirmation — weight it below cohort retention
   evidence. If fewer than 100 qualified respondents exist, flag the result as statistically
   unreliable. Never apply the survey to total registered users; the resulting number is
   an artefact of the sampling frame, not product reality.

5. **Diagnose the PMF Treadmill position.** Apply Casey Winters and Fareed Mosavat's PMF
   Treadmill framework (Reforge): ask whether the product's current experience quality still
   meets the market's current reference class, not the reference class at the time PMF was
   first declared. Consumer expectations accumulate upward as competitive alternatives
   improve. Use the Kano model's degradation pattern to diagnose which formerly differentiating
   features have migrated to basic expectations (must-haves), producing a treadmill drag
   effect. The Chegg 2024 case is the canonical quantified example: 90% valuation decline and
   loss of approximately 500,000 subscribers in 10 months, attributed to Kano-classification
   degradation accelerated by the emergence of AI-native study tools as a new reference class.

6. **Classify roadmap work using Winters' five types.** Categorise all current and planned
   roadmap initiatives into Casey Winters' five types of product work (Reforge): PMF Work
   (closing gaps between product and market need), Feature Work (extending capability for
   existing users), Growth Work (scaling acquisition and activation), Scaling Work (sustaining
   quality under load), and PMF Expansion Work (entering adjacent segments). Name the type
   explicitly on each initiative. If the roadmap shows 80%+ capacity in Feature Work and
   Growth Work with zero PMF Work, flag the silent PMF maintenance risk — this is the most
   common misallocation pattern in scaling-stage companies that have previously achieved PMF.

7. **Produce the PMF verdict with a mandatory re-evaluation trigger.** Issue a structured
   verdict: Strong PMF / Weak PMF / No PMF / PMF at Risk (treadmill). State the primary
   signal driving the verdict (behavioural over survey) and the primary counter-evidence.
   Then define the re-evaluation trigger: the specific conditions and time horizon under
   which this diagnosis must be re-run — not as an annual ritual but tied to observable
   events such as a new competitive entrant achieving critical mass, a cohort retention
   decline of more than 10 percentage points, or an organic CAC increase above threshold.
   This trigger is a hard output requirement; a one-time PMF designation with no re-evaluation
   condition is constitutionally incomplete.

8. **Produce SO-WHAT and next steps.** State the strategic implication of the verdict,
   the single most important assumption to validate next, and the appropriate handoff:
   soldier-north-star for metric architecture, soldier-market-sizing for structural entry
   decisions, soldier-kano for feature expectation migration analysis, or an O2 officer
   for roadmap and OKR structuring.

## Output format

```
PRODUCT-MARKET FIT DIAGNOSIS — <product / context>
Context detected: <B2B/B2C · sector · stage>

FIVE FORCES STRUCTURAL GATE (Porter, 1980)
  Competitive rivalry       : Low / Medium / High — [rationale]
  Buyer bargaining power    : Low / Medium / High — [rationale]
  Supplier bargaining power : Low / Medium / High — [rationale]
  Threat of new entrants    : Low / Medium / High — [rationale]
  Threat of substitutes     : Low / Medium / High — [rationale]
  Structural verdict        : Attractive / Borderline / Unattractive

BEHAVIOURAL SIGNALS (weighted primary)
  Cohort retention shape    : [Flattening / Declining / Declining to zero] — [period observed]
  DAU/MAU ratio             : [%] vs. benchmark [50%+ for daily-habit; source]
  Organic CAC trajectory    : [Declining / Stable / Rising] — [channel mix note]
  Signal weight verdict     : [Supports PMF / Neutral / Contradicts PMF]

DECLARED PREFERENCE SIGNALS (weighted secondary)
  Ellis 40% survey result   : [%] very disappointed (n=[respondents], window=[days])
  Scope constraint check    : [Active last 14 days? Minimum 100? Yes / No / Unknown]
  Survey reliability        : [Reliable / Unreliable — reason]
  NPS (if available)        : [score] — [used as guardrail only, not PMF confirmation]

PMF TREADMILL ASSESSMENT (Winters & Mosavat, Reforge)
  Reference class shift     : [What has the competitive baseline become since PMF was declared?]
  Kano degradation detected : [Which formerly-differentiating features are now must-haves?]
  Treadmill risk level      : Low / Medium / High
  Chegg precedent relevance : [Applicable / Not applicable — reason]

ROADMAP WORK CLASSIFICATION (Winters, Reforge — five types)
  PMF Work          : [initiatives — %]
  Feature Work      : [initiatives — %]
  Growth Work       : [initiatives — %]
  Scaling Work      : [initiatives — %]
  PMF Expansion Work: [initiatives — %]
  Misallocation flag: [Yes / No — description if yes]

PMF VERDICT
  Verdict           : Strong PMF / Weak PMF / No PMF / PMF at Risk (treadmill)
  Primary signal    : [behavioural / survey — which signal drives this verdict]
  Counter-evidence  : [what contradicts or limits confidence in the verdict]
  Confidence level  : High / Medium / Low

RE-EVALUATION TRIGGER (mandatory — not a one-time milestone)
  Cadence           : [time-based and event-based conditions]
  Event triggers    : [new entrant at scale / retention decline threshold / CAC spike]
  Owner             : [who is accountable for running the next diagnosis]

SO-WHAT / NEXT STEPS
  - [Strategic implication of the verdict]
  - [Single most important assumption to validate next]
  - [Handoff: soldier-north-star / soldier-market-sizing / soldier-kano / O2 officer]

SOURCES (every external fact cited; nothing invented)
  - Casey Winters & Fareed Mosavat — PMF Treadmill (Reforge) — https://www.reforge.com
  - Sean Ellis — 40% survey methodology (2010) — https://www.startup-marketing.com
  - Lenny Rachitsky & Yuriy Timen — How the biggest consumer apps got their first 1,000 users
    (500+ products study) — https://www.lennysnewsletter.com
  - Michael Porter — Competitive Strategy (Free Press, 1980)
  - Casey Winters — Five Types of Product Work (Reforge) — https://www.reforge.com
  - [Any additional sources used in this specific output]
```
