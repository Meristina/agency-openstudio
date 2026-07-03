---
name: shape-up
description: >-
  Runs a structured Shape Up shaping session following Ryan Singer's method
  (Basecamp/37signals, 2019): defines appetite before scope, produces a
  fat-marker sketch and breadboard, and writes a pitch with problem, appetite,
  solution boundaries, rabbit holes, and circuit-breaker clause. Use when a
  team needs to transform a raw idea or complaint into a bet-ready pitch that
  the betting table can accept or reject in a single cycle. Produces a
  complete, structured pitch document with explicit no-go zones.
---

# Skill — Shape Up (Ryan Singer / Basecamp)

Shape Up is Basecamp's product development method, documented by Ryan Singer
(Basecamp/37signals, 2019). Its core insight is that scope should be shaped to
fit an appetite — the fixed time budget a team is willing to spend — rather than
estimated to fit a scope. A shaped piece of work travels through three phases:
shaping (defining the problem and rough solution at the right level of
abstraction), betting (a single named Decider allocates cycles at the betting
table), and building (a small team owns the shaped scope end-to-end, with no
interruptions and no automatic extensions). The hill chart makes uncertainty
visible: uphill movement means discovering how to solve the problem; downhill
means executing known work. Because 70–90% of delivery lead time is wait time
and uncertainty rather than execution time (Womack & Jones, Lean Thinking,
1996; validated by Value Stream Mapping research), the hill chart functions as a
queue-visibility instrument that surfaces stuck work before it becomes a crisis.

> **Doctrine:** Every claim about Shape Up cites Ryan Singer, Shape Up,
> Basecamp/37signals, 2019 (freely available at basecamp.com/shapeup). The
> betting table Decider role maps to Bain's RAPID framework — cite Bain & Co /
> Rogers & Blenko, HBR 2006 for the RAPID claim, never attribute it to Singer.
> Never cite "50% of features never used" — origin is untraceable. Never frame
> velocity or story points as outcomes. The circuit breaker is a structural
> mechanism, not a punishment — never editorialize. Do not invent appetite
> durations, hill-chart positions, or betting-table outcomes; unknown → say
> "unknown [assumption — verify]".

## Procedure

1. **Define the raw idea and the problem it solves.** Before any solution work,
   state the problem in one or two sentences from the customer's point of view.
   What is the struggling moment? Who experiences it and when? A pitch without
   a clearly stated problem is not shapeable — the betting table cannot evaluate
   what a solution is worth if the cost of the problem is invisible (Singer,
   Shape Up, 2019, Ch. 5).

2. **Set the appetite, not the estimate.** Ask: how much time is this problem
   worth? Choose a fixed appetite — typically a small batch (1–2 weeks for one
   or two people) or a standard six-week cycle. Appetite is a design constraint,
   not a forecast. If the rough solution cannot fit the appetite, change the
   solution, not the appetite. Never negotiate the appetite upward to fit a
   feature wish list (Singer, Shape Up, 2019, Ch. 3).

3. **Produce the fat-marker sketch.** Draw the solution at the coarsest level
   of fidelity that captures the key idea without prescribing UI details.
   Fat-marker sketches are intentionally rough: they communicate affordances
   and flow without locking in layout or copy. The goal is to prevent
   over-specification that removes judgment from the building team. Annotate
   only what the team must not miss; leave everything else open (Singer,
   Shape Up, 2019, Ch. 8).

4. **Build the breadboard (interaction flow).** For interaction-heavy flows,
   replace or complement the fat-marker sketch with a breadboard: a text-based
   diagram of places (screens or surfaces), affordances (buttons, links,
   inputs), and connection lines (navigation flow). Breadboards communicate
   interaction logic without visual design noise, keeping focus on what the
   interface does rather than how it looks (Singer, Shape Up, 2019, Ch. 8).

5. **Identify and explicitly mark rabbit holes and no-go zones.** After the
   sketch and breadboard, list every sub-problem or edge case that could expand
   scope unpredictably. Classify each as: (a) in scope with a known approach,
   (b) explicitly out of scope — not this cycle, or (c) a rabbit hole requiring
   a deliberate decision before building begins. The pitch must declare these
   explicitly; leaving them implicit is the primary cause of mid-cycle scope
   creep (Singer, Shape Up, 2019, Ch. 9).

