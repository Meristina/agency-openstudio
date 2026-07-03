---
name: beta-program
description: >-
  Structures a rigorous beta program from pre-launch pre-mortem through
  progressive rollout to mandatory learning review. Use when a team is about
  to release a feature or product to a limited cohort and needs kill thresholds,
  blast-radius containment, organizational readiness gates, and sequential
  statistical testing — not anecdote collection. Produces a complete beta brief
  with predefined closure criteria and a COE-equivalent learning artefact.
---

# Skill — Beta Program (Pre-mortem · Kill Threshold · Progressive Rollout · COE Close)

A beta program is a time-boxed, statistically governed release to a limited cohort,
designed to generate falsifiable evidence before full rollout — not to build goodwill
or de-risk politically. Its value comes from three structural disciplines working
together: blast-radius containment (limiting the scope of any failure through
progressive delivery architecture), sequential statistical testing (detecting signal
early without inflating false-positive rates), and a predefined kill threshold
(the specific metric level at which the feature is cancelled, not renegotiated).
Without a kill threshold set before launch, a beta program accumulates organizational
debt rather than learning — O5 doctrine upgrade #5: 'Beta programs without a kill
threshold are theater.' At close, the learning review converts outcomes into systemic
improvements, functioning as the equivalent of Amazon's Correction of Errors process.

> **Doctrine:** Every factual claim cites a real source (author/firm/year). The
> ABlaze sequential testing reference is Netflix's published methodology for
> early stopping with false-positive rate control — cite the Netflix Tech Blog.
> The Bain Change Power Index belongs to Bain & Company's Results Delivery
> framework — cite Bain & Company, not a proxy. The blast-radius framing is
> Spotify's; cite Kniberg & Ivarsson (2012) or Spotify Engineering Culture (2014).
> The COE close artefact belongs to Amazon; cite Bryar & Carr, Working Backwards
> (2021). The circuit breaker analogy cites Ryan Singer, Shape Up (2019).
> Never invent a rollout percentage, a CPI threshold, or a statistical power claim.
> Unknown → say "unknown [assumption — verify]".

## Procedure

1. **Run the pre-mortem — enumerate all failure modes before launch.** Before any
   cohort is recruited, hold a structured pre-mortem: assume the beta has failed
   and work backward to name every plausible cause. Categorize failure modes as
   technical (crashes, latency regressions, data loss), product (adoption, task
   completion, satisfaction collapse), and organizational (team unready, support
   overload, escalation cascade). This discipline is drawn directly from Amazon's
   COE culture, where pre-launch failure enumeration is required — not optional —
   before high-risk releases (Bryar & Carr, Working Backwards, 2021, Ch. 5).
   Document each failure mode with a detection method and a response owner.

2. **Define the kill threshold — one metric, one number, one date — before launch.**
   The kill threshold is the non-negotiable criterion: if the primary outcome metric
   (retention, task success, error rate, or the governing north-star input) does not
   clear this threshold by a predefined date, the feature is cancelled and not
   extended. The threshold is set before the beta opens. No automatic extension is
   permitted — structurally analogous to Shape Up's circuit breaker, where passive
   continuation is eliminated and every recommitment is an active decision (Singer,
   Shape Up, Basecamp/37signals, 2019, Ch. 12). O5 anti-pattern: 'Beta sans kill
   threshold' — the correction is a metric, threshold, and deadline locked before
   the cohort sees the feature.

3. **Run the Bain Change Power Index as an organizational readiness gate.**
   Before widening the cohort beyond the initial 1% slice, measure organizational
   readiness across three dimensions: leadership alignment, middle management support,
   and frontline readiness. All three must clear their respective thresholds before
   the rollout advances. This gate operationalizes Bain & Company's Results Delivery
   framework Change Power Index (Bain & Company, Results Delivery, 2012): programs
   that scale before the organization is ready predictably produce escalation risk
   that the governance cadence must absorb. Document CPI scores and block the rollout
   expansion if any dimension falls below threshold; do not bypass the gate.

4. **Architect blast-radius containment using feature flags.** Implement the
   progressive delivery architecture before opening the beta. Feature flags enable
   a 1% user release with rollback possible in minutes, structurally limiting the
   blast radius of any incident. This is Spotify's canonical approach: canary
   releases and feature toggles separate deployment from rollout, so a defect in
   production never automatically reaches the full user base (Spotify Engineering
   Culture, Henrik Kniberg, 2014; Kniberg & Ivarsson, Scaling Agile @ Spotify,
   2012). Record the rollout gates — 1% → 10% → 50% → 100% — with explicit go/no-go
   criteria at each step. Confirm rollback SLA (target: under 5 minutes) before
   the beta opens.

