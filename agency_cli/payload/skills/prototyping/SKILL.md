---
name: prototyping
description: >-
  Guides teams through the full prototyping fidelity spectrum — low-fi (structure and
  information architecture), mid-fi (layout and navigation), high-fi (visual design),
  and interactive (full user-flow simulation) — matching fidelity to learning objective.
  Use when a team needs to test a hypothesis about form, flow, or feasibility before
  committing to engineering. Produces a fidelity-matched prototype plan, a clear
  hypothesis statement, and a testable artifact brief aligned to GV Sprint Day 4 quality
  standards.
---

# Skill — Fidelity-Matched Prototyping

Prototyping is a hypothesis-testing practice, not a delivery artifact. The discipline
spans a fidelity spectrum — from paper sketches that test information architecture to
interactive flows that simulate full user journeys — and each level serves a distinct
learning objective. IDEO's prototyping canon (IDEO Design Kit; Tom and David Kelley,
Creative Confidence, Crown Business, 2013) distinguishes paper prototypes for structural
validation, bodystorming and role-play for service interaction design, Wizard of Oz
methods for simulating capabilities not yet built, and storyboards for communicating
context to non-design stakeholders. Ryan Singer (Shape Up, Basecamp/37signals, 2019)
prescribes fat-marker sketches and breadboards as deliberately low-resolution shaping
tools — resisting over-specification before the problem scope is stable. The Google
Ventures Sprint standard (Jake Knapp, Sprint, Simon & Schuster, 2016, Day 4) sets the
quality bar: prototypes must be "good enough to provoke authentic reactions" — not
pixel-perfect, but believable enough to generate real behavioral signal. Apple's
hardware cadence (documented by Adam Lashinsky, Inside Apple, Fortune/Crown, 2012)
provides a discipline benchmark for parallel exploration: multiple physical candidates
fabricated in 4–6 week cycles before convergence on a launch version. The implication
for digital product teams is to test multiple fidelity levels in parallel, not to
iterate linearly on a single candidate.

> **Doctrine:** Cite every framework by author, source, and year. Do NOT recycle a
> sprint prototype as a development specification — Knapp (Sprint, 2016) is explicit:
> the sprint prototype is a hypothesis-testing artifact, and teams that reuse it as a
> dev spec destroy the sprint's primary value. Never fabricate a quote, benchmark, or
> usability standard. Unknown → say "unknown". Flag when a Wizard of Oz prototype
> risks creating false capability expectations for participants — this is an ethical
> research obligation, not a UX preference.

## Procedure

1. **Define the learning objective and hypothesis.** Before selecting a fidelity level,
   write the prototype hypothesis as a falsifiable statement: "We believe [user segment]
   will [behaviour] because [assumption]. We will know this is true when we observe
   [signal]." The fidelity choice must be driven by this hypothesis, not by available
   tooling or designer preference. A structural hypothesis (is our information architecture
   logical?) demands low-fi. A visual-reaction hypothesis (does this feel trustworthy?)
   demands high-fi. Conflating them wastes cycles.

2. **Select fidelity level against learning objective.** Map the hypothesis to the
   correct fidelity tier: (a) Low-fi — paper prototypes, fat-marker sketches (Singer,
   Shape Up, 2019), index cards. Use for information architecture, content hierarchy,
   and navigation structure. Speed is the advantage; avoid investing in visual polish.
   (b) Mid-fi — wireframes with real navigation links. Use when the layout and flow
   hypothesis requires click-through, but visual fidelity would distract from structural
   feedback. (c) High-fi — pixel-resolved screens with real typography and spacing.
   Use when the hypothesis concerns visual trust, brand perception, or the readability
   of specific UI elements. (d) Interactive — fully navigable prototype simulating a
   complete user flow. Use for usability testing, stakeholder demos requiring authentic
   reactions, and GV Sprint Day 4 tests (Knapp, Sprint, 2016).

3. **Select the prototyping method against context.** Beyond fidelity, match the method
   to what is being tested. Paper prototypes (IDEO) for structure validation with a live
   facilitator "operating" the interface. Bodystorming (IDEO Design Kit) for physical
   service contexts — team members embody the service roles and act through the journey
   to expose friction invisible on a screen. Role-play and service prototyping for
   interaction-design decisions where dialogue, timing, and handoffs between people or
   systems are the design variables. Wizard of Oz (Kelley and Kelley, Creative
   Confidence, 2013; original WoZ method attributed to John F. Kelley, IBM, 1980s) for
   simulating AI capabilities, voice interfaces, or back-end logic not yet built — a
   human operator provides responses the system would eventually automate. Storyboards
   for communicating user journey context to non-design stakeholders without requiring
   them to interact with a prototype artifact.

