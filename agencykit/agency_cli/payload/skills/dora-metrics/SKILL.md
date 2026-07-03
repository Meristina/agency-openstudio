---
name: dora-metrics
description: >-
  Measures and interprets the five DORA delivery performance metrics —
  Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time
  to Recover, and Rework Rate — benchmarks them against elite/high/medium/low
  performer bands, audits the three architectural prerequisites, and positions
  Value Stream Mapping as a structural diagnostic complement. Use when a team
  wants to establish a delivery performance baseline, identify the binding
  constraint in their software delivery system, or prepare an evidence-backed
  case for engineering investment. Produces a scored DORA block with benchmark
  gaps, architectural audit, and prioritised next steps.
---

# Skill — DORA Five Metrics

DORA (DevOps Research and Assessment) is the only empirically validated framework
for measuring software delivery performance. Originating from research by Nicole
Forsgren, Jez Humble, and Gene Kim — synthesised in Accelerate (2018) and extended
annually through the State of DevOps Report — DORA identifies four throughput and
stability metrics that consistently predict organisational performance: Deployment
Frequency, Lead Time for Changes, Change Failure Rate, and Mean Time to Recover.
The 2024 State of DevOps Report introduced Rework Rate as a fifth metric, measuring
the proportion of work that must be redone, thereby capturing quality debt in the
delivery pipeline. Elite performers show gaps of 182x more frequent deployments and
127x faster lead time versus low performers (Forsgren, Humble, Kim, Accelerate, 2018).
The framework matters for product management because it provides lagging outcome
indicators that translate engineering investment into board-level language — and
because it pairs with Value Stream Mapping and Little's Law to form a complete
diagnostic chain from symptom to root cause to intervention.

> **Doctrine:** Cite Forsgren, Humble, Kim — Accelerate (2018) for the four core DORA
> metrics and elite/low performer benchmarks. Cite the DORA 2024 State of DevOps Report
> for Rework Rate as the fifth metric. Cite the Lean Enterprise Institute / Toyota TPS
> finding for the 70–90% wait-time statistic. Cite Little's Law (John D.C. Little, 1961)
> for the WIP-cycle-time relationship. Cite Forsgren, Storey et al. (ACM Queue, 2021)
> for the SPACE Framework. Never invent a benchmark, elite threshold, or percentage —
> research every external figure and cite it. If a team's data is unavailable, label
> the field "[assumption — verify]". Change Failure Rate and Lead Time for Changes are
> the empirically validated lagging indicators of technical debt presentable to executives.

## Procedure

1. **Establish context and current baselines.** Identify the team or organisation scope
   (single squad, product area, or organisation-wide), the deployment target (production,
   staging, feature flags), and the measurement window (trailing 90 days is the standard
   DORA window). Collect or estimate current values for all five metrics. If data is
   unavailable, proceed with directional estimates and tag each as "[assumption — verify]".
   Note whether DORA metrics are tracked automatically (CI/CD instrumentation) or manually
   (post-incident reviews, sprint retrospectives).

2. **Score each metric against DORA bands.** Map each metric to its performer band — Elite,
   High, Medium, or Low — using the validated thresholds from Accelerate (2018) and the
   annual State of DevOps Report. Deployment Frequency: Elite = on-demand (multiple deploys
   per day); High = between once per day and once per week; Medium = between once per week
   and once per month; Low = between once per month and once every six months. Lead Time for
   Changes: Elite = less than one hour; High = between one day and one week; Medium = between
   one week and one month; Low = between one month and six months. Change Failure Rate: Elite
   = 0–5%; High/Medium = 10–15%; Low = 46–60%. Mean Time to Recover: Elite = less than one
   hour; High = less than one day; Medium = between one day and one week; Low = between one
   week and one month. Rework Rate (2024): flag percentage of work items requiring rework;
   no fixed band thresholds published at time of writing — track directionally and compare
   quarter over quarter (DORA 2024 State of DevOps Report).

