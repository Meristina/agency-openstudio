---
name: market-sizing
description: >-
  Market sizing — quantify TAM / SAM / SOM for a product in a market, with an explicit,
  defensible method. Triangulates top-down (industry reports) against bottom-up
  (#buyers × price × frequency) and value-theory cross-checks, states every assumption,
  cites every source, and never passes a guess off as a figure. Feeds Officer 1's insight
  base and the business case (sizing the prize before strategy commits to it).
---

# Skill — Market Sizing (TAM / SAM / SOM)

Put a defensible number on the opportunity. Three nested sizes:
- **TAM** — Total Addressable Market: total demand if you had 100% of everyone who could
  ever buy the category.
- **SAM** — Serviceable Addressable Market: the slice your model/geography/segment can
  actually serve.
- **SOM** — Serviceable Obtainable Market: the share you can realistically win in the
  planning horizon (given competition, reach, capacity).

> **Doctrine — method over magnitude.** A number with no method is worthless. Always show
> **how** you got there, **triangulate at least two independent methods**, and state every
> assumption with its source. **Never invent** a figure; label any unsourced input
> `[assumption — verify]`. A range with confidence beats a false-precision point estimate.

## Methods (use ≥2 and reconcile)
1. **Top-down** — start from a published industry/market figure, then narrow by segment,
   geography, and qualification %. Source the starting figure (analyst report, gov stats,
   association data); never start from an uncited "the market is $X bn".
2. **Bottom-up** — `# potential buyers × adoption/qualification % × price × purchase
   frequency`. Usually the most defensible; build each factor from sourced inputs.
   - B2B: # target accounts (firmographic filters) × ACV × renewal/expansion.
   - B2C: # households/individuals in segment × penetration × spend × frequency.
3. **Value-theory cross-check** — what the product is worth to the buyer (value created ×
   capturable share) — a sanity bound, especially for new categories with no top-down data.

## Procedure
1. **Define the unit & boundary precisely**: the product, the buyer, the geography, the
   time period (annual unless stated), and currency. Ambiguity here invalidates the number.
2. **Compute TAM** by top-down AND bottom-up; **reconcile** — if they diverge widely, find
   why (different boundary, double counting, stale data) and report the gap, don't average
   blindly.
3. **Derive SAM** by applying explicit serviceability filters (segment, geography, channel,
   regulatory) to TAM. List each filter and its %.
4. **Derive SOM** from realistic share: current/target market share, competitive intensity,
   reach & capacity, and ramp over the horizon. Tie it to the plan, not to optimism.
5. **State assumptions, ranges, and confidence**: low / base / high; mark the 2-3
   assumptions the answer is most sensitive to (sensitivity flags).
6. **Hand off:** the sized prize + key assumptions feed positioning/targeting (Officer 2),
   budget scale (Officer 6), and the baseline (does current revenue square with this SOM?).

## Output format
```
MARKET SIZING — <product / market>
Context detected: <B2B/B2C · market · stage>
Boundary: <product · buyer · geography · period · currency>

TAM  (two methods, reconciled)
  Top-down:  <figure> — from <sourced start> narrowed by <filters>
  Bottom-up: <#buyers> × <price> × <freq> = <figure>  (each factor sourced)
  Reconciled TAM: <range, base>   |  divergence explained: …

SAM  = TAM × serviceability filters
  | Filter (segment/geo/channel/regulatory) | % applied | source |
  Reconciled SAM: <range, base>

SOM  = SAM × realistic obtainable share (horizon: <period>)
  Share logic: <current/target share · competition · reach/capacity · ramp>
  SOM: <range, base>

KEY ASSUMPTIONS & SENSITIVITY
  - <assumption> [source / "assumption — verify"] — impact: H/M/L
  Most sensitive: <2-3 drivers>

CONFIDENCE: <low/med/high> + what would tighten it.

SOURCES (every figure & rate cited; nothing invented)
  - <reports / gov stats / pricing / association data researched live>
```
