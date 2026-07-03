---
name: first-party-cdp
description: >-
  First-party data & CDP foundation — design the consented data architecture that powers
  lifecycle, personalisation, and measurement in the post-cookie era: first-party/zero-party data
  collection, identity resolution, a customer data platform (CDP) as the unified profile layer,
  consent/governance, and activation to channels. Based on McKinsey's closed-loop data
  architecture — FLAGGED AS DATED (pre-2023) and re-verified against current post-cookie practice.
  Grounds every claim in evidence and consent law; never invents a vendor capability or stat.
---

# Skill — First-Party Data & CDP Foundation

Build the **data foundation** the rest of lifecycle/retention stands on: collect first-party and
zero-party data with consent, resolve identity into a single customer view, unify it in a CDP,
govern it, and activate it to the channels (CRM/email, paid, product). As third-party cookies and
cross-site identifiers decay, owned first-party data becomes the durable asset.

> **Doctrine — dated reference, verify freshness.** The canonical model here is **McKinsey's
> closed-loop data architecture** — the structure is durable, but the source is **pre-2023; FLAG
> IT AS DATED** and **re-verify against current post-cookie practice** (consent frameworks,
> identifier deprecation timelines, clean rooms, server-side, on-device/Privacy Sandbox-type
> shifts) with live research. **Do NOT cite the refuted claim** that "legacy systems (CRM/MDM/MRM)
> are insufficient for personalisation". Consent and data law are **central, not a footnote**
> (GDPR/CCPA/ePrivacy/local → Inspector). **Never invent** a vendor capability, adoption stat, or
> match rate — research/verify it or label `[assumption — verify]`; unknown → "unknown".

## Procedure
1. **Goal & data audit:** what decisions the data must power (lifecycle, personalisation,
   measurement, suppression); inventory current first-party sources, gaps, and quality. State the
   business use cases first — don't build a CDP for its own sake.
2. **First-party & zero-party collection:** the value exchange that earns consented data (declared
   preferences, progressive profiling, loyalty, accounts); minimise to what's used; design for
   consent and transparency from the start.
3. **Identity resolution:** deterministic (logged-in, email) and, cautiously, probabilistic;
   define the unified customer profile and the match logic; flag match-rate assumptions.
4. **CDP / unified profile layer:** the role of a CDP (ingest → unify → segment → activate) vs the
   existing stack (CRM/MDM/DWH) — **don't assume legacy is "insufficient"; assess what's reusable.**
   Decide build/buy and where the CDP fits; avoid duplicate sources of truth.
5. **Consent & governance (central):** consent capture/propagation, preference management, data
   retention/minimisation, access controls, regional rules (GDPR/CCPA/ePrivacy/local) — verified
   by the Inspector. Privacy-by-design, not bolted on.
6. **Post-cookie freshness check (mandatory):** re-verify the architecture against current practice
   — identifier deprecation status, clean rooms, server-side/conversions APIs, contextual,
   modelled conversions. Note where the dated McKinsey model needs updating.
7. **Activation & measurement:** push unified, consented profiles to CRM/email (lifecycle-crm),
   paid (suppression/lookalikes within privacy rules), and measurement (→ O6 incrementality/MMM
   need clean first-party signals). Close the loop back to the data.
8. **Hand off:** the program that uses the data ↔ lifecycle-crm-email; loyalty data ↔
   retention-loyalty; clean signals for causal measurement ↔ O6; consent/compliance ↔ Inspector.

## Output format
```
FIRST-PARTY DATA & CDP — <brand>
Context detected: <B2B/B2C · market · stage>
⚠️ Reference (McKinsey closed-loop architecture) is PRE-2023 — flagged dated; re-verified vs current post-cookie practice.

DATA GOAL & AUDIT
  Use cases the data must power · current first-party sources/gaps/quality.

FIRST-PARTY / ZERO-PARTY COLLECTION
  Value exchange for consent · declared/progressive/loyalty · data minimisation.

IDENTITY RESOLUTION
  Deterministic / probabilistic · unified profile · match logic [assumptions flagged].

CDP / UNIFIED PROFILE LAYER
  CDP role (ingest→unify→segment→activate) vs existing stack (CRM/MDM/DWH — what's reusable).
  Build/buy · avoid duplicate truth.  (Do NOT assume legacy is "insufficient".)

CONSENT & GOVERNANCE (central)
  Consent capture/propagation · preference mgmt · retention/minimisation · access · regional law → Inspector.

POST-COOKIE FRESHNESS CHECK
  Identifier deprecation status · clean rooms · server-side/CAPI · modelled conversions — where the dated model updates.

ACTIVATION & MEASUREMENT
  To CRM/email · paid (privacy-safe) · O6 (clean signals for incrementality/MMM). Closed loop.

HANDOFF: → lifecycle-crm-email · → retention-loyalty · → O6 (signals) · → Inspector (consent).

SOURCES (live + dated flagged; nothing invented)
  - McKinsey closed-loop data architecture (PRE-2023 — dated) + <current post-cookie sources researched live>.
```
