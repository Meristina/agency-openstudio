---
name: four-risks
description: >-
  Sequences and designs the cheapest possible test for each of the four
  hypothesis risk types — desirability, viability, feasibility, and usability —
  derived from Teresa Torres's OST taxonomy and Robert Cooper's Stage-Gate kill
  criteria. Use before any engineering investment when assumption risk is
  unquantified. Produces a risk register ranked by severity × test cost, a
  per-risk test prescription, and an explicit kill-or-go decision at each gate.
---

# Skill — Four-Risk Hypothesis Testing

Four-risk hypothesis testing is the discipline of classifying every product
assumption into one of four failure modes — desirability (do users want this?),
viability (can the business sustain this?), feasibility (can the team build
this?), usability (can users operate this without friction?) — and then
sequencing tests by the product of risk severity and test cost, not by
category. Teresa Torres formalised this taxonomy within the Opportunity Solution
Tree (OST) framework (Torres, Continuous Discovery Habits, 2021), where
assumption classification is the mandatory gate between solution leaves and
experiment design. Robert Cooper's Stage-Gate model adds the structural kill
discipline: the Stage 2 Business Case gate requires evidence on all four risk
dimensions before full resource commitment, and the Kill decision at any gate
must be exercised with the same rigour as the Go decision (Cooper, Winning at
New Products, 4th ed., 2011). BCG's transformation sequence — Diagnose, Design,
Pilot, Scale, Embed — treats the Pilot phase as the non-negotiable gate before
Scale; no resources escalate until pilot evidence clears all four risk types
(BCG, Large-Scale Change, 2019). The operational implication: constructing a
feature in order to "test" it is validation deferred at maximum cost, not
hypothesis testing.

> **Doctrine:** Every risk classification and test recommendation must cite its
> source (Torres, Cooper, BCG — year and publication). Never cite "50% of
> features never used" — that figure is untraceable. Do not treat a single
> viability model as validated; NielsenIQ BASES is the primary volumetric
> forecasting instrument for CPG/consumer contexts (calibrated against 300,000+
> concept tests), but is proprietary and must be labelled [assumption — verify]
> when unavailable. The Kill decision is structurally equal to the Go decision
> (Cooper, 2011) — never omit it from gate outputs. Severity is assessed from
> user and market evidence, never from team conviction.

## Procedure

1. **Inventory all assumptions for the target solution.** Before writing a
   single test, list every untested belief the solution depends on. Use the
   five-whys cascade: "What must be true for this solution to work?" Repeat
   until no further assumption can be unpacked. Aim for completeness — omitted
   assumptions become post-launch surprises. Record each assumption as a
   falsifiable statement (if false, consequence X follows).

2. **Classify each assumption into one of the four risk types.** Apply Torres's
   OST hypothesis taxonomy (Torres, 2021): Desirability — users want or need
   this, the problem is real, and the solution addresses it. Viability — the
   business model, unit economics, pricing, and regulatory context make this
   sustainable. Feasibility — the team can build, maintain, and operate this
   with available technology, talent, and timeline. Usability — users can
   discover, learn, and operate this without unacceptable friction or error.
   An assumption may straddle categories; assign to the dominant failure mode
   and note the overlap.

3. **Rate severity for each assumption.** Severity is the magnitude of damage
   if the assumption is false: what revenue, retention, or mission impact
   follows from failure? Use a 1–5 ordinal scale: 1 = low (recoverable in one
   sprint), 5 = critical (invalidates the entire solution or threatens the
   business case). Severity ratings must reference user research or financial
   data, never team opinion alone. Flag all severity ratings lacking evidence
   as [assumption — verify].

4. **Estimate the cost of the cheapest test per assumption.** Map each risk
   type to its canonical cheapest test instrument — desirability: fake door or
   smoke test (landing page, email campaign, pre-launch sign-up); viability:
   financial modelling, unit-economics spreadsheet, or NielsenIQ BASES
   volumetric forecast for CPG contexts; feasibility: engineering spike (a
   time-boxed prototype or proof-of-concept, typically 1–5 days); usability:
   task-based usability test with 5 representative users (Nielsen, 1994,
   documented that 5 users surface ~85% of usability issues). Cost = time ×
   people × opportunity cost. Do not build the full feature to test a
   desirability assumption — that is the highest-cost test available.

5. **Sequence tests by severity × test cost (descending).** Compute a
   sequencing score: severity (1–5) × cost bucket (1 = hours, 2 = days,
   3 = weeks, 4 = sprint, 5 = quarter). Tests with the highest severity and
   lowest cost run first. This is the operative doctrine: Torres (2021) and
   Cooper's Stage-Gate (2011) both prescribe cheap early falsification before
   expensive later elaboration. Tests that are cheap AND address critical
   assumptions are always the first in the queue regardless of category.