3. **Identify the binding constraint using the DORA diagnostic hierarchy.** Do not treat all
   five metrics equally. Apply the Theory of Constraints lens (Goldratt, The Goal, 1984):
   identify the single metric furthest from its elite band — that is the most likely binding
   constraint. A long Lead Time for Changes almost always points to a queue or handoff
   bottleneck, not individual developer speed. A high Change Failure Rate points to insufficient
   test automation coverage or a tightly coupled architecture. A slow Mean Time to Recover
   points to observability debt or manual incident response. Rework Rate elevations point to
   upstream discovery or requirements quality failure.

4. **Audit the three architectural prerequisites for elite performance.** Elite DORA scores
   require three structural conditions — not practices, not tooling, but architectural choices
   (Forsgren, Humble, Kim, Accelerate, 2018). Audit each explicitly: (1) Trunk-based
   development: are all engineers integrating to a shared trunk at least daily? Long-lived
   feature branches are a structural blocker to high Deployment Frequency and short Lead Time.
   (2) Full test automation: does the pipeline gate deploys on a comprehensive automated test
   suite? Manual QA gates are the dominant cause of Lead Time inflation. (3) Loosely coupled
   architecture: can a team deploy their service without coordinating a release window with
   other teams? Tight coupling converts Change Failure Rate and Mean Time to Recover into
   organisation-wide blast radius metrics. Flag each prerequisite as Met, Partial, or Absent.

5. **Apply Little's Law to quantify the WIP reduction opportunity.** Little's Law states:
   average cycle time = average WIP / average throughput (Little, 1961). This is not a
   heuristic — it is an algebraic identity. If a team's Lead Time for Changes is above the
   elite threshold, compute the implied WIP reduction needed to reach elite without increasing
   team size. The Lean Enterprise Institute and Toyota TPS research indicates that 70–90% of
   software delivery lead time is wait time between functions — queues and handoffs, not
   execution time (Gene Kim, The Phoenix Project, 2013). Therefore, investments in individual
   developer speed have near-zero effect when the real constraint is a QA bottleneck or a
   deployment approval gate. Quantify this explicitly in the output.

6. **Position Value Stream Mapping as the structural diagnostic complement.** DORA metrics
   measure the magnitude of the delivery gap; Value Stream Mapping (VSM) locates where in
   the value stream the gap lives. VSM + Little's Law + Theory of Constraints constitutes
   the full diagnostic chain: symptom (DORA scores) → root cause (constraint location in the
   value stream) → intervention (CI/CD automation, WIP limits, handoff elimination). If DORA
   scores are materially below elite across multiple metrics, recommend a VSM exercise scoped
   to the delivery value stream as the next diagnostic step. Hand off VSM work to
   soldier-vsm-flow-analyst.

7. **Reference the SPACE Framework for multidimensional completeness.** DORA measures delivery
   outcomes (throughput and stability). The SPACE Framework — Satisfaction, Performance,
   Activity, Communication/Collaboration, and Efficiency/Flow — adds individual and team
   dimensions that DORA does not capture (Forsgren, Storey et al., ACM Queue, 2021). Where
   DORA scores are declining despite engineering investment, flag whether SPACE dimensions
   (particularly Satisfaction and Efficiency) may be masking a developer experience constraint
   that DORA cannot surface alone.

8. **Produce the output block with benchmark gaps and prioritised next steps.** Format the
   full DORA block using the output template below. Every metric must show current value,
   performer band, gap to elite, and the implied architectural root cause. End with SO-WHAT /
   NEXT STEPS that name the single highest-leverage intervention — not a list of five equally
   weighted actions. Cite every external benchmark; nothing in the output may be invented.

## Output format

