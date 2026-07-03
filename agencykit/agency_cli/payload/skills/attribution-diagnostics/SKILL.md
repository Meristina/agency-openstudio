---
name: attribution-diagnostics
description: >-
  Attribution diagnostics — use last-touch / multi-touch attribution (MTA) and platform-reported
  conversions as a FAST TACTICAL DIAGNOSTIC for in-flight optimisation, while treating them as
  SYSTEMATICALLY BIASED and NEVER the verdict on what worked. Reads platform numbers for relative,
  directional signal (creative/audience/keyword level), cross-checks against incrementality and
  MMM, and explicitly discounts the over-counting. Grounded in Gordon, Moakler & Zettelmeyer (2023):
  observational/last-touch overstate lift ~5-13×; 69% of practitioners distrust last-touch.
  Never reports attribution as causal truth or invents a conversion number.
---

# Skill — Attribution Diagnostics

Use the numbers the ad platforms and analytics tools hand you — last-touch, multi-touch (MTA),
platform-reported conversions — for what they're actually good at: **fast, granular, in-flight
optimisation signal** (which creative, audience, keyword, or placement is moving relatively).
Treat them as a **biased diagnostic, never the verdict** on marketing's true effect.

> **Doctrine — biased diagnostic, NEVER alone.** Platform last-touch / MTA is **systematically
> biased** — it over-credits lower-funnel and retargeting and double-counts across walled gardens.
> Observational/last-touch methods **overstate lift ~5-13×** (Gordon, Moakler & Zettelmeyer,
> *Marketing Science* 2023; 69% of practitioners distrust last-touch). So: use attribution for
> **relative, directional, tactical** decisions only; the **causal verdict belongs to
> incrementality**, and **MMM allocates** — attribution is reconciled *against* them, never reported
> as the truth. **Never present an attribution number as causal or de-duplicated across platforms.**
> **Never invent** a conversion count, ROAS, or path metric — pull it from the platform/source or
> label `[assumption — verify]`; unknown → "unknown".

## Procedure
1. **Frame the tactical question:** what in-flight decision needs fast signal (pause a creative,
   shift between audiences/keywords, spot a broken funnel step)? Attribution is for *this*, not for
   "did marketing work?" (that's incrementality).
2. **Pick the model & state its bias:** last-touch (biased to the closer), first-touch (biased to
   the opener), linear/time-decay/position-based (arbitrary weights), data-driven (opaque). Name
   the bias of whichever you use; don't pretend any model is "correct".
3. **Read relative, not absolute:** use the numbers for **ranking and direction** (A vs B, trend
   up/down), not as the true incremental count. Compare like-for-like windows and settings.
4. **Account for the known distortions:** view-through inflation, retargeting taking credit for
   demand it didn't create, walled-garden double-counting (each platform claims the same sale),
   attribution-window and iOS/consent gaps. Discount accordingly.
5. **Cross-check & reconcile (mandatory):** hold attribution **up against incrementality** (the
   causal anchor) and **MMM** (the allocator). Where attribution disagrees, **attribution loses** —
   report the gap and the discount factor, not the platform number.
6. **Use it for what it's good at:** rapid creative/audience/keyword iteration, funnel-leak spotting,
   anomaly detection — granular and timely where experiments are too slow.
7. **Hand off:** the causal verdict ↔ incrementality; budget allocation ↔ mmm + budget-balance;
   on-site funnel issues ↔ conversion-cro (O4); data/consent gaps ↔ Inspector.

## Output format
```
ATTRIBUTION DIAGNOSTICS — <channel / campaign>
Context detected: <B2B/B2C · market · stage>   |  Tactical decision: <pause/shift/spot leak>
⚠️ BIASED diagnostic — NEVER the verdict. Last-touch/observational overstates lift ~5-13x (Gordon et al. 2023). Causal truth = incrementality.

MODEL & ITS BIAS
  Model used: <last-touch / MTA / data-driven> — known bias: …  (no model is "correct")

RELATIVE READ (direction, not absolute truth)
  | Creative/audience/keyword | Platform-reported signal | Trend | Relative rank |
  …  Like-for-like windows/settings: …

KNOWN DISTORTIONS DISCOUNTED
  View-through inflation · retargeting over-credit · walled-garden double-count · window/iOS/consent gaps.

CROSS-CHECK & RECONCILE (mandatory)
  vs incrementality (causal anchor): …  vs MMM (allocator): …  Where attribution disagrees → discounted; gap: …

TACTICAL USE (what it's good for)
  Creative/audience/keyword iteration · funnel-leak spotting · anomaly detection.

HANDOFF: → incrementality (verdict) · → mmm/budget-balance (allocation) · → conversion-cro (funnel) · → Inspector.

SOURCES (every conversion/ROAS figure cited; nothing invented)
  - Gordon, Moakler & Zettelmeyer 2023 (overstate ~5-13x) · <platform/analytics data — flagged biased>.
```