6. **Apply Cooper's Stage-Gate kill criteria at each gate.** For each test,
   define the pre-specified kill threshold: the measurable outcome below which
   the solution is killed or pivoted before proceeding to the next phase. Kill
   criteria must be defined before the test runs — not after results are seen.
   For Stage 2 (Business Case gate), all four risk types require a passing
   threshold before engineering resources are committed (Cooper, Winning at New
   Products, 4th ed., 2011). The Kill decision requires equal discipline to the
   Go decision; a failed kill criterion that is waived without documented
   justification is a governance failure.

7. **Apply the BCG Pilot gate before Scale.** After individual assumption tests
   pass, the BCG Diagnose→Design→Pilot→Scale→Embed sequence requires a
   structured Pilot phase in which the integrated solution is validated in a
   real-world limited-scope deployment before full resource escalation (BCG,
   Large-Scale Change, 2019). The Pilot is non-negotiable: it tests assumption
   interactions that individual tests cannot detect (e.g., a technically
   feasible feature that proves commercially unviable in a real pricing context).
   Define the Pilot scope, success metrics, and duration before entry.

8. **Produce the risk register and so-what output.** Deliver a complete ranked
   risk register with test sequence, kill criteria, and go/kill decisions for
   all completed tests. Call out the single highest-priority test to run next,
   its owner, timeline, and the specific kill threshold. Connect residual risks
   to downstream officers: unresolved viability risk escalates to the CPO or
   finance gate; unresolved feasibility risk escalates to engineering leadership
   before any roadmap commitment.

## Output format

```
FOUR-RISK HYPOTHESIS TESTING — <product / solution / context>
Context detected: <B2B/B2C · sector · stage>

ASSUMPTION INVENTORY
  Total assumptions identified: N
  By risk type: Desirability (n) · Viability (n) · Feasibility (n) · Usability (n)

RISK REGISTER (ranked by severity × cost)
  Rank | Assumption | Risk Type | Severity (1–5) | Cheapest Test | Est. Cost | Kill Threshold | Status
  ─────┼────────────┼───────────┼────────────────┼───────────────┼───────────┼────────────────┼────────
  1    | [statement]| Desirb.   | 5              | Fake door     | 2 days    | >200 sign-ups  | PENDING
  2    | [statement]| Viab.     | 4              | Unit-econ model| 1 day    | CAC < $X       | PENDING
  3    | [statement]| Feasib.   | 4              | Eng. spike    | 3 days    | API latency <200ms| PENDING
  4    | [statement]| Usab.     | 3              | 5-user test   | 2 days    | Task success >80%| PENDING

GATE DECISIONS (Cooper Stage-Gate — Stage 2 Business Case)
  Desirability gate : [PASS / FAIL / PENDING — evidence summary]
  Viability gate    : [PASS / FAIL / PENDING — evidence summary]
  Feasibility gate  : [PASS / FAIL / PENDING — evidence summary]
  Usability gate    : [PASS / FAIL / PENDING — evidence summary]
  Overall gate      : [GO / KILL / HOLD — rationale]

BCG PILOT GATE
  Pilot scope       : [geography / segment / duration]
  Pilot success metric: [measurable threshold]
  Scale trigger     : [what evidence unlocks Scale phase]
  Current status    : [PENDING / IN PROGRESS / PASSED / KILLED]

SO-WHAT / NEXT STEPS
  - Highest-priority test to run next: [test name, owner, deadline, kill threshold]
  - Residual viability risk escalation: [to whom, by when]
  - Residual feasibility risk escalation: [to whom, by when]
  - BCG Pilot gate timeline: [date and entry criteria]

SOURCES (every external fact cited; nothing invented)
  - Teresa Torres — Continuous Discovery Habits, Product Talk, 2021
    https://www.producttalk.org/continuous-discovery-habits/
  - Robert G. Cooper — Winning at New Products, 4th ed., Basic Books, 2011
    [Stage-Gate kill criteria and Business Case gate structure]
  - BCG — Large-Scale Change (Diagnose→Design→Pilot→Scale→Embed), 2019
    https://www.bcg.com/capabilities/transformation [assumption — verify exact URL]
  - NielsenIQ BASES — Volumetric concept testing, 300,000+ concept database
    https://nielseniq.com/global/en/solutions/bases/ [assumption — verify]
  - Jakob Nielsen — "Why You Only Need to Test with 5 Users", NN/g, 2000
    https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/
```
