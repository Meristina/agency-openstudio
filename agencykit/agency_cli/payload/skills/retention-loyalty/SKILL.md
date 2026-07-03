---
name: retention-loyalty
description: >-
  Retention & loyalty strategy — reduce avoidable churn and grow customer value through better
  experience, proactive retention, and (where it earns its keep) a loyalty program. Diagnoses why
  customers leave, segments by value and risk, and designs interventions measured by INCREMENTAL
  retention/CLV (holdouts), not gross numbers. Honest about the evidence: growth is mostly
  penetration, not loyalty — so loyalty programs are justified on margin/retention/data, not as a
  growth engine, and many "loyalty" gains are just heavy buyers who'd stay anyway. Never invents a
  churn, CLV, or program-ROI figure.
---

# Skill — Retention & Loyalty

Keep more of the customers you win, and grow their value — by fixing the reasons they leave,
intervening before at-risk customers churn, and (selectively) rewarding the behaviour that's
worth rewarding. The goal is **incremental** retention and CLV, not vanity "members" counts.

> **Doctrine — loyalty in its proper place.** Ehrenberg-Bass evidence: growth is **mostly
> penetration (~82%), not loyalty (~2%)**; loyalty/repeat largely follows penetration and
> **double-jeopardy** (big brands have more buyers AND slightly more loyal ones — not the reverse).
> So: **don't sell a loyalty program as a growth strategy**; justify it on **margin, retention of
> at-risk value, first-party data, and experience**. Beware the classic trap — a program that
> **rewards buyers who'd have stayed anyway** shows fake ROI; only **incremental** lift (holdouts)
> counts. **Never invent** a churn rate, CLV, retention %, or program ROI — measure/source it or
> label `[assumption — verify]`; unknown → "unknown".

## Procedure
1. **Diagnose churn:** why do customers actually leave? Separate **involuntary** (failed payments,
   expiry) from **voluntary** (value, price, experience, competitor); use cohort/retention curves,
   exit data, and the JTBD pains. Quantify from data; flag estimates.
2. **Segment by value × risk:** map customers on value (CLV/margin tier) and churn risk; focus
   retention spend where **value at risk** is highest — not on everyone equally, and not on
   already-loyal heavy buyers who don't need it.
3. **Experience & product retention first:** the durable retention lever is delivering the value
   (onboarding to the "aha", reliability, support, reducing effort) — fix the leaks before bribing
   people to stay. Tie to the lifecycle program (lifecycle-crm-email) and PLG activation.
4. **Proactive retention interventions:** at-risk triggers and save flows, involuntary-churn
   recovery (dunning, card updates), win-back; matched to the churn reason, not generic discounts
   that train customers to wait for deals.
5. **Loyalty program (only if it earns its keep):** decide whether a program is justified; if so,
   choose the type (points/tiers/paid/community/value-based) and the **value metric**; design it to
   change **incremental** behaviour and capture first-party data — not to reward the inevitable.
   State the cannibalisation/margin risk.
6. **Measure incrementally (mandatory):** retention lift, CLV, churn reduction, program ROI — with
   **holdouts/control groups** so you measure causal lift, not heavy-buyer correlation (→ O6).
   Report the honest number, including "no incremental effect" if that's the result.
7. **Hand off:** the program execution ↔ lifecycle-crm-email; the data foundation ↔ first-party-cdp;
   expansion/NRR motions ↔ plg (O4); causal lift ↔ O6; consent/terms compliance ↔ Inspector.

## Output format
```
RETENTION & LOYALTY — <brand>
Context detected: <B2B/B2C · market · stage>
⚠️ Justified on margin/retention/data, NOT as a growth engine (growth ≈ penetration; double-jeopardy).

CHURN DIAGNOSIS
  Involuntary vs voluntary · reasons (value/price/experience/competitor) · cohort/retention curves [sourced].

VALUE × RISK SEGMENTATION
  | Segment | CLV/margin tier | Churn risk | Value at risk | Priority |
  …  Focus where value-at-risk is highest (not everyone; not the already-loyal).

EXPERIENCE & PRODUCT RETENTION (first lever)
  Onboarding-to-value · reliability · support · effort reduction. (Fix leaks before bribing.)

PROACTIVE INTERVENTIONS
  At-risk save flows · involuntary-churn recovery (dunning/card update) · win-back — matched to reason.

LOYALTY PROGRAM (only if justified)
  Justified? <yes/no + why>  Type · value metric · incremental behaviour targeted · first-party data.
  Risks: cannibalisation / margin / rewarding the inevitable.

MEASUREMENT (holdouts → O6)
  Retention lift · CLV · churn reduction · program ROI — INCREMENTAL, not heavy-buyer correlation.

HANDOFF: → lifecycle-crm-email · → first-party-cdp · → plg/O4 (expansion) · → O6 (lift) · → Inspector.

SOURCES (every churn/CLV/retention/ROI figure cited; nothing invented)
  - <retention analytics / category benchmark sources researched live>  · jtbd + segments.
```
