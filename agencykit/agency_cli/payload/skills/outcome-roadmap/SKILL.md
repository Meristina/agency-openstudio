---
name: outcome-roadmap
description: >-
  Structures a product roadmap using the Now/Next/Later commitment-horizon framework,
  enforcing Ryan Singer's betting-table circuit breaker (Shape Up, Basecamp 2019) and
  refusing commitments beyond the current quarter. Use when a team needs a live roadmap
  artefact that preserves strategic optionality, avoids ghost commitments, and sequences
  delivery waves with explicit portfolio trade-offs. Produces a structured roadmap block
  with horizon assignments, circuit-breaker status, wave sequencing, and full citations.
---

# Skill — Outcome Roadmap (Now / Next / Later)

The Outcome Roadmap is a commitment-horizon artefact that divides product bets into three
zones — Now (in progress this cycle), Next (shaped and prioritised, startable this quarter),
and Later (directional, deliberately vague, revisable without apology) — and combines this
horizon discipline with Ryan Singer's Shape Up betting-table circuit breaker (Basecamp /
37signals, 2019): work not selected in a betting cycle is dropped, not queued, and must
re-justify itself from zero if it resurfaces. The forcing function eliminates passive backlog
accumulation and the ghost commitments that accrue when incomplete projects receive automatic
extensions. Netflix, Airbnb, Spotify, and Basecamp have independently converged on
abandoning annual roadmap locks in favour of rolling quarterly commitments; Airbnb's
calibrated architecture — clear 18-month visibility with an intentionally vague 3-year
directional view — is the canonical reference for preserving strategic optionality without
signalling instability. McKinsey's wave-based sequencing (10–12-week waves: quick wins,
scaled wins, long-build) provides a delivery mobilisation overlay. Portfolio sequencing
decisions are governed by the BCG Growth-Share Matrix (Bruce Henderson, 1970): Stars receive
increased investment, Cash Cows are harvested, Question Marks receive small bets first with
a gate before scaling, Dogs are exited.

> **Doctrine:** Cite Ryan Singer / Shape Up (Basecamp, 2019) for the betting table and
> circuit breaker. Cite Netflix Now/Next/Later for horizon discipline. Cite Airbnb's
> 18-month/3-year split for commitment architecture. Cite McKinsey wave-based sequencing
> for delivery mobilisation. Cite BCG Growth-Share Matrix (Henderson, 1970) for portfolio
> trade-off overlays. Annual roadmap commitments are structurally incompatible with fast
> product markets — this skill must never produce commitments extending beyond the current
> quarter. Never invent a quote, statistic, or benchmark — research every external fact
> and cite it.

## Procedure

1. **Characterise product, context, and current cycle.** Identify product type
   (B2B/B2C/marketplace/platform), business stage (pre-PMF, scaling, mature), sector,
   and the current betting cycle (typically 6–8 weeks per Shape Up, or a quarterly
   cadence). Establish the current quarter as the hard commitment boundary. Any work
   assigned beyond the current quarter moves automatically to Later — no exceptions.

2. **Inventory all active and candidate bets.** Collect every item the team is tracking:
   in-flight work, shaped pitches, feature requests, strategic initiatives, and technical
   investments. Do not treat this inventory as a backlog to be committed to. Each item is
   a candidate for classification, not a promise. Apply the circuit-breaker principle from
   the outset: items already in flight that are overrunning their cycle receive no automatic
   extension — they must be re-bet or dropped (Singer, Shape Up, 2019).

3. **Classify each item into Now / Next / Later.** Now: work actively in progress within
   the current cycle — it has a named owner, a shaped pitch or equivalent, and a defined
   appetite. Next: work that is shaped, prioritised, and could plausibly start within the
   current quarter — the team has done enough discovery that a bet is credible. Later:
   everything else — directional themes, unshaped ideas, strategic hypotheses — kept
   deliberately vague per the Netflix and Airbnb precedent; no delivery dates, no feature
   specifications, no implicit commitments.

4. **Apply the betting-table circuit breaker to all Now items.** For each item in Now,
   confirm: (a) it has a defined cycle appetite (time-box), (b) a named team with no
   other conflicting commitments, and (c) an explicit circuit-breaker condition — the
   specific observable signal that ends the bet without extension. Items lacking a
   circuit-breaker condition are reclassified to Next until the condition is named.
   This is the structural mechanism that prevents passive accumulation of ghost commitments
   (Singer, Shape Up, Basecamp 2019).

