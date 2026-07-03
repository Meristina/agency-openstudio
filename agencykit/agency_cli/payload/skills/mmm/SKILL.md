---
name: mmm
description: >-
  Marketing-Mix Modelling (MMM) — a privacy-resilient, top-down statistical model that estimates
  each channel's contribution to a business outcome and allocates budget across the portfolio,
  accounting for adstock (carryover), saturation (diminishing returns), and baseline/external
  factors. Modern practice (Google Meridian, open-source Bayesian) is CALIBRATED BY INCREMENTALITY
  EXPERIMENTS as priors — not run blind. It is the allocator, not the causal truth (that's
  incrementality). Grounds every estimate in data with uncertainty; never invents a coefficient or ROI.
---

# Skill — Marketing-Mix Modelling (MMM)

Estimate **how much each channel contributes** to sales/conversions and **where the next dollar
should go**, using a top-down statistical model over historical spend + outcomes + context. MMM
needs no user-level tracking, so it is **privacy-resilient** — its main advantage in the
post-cookie world. It answers portfolio allocation; it does not, alone, prove causality.

> **Doctrine — the allocator, calibrated by experiments.** In the triangulation stack, **MMM is
> the privacy-resilient PORTFOLIO ALLOCATOR** — and modern MMM (**Google Meridian**, open-source,
> Bayesian) must be **calibrated by incrementality experiments as priors**, not run blind.
> Incrementality is the causal truth that anchors MMM; MMM then extends that truth across the
> whole budget and time. **MMM is correlational at heart** — without experiment calibration it can
> confidently mis-estimate. **Report estimates with uncertainty (credible intervals), never point
> ROIs as fact.** **Never invent** a coefficient, contribution %, mROI, or saturation point —
> derive it from data or label `[assumption — verify]`; unknown → "unknown".

## Core concepts (model these explicitly)
- **Adstock / carryover:** advertising effect decays over time, not instant; estimate the decay.
- **Saturation / diminishing returns:** each channel has a response curve that flattens; the
  marginal ROI (mROI) at current spend is what drives reallocation, not average ROI.
- **Baseline vs incremental:** separate what would have sold anyway (base) from media-driven.
- **External factors / controls:** seasonality, price, promotions, distribution, competitor
  activity, macro — omitting them biases the media estimates.
- **Bayesian priors (Meridian):** experiment-derived effect sizes enter as priors → calibration.

## Procedure
1. **Frame the question & data:** the outcome (revenue/conversions), the channels, the geography/
   time grain, and the decision (reallocate / size a channel / set total budget). Audit data
   availability and quality (≥1-2 years, weekly, with spend + context); flag gaps.
2. **Specify the model:** channels + controls; adstock and saturation forms; geo/national;
   Bayesian (Meridian) with **priors from the incrementality soldier's experiments**. State
   identifying assumptions and what could confound.
3. **Calibrate with experiments (mandatory):** fold geo-lift/incrementality results in as priors/
   validation. Where they disagree, the experiment wins for that channel; reconcile and explain.
4. **Estimate & validate:** fit; check fit/holdout, residuals, and stability; report contribution
   and **mROI per channel with credible intervals** — not single numbers. Stress-test against
   alternative specifications.
5. **Optimise allocation:** use the saturation curves + mROI to find the reallocation that lifts
   total outcome (move spend from low-mROI saturated channels to high-mROI ones); respect the
   budget-balance (60:40/ESOV → budget-balance soldier) and diminishing returns. Give a range.
6. **State limits honestly:** correlational core, collinearity between channels, can't see very
   short-term or creative effects well, needs recalibration; not a substitute for experiments.
7. **Hand off:** priors/validation ↔ incrementality; the 60:40/ESOV split ↔ budget-balance;
   attribution reconciliation ↔ attribution-diagnostics; long-term brand effects ↔
   brand-tracking; data/privacy ↔ Inspector.

## Output format
```
MARKETING-MIX MODELLING (MMM) — <brand / portfolio>
Context detected: <B2B/B2C · market · stage>   |  Decision: <reallocate / size channel / set budget>
⚠️ The ALLOCATOR, calibrated by experiments (priors). Correlational at heart — not the causal truth (that's incrementality).

DATA & MODEL SPEC
  Outcome · channels · controls (seasonality/price/promo/distribution/competitor/macro) · grain ·
  adstock + saturation forms · Bayesian (Meridian) · identifying assumptions.

EXPERIMENT CALIBRATION (mandatory)
  Incrementality priors folded in: …  Where MMM vs experiment disagree → experiment wins; reconciled: …

ESTIMATES (with uncertainty)
  | Channel | Contribution % | mROI @ current spend | Saturation point | Credible interval |
  …  Baseline vs incremental split: …

ALLOCATION OPTIMISATION
  Move from low-mROI/saturated → high-mROI (range, not a point) · respect 60:40/ESOV (→ budget-balance).

LIMITS (honest)
  Correlational core · collinearity · weak on short-term/creative · needs recalibration · not a substitute for experiments.

HANDOFF: → incrementality (priors) · → budget-balance (split) · → attribution-diagnostics (reconcile) · → brand-tracking · → Inspector.

SOURCES (every coefficient/ROI/benchmark cited; nothing invented)
  - Google Meridian (open-source Bayesian MMM) · incrementality priors · <data/category sources researched live>.
```
