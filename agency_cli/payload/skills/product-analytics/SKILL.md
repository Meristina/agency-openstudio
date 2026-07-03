---
name: product-analytics
description: >-
  Builds a unified product measurement architecture integrating the NSM input-metrics
  tree, Amazon WBR dashboard discipline, Google HEART framework, and McKinsey Value
  Bridge. Use when a product team needs to move from output-metric dashboards to a
  causally structured system of controllable input metrics — producing a scored
  measurement architecture with ownership, cadence, and financial credibility layers.
---

# Skill — Product Measurement Architecture

Product measurement architecture is the structured design of a metric system that enables
product teams to act on leading indicators rather than trailing outcomes. The foundational
doctrine, articulated by Colin Bryar and Bill Carr in Working Backwards (2021), is that
managing output metrics — revenue, profit, conversion rate — is not product management.
The PM's job is identifying and moving controllable input metrics that causally produce
those outputs. Amazon characterises identifying the right input metrics as "deceptively
difficult and requiring repeated trial and error." This skill integrates four frameworks
into a unified architecture: the NSM input-metrics tree (amplitude hierarchy), the Amazon
Weekly Business Review (WBR) dashboard discipline, the Google HEART framework for UX
quality measurement, and the McKinsey Value Bridge for financial credibility. Together
they provide the causal chain from daily team decisions to board-level outcomes.

> **Doctrine:** Cite Bryar & Carr — Working Backwards (2021) for the WBR 200+ input
> metrics discipline and the input vs output metric distinction. Cite Rodden, Hutchinson,
> and Fu — "Measuring the User Experience on a Large Scale" (CHI, 2010) for the HEART
> framework. Cite Forsgren, Storey et al. (ACM Queue, 2021) for the SPACE Framework as
> the delivery-performance complement. Cite the McKinsey Value Bridge by firm and year.
> Never cite "50% of features are never used" (unsourced), NPS as the sole growth driver,
> or story-points as a productivity signal (Article I prohibition). Never position NPS
> as a North Star Metric — it is a guardrail metric only. Flag GDPR and CCPA obligations
> whenever behavioural instrumentation or user-level event tracking is introduced.

## Procedure

1. **Anchor to the North Star and confirm causal eligibility.** Before building the
   measurement architecture, verify that the team's North Star Metric (NSM) sits at
   the correct abstraction level — moveable by a coordinated portfolio of features over
   quarters, not by a single team shipping one feature. If the NSM fails this test, it
   is an operational KPI and must be elevated before input metrics are layered beneath
   it (Cutler, Amplitude North Star Playbook, 2019). Confirm the product type
   (B2B/B2C/marketplace/platform), growth stage (pre-PMF, scaling, mature), and primary
   business model — these determine which metric categories are structurally eligible.

2. **Apply the input/output causal inversion.** Audit the team's existing dashboard.
   Classify each current metric as input (controllable by the team, leading indicator)
   or output (lagging outcome of customer behaviour at scale). Flag every output metric
   that is being managed as if it were an input — this is the primary measurement failure
   mode. Output metrics such as revenue, DAU, and conversion rate are results; they cannot
   be directly pulled. Build the causal map: identify which controllable team actions move
   which input metrics, and which input metrics causally produce which output metrics.
   Amazon's WBR practice treats 200+ input metrics as the operational system and output
   metrics as the confirmation layer — reviewed weekly in 60 minutes (Bryar & Carr,
   Working Backwards, 2021).

3. **Build the NSM input-metrics tree (3–5 causal levers).** For the confirmed NSM,
   identify 3–5 directly influenceable input metrics that form a causal path from daily
   product decisions to NSM movement. Use the Amplitude North Star Playbook canonical
   dimensions as a structuring lens: adoption breadth, usage depth, frequency, efficiency,
   customer outcomes. Each lever must be owned by a named team or squad, must be
   measurable within a two-week sprint cycle, and must be directionally falsifiable —
   a team must be able to run an experiment that plausibly moves it. Reject any candidate
   lever that requires six months of observation to detect movement.

4. **Map HEART dimensions to the UX measurement layer.** The HEART framework — Happiness,
   Engagement, Adoption, Retention, Task Success — replaces the deprecated PULSE framework
   and provides a structured method for measuring UX quality upstream of business outcomes
   (Rodden, Hutchinson, Fu — CHI 2010). For each HEART dimension relevant to the product,
   define: (a) the Goal — what user behaviour or attitude the team wants to influence;
   (b) the Signal — an observable user action or attitude that indicates progress toward
   the Goal; (c) the Metric — the specific, measurable operationalisation of the Signal.
   Map HEART dimensions to OKR structure: Dimensions become Objectives; Signal/Metrics
   become Key Results. This gives HEART operational teeth. Note which dimensions require
   survey instrumentation (Happiness) versus event-based instrumentation (Engagement,
   Adoption, Retention, Task Success) and flag any GDPR/CCPA consent implications for
   user-level event collection.

5. **Construct the WBR dashboard using Amazon's controllable-input discipline.** Design
   the weekly review dashboard around input metrics, not output metrics. Each metric in
   the WBR must meet three criteria: (1) the team can influence it within a two-week
   cycle; (2) movement in the metric is causally upstream of at least one output metric;
   (3) the metric has a named owner who attends the weekly review. Structure the WBR to
   complete in 60 minutes or fewer: the first 40 minutes on metrics deviating from target
   (exception-based), the last 20 minutes on next-week commitments. Output metrics appear
   in the dashboard as confirmation, not as action items — if an output metric is
   off-target, the diagnosis must identify which input metric moved first.