```
DORA FIVE METRICS — <product / team / organisation>
Context detected: <B2B/B2C · sector · stage>
Measurement window: <trailing 90 days | [assumption — verify]>

METRIC SCORECARD
  Deployment Frequency
    Current:       <value — e.g. "twice per week">
    Performer band: <Elite | High | Medium | Low>
    Elite threshold: on-demand (multiple per day)  [Accelerate, 2018]
    Gap to elite:  <delta>

  Lead Time for Changes
    Current:       <value — e.g. "4 days">
    Performer band: <Elite | High | Medium | Low>
    Elite threshold: < 1 hour  [Accelerate, 2018]
    Gap to elite:  <delta>

  Change Failure Rate
    Current:       <value — e.g. "18%">
    Performer band: <Elite | High | Medium | Low>
    Elite threshold: 0–5%  [Accelerate, 2018]
    Gap to elite:  <delta>

  Mean Time to Recover
    Current:       <value — e.g. "2 days">
    Performer band: <Elite | High | Medium | Low>
    Elite threshold: < 1 hour  [Accelerate, 2018]
    Gap to elite:  <delta>

  Rework Rate (5th metric — DORA 2024)
    Current:       <% of work items requiring rework>
    Trend:         <Improving | Stable | Degrading>
    Band:          <no fixed thresholds published — track directionally>

BINDING CONSTRAINT (Theory of Constraints — Goldratt, 1984)
  Most lagging metric: <metric name>
  Root cause hypothesis: <architectural / process / tooling>
  Little's Law implication: avg cycle time = avg WIP / avg throughput
    Implied WIP reduction to reach elite without headcount increase: <calculation or [assumption — verify]>
  Wait-time share: 70–90% of delivery lead time is queue/handoff, not execution
    [Lean Enterprise Institute / Toyota TPS; Kim, The Phoenix Project, 2013]

ARCHITECTURAL PREREQUISITES AUDIT  [Forsgren et al., Accelerate, 2018]
  (1) Trunk-based development:      <Met | Partial | Absent — evidence>
  (2) Full test automation:         <Met | Partial | Absent — evidence>
  (3) Loosely coupled architecture: <Met | Partial | Absent — evidence>
  Prerequisites absent: <count> — elite DORA performance structurally blocked until resolved

ELITE vs LOW PERFORMER REFERENCE GAPS  [Accelerate, 2018]
  Deployment Frequency:   182x more frequent (elite vs low)
  Lead Time for Changes: 127x faster (elite vs low)
  Change Failure Rate:    3x lower (elite vs low)
  MTTR:                   2,604x faster (elite vs low)

DIAGNOSTIC COMPLEMENT
  VSM recommendation: <Yes — map delivery value stream to locate constraint | No>
  SPACE Framework gaps: <Satisfaction / Performance / Activity / Communication / Efficiency>
    [Forsgren, Storey et al., ACM Queue, 2021]
  Hand off to: soldier-vsm-flow-analyst for value stream mapping

SO-WHAT / NEXT STEPS
  - Priority 1 (binding constraint): <single highest-leverage intervention>
  - Priority 2: <second action — architectural prerequisite or tooling>
  - Executive framing: CFR and LTFC are the empirically validated lagging indicators
    of technical debt load — use these for board-level investment cases

SOURCES (every external fact cited; nothing invented)
  - Forsgren, N., Humble, J., & Kim, G. Accelerate: The Science of Lean Software and
    DevOps. IT Revolution Press, 2018.
  - DORA. 2024 State of DevOps Report. Google Cloud / DORA, 2024.
    https://dora.dev/research/2024/dora-report/
  - Forsgren, N., Storey, M.-A., et al. "The SPACE of Developer Productivity."
    ACM Queue, Vol. 19, No. 1, 2021. https://queue.acm.org/detail.cfm?id=3454124
  - Kim, G., Behr, K., & Spafford, G. The Phoenix Project. IT Revolution Press, 2013.
  - Goldratt, E. M., & Cox, J. The Goal. North River Press, 1984.
  - Little, J. D. C. "A Proof for the Queuing Formula: L = λW." Operations Research,
    9(3), 383–387, 1961.
  - [Additional sources as needed — author, title, year, URL or [assumption — verify]]
```
