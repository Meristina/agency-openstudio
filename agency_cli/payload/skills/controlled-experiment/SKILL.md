---
name: controlled-experiment
description: >-
  Produces a complete A/B experiment brief — pre-registered hypothesis, primary metric,
  counter-metrics, MDE with power calculation (α=0.05, 80% power), and a pre-mortem
  enumerating failure modes — before any code is written. Use when a product team needs
  to validate a causal claim about a change (UX, copy, pricing, algorithm) through
  random assignment rather than observational data. Outputs a structured experiment
  record that gates engineering work on statistical rigour, not intuition.
---

# Skill — Controlled Experiment (A/B Test)

A controlled experiment randomly assigns users to a treatment condition (the change) and a
control condition (the status quo), then measures the causal effect on a pre-defined primary
metric. Random assignment is what separates A/B testing from before/after comparisons and
makes causal attribution possible. Google's Weblab platform has run more than 12,000
experiments per year, establishing the canonical industrial benchmark for experimentation
throughput (Google, various; Kohavi, Longbotham et al., "Controlled Experiments on the Web",
2009). Netflix operates ABlaze with thousands of experiments running simultaneously. The
throughput these organisations achieve is only possible when the cognitive and process cost
of launching each experiment decreases continuously — which requires a mandatory pre-registration
discipline that catches under-powered and ambiguously defined tests before they consume
engineering resources. Forsgren, Humble, and Kim (Accelerate, 2018) establish power calculation
at α=0.05 and 80% power as the software-industry standard for minimum statistical rigour;
experiments with higher downside risk (pricing, trust-sensitive features) should be elevated
to 90% power. The peeking anti-pattern — stopping a test early at first positive results or
running post-hoc power calculations on a completed test — is the primary source of false
positives in product experiment libraries (Johari et al., "Peeking at A/B Tests", 2015).

