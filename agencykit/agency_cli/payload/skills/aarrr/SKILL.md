---
name: aarrr
description: >-
  Runs a structured AARRR lifecycle diagnostic to identify the largest gap across
  Acquisition, Activation, Retention, Referral, and Revenue — then determines whether
  a funnel or growth-loop model fits the product. Produces a ranked gap diagnosis, a
  funnel-vs-loop classification, and a transition prescription to a North Star Metric
  plus input metrics tree for daily execution. Use once per planning cycle as a
  diagnostic audit, not as an ongoing measurement model.
---

# Skill — AARRR Pirate Metrics Lifecycle Diagnostic

AARRR (Acquisition, Activation, Retention, Referral, Revenue) is a five-stage lifecycle
framework introduced by Dave McClure in his 2007 "Startup Metrics for Pirates" presentation
at 500 Startups. Its primary function is diagnostic: it forces a team to quantify conversion
rates across every stage of the customer lifecycle and surface where the largest structural
gap sits before deciding where to invest. The framework carries three documented structural
critiques from Reforge (Brian Balfour, 2019): it generates more metrics than most teams can
act on, it models the journey as a linear funnel when empirical journeys are non-linear and
concurrent, and it fails to distinguish high-value users from low-value users, making
retention analysis imprecise. A companion distinction from Reforge is the growth loops vs
funnels model: funnels require proportional incremental spending at each stage to produce
more output, while loops reinvest outputs back into inputs and produce compound returns —
a structurally different engine that the AARRR framework does not encode. McClure himself
identified a recurring misallocation pattern: most early-stage teams over-invest in
Acquisition and under-invest in Activation and Retention, the stages that determine whether
Acquisition spending compounds or leaks.

> **Doctrine:** Cite Dave McClure, "Startup Metrics for Pirates" (500 Startups, 2007) for
> the five stages and the Acquisition over-investment anti-pattern. Cite Brian Balfour /
> Reforge for the three structural critiques and the growth loops vs funnels distinction.
> Cite Chamath Palihapitiya for the 3-component operational alternative (top-of-funnel,
> magic moment, retention and resurrection) derived from Facebook's growth team 2007–2012.
> Cite Dropbox's 3,900% growth in 15 months and 35% of daily signups from referrals as
> empirical evidence that Referral operates upstream of Acquisition in compounding systems
> (Drew Houston / Dropbox, reported by Andrew Chen and multiple growth practitioner sources).
> Never invent a quote, statistic, or benchmark — research every external fact and cite it.
> AARRR is a one-time diagnostic instrument, not a daily KPI dashboard — encode this
> constraint in every output.

## Procedure

1. **Frame the diagnostic scope.** Confirm product type (B2B/B2C/marketplace/platform),
   growth stage (pre-PMF, post-PMF, scaling), business model, and the planning cycle
   being assessed. These inputs determine which AARRR stages are structurally active —
   a pre-revenue product has no Revenue stage to diagnose; a marketplace has two-sided
   Acquisition to quantify separately. Establishing scope prevents the framework from
   generating metrics for stages that do not yet apply.

2. **Populate all five stages with current data.** For each stage, collect the primary
   rate metric: Acquisition (channel CAC and volume by source), Activation (percentage
   of new users who reach a first meaningful value moment within a defined window, e.g.
   D0–D7), Retention (D1/D7/D30 return rate or equivalent natural-cadence metric),
   Referral (percentage of users who generate at least one new user; viral coefficient
   K), Revenue (conversion to paid, ARPU, and LTV:CAC ratio where available). Flag any
   stage where data is absent or unreliable — an unknown stage is itself a diagnostic
   finding and must be labelled explicitly rather than estimated.

3. **Apply the McClure misallocation audit.** Check the team's current investment
   distribution across the five stages. Per Dave McClure's 2007 diagnosis, the default
   failure mode is over-investment in Acquisition (paid channels, top-of-funnel
   marketing) paired with under-investment in Activation (onboarding, time-to-value)
   and Retention (habit formation, re-engagement). Quantify the imbalance: what
   fraction of engineering and marketing spend targets each stage? A team spending 70%+
   on Acquisition with a D30 retention rate below category median is exhibiting the
   canonical misallocation pattern.

4. **Identify the largest lifecycle gap.** Rank the five stages by the magnitude of
   their conversion drop or performance deficit relative to category benchmarks where
   available. The largest gap is the primary diagnostic output. Only one stage should
   be designated as the primary gap — the constraint is intentional, because addressing
   multiple stages simultaneously prevents clean measurement of intervention impact.
   State the gap as a falsifiable hypothesis: "We believe [stage] is the binding
   constraint because [evidence]; confirmed by [leading metric]."

