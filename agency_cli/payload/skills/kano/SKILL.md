---
name: kano
description: >-
  Classifies product attributes into must-haves, performance attributes, and delighters
  using the Kano survey protocol, then applies PMF Treadmill aging to timestamp each
  classification and a Kano × margin composite filter (Roland Berger Design-to-Value)
  to prevent investment in high-excitement attributes that destroy unit economics. Use
  when prioritising a feature backlog, validating a roadmap, or auditing whether historical
  classifications still hold. Produces a timestamped attribute map, a composite priority
  matrix, and a set of actionable next steps tied to real investment decisions.
---

# Skill — Kano Model with PMF Treadmill Aging

The Kano model (Noriaki Kano, 1984) classifies product attributes along three orthogonal
curves: must-be (basic) attributes whose absence causes dissatisfaction but whose presence
is invisible; one-dimensional (performance) attributes where more = more satisfaction
linearly; and attractive (excitement/delighter) attributes that surprise and delight when
present but generate no dissatisfaction when absent. A fourth, inverse category captures
attributes that actively annoy customers when present. The model was originally published as
"Attractive Quality and Must-Be Quality" in the Journal of the Japanese Society for Quality
Control (Vol. 14, No. 2, 1984). Its strategic significance is that it prevents teams from
over-investing in must-be attributes (beyond threshold) and from ignoring delighters that
actually drive differentiation. The PMF Treadmill enrichment (Casey Winters and Fareed
Mosavat, Reforge) adds a temporal axis: consumer expectations compound upward, so a 2020
delighter may already be a 2024 must-have. The Chegg case (2024) is the canonical failure
— 90% valuation collapse and 500,000 subscriber loss in ten months — driven precisely by
excitement attributes that had silently drifted to must-haves without re-survey. Roland
Berger's Design-to-Value (DtV) adds a cross-functional margin layer: variant-level teardown
identifies which features contribute margin versus which add complexity cost, replacing
satisfaction alone as the investment filter. Apple's portfolio coherence constraint (Steve
Jobs, documented by Adam Lashinsky, Inside Apple, 2012) adds a final gate: a highly rated
excitement attribute that dilutes product focus must still be cut.

> **Doctrine:** Every Kano classification must carry a datestamp; treat any classification
> older than 12 months as a hypothesis requiring re-validation, not a fact. Never cite
> "50% of features are never used" — this figure is untraceable. Never use NPS as the
> sole satisfaction input to a Kano survey. The PMF Treadmill is conceptual, not a
> calibrated statistical model — label any aging projections [assumption — verify] unless
> backed by a re-run survey. All Roland Berger DtV figures (e.g., 45% variant reduction)
> cite the firm's published reports; do not generalise to untested contexts. Research every
> external fact; invent nothing.

## Procedure

1. **Scope and context gate.** Before writing a single survey question, document: product
   name and stage (pre-PMF, growth, mature), B2B or B2C, primary user segment, and the
   strategic question this Kano run must answer (roadmap prioritisation, competitive
   benchmarking, cost reduction). Record the date — this is the classification timestamp.
   If a prior Kano run exists, retrieve its date; if >12 months old, flag as expired under
   the PMF Treadmill doctrine (Winters & Mosavat, Reforge). An expired map is treated as
   a hypothesis, not a finding.

2. **Attribute enumeration.** List every product feature or attribute under evaluation.
   Sources: product analytics (usage frequency by feature), customer support themes,
   sales objection logs, prior JTBD or user-interview outputs. Limit to 15–25 attributes
   per survey run; more than 25 produces respondent fatigue that degrades data quality
   (Nielsen Norman Group, survey design guidelines [assumption — verify exact threshold]).
   Each attribute must be stated as a specific, observable capability — not a vague value
   proposition.

