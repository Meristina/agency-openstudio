---
name: value-prop-design
description: >-
  Value Proposition Design — engineer the fit between what a product offers and what a
  customer segment actually wants, using Osterwalder's Value Proposition Canvas: the customer
  profile (jobs, pains, gains) vs the value map (products & services, pain relievers, gain
  creators), then the fit. Shared by Officer 2 (the offer behind the positioning) and Officer
  4 (the promise behind activation/conversion). Reuses JTBD & segment inputs; grounds claims
  in evidence and ends with the fit hypotheses to test. Never invents a benefit or proof.
---

# Skill — Value Proposition Design

Make explicit *why a customer would choose this offer* by engineering **fit** between two
sides of Osterwalder's canvas:
- **Customer profile** — the segment's **Jobs** (functional/emotional/social), **Pains**
  (obstacles, risks, bad outcomes), **Gains** (required/expected/desired/unexpected wins).
- **Value map** — your **Products & services**, **Pain relievers** (how you kill specific
  pains), **Gain creators** (how you produce specific gains).
- **Fit** — each reliever/creator maps to a ranked pain/gain; the strongest value props
  address the *most intense, most frequent, most under-served* jobs/pains/gains.

> **Doctrine — fit, not a feature list.** A value proposition is the *match*, not a list of
> features. Reuse the **JTBD** output (the jobs) and the **persona-segmentation** output
> (the segment) — don't re-derive them. Rank pains/gains by intensity; only claim relievers/
> creators you can prove. **Never invent** a benefit, a stat, or a "saves X%" — source it or
> label `[assumption — verify]`; unknown → "unknown". The canvas produces **fit hypotheses
> to test**, not proven demand.

## Procedure
1. **Pick the segment & job** (reuse persona-segmentation + jtbd). One value prop per
   segment — don't blur segments into one mushy promise.
2. **Build the customer profile:** list Jobs, then Pains, then Gains; **rank each** by
   intensity/frequency/under-service (severe → nice-to-have). Ground from research/verbatims,
   not imagination.
3. **Build the value map:** Products & services → Pain relievers → Gain creators. For each
   reliever/creator, name the *specific* pain/gain it targets.
4. **Assess fit:** map relievers↔pains and creators↔gains; mark **strong fit** (addresses a
   top-ranked, under-served item with proof), **weak fit** (low-rank or unproven), and
   **gaps** (top pains/gains with no reliever/creator). Kill features that fit nothing.
5. **Write the value proposition:** a crisp promise (who · the job · the top pains killed /
   gains created · why believe), plus a one-line headline candidate. Keep it to the few
   highest-fit points, not everything.
6. **Fit hypotheses & validation:** list the assumptions the value prop rests on and the
   cheapest test for each (ties to ai-synthetic-audience probes and real-user tests).
7. **Hand off:** for Officer 2, the value prop sits under the positioning (the *offer* behind
   the *place in the mind*); for Officer 4, it is the **promise** that conversion/CRO and
   activation messaging will test and optimise. Flag proof gaps for the Inspector.

## Output format
```
VALUE PROPOSITION DESIGN — <product / segment>
Context detected: <B2B/B2C · market · stage>   |  Serving officer: <O2 strategy / O4 demand>
Segment & job (reused): <from persona-segmentation + jtbd>

CUSTOMER PROFILE (ranked)
  Jobs:  1) … 2) …            (functional / emotional / social)
  Pains: 1) … (severity) 2) …
  Gains: 1) … (importance) 2) …

VALUE MAP
  Products & services: …
  Pain relievers:  <reliever> → kills <ranked pain> [proof / assumption]
  Gain creators:   <creator>  → creates <ranked gain> [proof / assumption]

FIT ASSESSMENT
  Strong fit: …   |   Weak/unproven: …   |   GAPS (top pains/gains unaddressed): …
  Features that fit nothing (cut): …

VALUE PROPOSITION
  For <segment> doing <job>, <product> <kills top pains / creates top gains>, unlike
  <alternative>, because <reason to believe>.
  Headline candidate: "<…>"

FIT HYPOTHESES TO TEST  (assumption → cheapest validation)
  1. … 2. …

SOURCES (every benefit / stat / proof cited; nothing invented)
  - <proof / market / verbatim sources>  · jtbd + persona-segmentation (the inputs).
```