5. **Apply the BCG portfolio overlay to the Now / Next set.** Classify each item in Now
   and Next against the BCG Growth-Share Matrix (Henderson, 1970): Stars (high share, high
   growth — increase investment), Cash Cows (high share, low growth — harvest for margin),
   Question Marks (low share, high growth — small bet first, gate before scaling), Dogs
   (low share, low growth — exit). Sequence Next items using this classification: Stars
   advance first, Question Marks require a discovery gate, Dogs are removed from the
   roadmap entirely. Document the sequencing rationale.

6. **Structure delivery into McKinsey waves.** Map Now and Next items onto 10–12-week
   delivery waves (McKinsey wave-based sequencing): Wave 1 delivers quick wins that prove
   value and build organisational confidence; Wave 2 scales validated wins from Wave 1;
   Wave 3 addresses long-build strategic initiatives that depend on Wave 1–2 foundations.
   Each wave must demonstrate ROI before the next wave receives a funding commitment.
   Do not pre-commit Wave 3 scope until Wave 1 delivers.

7. **Define Later as strategic optionality, not a backlog.** Later items must be held as
   directional themes, not feature specifications. Following Airbnb's architecture, the
   18-month view should be legible at the theme level; the 3-year view is deliberately
   ambiguous. Do not assign dates, owners, or sequencing to Later items. Any stakeholder
   pressure to commit Later items to a quarter is a structural warning sign — flag it
   and hold the boundary. Items that drop out of Now or Next are moved to Later and must
   re-justify themselves from zero in the next betting cycle (Singer, 2019).

8. **Produce the output block and cite all sources.** Render the full structured roadmap
   output (see format below). Each item must show its horizon, BCG classification, wave
   assignment (where applicable), circuit-breaker condition (for Now items), and outcome
   orientation (problem being solved, not feature being shipped). End with SO-WHAT / NEXT
   STEPS and a SOURCES section. Every external fact must be cited; nothing may be invented.

## Output format

```
OUTCOME ROADMAP — <product / context>
Context detected: <B2B/B2C · sector · stage · current quarter>

COMMITMENT BOUNDARY
  Hard limit       : current quarter only — no commitments beyond <Q / Year>
  Betting cadence  : <cycle length — e.g. 6-week cycles per Shape Up>
  Circuit breaker  : active — items that overrun their cycle are dropped, not extended

NOW (in-progress this cycle — named owner, shaped, time-boxed)
  Item             : <name>
  Outcome targeted : <problem being solved, not feature being shipped>
  Appetite         : <time-box — e.g. 6 weeks>
  Owner            : <team or person>
  BCG class        : <Star / Cash Cow / Question Mark / Dog>
  Circuit breaker  : <observable signal that ends this bet without extension>

  [Repeat for each Now item]

NEXT (shaped, prioritised, startable this quarter)
  Item             : <name>
  Outcome targeted : <problem being solved>
  BCG class        : <classification>
  Wave             : <Wave 1 / Wave 2 — scale after Wave 1 ROI confirmed>
  Gate condition   : <what must be true before this bet is opened>

  [Repeat for each Next item]

LATER (directional themes — deliberately vague, no dates, no specs)
  Theme            : <high-level directional label>
  Strategic intent : <one sentence — why this matters, not what it is>
  Re-entry gate    : must re-justify from zero in the next betting cycle

  [Repeat for each Later theme]

PORTFOLIO TRADE-OFF (BCG overlay)
  Stars            : [items — increase investment]
  Cash Cows        : [items — harvest]
  Question Marks   : [items — small bet first; gate before scaling]
  Dogs             : [items — exit; removed from roadmap]

WAVE SEQUENCING (McKinsey 10–12-week waves)
  Wave 1 (quick wins)  : [items] — ROI signal: [what proves Wave 1 delivered]
  Wave 2 (scale wins)  : [items] — unlocked after: [Wave 1 ROI condition]
  Wave 3 (long-build)  : [items] — unlocked after: [Wave 2 ROI condition]

SO-WHAT / NEXT STEPS
  - ...

SOURCES (every external fact cited; nothing invented)
  - Ryan Singer — Shape Up (Basecamp / 37signals, 2019) — https://basecamp.com/shapeup
  - Netflix — Now/Next/Later roadmap format — [assumption — verify primary URL]
  - Airbnb — 18-month roadmap visibility / 3-year directional view — [assumption — verify]
  - McKinsey — wave-based sequencing (10–12-week waves) — [assumption — verify]
  - Bruce Henderson / BCG — Growth-Share Matrix (1970) — [assumption — verify]
```