4. **Apply the GV Sprint Day 4 quality standard.** For any prototype that will be tested
   with real users, apply Knapp's "good enough to provoke authentic reactions" gate
   (Sprint, Simon & Schuster, 2016, Chapter: Day 4). This means: real (or realistic)
   content, not lorem ipsum; navigable flows from start to finish of the tested task;
   and a surface that passes the "five-second first impression" test — participants
   must believe it could be real. It does NOT mean pixel-perfect or production-ready.
   Reject scope additions that do not serve the test hypothesis.

5. **Run parallel exploration before convergence.** Do not iterate linearly on a single
   prototype candidate. Following Apple's parallel hardware fabrication discipline
   (Lashinsky, Inside Apple, 2012) — adapted for digital teams — build two to three
   low-fi variants representing meaningfully different structural hypotheses, test them
   against the same learning objective, and converge only after signal is collected.
   Premature convergence on a single candidate is the most common prototyping failure
   mode in fast-moving teams.

6. **Conduct the test and capture signal.** Run the prototype with the target user
   segment. For paper and low-fi prototypes, use a facilitator-operated "human computer"
   format (IDEO). For interactive prototypes, apply a think-aloud protocol. Capture
   behavioral signal — where users hesitate, mis-tap, or abandon — separately from
   verbal signal. Do not conflate what users say they prefer with what their behavior
   reveals. Flag GDPR Art. 6 / CCPA consent obligations for any session involving
   recording or personal data.

7. **Debrief and document invalidated assumptions.** Within 24 hours of the test,
   record which hypothesis was confirmed, which was invalidated, and what the prototype
   did NOT test. Do not convert a sprint prototype into a development specification
   (Knapp, Sprint, 2016 — explicit warning). State the next fidelity step or
   convergence decision, and hand off to the relevant soldier or officer: structural
   findings to the O1 OST soldier; usability findings to the O4 usability-testing
   soldier; validated concepts ready for shaping to the O3 Shape Up soldier.

## Output format

```
PROTOTYPING — <product / context>
Context detected: <B2B/B2C · sector · stage>

PROTOTYPE BRIEF
  Hypothesis:       <falsifiable statement — "We believe X will Y because Z">
  Learning obj.:    <what must be learned to reduce risk>
  Fidelity chosen:  <low-fi / mid-fi / high-fi / interactive — reason>
  Method chosen:    <paper / bodystorm / WoZ / role-play / storyboard / interactive — reason>
  Scope boundary:   <what this prototype does NOT test — explicit>

FIDELITY MAP
  Low-fi target:    <structural element being tested — content hierarchy, IA, navigation>
  Mid-fi target:    <layout or flow element, if applicable>
  High-fi target:   <visual trust, typography, spacing signal, if applicable>
  Interactive flow: <full task scenario, if applicable>

METHOD NOTES
  Paper prototype:  <facilitator role; how the "human computer" will operate it>
  Bodystorming:     <service roles assigned; physical or simulated environment>
  Wizard of Oz:     <human operator instructions; debrief disclosure plan for participants>
  Storyboard:       <audience; communication objective>

GV SPRINT DAY 4 QUALITY GATE
  Real content:     <yes / no — lorem ipsum = fail>
  Full flow:        <navigable start-to-finish for the tested task: yes / no>
  5-sec impression: <participants will believe it could be real: yes / no>
  Scope additions rejected: <list of removed-scope items and why>

PARALLEL EXPLORATION
  Variant A:        <structural hypothesis being tested>
  Variant B:        <alternative structural hypothesis>
  Convergence rule: <signal threshold that triggers convergence>

TEST FINDINGS
  Behavioral signal: <what users did — hesitations, errors, abandonment>
  Verbal signal:     <what users said — separated from behavioral signal>
  Invalidated assumptions: <which hypothesis was falsified and what that implies>

SO-WHAT / NEXT STEPS
  - <Fidelity decision: increase / maintain / reduce — reason>
  - <Convergence or divergence decision>
  - <Assumption that must be tested before any increase in fidelity>
  - <Handoff: OST soldier / usability-testing soldier / Shape Up soldier>

SOURCES (every external fact cited; nothing invented)
  - Jake Knapp, Sprint, Simon & Schuster, 2016 — Day 4 "good enough to provoke
    authentic reactions" standard; explicit warning against reusing sprint prototypes
    as development specs
  - IDEO, Design Kit — paper prototypes, bodystorming, role-play, service prototyping
    methods; human-computer facilitated format
  - Tom Kelley and David Kelley, Creative Confidence, Crown Business, 2013 — Wizard
    of Oz prototyping for simulating capabilities not yet built
  - Ryan Singer, Shape Up, Basecamp/37signals, 2019 — fat-marker sketches and
    breadboards as low-resolution shaping tools; resisting over-specification
  - Adam Lashinsky, Inside Apple, Fortune/Crown Business, 2012 — Apple parallel
    hardware prototyping cadence; 4–6 week refabrication cycles before convergence
  - [Any additional citations for claims made in this output]
```
