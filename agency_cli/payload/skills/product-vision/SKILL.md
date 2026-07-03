---
name: product-vision
description: >-
  Produces a validated product vision artifact using Amazon's PR/FAQ protocol,
  McKinsey's SCR narrative pyramid, and Brian Chesky's 90-day kill-test. Use when
  a team needs to establish, stress-test, or communicate a product direction before
  any design work begins. Output is a press-release-format vision document with a
  mandatory kill-evidence audit.
---

# Skill — Product Vision (PR/FAQ + SCR + Kill-Test)

Product vision is the primary mechanism by which a product team aligns on what they are
building, for whom, and why — before a single pixel is designed. Amazon's Working Backwards
method (Bryar & Carr, 2021) treats the press release as the vision artifact itself: if the
team cannot write a compelling one-page PR/FAQ, the product is not ready to be built.
McKinsey's SCR pyramid (Barbara Minto, Pyramid Principle, 1987) governs how that vision is
communicated to executives and cross-functional partners. Brian Chesky's kill-test (Config
2023) provides the ongoing validity criterion: a vision that has not been used to say "no"
in the last 90 days is decoration, not strategy.

> **Doctrine:** Cite only real sources (author/book/firm/year) for every external claim.
> Never cite "50% of features are never used" (untraceable), NPS as sole growth driver,
> or the 40% PMF threshold as a universal law. A press release is not a summary — it is
> the vision artifact. A vision that only inspires without constraining is wallpaper.
> The kill-test (Chesky, 2023) is a hard gate: if the vision has not produced a "no"
> decision in 90 days, it must be sharpened or declared decorative before proceeding.

## Procedure

1. **Gather context and detect product type.** Identify the product domain, stage (0→1,
   scaling, mature), customer segment (B2B / B2C / marketplace), and any live regulatory
   surface (GDPR, CCPA, HIPAA). Confirm whether a prior vision document exists. If one
   exists, retrieve the date of its last kill-decision before drafting anything new.

2. **Draft the Amazon PR/FAQ press release.** Write a one-page document — exactly as
   specified in Bryar & Carr (Working Backwards, 2021) — containing six elements: (a)
   headline naming the product and primary customer benefit; (b) subheadline with a
   one-sentence summary of the problem solved; (c) three-paragraph body covering the
   customer problem, how the product solves it, and what success looks like; (d) a
   company quote from a named executive role (not a real name — use a role title);
   (e) a customer quote in the customer's own voice describing the before/after;
   (f) a call to action. Do not proceed to SCR framing until the PR/FAQ passes internal
   coherence — if the PR sounds unconvincing, the product definition is incomplete.

3. **Apply Apple's Focus Doctrine (what the vision is NOT).** Following Jobs' documented
   discipline (described in Walter Isaacson, Steve Jobs, 2011) of listing ten strategic
   directions, eliminating seven, and committing to three: produce an explicit exclusion
   list. A vision without a "not this" list cannot be used to make tradeoff decisions.
   Minimum three explicit exclusions required. Each exclusion must be a real strategic
   alternative the team could plausibly have chosen, not a trivially irrelevant idea.

4. **Structure the executive narrative using SCR.** Apply Barbara Minto's Pyramid
   Principle (1987) — Situation / Complication / Resolution — to frame the vision for
   stakeholder communication. Situation: state only incontestable facts about the current
   market or customer context (no editorializing). Complication: describe what has changed
   or what is at risk that makes the status quo untenable. Resolution: state the vision
   as the answer to the complication. The SCR structure is a communication layer on top
   of the PR/FAQ, not a replacement for it.

5. **Apply Bain's Clear Ambition stakeholder completeness check.** Verify that the vision
   simultaneously addresses all four stakeholder dimensions identified by Bain's Clear
   Ambition framework: customers (what problem is solved and for whom), shareholders
   (what economic value is created), employees (what mission makes this work meaningful),
   and society (what externalities or broader contribution are acknowledged). A vision
   that addresses only customers and shareholders is incomplete. Flag any missing dimension
   explicitly.

6. **Run the 90-day kill-test audit.** Following Chesky's Config 2023 criterion: if the
   vision is pre-existing, document whether it was used to kill or decline a feature,
   initiative, or partner request in the last 90 days. If no kill-decisions are on record,
   classify the vision as decorative and flag it as requiring sharpening. If the vision is
   new, record a forward commitment: identify three candidate initiatives that the vision
   already implies a "no" to, and name them explicitly. This aligns with Ryan Singer's
   Shape Up circuit-breaker logic (37signals, 2019): inability to define scope boundaries
   signals an absence of a real outcome commitment.

7. **Produce the output block.** Deliver the complete PR/FAQ, SCR narrative, exclusion
   list, stakeholder completeness check, and kill-test evidence in the structured format
   below. Every external claim must be sourced. Unsourced facts are tagged
   [assumption — verify].

8. **Flag ethics, compliance, and data risks.** If the vision involves personal data
   collection, AI-driven decisions, or content targeting, explicitly flag applicable
   regulations (GDPR, CCPA, COPPA, HIPAA) and surface any dark-pattern risks in the
   proposed customer experience before sign-off.

## Output format

```
PRODUCT VISION — <product / context>
Context detected: <B2B/B2C · sector · stage>

PR/FAQ — PRESS RELEASE
  Headline:      ...
  Subheadline:   ...
  Problem (¶1):  ...
  Solution (¶2): ...
  Success (¶3):  ...
  Company quote: "[Role, not name]: ..."
  Customer quote: "..."
  Call to action: ...

SCR EXECUTIVE NARRATIVE
  Situation (incontestable facts only): ...
  Complication (what changed or is at risk): ...
  Resolution (the vision statement): ...

FOCUS DOCTRINE — WHAT THIS VISION IS NOT
  Excluded direction 1: ... [rationale: ...]
  Excluded direction 2: ... [rationale: ...]
  Excluded direction 3: ... [rationale: ...]

STAKEHOLDER COMPLETENESS (Bain Clear Ambition)
  Customers:    ... [present / missing]
  Shareholders: ... [present / missing]
  Employees:    ... [present / missing]
  Society:      ... [present / missing]

KILL-TEST AUDIT (90-day cadence — Chesky, Config 2023)
  Last kill-decision on record: <date or "none">
  Kill-test status: ACTIVE / DECORATIVE
  If new vision — implied "no" decisions:
    - Initiative A: declined because ...
    - Initiative B: declined because ...
    - Initiative C: declined because ...

COMPLIANCE & ETHICS FLAGS
  - [Any GDPR / CCPA / HIPAA / dark-pattern risks surfaced, or "none detected"]

SO-WHAT / NEXT STEPS
  - ...

SOURCES (every external fact cited; nothing invented)
  - Colin Bryar & Bill Carr, Working Backwards, 2021 — PR/FAQ protocol
  - Barbara Minto, The Pyramid Principle, 1987 — SCR narrative structure
  - Brian Chesky, Config 2023 keynote — 90-day kill-test criterion
  - Walter Isaacson, Steve Jobs, 2011 — Focus Doctrine (ten directions → three)
  - Ryan Singer, Shape Up, 37signals, 2019 — scope boundaries as outcome commitment
  - [Any additional sources for domain-specific facts, or [assumption — verify]]
```
