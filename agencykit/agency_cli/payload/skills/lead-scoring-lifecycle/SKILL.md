---
name: lead-scoring-lifecycle
description: >-
  Lead scoring & lifecycle handoff — define the lifecycle stages a prospect moves through
  (visitor → lead → MQL → SQL/PQL → opportunity → customer), score leads on fit × engagement,
  and engineer the marketing→sales handoff (definitions, SLA, routing, feedback loop). Connects
  demand generation (Officer 4) to retention (Officer 5) and revenue. Grounds scoring in real
  conversion data (or flags it as a hypothesis to validate); never invents a score weight,
  conversion rate, or "MQL→SQL %" benchmark.
---

# Skill — Lead Scoring & Lifecycle Handoff

Turn raw demand into a disciplined pipeline: agree the **lifecycle stages**, **score** leads so
the best get attention first, and make the **marketing→sales handoff** clean (shared
definitions, an SLA, routing, and a feedback loop). This is where Officer 4's demand becomes
qualified pipeline and connects to Officer 5's lifecycle/retention.

> **Doctrine — shared definitions and a closed loop, scored on evidence.** The classic failure
> is marketing and sales disagreeing on what a "qualified lead" is. Fix it with **explicit
> stage definitions** and a **two-way SLA**. Score on **fit (firmographic/ICP) × engagement
> (behaviour)** — and, for PLG, **product-qualified signals (PQLs)** which often beat
> traditional MQLs. **Base score weights on real conversion data**; if absent, label the model
> a **hypothesis to validate**, don't present it as truth. **Never invent** a score weight,
> conversion rate, or "MQL→SQL %" — measure/source it or label `[assumption — verify]`; unknown
> → "unknown". Privacy/consent on tracked behaviour → Inspector.

## Procedure
1. **Define the lifecycle stages:** visitor → lead → MQL → SQL (and/or **PQL** for product-led)
   → opportunity → customer → (expansion/retention → Officer 5). One agreed definition per
   stage, with the entry/exit criteria. Map to the funnel from full-funnel-paid-media / content.
2. **Design the scoring model:**
   - **Fit / ICP** (explicit): firmographics (B2B), demographics/segment (B2C), match to the
     target from STP. Negative scoring for poor fit.
   - **Engagement / behaviour** (implicit): meaningful actions (high-intent pages, demo, trial
     usage), recency/frequency, decay over time.
   - **PQL signals** (if PLG): activation/"aha", usage depth, team invites.
   Set thresholds for stage transitions; weight from conversion data or flag as hypothesis.
3. **Marketing→sales handoff:** the MQL/SQL definition both sides sign; the **SLA** (response
   time, follow-up cadence) and routing (territory/round-robin/owner); what context passes with
   the lead (source, score, behaviour, JTBD signals).
4. **Feedback loop (closed loop):** sales dispositions leads back (accepted/rejected/won/lost);
   feed it to recalibrate scoring and to demand (which sources/segments convert). Without this,
   scoring drifts.
5. **Nurture vs route:** not-yet-ready leads → nurture (hand to Officer 5 lifecycle/CRM/email),
   ready leads → sales now. Define the recycle path for rejected-but-not-dead leads.
6. **Metrics & guardrails:** MQL→SQL→win rates by source/segment, velocity, lead-to-customer
   conversion; guard against gaming the score or over-counting MQLs. Measure quality, not volume.
7. **Hand off:** demand sources ↔ full-funnel / content-seo / plg; nurture & retention ↔ Officer
   5; pipeline/revenue measurement & alignment ↔ Officer 6 (revops); compliance ↔ Inspector.

## Output format
```
LEAD SCORING & LIFECYCLE HANDOFF — <brand / pipeline>
Context detected: <B2B/B2C · market · stage>   |  Motion: <sales-led / PLG / hybrid>

LIFECYCLE STAGES (agreed definitions + entry/exit criteria)
  visitor → lead → MQL → SQL/PQL → opportunity → customer → (expansion → O5)

SCORING MODEL
  Fit / ICP (explicit): … (+ negative scoring)
  Engagement (implicit): … (recency/frequency/decay)
  PQL signals (if PLG): …
  Thresholds: …   Weights basis: <conversion data / HYPOTHESIS to validate>

MARKETING→SALES HANDOFF
  MQL/SQL definition (both sign) · SLA (response/cadence) · routing · context passed.

CLOSED-LOOP FEEDBACK
  Sales disposition → recalibrate scoring + inform demand (which sources/segments convert).

NURTURE vs ROUTE
  Not-ready → nurture (→ O5) · ready → sales · recycle path for rejected-not-dead.

METRICS & GUARDRAILS
  MQL→SQL→win by source/segment · velocity · lead→customer. Guard: gaming / vanity MQLs. Quality > volume.

HANDOFF: → full-funnel/content/plg (sources) · → O5 (nurture/retention) · → O6 (revops/measurement) · → Inspector (consent).

SOURCES (every weight/rate/benchmark cited; nothing invented)
  - <CRM / conversion-data / category sources researched live>  · STP (ICP) · jtbd.
```
