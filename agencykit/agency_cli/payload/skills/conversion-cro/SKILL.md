---
name: conversion-cro
description: >-
  Conversion-rate optimisation — diagnose where a funnel/journey leaks and improve the rate at
  which visitors take the desired action, through evidence-led hypotheses and valid experiments.
  Maps the conversion journey, quantifies drop-off, prioritises frictions (reach × impact ×
  ease), runs properly-powered A/B tests, and reads results honestly (statistical significance,
  no peeking, guard against local maxima). Removes friction against the value prop's promise;
  grounds every rate in data, never invents an uplift.
---

# Skill — Conversion-Rate Optimisation (CRO)

Improve the share of visitors who take the desired action — by **finding where the journey
leaks** and **testing fixes**, not by guessing at button colours. CRO is reframed classic
optimisation: structured diagnosis + controlled experiments against a real baseline.

> **Doctrine — evidence and valid experiments, not opinion.** Ground every rate and drop-off in
> **measured data** (analytics, session data, the baseline from O1). Improvements are
> **hypotheses tested with properly-powered experiments**, read honestly (pre-set sample size &
> duration, statistical significance, **no peeking / no stopping early**, watch for novelty
> effects and **local maxima**). CRO removes friction against the **value prop's promise** (it
> doesn't invent a new promise — that's value-prop-design). **Never invent** a conversion rate,
> uplift %, or benchmark — measure/source it or label `[assumption — verify]`; unknown →
> "unknown". A "+30% uplift" with no valid test is noise.

## Procedure
1. **Define the conversion goal & baseline:** the primary action (purchase, signup, lead) and
   any micro-conversions; the current rate from analytics (sourced, with the segment/time basis).
2. **Map the journey & quantify leaks:** step-by-step funnel (landing → … → conversion); the
   drop-off at each step; segment it (device, source, audience) to find where the loss
   concentrates — fix the biggest leak, not the loudest opinion.
3. **Diagnose friction (evidence-led):** combine quantitative (funnel/heatmaps/session
   replays/forms analytics) and qualitative (user testing, surveys, support tickets, the JTBD
   pains). Classify frictions: clarity, motivation/value, trust/risk, effort/usability, cost.
4. **Hypothesise & prioritise:** write each as "if we change X for audience Y, conversion will
   improve because Z (friction)". Prioritise by **reach × impact × ease** (e.g. PIE/ICE);
   tie each to the value prop and a friction, not to aesthetics.
5. **Experiment design:** A/B or multivariate; **pre-compute sample size & duration** for the
   baseline rate and minimum detectable effect; one primary metric + guardrail metrics; define
   stop rules. State the test is invalid if under-powered or stopped on a peek.
6. **Read results honestly:** significance + confidence interval, not just point uplift; check
   guardrails (don't win conversion while wrecking AOV/retention); beware novelty and
   seasonality; watch for a local maximum (small wins that block a bigger redesign).
7. **Hand off:** validated wins → ship + feed the funnel plan (full-funnel-paid-media);
   promise/positioning issues → value-prop-design / O2; causal lift confirmation → O6
   (incrementality); lead-quality handoff → lead-scoring-lifecycle.

## Output format
```
CONVERSION-RATE OPTIMISATION — <product / journey>
Context detected: <B2B/B2C · market · stage>
Conversion goal + baseline rate: …%  [analytics source · segment/time basis]

JOURNEY MAP & LEAKS (quantified)
  | Step | Rate / drop-off | Where loss concentrates (segment) |
  …  Biggest leak: …

FRICTION DIAGNOSIS (quant + qual)
  | Friction (clarity/motivation/trust/effort/cost) | Evidence | Severity |
  …

HYPOTHESES (prioritised: reach × impact × ease)
  1. If we change <X> for <Y>, conversion improves because <Z friction>.  [PIE/ICE]
  …

EXPERIMENT DESIGN
  Test type · primary + guardrail metrics · sample size & duration (pre-computed) · stop rules.
  ⚠️ Invalid if under-powered or stopped early; no peeking.

READING RESULTS (when run)
  Significance + CI · guardrails held? · novelty/seasonality · local-maximum risk.

HANDOFF: → ship + full-funnel plan · → value-prop-design/O2 (promise) · → O6 incrementality · → lead-scoring.

SOURCES (every rate/uplift/benchmark cited; nothing invented)
  - <analytics / category CRO benchmark sources researched live>  · baseline (O1).
```