6. **Write the pitch.** Assemble the five elements of a complete pitch:
   (1) Problem — the struggling moment in customer language; (2) Appetite — the
   fixed time budget; (3) Solution — fat-marker sketch and/or breadboard with
   annotations; (4) Rabbit holes — explicitly named no-go zones and risky
   sub-problems; (5) No-gos — anything deliberately left out to protect the
   appetite. The pitch is a proposal for a bet, not a requirements document.
   It must fit on a single document that can be read in under ten minutes
   (Singer, Shape Up, 2019, Ch. 6).

7. **Bring to the betting table with a circuit-breaker clause.** The betting
   table is a small group (typically CEO, CTO, senior product) that selects
   which pitches receive a cycle. A single named Decider has authority to
   resolve disagreement — this is structurally equivalent to the Decide role in
   Bain's RAPID framework, where a single named role ends deliberation and
   prevents committee paralysis (Rogers & Blenko, "Who Has the D?", HBR 2006).
   Every bet carries an automatic circuit breaker: if the work is not shippable
   by the end of the cycle, it does not automatically roll over. The team must
   re-pitch and re-bet in the next cycle. This eliminates the accumulation of
   underperforming projects through passive continuation — structurally
   analogous to forcing an active recommitment decision (Singer, Shape Up,
   2019, Ch. 12).

8. **Protect the cool-down period.** After each six-week cycle, a 2-week
   cool-down period provides time for bug fixes, technical debt, exploration,
   and shaping of future work. This inter-cycle buffer protects the reflection
   and reshaping time that delivery pressure would otherwise absorb — analogous
   to McKinsey's inter-wave periods in transformation programs, where
   deliberate pauses allow consolidation before the next initiative wave.
   Never compress cool-down into building time (Singer, Shape Up, 2019, Ch. 13).

## Output format

```
SHAPE UP PITCH — <product / feature / context>
Context detected: <B2B/B2C · sector · stage>

PROBLEM
  Struggling moment : [one or two sentences from the customer's point of view]
  Who experiences it: [role or segment — not a persona archetype]
  When it occurs    : [triggering situation or workflow step]

APPETITE
  Cycle type : [Small batch (1–2 weeks) / Standard cycle (6 weeks)]
  Team size  : [number of people — typically 1 designer + 1–2 engineers]
  Fixed by   : [appetite is a design constraint, not a forecast]

SOLUTION
  Fat-marker sketch:
    [Describe the rough layout or flow — key affordances only, no UI detail]

  Breadboard (if applicable):
    Place 1  →  Affordance A → Place 2
    Place 2  →  Affordance B → Place 3
    [Continue for the key interaction flow]

  Key design decisions:
    - [What must the solution do — the non-negotiable elements]
    - [What is deliberately left open for the building team to decide]

RABBIT HOLES & NO-GO ZONES
  Rabbit hole 1: [sub-problem that could expand scope] → Decision: [in/out/resolve before build]
  Rabbit hole 2: ...
  Explicit no-gos:
    - [Feature or edge case deliberately excluded this cycle]
    - [...]

BETTING TABLE INPUTS
  Decider role  : [Name or role — single person with authority to commit the cycle]
  RAPID mapping : Recommend = shaper · Agree = tech lead · Perform = building team ·
                  Input = stakeholders · Decide = betting table chair
  Circuit breaker: If not shippable by end of cycle → no automatic rollover;
                   team must re-pitch in next cycle

HILL CHART SNAPSHOT (optional — for work already in progress)
  Uphill (uncertain / figuring out): [tasks still in discovery]
  Peak (understood, ready to execute): [tasks at the inflection point]
  Downhill (known / execution): [tasks in execution with clear path]
  Stuck indicators: [any task with no uphill movement for > 3 days]

COOL-DOWN PLAN
  Duration  : [2 weeks standard]
  Activities: [bug fixes · tech debt · shaping candidates for next cycle]

SO-WHAT / NEXT STEPS
  - [Primary bet recommendation — go / no-go and the reasoning]
  - [Rabbit hole that must be resolved before building begins]
  - [Any scope reduction needed to fit the appetite]
  - [Next cycle shaping candidates surfaced during cool-down]

SOURCES (every external fact cited; nothing invented)
  - Ryan Singer — Shape Up, Basecamp/37signals (2019) — https://basecamp.com/shapeup
  - Rogers & Blenko — "Who Has the D?", Harvard Business Review (Jan 2006) — RAPID framework
  - Womack & Jones — Lean Thinking (1996) — 70–90% of lead time is wait/uncertainty
```