5. **Classify: funnel or growth loop.** Apply the Reforge funnel-vs-loop test (Brian
   Balfour, Reforge, 2019): ask whether the output of one stage can be reinvested as
   input into an upstream stage without proportional incremental spend. If Referral
   outputs feed Acquisition inputs at no marginal CAC — as Dropbox demonstrated with
   35% of daily signups from referrals generating 3,900% growth over 15 months — the
   product has a growth loop, not a funnel, and the AARRR linear model actively
   misrepresents the compounding engine. Document which loop type is present (viral
   loop, content loop, user-generated-content loop, sales loop) or confirm that a
   funnel is the correct model.

6. **Apply the Palihapitiya 3-component check.** Overlay Chamath Palihapitiya's
   operational framework, derived from leading Facebook's growth team between 2007 and
   2012: (1) top-of-funnel conversion — are enough users entering to make retention
   economics viable?; (2) magic moment discovery — have users reached the specific
   moment of perceived value that predicts long-term retention?; (3) retention and
   resurrection — what is the programme for users who found the magic moment but lapsed?
   This check adds precision to the AARRR diagnosis because it forces a distinction
   between Activation (reaching the magic moment) and Retention (returning after it),
   which the raw AARRR stage definitions do not enforce.

7. **Encode the anti-pattern and prescribe the exit.** State explicitly whether the
   team is maintaining 5+ AARRR metrics as daily KPIs — the documented operational
   failure mode. If so, prescribe the exit: reposition AARRR as a one-time diagnostic,
   then transition to a North Star Metric plus an input metrics tree for daily execution.
   The NSM should reflect the product's core value delivery (hand off to
   soldier-north-star, O6); the input metrics tree should provide 3–5 directly
   influenceable levers that form a causal path from daily decisions to NSM movement.

8. **Produce the output block.** Render the full structured output including the gap
   ranking, loop classification, Palihapitiya overlay, anti-pattern check, and
   transition prescription. End with SO-WHAT / NEXT STEPS and a SOURCES section citing
   every external fact used. Nothing in the output may be uncited. Unknown facts are
   labelled "unknown".

## Output format

```
AARRR DIAGNOSTIC — <product / context>
Context detected: <B2B/B2C · sector · stage>

LIFECYCLE STAGE DATA
  Acquisition  : [channel mix · CAC by source · volume · data quality: reliable / missing]
  Activation   : [% reaching value moment within D0–D7 window · definition of value moment]
  Retention    : [D1 / D7 / D30 rates · curve shape: flattening / still declining]
  Referral     : [% users generating ≥1 new user · viral coefficient K · data quality]
  Revenue      : [conversion to paid · ARPU · LTV:CAC · data quality]

MCCLURE MISALLOCATION AUDIT
  Acquisition spend share : [%]
  Activation spend share  : [%]
  Retention spend share   : [%]
  Misallocation signal    : present / absent — [evidence]

GAP RANKING (primary gap identified first)
  1. [Stage] — [metric value vs benchmark / expected] — [gap magnitude]
  2. [Stage] — ...
  3. [Stage] — ...
  Primary gap hypothesis  : "We believe [stage] is the binding constraint because
                             [evidence]; confirmed by [leading metric to track]."

FUNNEL vs GROWTH LOOP CLASSIFICATION
  Model type              : funnel / growth loop / hybrid
  Loop type (if loop)     : viral / content / UGC / sales / other
  Evidence                : [which stage outputs feed upstream stage inputs]
  AARRR linearity error   : [what the funnel model misrepresents in this product]

PALIHAPITIYA 3-COMPONENT OVERLAY
  Top-of-funnel conversion : [finding]
  Magic moment             : [identified / hypothesised / unknown — definition]
  Retention & resurrection : [programme present / absent · re-engagement mechanism]

ANTI-PATTERN CHECK
  AARRR used as daily KPI dashboard : yes / no
  Recommended correction            : reposition as one-time diagnostic →
                                      transition to NSM + input metrics tree

TRANSITION PRESCRIPTION
  Recommended NSM         : [candidate — hand off to soldier-north-star for validation]
  Input metrics tree      : [3–5 influenceable levers mapped to NSM]
  Hand-off               : soldier-north-star (O6) for NSM definition and validation

SO-WHAT / NEXT STEPS
  - [Primary action derived from gap ranking]
  - [Loop or funnel implication for investment allocation]
  - [Next soldier or officer to engage]

SOURCES (every external fact cited; nothing invented)
  - Dave McClure — "Startup Metrics for Pirates", 500 Startups (2007) — [assumption — verify URL]
  - Brian Balfour / Reforge — "Growth Loops vs Funnels" (2019) — https://www.reforge.com/blog/growth-loops
  - Chamath Palihapitiya — Facebook growth team framework (2007–2012); widely cited in Reforge curricula and growth practitioner literature — [assumption — verify primary source]
  - Drew Houston / Dropbox — 3,900% growth in 15 months; 35% of daily signups from referrals — [assumption — verify primary source; reported by Andrew Chen and growth practitioner sources]
  - [Any additional sources used in this specific output]
```
