---
name: north-star
description: >-
  Defines, validates, and structures a product's North Star Metric using John Cutler's
  abstraction-level constraint (Amplitude, 2019). Produces a single compound output
  containing the NSM, mandatory counter-metrics, input metric tree, and structural audit
  against the NSM/OKR boundary. Use when a team needs a compass metric that sits above
  daily feature decisions and survives product scope expansion.
---

# Skill — North Star Metric

The North Star Metric (NSM) is the single metric that best captures the core value a product
delivers to its customers and serves as the primary long-range compass for the product
organisation. Its defining structural property, articulated by John Cutler in the Amplitude
North Star Playbook (2019), is that it must sit one level of abstraction above what any
individual team can directly manipulate: if shipping a feature moves the metric, the metric
is an operational KPI, not a North Star. The canonical dual-sided case is Airbnb's "Nights
Booked", which simultaneously captures supply-side host behaviour and demand-side guest
behaviour in a single number. The Meta evolution (DAU → DAU/MAU → Family Daily Active
People with cross-app deduplication) demonstrates that NSMs are structurally invalidated
when product scope expands; the redefinition cycle must be anticipated, not managed
reactively. Counter-metrics (guardrails) are a non-optional component: without named
guardrails, teams optimise the NSM while silently degrading unmeasured dimensions.

> **Doctrine:** Cite John Cutler / Amplitude North Star Playbook (2019) for the abstraction
> constraint and counter-metric requirement. Cite the Meta DAU→Family DAP evolution for
> scope-expansion invalidation. Cite Airbnb "Nights Booked" for dual-sided alignment.
> Draw the NSM/OKR boundary explicitly using Cutler's framing (compass vs. waypoints).
> Never invent a quote, statistic, or benchmark — research every external fact and cite it.
> NPS must never be named as a North Star Metric; it is a guardrail metric only (Article I).

## Procedure

1. **Characterise product and context.** Identify product type (B2B/B2C/marketplace/platform),
   growth stage (pre-PMF, PMF, scaling, mature), business model, and primary customer segment.
   These inputs determine which candidate NSM categories are structurally eligible; a B2B SaaS
   tool and a consumer social app have categorically different NSM shapes.

2. **Apply the abstraction-level gate.** For each candidate NSM, ask: "Can a single team move
   this metric by shipping one feature?" If yes, the candidate is an operational KPI, not a
   North Star. Discard it or elevate to the appropriate abstraction level. This gate is the
   primary structural rule from John Cutler (Amplitude North Star Playbook, 2019) and must
   be applied before any candidate advances.

3. **Audit for dual-sided and scope alignment.** For marketplace and platform products, verify
   that the candidate NSM captures both supply and demand behaviour simultaneously, following
   the Airbnb "Nights Booked" pattern. For multi-product or expanding-scope companies, check
   whether the candidate NSM will survive a portfolio expansion event; if not, design the
   redefinition trigger up front, as Meta did transitioning from DAU to Family Daily Active
   People (Amplitude North Star Playbook; Meta investor communications, 2021).

4. **Define mandatory counter-metrics.** Name a minimum of two guardrail metrics that detect
   degradation in unmeasured dimensions while the NSM is being optimised. Candidates include
   churn rate, support ticket volume, negative NPS, error rates, and time-to-value for new
   users. This requirement is non-optional per the constitution (Article IX, Check 3) and the
   Amplitude North Star Playbook doctrine: an NSM without named guardrails creates a
   single-dimensional optimisation trap.

5. **Build the input metric tree.** Identify 3 to 5 directly influenceable input metrics that
   form a causal path from daily product decisions to movement of the North Star. Per the
   Amplitude North Star Playbook, canonical input dimensions are: adoption breadth (who is
   using the product), usage depth (how completely they use it), frequency (how often),
   efficiency (how fast/easily), and customer outcomes (what they achieve). Teams that cannot
   name these input levers are managing an output metric, not a North Star.

6. **Draw the NSM/OKR boundary.** Explicitly distinguish the NSM (a directional compass
   providing orientation over quarters and years) from OKRs (quarterly hypothesis-driven
   waypoints). The NSM should not change every quarter; OKRs should. Collapsing both
   instruments into the same artefact destroys the benefit of each. Name one owner of the
   NSM (typically the CPO or equivalent) and confirm that OKRs at team level are expressed
   as movements in input metrics, not the NSM itself.

7. **Validate the redefinition trigger.** State the explicit conditions under which this NSM
   would need to be redefined: product scope expansion, audience shift, business model change,
   or acquisition of a complementary product line. This is the structural lesson from Meta's
   DAU → Family DAP transition; the trigger should be pre-specified, not discovered post hoc.

8. **Produce the output block.** Render the full structured output (see format below), ending
   with a SO-WHAT / NEXT STEPS section and a SOURCES section citing every external fact used.
   Nothing in the output may be uncited. Unknown facts are labelled "unknown".

## Output format

```
NORTH STAR METRIC — <product / context>
Context detected: <B2B/B2C · sector · stage>

NSM DEFINITION
  Metric name      : ...
  Metric formula   : ...
  Abstraction test : passes / FAILS — [reason if fails]
  Owner            : ...

DUAL-SIDED / SCOPE AUDIT
  Supply signal    : ...
  Demand signal    : ...
  Scope risk       : [what would invalidate this NSM and when]
  Redefinition trigger : ...

COUNTER-METRICS (mandatory guardrails — minimum 2)
  1. [metric name] — monitors: [what degradation it catches]
  2. [metric name] — monitors: [what degradation it catches]
  3. [optional additional guardrail]

INPUT METRIC TREE (3-5 influenceable levers)
  NSM: [name]
  ├── Adoption breadth  : [metric] — [how teams move it]
  ├── Usage depth       : [metric] — [how teams move it]
  ├── Frequency         : [metric] — [how teams move it]
  ├── Efficiency        : [metric] — [how teams move it]
  └── Customer outcomes : [metric] — [how teams move it]

NSM / OKR BOUNDARY
  NSM horizon    : [quarters / years]
  OKR horizon    : quarterly waypoints expressed as input metric movements
  Collapse risk  : [what is lost if the two instruments are merged]

REDEFINITION TRIGGER
  Condition      : [scope expansion / audience shift / model change / M&A]
  Precedent      : Meta DAU → Family Daily Active People (2021) — cross-app deduplication
                   required when portfolio expanded beyond a single surface

SO-WHAT / NEXT STEPS
  - ...

SOURCES (every external fact cited; nothing invented)
  - John Cutler / Amplitude — North Star Playbook (2019) — https://amplitude.com/north-star
  - Amplitude — North Star Playbook (product edition) — [assumption — verify URL]
  - Meta — Investor Communications / Earnings Calls (2021) — DAU → Family DAP transition
  - [Any additional sources used in this specific output]
```
