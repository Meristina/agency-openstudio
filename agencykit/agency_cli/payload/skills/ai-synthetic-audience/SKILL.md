---
name: ai-synthetic-audience
description: >-
  AI synthetic-audience probing — use an LLM to simulate a target persona for fast, cheap,
  DIRECTIONAL signal (reaction to messaging, objection discovery, hypothesis generation)
  BEFORE committing real research budget. Strictly exploratory: synthetic responses are a
  hypothesis engine, never evidence and never a substitute for real users. Grounds every
  persona input in real research, labels all output as unvalidated, and ends with a
  validation plan against humans.
---

# Skill — AI Synthetic-Audience Probing

Stand up an LLM-simulated version of a target persona to probe reactions **quickly and
cheaply** — pressure-test a value prop, surface likely objections, generate message
hypotheses, or stress a concept — *before* spending on surveys, interviews, or media.

> **IRON RULE — exploratory only.** Synthetic-audience output is a **hypothesis engine,
> not evidence.** AI is a frontier workflow layer (industry: high adoption, *only ~7%
> "fully scaled"* — research-backed), and the evidence for synthetic audiences specifically
> is **thin**. Never present a synthetic result as a finding, a stat, or a substitute for
> real users. Every probe ends with a **plan to validate against humans**. The model can be
> confidently wrong, average-biased, and blind to your actual market — treat it that way.

## When to use (and not)
- **Use** for: early divergence (generate objections/angles to test), sanity-checking
  message clarity, prioritising which questions to ask real users, cheap iteration.
- **Do NOT use** for: market sizing, willingness-to-pay numbers, segment shares, "X% of
  customers prefer…", or any claim that needs to be true. Those need real data — route to
  market-sizing or primary research.

## Procedure
1. **Build the synthetic persona from REAL inputs** — reuse the `persona-segmentation` and
   `jtbd` outputs (sourced). Don't invent the persona; the simulation is only as good as the
   grounded brief behind it. State the persona's context, JTBD, CEPs, and decision criteria.
2. **Frame the probe**: one decision the probe should inform (e.g. "which of these 3 value
   props reads clearest / triggers which objection?"). Narrow beats broad.
3. **Run the simulation** with explicit guardrails: ask the persona to react, object, and
   say what would make it switch; force it to surface *uncertainty* and where a real human
   might differ. Run a few variations to expose model sensitivity, not one tidy answer.
4. **Extract HYPOTHESES, not conclusions**: list the reactions/objections/angles as *things
   to test*, each tagged with a confidence-it-generalises (low by default).
5. **Write the VALIDATION PLAN**: for each high-value hypothesis, the cheapest real-user
   test that would confirm/kill it (interview, survey, landing-page test, ad test, sales
   call). This is mandatory — a probe without a validation plan is incomplete.
6. **Hand off**: validated-later hypotheses feed positioning/messaging (O2/O3) and CRO (O4).
   Flag everything as UNVALIDATED for the Inspector.

## Output format
```
AI SYNTHETIC-AUDIENCE PROBE — <persona / decision>
⚠️ EXPLORATORY — hypotheses only, NOT evidence; validate against real users before acting.
Context detected: <B2B/B2C · market · stage>

SYNTHETIC PERSONA (grounded in real research)
  Built from: <persona-segmentation / jtbd outputs + sources>
  Context · JTBD · CEPs · decision criteria: …

PROBE: <the one decision this informs>

HYPOTHESES GENERATED (to TEST, not to believe)
  | Hypothesis (reaction/objection/angle) | Generalises? (conf.) | How to validate |
  …
  Model-sensitivity notes: <where variations disagreed = low confidence>

VALIDATION PLAN (mandatory — cheapest real test per high-value hypothesis)
  1. <hypothesis> → <interview / survey / LP test / ad test> — success signal: …

SO-WHAT (provisional)
  - Angles worth real testing; questions to put to real users next.

SOURCES (for the persona inputs; the simulation itself is NOT a source)
  - <persona/JTBD sources> · McKinsey, State of AI (AI = frontier, ~7% fully scaled).
```