3. **Kano survey design.** For each attribute, write one functional question ("How would
   you feel if this feature were present?") and one dysfunctional question ("How would you
   feel if this feature were absent?"). Use the standard 5-point Kano response scale:
   (1) I like it, (2) I expect it, (3) I am neutral, (4) I can tolerate it, (5) I dislike
   it. Apply the Kano evaluation table (functional × dysfunctional response pair) to
   classify each attribute as: M (must-be), O (one-dimensional / performance), A
   (attractive / delighter), I (indifferent), R (reverse), or Q (questionable —
   inconsistent response, exclude from analysis). Minimum viable sample: 30 respondents
   per primary segment; 100+ preferred for statistical stability.

4. **Classification and satisfaction coefficient calculation.** For each attribute, compute
   the Better coefficient (extent to which presence increases satisfaction) and Worse
   coefficient (extent to which absence creates dissatisfaction) using the Kano formulas:
   Better = (A + O) / (A + O + M + I); Worse = −1 × (O + M) / (A + O + M + I). Plot
   attributes on a Better/Worse quadrant. High Better + low |Worse| = delighters. High
   Better + high |Worse| = performance. Low Better + high |Worse| = must-haves. Low
   Better + low |Worse| = indifferent — strong candidates for removal. Datestamp every
   classification with the survey run date.

5. **PMF Treadmill aging audit.** Apply the Winters-Mosavat temporal lens: for each
   attribute currently classified as delighter or performance, assess whether market
   conditions, competitive parity, or elapsed time since last survey suggest category
   drift. Flag attributes where competitive benchmarking or user interviews surface
   language like "of course it should do X" — this phrasing signals drift to must-have.
   The Chegg 2024 case (90% valuation collapse, 500,000 subscriber loss in 10 months)
   demonstrates the cost of treating Kano classifications as permanent. Schedule the next
   Kano re-run: default cadence is annual minimum; accelerate to semi-annual in fast-moving
   markets or post-major-competitive-event.

6. **Roland Berger Design-to-Value margin overlay.** For each attribute, obtain or estimate
   the marginal cost to deliver (engineering, support, infrastructure) and the marginal
   revenue contribution (willingness-to-pay uplift, retention delta). Compute the
   Kano × margin composite score: Kano category (A > O > M > I priority ordering) ×
   margin contribution (positive, neutral, or negative). Attributes scoring high excitement
   but negative margin are investment traps — documented Roland Berger DtV teardowns
   produced a 45% reduction in variants without revenue loss by eliminating this category
   (Roland Berger, Design-to-Value methodology, published case studies). Flag every
   attribute where margin data is unavailable as [assumption — verify].

7. **Apple portfolio coherence gate.** Apply the Jobs focus doctrine: list the top-rated
   delighters and performance attributes; if any dilute the coherence of the core product
   narrative, flag for elimination regardless of satisfaction score. The operational
   exercise: list ten top-rated strategic directions and eliminate seven, committing to
   three (Steve Jobs, documented by Adam Lashinsky, Inside Apple, 2012). This gate
   prevents feature accumulation that individually tests well but collectively fragments
   product identity.

8. **Priority matrix and next steps.** Produce a 2×2 table: Kano category (vertical) ×
   margin contribution (horizontal). Quadrant 1 (must-have × positive margin): protect,
   monitor for quality regression. Quadrant 2 (performance × positive margin): invest,
   measure satisfaction improvement. Quadrant 3 (delighter × positive margin): roadmap
   for differentiation. Quadrant 4 (any × negative margin or indifferent): phase-out
   candidates. Assign a named owner and a next-action to every attribute in Quadrants 3
   and 4. Document residual risks: sample representativeness, margin estimate confidence,
   and the re-survey schedule.

## Output format

```
KANO MODEL — <product / context>
Survey date: <YYYY-MM-DD>   |   Next re-survey due: <YYYY-MM-DD>   |   PMF Treadmill status: <current / expired>
Context detected: <B2B/B2C · sector · stage>

ATTRIBUTE CLASSIFICATION TABLE
  Attribute                | Category   | Better | Worse | Datestamp  | Drift risk
  -------------------------|------------|--------|-------|------------|------------
  <attribute 1>            | Must-be    | 0.18   | −0.82 | YYYY-MM-DD | Low
  <attribute 2>            | Delighter  | 0.74   | −0.12 | YYYY-MM-DD | HIGH — re-survey triggered
  <attribute n>            | Indifferent| 0.09   | −0.07 | YYYY-MM-DD | —

PMF TREADMILL AUDIT
  Expired classifications (>12 months): <list or "none">
  Drift-flagged attributes: <list with rationale>
  Re-survey schedule: <date and trigger conditions>

KANO × MARGIN COMPOSITE MATRIX
  Quadrant 1 — Must-have × positive margin (PROTECT):
    - <attribute>: action, owner
  Quadrant 2 — Performance × positive margin (INVEST):
    - <attribute>: action, owner
  Quadrant 3 — Delighter × positive margin (ROADMAP):
    - <attribute>: action, owner
  Quadrant 4 — Indifferent or negative margin (PHASE-OUT CANDIDATES):
    - <attribute>: action, owner
  Margin data missing (flag): <list [assumption — verify]>

PORTFOLIO COHERENCE GATE (Jobs doctrine)
  Top-rated attributes evaluated: <list>
  Eliminated for coherence dilution: <list with rationale>
  Committed priority set (max 3): <list>

SO-WHAT / NEXT STEPS
  - <Specific investment decision, owner, deadline>
  - <Specific phase-out or scope reduction decision>
  - <Re-survey trigger: date or event>
  - <Margin validation task for flagged attributes>

SOURCES (every external fact cited; nothing invented)
  - Noriaki Kano, "Attractive Quality and Must-Be Quality," Journal of the Japanese Society
    for Quality Control, Vol. 14, No. 2, 1984
  - Casey Winters & Fareed Mosavat, "The PMF Treadmill," Reforge (year of publication
    [assumption — verify exact year]) — https://www.reforge.com
  - Roland Berger, Design-to-Value methodology — published case studies
    https://www.rolandberger.com [assumption — verify specific report title and year]
  - Adam Lashinsky, Inside Apple: How America's Most Admired and Secretive Company Really
    Works, Business Plus, 2012
  - Chegg 2024 — valuation collapse and subscriber loss documented in SEC filings and
    press reports, 2024 [assumption — verify specific filing references]
```
