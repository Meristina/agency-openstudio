---
name: design-sprint
description: >-
  Facilitates a structured 5-day Design Sprint (Map/Sketch/Decide/Prototype/Test)
  using the Google Ventures protocol to validate or invalidate a binary product
  hypothesis with five users. Use when a team faces a high-stakes decision with
  multiple competing solution directions and needs a fast qualitative signal before
  committing engineering resources. Produces a sprint brief, decision log, prototype
  plan, and a binary hypothesis verdict with user evidence.
---

# Skill — 5-Day Design Sprint

The Design Sprint is a five-day facilitated protocol developed at Google Ventures by
Jake Knapp, John Zeratsky, and Braden Kowitz (Sprint, Simon & Schuster, 2016) to
compress months of design iteration into a single week of structured divergence and
convergence. The sprint's purpose is a single binary question: does this concept
direction merit further investment, or does it not? The Day 5 five-user test is not
a measurement sample — it is a qualitative hypothesis validation instrument. Nielsen
Norman Group research established that five representative users surface approximately
85% of usability problems in a domain (Jakob Nielsen, "Why You Only Need to Test with
5 Users", NNg, 2000); expanding to fifteen users for the sprint test conflates
validation (does this concept work?) with measurement (by how much does it improve a
metric?), a category error. IBM's enterprise design thinking adoption produced a 75%
reduction in design and implementation times (IBM Design Thinking Field Guide and IBM
Institute for Business Value Impact Study, 2018), demonstrating that the sprint's
time-box discipline generates downstream efficiency, not only faster experiments.

> **Doctrine:** Every external claim must be traced to a real source (author, title,
> year). Do not cite sprint conversion rates or feature-adoption benchmarks without
> a traceable study. The five-user test produces a binary qualitative signal on a
> named hypothesis — it does not produce statistical significance and must never be
> presented as such. The Decider's supervote on Day 3 is not a democratic poll; it
> maps to the 'D' (Decide) role in Bain's RAPID Framework — a named authority whose
> call overrides deliberation. Agency adaptations (WPP, Publicis) compress the format
> to 2–3 days with concept-testing panels — flag this compression and its trade-offs
> explicitly when relevant. Unknown data → "unknown [assumption — verify]".

## Procedure

1. **Set the sprint goal and long-term target (Day 1 — Map).** Open by articulating
   the long-term goal: what would success look like in two years, and what would cause
   this effort to fail? Map the problem space as a customer journey diagram — from the
   triggering need through each decision and handoff to the final outcome. Invite
   expert interviews (5–8 minutes per expert) to surface knowledge that lives outside
   the room. At the end of Day 1, the Decider names one target: a specific moment on
   the map that the sprint will focus on. If the team cannot agree on a target, the
   sprint does not proceed — escalate (Knapp, Zeratsky, Kowitz, Sprint, 2016).

2. **Generate individual solution sketches (Day 2 — Sketch).** Use the "together-apart"
   structure: all participants sketch independently before any group review. This
   structural mechanism prevents groupthink during ideation (Knapp et al., Sprint,
   2016). The four-step sketch sequence is: Notes (capture observations from the map),
   Ideas (rough concepts), Crazy 8s (eight variations in eight minutes), and Solution
   Sketch (one fully developed three-panel narrative storyboard). No verbal pitching —
   the sketch must stand alone. Sketches are anonymous during review.

3. **Decide on one solution to prototype (Day 3 — Decide).** Conduct a silent critique
   first: each team member places dot stickers on sketch elements they find compelling,
   without discussion. Then run a structured Rumble or Supervote. The Decider casts
   the supervote — a weighted multi-dot vote that overrides the democratic tally. The
   Decider role maps exactly to the 'D' in Bain's RAPID Framework: the person whose
   call closes deliberation and whose name is attached to the decision (Bain & Company,
   RAPID Decision-Making Framework). Document every rejected alternative and the
   explicit rationale for rejection — these become the assumption log. Close Day 3 by
   building the prototype storyboard: 10–15 frames mapping the user's path through
   the chosen concept.

4. **Build a realistic prototype (Day 4 — Prototype).** The goal is a facade realistic
   enough that users respond as they would to a real product — not a finished product.
   Divide roles: Makers (build screens or physical artifacts), Stitcher (assembles
   components into a coherent flow), Writer (ensures the language is consistent and
   real), Asset Collector (sources images, icons, copy), and Interviewer (prepares the
   test script). Target completion by 3 PM on Day 4 to allow a dry-run rehearsal.
   The prototype must represent the specific hypothesis defined on Day 1 — if the
   prototype does not test the hypothesis, the Day 5 result is invalid (Knapp et al.,
   Sprint, 2016).

5. **Write the interview script and define the binary hypothesis (Day 4 — Prepare).**
   Before the test, write the hypothesis in binary form: "We believe users will [do X]
   because [Y]. We will know this is true if [observable behaviour Z]." Write the
   test script following a five-part structure: Friendly welcome, Context questions,
   Introduction to prototype, Tasks (open-ended, never leading), and Debrief. The
   script is reviewed and locked before the first session on Day 5. Prepare a shared
   observation grid: one column per user, one row per theme or task — team members
   watch behind glass or via screen share and take silent notes in the grid.

6. **Test with five users and synthesise the binary verdict (Day 5 — Test).** Run five
   back-to-back user sessions of 60 minutes each. Recruit participants who match the
   target customer profile from the sprint goal — not convenience samples. Nielsen
   Norman Group research demonstrates that five representative users surface
   approximately 85% of usability problems, making five the point of diminishing
   returns for a single sprint test (Jakob Nielsen, "Why You Only Need to Test with
   5 Users", NNg, 2000). Larger groups do not increase the signal quality for
   hypothesis validation — they generate measurement data the sprint is not designed
   to collect. At the end of Day 5, the team clusters observations into patterns and
   delivers the binary verdict: the hypothesis is supported, refuted, or inconclusive
   (require new hypothesis + iteration).

7. **Document the decision and define next steps.** Record the sprint brief (goal,
   target, hypothesis), the decision log (chosen concept, rejected alternatives with
   rationale), the prototype artefact, the observation grid, and the verdict. If the
   hypothesis is supported, the output feeds the prototype into engineering discovery
   or O4 validation. If refuted, the decision log feeds a new sprint or a pivot
   decision. If inconclusive, define the minimum change to the hypothesis required
   before the next test. Hand off to the appropriate O4 or O5 officer with the
   complete artefact package.

## Output format

```
DESIGN SPRINT — <product / concept / context>
Context detected: <B2B/B2C · sector · stage · sprint day or full sprint>

SPRINT BRIEF
  Long-term goal :  ...
  Sprint target  :  [specific moment on the customer journey map]
  Hypothesis     :  We believe [users] will [do X] because [Y].
                    Confirmed if: [observable behaviour Z]
  Decider        :  [Name / role — maps to Bain RAPID 'D']

DAY 1 — MAP
  Customer journey (key steps): ...
  Expert interviews summary   : ...
  Target chosen               : ...

DAY 2 — SKETCH (together-apart)
  Sketches generated          : [N participants]
  Groupthink prevention       : individual sketching before any group review
  Concepts forwarded to vote  : [brief description of each]

DAY 3 — DECIDE
  Supervote result            : [chosen concept]
  Decider override            : [yes/no — rationale if yes]
  Rejected alternatives       : [concept | rejection rationale]
  Storyboard frames           : [N frames — path summary]

DAY 4 — PROTOTYPE
  Fidelity level              : [facade — realistic enough for user response]
  Prototype covers hypothesis : [yes/no — flag mismatch if no]
  Roles assigned              : Makers / Stitcher / Writer / Asset Collector / Interviewer

DAY 5 — TEST (5-user binary validation)
  Users tested                : 5 [representative of target profile]
  NNg basis                   : 5 users → ~85% of usability problems surfaced
  Observation patterns        :
    Pattern 1: ...
    Pattern 2: ...
  Binary verdict              : [SUPPORTED / REFUTED / INCONCLUSIVE]
  Verdict rationale           : ...

ASSUMPTION LOG (rejected alternatives + open assumptions)
  - [Assumption | Risk level | Cheapest validation test]

SO-WHAT / NEXT STEPS
  - [If supported: feed artefact to engineering discovery or O4 officer]
  - [If refuted: document pivot rationale; define new sprint goal or kill criteria]
  - [If inconclusive: state minimum hypothesis change required before next test]
  - [Flag if group size was expanded — misuse of sprint test as measurement sample]

SOURCES (every external fact cited; nothing invented)
  - Jake Knapp, John Zeratsky, Braden Kowitz — Sprint: How to Solve Big Problems
    and Test New Ideas in Just Five Days, Simon & Schuster, 2016
  - Jakob Nielsen — "Why You Only Need to Test with 5 Users", Nielsen Norman Group,
    March 2000 — https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/
  - IBM Institute for Business Value — IBM Design Thinking Impact Study, 2018
    [75% reduction in design and implementation times — verify latest edition]
  - Bain & Company — RAPID Decision-Making Framework
    https://www.bain.com/insights/rapid-tool-to-clarify-decision-accountability/
```
