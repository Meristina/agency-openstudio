---
name: incrementality
description: >-
  Incrementality / geo-lift experiments — measure the CAUSAL effect of marketing (what spend
  actually caused, vs what would have happened anyway) through randomised/quasi-experiments: geo
  holdouts, ghost ads/PSA, conversion-lift, switchback tests. The causal source of truth that
  calibrates MMM and exposes attribution bias. Grounded in Gordon, Moakler & Zettelmeyer (2023,
  663 RCTs): observational/last-touch methods overstate lift ~5-13×. Designs valid experiments,
  reads them honestly (power, CIs), and never invents an effect size or claims correlation as cause.
---

# Skill — Incrementality / Geo-Lift Experiments

Answer the only question that matters for ROI: **what did the marketing actually cause?** —
the *incremental* conversions/revenue vs a counterfactual where the spend didn't happen. This is
the **causal source of truth** in the measurement stack: it validates everything else.

> **Doctrine — causality over correlation.** Observational and last-touch methods **systematically
> overstate lift ~5-13×** (Gordon, Moakler & Zettelmeyer, "Close Enough?", *Marketing Science*
> 2023, 663 Facebook RCTs). So **experiments are the truth layer**: incrementality results
> **calibrate MMM** (as priors) and **expose attribution bias** — never the reverse. **Never
> present a non-experimental number as causal.** A test only measures cause if it's **valid**:
> proper randomisation, adequate power, a clean control, and an honest read (CIs, not point hopes).
> **Never invent** an effect size, lift %, or p-value — measure/source it or label `[assumption —
> verify]`; unknown → "unknown". Report "no detectable incremental effect" when that's the result.

## Methods (choose by what's manipulable)
- **Geo holdout / geo-lift:** hold out matched geographies from a channel/campaign; compare
  treated vs control regions. Best when you can't randomise at user level (privacy-resilient).
- **Conversion-lift / ghost ads / PSA control:** randomise exposure at user level (platform
  lift tools); the control sees a placebo/no ad. Strong causality where available.
- **Switchback / on-off (pulsing) tests:** alternate spend on/off over time/regions; good for
  always-on channels and budget-level questions.
- **Quasi-experiments (matched-market, synthetic control, regression discontinuity):** when true
  randomisation is impossible — weaker, state the identifying assumptions explicitly.

## Procedure
1. **Define the causal question & decision:** which channel/campaign/budget level, what KPI
   (incremental conversions/revenue), and the decision the result will drive (scale/cut/hold).
2. **Choose the design:** match the method to what you can manipulate and the data available;
   prefer randomisation; if quasi-experimental, name the assumptions and threats to validity.
3. **Power & design the test:** pre-compute MDE, sample/geo count, and duration for the baseline
   and expected effect; define treatment/control, randomisation unit, and the holdout. An
   under-powered test can't prove anything — say so.
4. **Guard validity:** contamination/spillover between geos, seasonality, novelty, concurrent
   campaigns; pre-register the analysis; no peeking / no stopping early.
5. **Read honestly:** the incremental lift with a **confidence interval**, incremental cost per
   acquisition / iROAS, and whether it clears the decision threshold. A wide CI crossing zero is
   "inconclusive", not "it worked".
6. **Feed the stack:** results become **priors/calibration for MMM** and the **benchmark that
   exposes attribution over-counting**. State the read-across explicitly.
7. **Hand off:** calibration → mmm; bias correction → attribution-diagnostics; budget reallocation
   → budget-balance; the verdict → the Commander/Inspector. Flag data/privacy compliance → Inspector.

## Output format
```
INCREMENTALITY / GEO-LIFT — <channel / campaign / budget question>
Context detected: <B2B/B2C · market · stage>   |  Decision this drives: <scale/cut/hold>
⚠️ Causal truth layer. Observational/last-touch overstates lift ~5-13x (Gordon et al. 2023) — calibrate, don't trust.

CAUSAL QUESTION & KPI
  What we're testing · incremental KPI · decision threshold.

DESIGN
  Method: <geo-holdout / conversion-lift / switchback / quasi-exp> — why.
  Treatment vs control · randomisation unit · holdout · (quasi: identifying assumptions + threats).

POWER & VALIDITY
  MDE · sample/geo count · duration (pre-computed) · contamination/seasonality/novelty guards · pre-registered. No peeking.

RESULTS (when run)
  Incremental lift + CONFIDENCE INTERVAL · incremental CPA / iROAS · clears threshold? 
  ⚠️ CI crossing zero = inconclusive, not "worked". "No detectable effect" reported if so.

READ-ACROSS TO THE STACK
  → calibrates MMM (priors) · → exposes attribution over-count · → informs budget-balance.

SOURCES (every effect size / benchmark cited; nothing invented)
  - Gordon, Moakler & Zettelmeyer, "Close Enough?" (Marketing Science 2023) · <test data / category sources>.
```