6. **Build the McKinsey Value Bridge for financial credibility.** Construct a monthly
   metric ledger co-owned with Finance that separates one-time gains from run-rate
   improvements. For each input metric improvement, translate movement into financial
   impact: quantify the unit economics (e.g., a 1pp improvement in trial-to-paid
   conversion at current volume equals £X ARR), name the owner, and track actuals
   vs forecast monthly. This is the analogous infrastructure to the Oliver Wyman
   Transformation Cockpit. The Value Bridge makes product measurement legible to C-suite
   and investment committees by expressing metric movements in the financial language
   of the business — it is the accountability layer that prevents metric theatre.

7. **Define review rhythm, ownership, and the redefinition trigger.** Assign a named
   owner to every metric in the architecture. Establish three cadences: weekly (WBR input
   metrics — exception-based review), monthly (Value Bridge financial translation —
   Finance co-owned), and quarterly (HEART framework and NSM structural review). Define
   the conditions under which each metric's target or definition changes — metric
   definitions must be stable within a quarter; targets are quarterly hypotheses. Define
   the NSM redefinition trigger: product scope expansion, audience shift, business model
   change, or M&A event. Pre-specify; never discover post hoc.

8. **Produce the output block with full citations.** Render the complete measurement
   architecture using the output template below. Every metric must show its type
   (input/output), its causal connection upstream and downstream, its owner, and its
   review cadence. End with SO-WHAT / NEXT STEPS naming the single highest-leverage
   measurement gap. Cite every external framework and benchmark — nothing in the output
   may be invented or uncited.

## Output format

```
PRODUCT MEASUREMENT ARCHITECTURE — <product / context>
Context detected: <B2B/B2C · sector · stage>
NSM confirmed: <NSM name — or [to be defined]>

CAUSAL AUDIT (Input vs Output Classification)
  Output metrics currently managed as inputs (anti-pattern):
    - <metric name>: managed as if controllable — reclassify as confirmation layer
  Confirmed input metrics (controllable, leading):
    - <metric name>: owned by <team> · causal path → <output metric>

NSM INPUT-METRICS TREE  [Bryar & Carr, Working Backwards, 2021; Cutler, Amplitude, 2019]
  NSM: <North Star Metric>
  Causal lever 1: <metric name>
    Owner: <team/squad>
    Cadence: <weekly | sprint>
    Causal path: this metric → <intermediate metric> → NSM
  Causal lever 2: <metric name>
    Owner: ...
  [Repeat for 3–5 levers]

HEART FRAMEWORK MAPPING  [Rodden, Hutchinson, Fu — CHI 2010]
  Happiness
    Goal:   <what attitude the team wants to influence>
    Signal: <observable user action or survey response>
    Metric: <specific measurable operationalisation>
    Instrumentation: <survey | event-based>
    GDPR/CCPA note: <consent requirement or N/A>
  Engagement
    Goal / Signal / Metric: ...
  Adoption
    Goal / Signal / Metric: ...
  Retention
    Goal / Signal / Metric: ...
  Task Success
    Goal / Signal / Metric: ...

WBR DASHBOARD DISCIPLINE  [Bryar & Carr, Working Backwards, 2021]
  Weekly review structure:
    Minutes 0–40: exception review (metrics deviating from target — input metrics only)
    Minutes 40–60: next-week commitments per owner
  Metrics in WBR: <count> input metrics · <count> output confirmation metrics
  Exception flags this week:
    - <metric>: <direction and magnitude of deviation>
  Output metric confirmation (not action items):
    - <output metric>: <current value vs target>

McKINSEY VALUE BRIDGE  [McKinsey & Company — Value Bridge Framework]
  Financial translation cadence: monthly · co-owned with Finance
  Metric → Financial impact mapping:
    <Input metric> +1pp → £<X> ARR at current volume
    Owner: <name/role>
    Actual vs forecast: <current month>
  One-time gains vs run-rate improvements:
    One-time: <description and £ value>
    Run-rate: <description and £ value>
  C-suite legibility: <narrative summary for investment committee>

REVIEW RHYTHM & OWNERSHIP
  Weekly (WBR):     input metric exception review · <owner>
  Monthly (Value Bridge): financial translation · Finance co-owned · <owner>
  Quarterly (HEART + NSM): structural review · product leadership · <owner>
  NSM redefinition trigger: <explicit conditions — scope expansion / audience shift / M&A>

SO-WHAT / NEXT STEPS
  - Highest-leverage measurement gap: <single priority — e.g. "no instrumentation on
    Task Success — team cannot detect UX regressions upstream of conversion drop">
  - Second priority: <e.g. "Value Bridge not co-owned by Finance — metrics lack P&L credibility">
  - Third priority: <e.g. "WBR reviewing output metrics as action items — invert to input discipline">

SOURCES (every external fact cited; nothing invented)
  - Bryar, C. & Carr, B. Working Backwards: Insights, Stories, and Secrets from Inside
    Amazon. St. Martin's Press, 2021.
  - Rodden, K., Hutchinson, H., & Fu, X. "Measuring the User Experience on a Large Scale:
    User-Centered Metrics for Web Applications." CHI 2010.
    https://research.google/pubs/pub36299/
  - Cutler, J. North Star Playbook. Amplitude, 2019.
    https://amplitude.com/north-star
  - Forsgren, N., Storey, M.-A., et al. "The SPACE of Developer Productivity."
    ACM Queue, Vol. 19, No. 1, 2021. https://queue.acm.org/detail.cfm?id=3454124
  - McKinsey & Company. Value Bridge Framework. [assumption — verify specific report/year]
  - [Additional sources as needed — author, title, year, URL or [assumption — verify]]
```
