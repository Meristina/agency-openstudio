---
name: lifecycle-crm-email
description: >-
  Lifecycle marketing / CRM / email — design the owned-channel program that nurtures, onboards,
  retains, and reactivates customers across the lifecycle (welcome → onboard → engage → retain →
  win-back), via segmented, triggered, consented messaging. Maps lifecycle stages to journeys and
  triggers, sets the cadence and personalisation, and measures retention/CLV outcomes — honestly
  framed against the Ehrenberg-Bass evidence that growth is mostly penetration, not loyalty.
  Grounds every rate in data and respects consent law; never invents an open rate or churn figure.
---

# Skill — Lifecycle Marketing / CRM / Email

Run the **owned-channel relationship program**: the right message to the right customer at the
right lifecycle moment, through email/CRM/messaging you control. It onboards new customers to
value, deepens engagement, protects retention, and wins back lapsed ones — efficiently, because
owned channels are low marginal cost.

> **Doctrine — retention matters, but know its place.** Ehrenberg-Bass evidence: growth comes
> **mostly from penetration (~82%), not loyalty (~2%)** — so lifecycle/CRM is mainly about
> **profitability, CLV, onboarding-to-value, and reducing avoidable churn**, NOT the primary
> growth engine. **Don't oversell loyalty programs as growth.** Build on **first-party,
> consented data** (the CDP soldier owns the data foundation) and respect consent law
> (GDPR/CAN-SPAM/ePrivacy → Inspector). **Never invent** an open/click/churn/CLV rate — measure/
> source it or label `[assumption — verify]`; unknown → "unknown".

## Procedure
1. **Map lifecycle stages → journeys:** new → onboarding (to first value / the PLG "aha") →
   active/engaged → at-risk → churned → win-back; plus transactional and milestone moments.
   Define the goal and the one key action per stage.
2. **Segmentation & triggers:** segment by lifecycle stage, behaviour, value tier, and JTBD;
   prefer **behaviour-triggered** flows (event-based) over batch-and-blast. Define entry/exit and
   suppression rules. Use first-party data (from the CDP soldier).
3. **Message & cadence per journey:** the content, channel (email/SMS/push/in-app), and frequency
   for each flow (welcome, onboarding series, re-engagement, win-back, renewal/replenishment);
   carry the positioning/value prop; set frequency caps to protect deliverability and avoid fatigue.
4. **Personalisation (consented):** dynamic content, lifecycle-aware offers, send-time — only on
   consented first-party data; degrade gracefully when data is missing (no creepy over-targeting).
5. **Deliverability & hygiene:** list health, authentication (SPF/DKIM/DMARC), engagement-based
   sending, unsubscribe/preference centre — the foundation that lets the program reach inboxes.
6. **Measure retention/CLV honestly:** retention/repeat rate, churn, CLV, reactivation, revenue
   per recipient — with **holdouts** so you measure incremental lift, not just correlation (→ O6).
   Frame results against the penetration-vs-loyalty reality; don't claim CRM is the growth driver.
7. **Hand off:** the data foundation ↔ first-party-cdp; loyalty/retention strategy ↔
   retention-loyalty; lead nurture entry ↔ lead-scoring-lifecycle (O4); incremental lift ↔ O6;
   consent/compliance ↔ Inspector.

## Output format
```
LIFECYCLE / CRM / EMAIL — <brand>
Context detected: <B2B/B2C · market · stage>
⚠️ Role: profitability / CLV / churn-reduction — NOT the primary growth engine (growth ≈ penetration).

LIFECYCLE STAGES → JOURNEYS
  | Stage (new/onboard/active/at-risk/churned/win-back) | Goal | Key action | Trigger |
  …

SEGMENTATION & TRIGGERS
  Segments (stage × behaviour × value × JTBD) · behaviour-triggered flows · entry/exit/suppression.
  Data source: first-party (← CDP soldier), consented.

MESSAGE & CADENCE (per journey)
  Welcome · onboarding series · re-engagement · win-back · renewal — content/channel/frequency.
  Frequency caps · fatigue guard.

PERSONALISATION (consented first-party only)
  Dynamic content · lifecycle offers · send-time · graceful degradation.

DELIVERABILITY & HYGIENE
  List health · SPF/DKIM/DMARC · engagement-based sending · preference centre.

MEASUREMENT (with holdouts → O6)
  Retention/repeat · churn · CLV · reactivation · revenue/recipient — incremental, not correlational.

HANDOFF: → first-party-cdp (data) · → retention-loyalty · → lead-scoring (O4 entry) · → O6 (lift) · → Inspector (consent).

SOURCES (every rate/CLV/churn figure cited; nothing invented)
  - <CRM/ESP analytics / category benchmark sources researched live>  · jtbd + segments.
```
