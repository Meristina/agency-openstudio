---
name: story-mapping
description: >-
  Builds a user story map following Jeff Patton's backbone-slice structure, annotates
  each backbone epic with a Ryan Singer Shape Up appetite to anchor scope to business
  value rather than past effort, and sequences release slices into McKinsey 10–12-week
  delivery waves with explicit ROI checkpoints. Use when a team needs a shared narrative
  of the end-to-end user journey, a release-slicing decision, or a wave-sequenced delivery
  plan that replaces flat backlogs and velocity KPIs. Produces a structured story map block
  with backbone activities, story slices, appetite annotations, wave assignments, flow
  metrics, and full citations.
---

# Skill — User Story Mapping

User story mapping, introduced by Jeff Patton (User Story Mapping, O'Reilly, 2014), is a
collaborative technique that arranges user stories on a two-axis grid: the horizontal
backbone runs left-to-right through the sequence of activities a user performs to reach
their goal; the vertical slices cut across the backbone to define minimum viable releases —
the shallowest horizontal cut that still delivers a coherent user journey. The technique
rejects flat backlogs, which destroy narrative context and make it impossible to reason
about what is and is not in a release (Patton, 2014, ch. 1). Ryan Singer's Shape Up
appetite framing (Basecamp / 37signals, 2019) overlays each backbone epic with a time-budget
annotation: instead of asking "how long will this take?" — which anchors scope to past
effort — the team asks "how much is this worth?" — which anchors scope to business value.
Epics carry an appetite annotation alongside, not instead of, story-point estimates; when
the two conflict, the appetite is the binding constraint and scope must shrink. McKinsey's
wave-based mobilisation (10–12 weeks per wave, with explicit ROI checkpoints before the
next wave is funded) then sequences the vertical slices into delivery waves, enforcing
evidence-based funding decisions rather than upfront annual commitments. McKinsey evidence
from 32 companies shows that programs structured in waves with explicit ROI checkpoints
outperform simultaneous portfolio execution.

> **Doctrine:** Cite Jeff Patton (User Story Mapping, O'Reilly, 2014) for backbone and
> slice structure. Cite Ryan Singer / Shape Up (Basecamp, 2019) for appetite framing and
> the explicit distinction between appetite ("how much is this worth?") and estimation
> ("how long will it take?"). Cite McKinsey wave-based sequencing for delivery mobilisation.
> Velocity in story points is a planning heuristic, not a performance KPI — team-level
> velocity comparisons systematically inflate story points, incentivise sandbagging, and
> displace outcome measurement; replace with flow metrics (cycle time, throughput) governed
> by Little's Law (J.D.C. Little, Operations Research, 1961). SAFe PI Objectives are a
> quality gate before sprint entry, not bureaucratic overhead — but flag endemic SAFe
> anti-patterns (PI Planning collapsing into waterfall plans, component ARTs masquerading
> as value-stream ARTs, velocity comparisons displacing outcome measurement) when observed.
> Never invent a quote, statistic, or benchmark — research every external fact and cite it.

## Procedure

1. **Establish the user goal and narrative spine.** Identify the primary user persona and
   the end-to-end goal they are trying to accomplish. Write the goal as a verb-noun job
   statement (e.g. "Buy a product online", "File an insurance claim"). This sentence becomes
   the frame for the entire map. Patton's central warning is that without a shared narrative
   spine the map devolves into a feature list that loses all sense of user flow and release
   coherence (User Story Mapping, O'Reilly, 2014, ch. 1).

2. **Build the backbone: activities left-to-right.** Walk the user's journey from first
   touch to goal completion and identify the major activity clusters — high-level user tasks
   that make up the workflow (e.g. Discover → Evaluate → Purchase → Receive → Return).
   Write each activity on a card and arrange them left-to-right on the backbone row.
   Activities are grouping headers, not stories. Aim for 5–10 backbone activities for a
   bounded product scope; more than 12 activities signals a scope that spans multiple maps.

3. **Decompose each activity into user tasks (stories).** Below each backbone activity,
   enumerate the specific user tasks — the things a user actually does within that activity.
   Write each as a short verb phrase or a "As a [user], I [action] so that [outcome]"
   statement. Arrange vertically by frequency and importance: the most common or critical-
   path tasks sit highest below the backbone; edge cases and enhancements sit lower. This
   vertical ordering is the slicing dimension from which release cuts are drawn (Patton, 2014).

4. **Annotate each backbone epic with a Shape Up appetite.** For each backbone activity
   (treated as an epic), assign a time-budget annotation: Small Batch (≤ 2 weeks), Standard
   Appetite (≤ 6 weeks), or Large Bet (≤ 12 weeks, requiring explicit sponsorship sign-off).
   The appetite answers "how much is this worth?" — not "how long will engineering take?"
   Record the appetite alongside any existing story-point estimate, but treat the appetite as
   the binding scope constraint. If appetite and estimate are incompatible, scope must shrink
   to fit the appetite — the appetite is never negotiated upward to accommodate scope growth
   (Singer, Shape Up, Basecamp / 37signals, 2019).

5. **Cut horizontal release slices across the backbone.** Draw a horizontal line below the
   minimum set of tasks across all backbone activities that still delivers a coherent user
   journey. This is Release 1 — the walking skeleton (Patton, User Story Mapping, 2014,
   ch. 3). Everything above the line ships in Release 1; tasks below the line are candidates
   for later releases. Repeat to define Release 2, Release 3, and so on. Each slice must
   deliver independent user value — a slice that only makes sense when combined with a future
   release is not a valid slice and must be reclassified or deferred.

6. **Apply a PI Objective quality gate before sprint assignment.** Before any story cluster
   enters a sprint, verify it has a SMART PI Objective — Specific, Measurable, Achievable,
   Relevant, Time-bound — with a named business value score (1–10). This is a forcing
   function for outcome clarity, not bureaucratic overhead. Story clusters without a
   measurable outcome are returned to the backlog. Flag SAFe anti-patterns explicitly if
   observed: PI Planning collapsing into a waterfall plan with locked scope, component ARTs
   masquerading as value-stream ARTs, or velocity comparisons being used as a performance
   or team-ranking signal.

7. **Sequence release slices into McKinsey delivery waves.** Map the release slices onto
   10–12-week delivery waves. Wave 1 contains the walking skeleton and quick wins that prove
   the core user journey functions end-to-end — the ROI signal must be observable before
   Wave 2 is funded. Wave 2 enriches and scales the validated slices from Wave 1. Wave 3
   addresses long-build strategic enhancements that depend on Wave 1–2 foundations and must
   not be pre-committed until Wave 2 delivers its ROI checkpoint. Pre-fund no wave beyond
   the current one (McKinsey wave-based mobilisation doctrine).

8. **Replace velocity KPIs with flow metrics.** Document the team's cycle time (median
   days per story from start to done) and throughput (stories completed per sprint). Velocity
   in story points may be used as an internal planning heuristic but must never appear as a
   team-level comparison signal or performance measure — doing so systematically degrades
   quality via story-point inflation, sandbagging, and completion-rate gaming. Govern the
   delivery system at the program level using Little's Law: throughput = WIP ÷ cycle time
   (J.D.C. Little, "A Proof for the Queuing Formula: L = λW", Operations Research, 1961).

9. **Produce the output block and cite all sources.** Render the full structured story map
   output (see format below). Each backbone activity must show its appetite annotation,
   story slice assignments, and wave allocation. End with SO-WHAT / NEXT STEPS and a SOURCES
   section. Every external fact must be cited; nothing may be invented.

## Output format

```
USER STORY MAP — <product / context>
Context detected: <B2B/B2C · sector · stage>

USER GOAL
  Persona          : <primary user persona>
  Goal statement   : <verb-noun — e.g. "File an insurance claim online">
  Narrative spine  : <1-sentence end-to-end journey description>

BACKBONE ACTIVITIES (left → right)
  1. <Activity 1>   Appetite: <Small Batch / Standard / Large Bet>   Wave: <1/2/3>
  2. <Activity 2>   Appetite: <…>                                    Wave: <…>
  [Repeat for each backbone activity — 5–10 total]

STORY SLICES BY ACTIVITY

  [Activity 1 — <name>]
    Release 1 (walking skeleton):
      - <user task>
      - <user task>
    Release 2:
      - <user task>
    Later:
      - <user task — no dates, no specs, must re-justify>

  [Repeat for each backbone activity]

APPETITE REGISTER (Shape Up overlay)
  Epic / Activity       Appetite          Story-pt estimate   Binding constraint
  <Activity 1>          <6 weeks>         <M pts>             Appetite — scope shrinks if over
  [Repeat for each backbone activity]

WAVE SEQUENCING (McKinsey 10–12-week waves)
  Wave 1 (walking skeleton):  [activities / slices]
    ROI signal: <observable outcome that proves Wave 1 delivered>
  Wave 2 (enrich & scale):    [activities / slices]
    Unlocked after: <Wave 1 ROI condition>
  Wave 3 (strategic build):   [activities / slices]
    Unlocked after: <Wave 2 ROI condition — do not pre-commit>

FLOW METRICS (not velocity KPIs)
  Cycle time          : <median days per story — target / current>
  Throughput          : <stories/sprint — target / current>
  Little's Law check  : throughput = WIP ÷ cycle time — flag if WIP exceeds capacity

SO-WHAT / NEXT STEPS
  - ...

SOURCES (every external fact cited; nothing invented)
  - Jeff Patton — User Story Mapping (O'Reilly, 2014) — https://www.jpattonassociates.com/user-story-mapping/
  - Ryan Singer — Shape Up (Basecamp / 37signals, 2019) — https://basecamp.com/shapeup
  - McKinsey — wave-based mobilisation, 10–12-week waves — [assumption — verify]
  - J.D.C. Little — "A Proof for the Queuing Formula: L = λW", Operations Research, 1961
```