> **Doctrine:** Cite Kohavi et al. (2009, 2020) for controlled experiment methodology;
> Forsgren et al. (Accelerate, 2018) for power calculation standards; Johari et al. (2015)
> for the peeking anti-pattern. MDE benchmarks by test type: layout and UX changes require
> 5–15% relative lift to be practically meaningful; copy and messaging 10–20%; pricing and
> discount changes 2–5% (Google Weblab internal benchmarks, cited in Kohavi et al., 2020;
> [assumption — verify exact values against Kohavi, "Trustworthy Online Controlled
> Experiments", Cambridge, 2020]). Never cite "50% of features are never used" — origin
> is untraceable. Never treat a statistically significant result that arrived before the
> pre-stated observation window as valid — the p-value is not interpretable. Unknown
> data → say "unknown [assumption — verify]".

## Procedure

1. **Pre-register the hypothesis.** Before writing a single line of code or configuring
   any experiment tooling, document the falsifiable hypothesis in writing: "We believe
   [treatment] will cause [primary metric] to change by at least [MDE threshold] because
   [causal mechanism], measured over [observation window] on [target population]." The
   causal mechanism must be explicit — it is what distinguishes a hypothesis from a wish.
   Pre-registration is not bureaucracy; it is the statistical contract that makes the
   p-value interpretable. Organisations without pre-registration accumulate a library of
   false-positive features that fail to replicate (Johari et al., 2015).

2. **Define the primary metric and counter-metrics.** The primary metric is the single
   observable outcome the experiment is designed to move; it must be measurable within
   the observation window and directly connected to the causal mechanism in the hypothesis.
   Counter-metrics are guardrail indicators that, if they move adversely during the
   experiment, signal that the treatment is causing harm the primary metric does not
   capture — for example, a checkout flow change may lift conversion (primary) while
   degrading customer support contact rate (counter). Define both before launch; adding
   counter-metrics after results are known is p-hacking by another name. Avoid composite
   scores as primary metrics — they obscure the direction of individual component
   movements and make replication impossible.

3. **Calculate MDE and required sample size.** The Minimum Detectable Effect (MDE) is
   the smallest relative lift that would be practically meaningful to the business —
   not the smallest effect the team hopes to detect. Reference benchmarks by test type:
   layout and UX changes, 5–15% relative lift; copy and messaging, 10–20%; pricing and
   discount changes, 2–5% (Kohavi et al., "Trustworthy Online Controlled Experiments",
   Cambridge, 2020; [assumption — verify exact thresholds]). With MDE, baseline
   conversion rate, α=0.05, and 80% power (elevated to 90% for high-downside experiments),
   compute required sample size per variant using a standard power calculator. If the
   required sample size exceeds the available traffic within a reasonable observation
   window, increase the MDE or reduce scope — never reduce α or power to hit a convenient
   number. Document the calculation and its inputs as part of the experiment record.

4. **Identify subgroups for stratified analysis.** Before launch, enumerate which user
   segments will be analysed separately in addition to the aggregate result. Mandatory
   candidates: new vs. returning users (novelty effect differential), mobile vs. desktop,
   high-value vs. low-value cohorts, and any segment where the causal mechanism is
   expected to operate differently. Stratifying in advance prevents Simpson's paradox
   (an aggregate result that masks a reversed pattern in a subgroup) from producing a
   misleading aggregate signal. If a subgroup analysis was not pre-registered, it is
   exploratory — label it explicitly and do not use it as the basis for a go decision.

5. **Run the pre-mortem.** Before any code ships or traffic splits, enumerate all ways
   this experiment can produce a misleading result. At minimum address three failure modes:
   (a) Simpson's paradox — identify which subgroups could reverse the aggregate result
   and confirm they are included in the stratified analysis plan. (b) Novelty effect —
   new or returning users may change behaviour in week one purely due to curiosity;
   define the minimum observation window (typically two full business cycles) required
   to clear the novelty window and reach behavioural steady state. (c) Network effect
   contamination — if treated and control users interact (social features, referral
   loops, marketplace supply/demand), the control group is not pure; determine whether
   randomised holdout is valid or whether a geographic holdout (incrementality testing)
   or cohort-based split is required. Incrementality testing via geographic holdout is
   used by 52% of US brand and agency marketers as of 2025–2026 for this reason
   (eMarketer / Advertiser Perceptions, 2025; [assumption — verify exact figure]).
   Document all failure modes in the same artefact as the hypothesis; a pre-mortem
   discovered after launch is a post-mortem.

6. **Execute the experiment without peeking.** Run the experiment for the full
   observation window established by the sample size calculation. Do not examine the
   primary metric against the significance threshold until the observation window closes.
   Peeking at interim results and stopping early at first positive significance inflates
   the false positive rate from 5% to as high as 26% at interim checkpoints (Johari et
   al., "Peeking at A/B Tests: Why It Matters and What to Do About It", 2015). If
   continuous monitoring is operationally required, use sequential testing methods (e.g.,
   always-valid p-values, mSPRT) designed for that purpose — do not use standard fixed-
   horizon p-values on interim data. Monitor counter-metrics and guardrail metrics
   throughout the window and pause for harm, not for positive signal.

7. **Analyse results against the pre-stated hypothesis.** At observation window close,
   compare the primary metric result to the MDE threshold with the pre-stated α and power.
   A result that is statistically significant and meets or exceeds the MDE in the predicted
   direction is a supported hypothesis — not proven truth, but sufficient evidence to
   proceed. A result below MDE is inconclusive regardless of p-value — it means the
   experiment was not powered to detect an effect this small, not that there is no effect.
   A result in the wrong direction is a refuted hypothesis. Run all pre-registered
   subgroup analyses and flag any Simpson's paradox pattern. Never run post-hoc power
   calculations on a completed test — they are mathematically circular and statistically
   invalid (Forsgren et al., Accelerate, 2018).

8. **Issue a go/no-go decision and document the learning.** Compare the full result
   profile — primary metric, counter-metrics, subgroup analyses — to the pre-registered
   hypothesis and MDE threshold. Issue a clear verdict: GO (ship and monitor), NO-GO
   (do not ship; update the causal model), or REDESIGN (inconclusive; increase sample
   size or revise the MDE). Record the experiment outcome in the team's experiment log
   with the full record: hypothesis, MDE, results, subgroup findings, and the causal
   interpretation. The Amazon Weblab flywheel — established in 2011, running at 12,000+
   experiments per year — is achievable only when every experiment, including failed ones,
   produces a documented causal learning that informs the next experiment design (Kohavi
   et al., 2020). Hand off shipping decisions to soldier-feature-flags (if applicable)
   or the O6 officer for cross-functional coordination.

## Output format

```
CONTROLLED EXPERIMENT — <product / feature / change>
Context detected: <B2B/B2C · sector · stage>

PRE-REGISTRATION RECORD
  Hypothesis:          We believe [treatment] will cause [primary metric] to change by
                       at least [MDE] because [causal mechanism], measured over
                       [observation window] on [target population]
  Registered:          [date — before any code ships]
  Test type:           [A/B / multivariate / holdout / geo-based incrementality]

PRIMARY METRIC & COUNTER-METRICS
  Primary metric:      [single observable outcome; no composite scores]
  Counter-metrics:     [guardrail indicators; adverse movement = harm signal]
  Excluded metrics:    [any metric explicitly excluded from the go/no-go rule, and why]

POWER CALCULATION
  MDE:                 [minimum relative lift meaningful to the business] — benchmark: [UX 5–15% / copy 10–20% / pricing 2–5%]
  Baseline rate:       [current conversion rate or metric value]
  α (significance):    0.05
  Power:               80% (or 90% — reason: [high-downside feature])
  Required n/variant:  [N] users
  Estimated duration:  [days at current traffic]
  Traffic split:       [50/50 or other; reason for asymmetric split if used]

SUBGROUP ANALYSIS PLAN (pre-registered)
  Segment 1:           [new vs. returning — novelty effect check]
  Segment 2:           [mobile vs. desktop — if UX change]
  Segment 3:           [high-value vs. low-value cohort — if revenue metric]
  [add segments specific to the causal mechanism]

PRE-MORTEM
  Simpson's paradox:   [which subgroups could reverse the aggregate; confirmed in plan above]
  Novelty effect:      [minimum observation window; risk level: low/medium/high]
  Network contamination: [network structure present? yes/no; split design: random / geo holdout / cohort]
  Other failure modes: [additional risks specific to this experiment design]
  Peeking guardrail:   [fixed-horizon or sequential method; no interim stopping on primary metric]

RESULTS (complete after observation window closes)
  Primary metric:      [observed lift] vs MDE [value] → [met / not met / wrong direction]
  Significance:        p = [value]; confidence interval: [lower, upper]
  Counter-metrics:     [observed movement] → [no harm / harm detected]
  Subgroup findings:   [any Simpson's paradox pattern; novelty decay observed yes/no]
  Qualitative signals: [customer verbatims or support signals corroborating or contradicting]

GO / NO-GO DECISION
  Verdict:             [GO — ship / NO-GO — do not ship / REDESIGN — inconclusive]
  Rationale:           [primary metric vs MDE + counter-metric status + subgroup result]
  Causal interpretation: [what the result tells us about the causal mechanism in the hypothesis]
  Next experiment:     [what the result implies for the subsequent test design]

SO-WHAT / NEXT STEPS
  - [Primary action: ship / descope / iterate based on verdict]
  - [Subgroup insight requiring a follow-up targeted experiment if detected]
  - [Experiment log entry: confirm hypothesis + MDE + result + causal learning recorded]
  - [Handoff target: soldier-feature-flags for rollout, or O6 officer for cross-functional coordination]

SOURCES (every external fact cited; nothing invented)
  - Ron Kohavi, Roger Longbotham et al. — "Controlled Experiments on the Web: Survey and
    Practical Guide", Data Mining and Knowledge Discovery (2009) — foundational A/B
    methodology; Google Weblab scale reference
  - Ron Kohavi, Diane Tang, Ya Xu — Trustworthy Online Controlled Experiments: A Practical
    Guide to A/B Testing, Cambridge University Press (2020) — MDE benchmarks by test type;
    Amazon Weblab 2011 flywheel; peeking anti-pattern
  - Nicole Forsgren, Jez Humble, Gene Kim — Accelerate: The Science of Lean Software and
    DevOps, IT Revolution Press (2018) — α=0.05 / 80% power as software-industry standard;
    post-hoc power calculation invalidity
  - Ramesh Johari, Pete Koomen, Leonid Pekelis, David Walsh — "Peeking at A/B Tests: Why
    It Matters and What to Do About It", KDD (2015) — peeking inflates FPR from 5% to 26%
  - eMarketer / Advertiser Perceptions — US Incrementality Testing Adoption (2025)
    [assumption — verify exact 52% figure against primary source]
```