5. **Apply sequential statistical testing — Netflix ABlaze approach.** Use a
   sequential testing framework rather than a fixed-horizon A/B test. Sequential
   testing enables early stopping when evidence is sufficiently strong while
   controlling the false-positive rate — eliminating the peeking anti-pattern, where
   analysts check results continuously against a fixed-sample p-value threshold and
   inflate Type I error. Netflix's ABlaze platform implements this discipline as the
   default for experimentation: continuous monitoring with false-positive rate control
   built into the stopping rule (Netflix Technology Blog, "Improving Experimentation
   Efficiency at Netflix with Meta-Analysis and Optimal Stopping", 2021). Pre-register
   the primary metric, the minimum detectable effect, and the sequential stopping
   boundary before the beta opens; do not adjust these post-launch.

6. **Execute the staged rollout — 1% → 10% → 50% → 100% — with kill-or-continue
   decisions at each gate.** At each rollout gate, evaluate: (a) has the primary
   metric cleared its directional target? (b) have error rates and latency stayed
   within SLAs? (c) has the Bain CPI cleared the readiness threshold for the next
   cohort size? (d) have any pre-mortem failure modes triggered? A 'continue'
   decision at each gate must be explicit and documented — not a default. If any gate
   criterion fails, the kill threshold check runs immediately. Rollback via feature
   flag if the kill threshold is breached; do not negotiate a soft extension.

7. **Conduct the learning review — COE-equivalent artefact — at beta close.**
   Whether the beta ends in full rollout, a kill decision, or a pivot, produce a
   structured learning artefact equivalent to Amazon's Correction of Errors document
   (Bryar & Carr, Working Backwards, 2021). The artefact contains: (a) what we
   believed before the beta opened (pre-registered hypotheses and kill threshold);
   (b) what the data showed (primary metric, secondary signals, failure modes
   triggered); (c) what we got wrong and why; (d) systemic improvement — process,
   tooling, or architecture change that prevents the same failure class in future
   betas. The COE is not a project retrospective — it is a systemic improvement
   mechanism. Distribute it to the squad, the O5 officer, and the SteerCo.

## Output format

```
BETA PROGRAM BRIEF — <product / feature / context>
Context detected: <B2B/B2C · sector · stage>

PRE-MORTEM — FAILURE MODE REGISTER
  Technical failures  : [crash / latency / data loss scenarios — each with detection method and owner]
  Product failures    : [adoption collapse / task failure / satisfaction drop — metric + trigger]
  Organizational risks: [support overload / escalation / CPI gap — owner + response]

KILL THRESHOLD (locked before launch — no automatic extension)
  Primary metric      : [metric name]
  Threshold           : [specific value or direction — e.g., D30 retention ≥ 42%]
  Deadline            : [date — not a rolling window]
  Kill decision owner : [single named role]
  Rollback SLA        : [target time to rollback via feature flag — e.g., < 5 min]

CHANGE READINESS GATE — Bain Change Power Index
  Leadership alignment      : [score or status — threshold / current]
  Middle management support : [score or status — threshold / current]
  Frontline readiness       : [score or status — threshold / current]
  Gate decision             : [PASS / BLOCKED — reason if blocked]
  Next CPI check            : [trigger point — e.g., before 10% → 50% expansion]

BLAST-RADIUS ARCHITECTURE
  Feature flag system : [tooling — e.g., LaunchDarkly, Unleash, custom]
  Rollout gates       : 1% → 10% → 50% → 100%
  Go/no-go criteria   : [metric thresholds and CPI gate at each step]
  Rollback confirmed  : [Yes/No — SLA: <N minutes]

STATISTICAL TESTING PROTOCOL — Sequential / ABlaze approach
  Primary metric      : [name — pre-registered, not changed post-launch]
  Min detectable effect: [% or absolute — pre-registered]
  Stopping rule       : [sequential boundary — e.g., mSPRT or alpha-spending]
  Anti-pattern avoided: [peeking on fixed-sample p-value — explicitly blocked]
  Monitoring cadence  : [daily / weekly — with designated analyst]

ROLLOUT PLAN
  1%  gate  : criteria → [list] | date →
  10% gate  : criteria → [list] | date →
  50% gate  : criteria → [list] | date →
  100% gate : criteria → [list] | date →

LEARNING REVIEW — COE Artefact (at close)
  Pre-registered hypotheses: [what we believed before launch]
  Outcome vs. hypothesis   : [what the data showed]
  What we got wrong        : [specific misses — do not soften]
  Systemic improvement     : [process / tooling / architecture change — owner + timeline]
  Distribution list        : [squad · O5 officer · SteerCo]

SO-WHAT / NEXT STEPS
  - [Kill / continue / pivot recommendation with primary metric evidence]
  - [Organizational readiness gap to address before scaling]
  - [Systemic improvement to implement before next beta]
  - [Handoff to SteerCo governance cadence if escalation risk surfaced]

SOURCES (every external fact cited; nothing invented)
  - Bryar & Carr — Working Backwards, St. Martin's Press (2021) — Amazon COE discipline
  - Netflix Technology Blog — "Improving Experimentation Efficiency at Netflix with
    Meta-Analysis and Optimal Stopping" (2021) — ABlaze sequential testing
  - Bain & Company — Results Delivery framework, Change Power Index (2012)
  - Kniberg & Ivarsson — "Scaling Agile @ Spotify" (2012) — blast-radius architecture
  - Henrik Kniberg — Spotify Engineering Culture, Parts 1 & 2 (2014) — feature flags
  - Ryan Singer — Shape Up, Basecamp/37signals (2019) — circuit breaker / no auto-extension
```
