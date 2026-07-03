---
name: assumption-testing
description: >-
  Sequences assumption tests from cheapest to most expensive using Teresa Torres's
  test ladder (fake door → smoke test → concierge → Wizard of Oz → data mining),
  guided by McKinsey hypothesis-driven consulting doctrine. Use when a product team
  needs to invalidate or confirm the highest-severity risks attached to a hypothesis
  node in the Opportunity Solution Tree before committing engineering resources.
  Produces a prioritised test plan with pre-experiment rigour checklist, pre-mortem,
  and a go/no-go decision rule for each test.
---

# Skill — Assumption Test Ladder

The assumption test ladder is the operational discipline that prevents teams from
building solutions before the riskiest underlying beliefs have been invalidated at
minimum cost. Teresa Torres (Continuous Discovery Habits, Product Talk, 2021)
defines a canonical sequence ordered by construction cost — fake door, smoke test,
concierge, Wizard of Oz, data mining — where the cheapest test that can meaningfully
refute the highest-severity assumption is always run first. The McKinsey/MBB
hypothesis-driven consulting methodology provides the epistemological frame: every
test is deductive, not exploratory — data is collected to confirm or disprove a
specific, pre-stated node in the hypothesis tree, never to "see what we find"
(McKinsey & Company, The McKinsey Way, Rasiel, 1999). The coupling with the OST
(Opportunity Solution Tree, Torres 2021) means every assumption test must map
explicitly to one hypothesis node, so the outcome of each test updates a specific
belief in the tree rather than floating as disconnected evidence.

> **Doctrine:** Cite Torres (2021) for the test ladder sequence; cite McKinsey /
> Rasiel (1999) for hypothesis-driven structure. Never cite "50% of features are
> never used" — origin is untraceable. The Ellis 40% survey is a desirability
> signal only — it does not substitute for a full assumption test ladder and must
> be scoped to users active in the last 14 days with a minimum of 100 responses
> (Torres, 2021). Never treat a single test result as validation of an entire
> solution — it validates exactly one hypothesis node. Unknown data → say
> "unknown [assumption — verify]".

## Procedure

1. **Map assumptions to OST hypothesis nodes.** Before any test design begins,
   surface all assumptions embedded in the solution under evaluation and map each
   to its corresponding node in the Opportunity Solution Tree. Classify each
   assumption by risk type — desirability (will users want this?), viability
   (can the business sustain it?), feasibility (can the team build it?), and
   usability (can users complete the core task?). The OST node reference is
   mandatory: a test without a node address is untraceable and cannot update the
   team's belief system (Torres, Continuous Discovery Habits, 2021).

2. **Score assumptions by severity and test cost.** Rate each assumption on two
   dimensions: severity (how catastrophically wrong would the business be if this
   assumption fails? — scale 1–5) and test cost (engineering + research hours to
   run the cheapest credible test — scale 1–5, where 1 = hours and 5 = weeks of
   build). Prioritise by the product of cost × severity, not by risk category alone.
   The highest cost × severity score identifies the assumption that must be tested
   next, regardless of whether it is a desirability, viability, or feasibility risk
   (Torres, 2021; O4 doctrine). Do not guess severity scores — anchor them to
   observable business consequences if the assumption is wrong.

3. **Select the appropriate test from the ladder.** Apply Torres's five-rung ladder
   in cost order: (a) Fake door — a call-to-action or landing page for a non-existent
   feature; measures intent to engage; construction cost: hours. (b) Smoke test —
   a minimal artefact (video, prototype, or ad) that presents the value proposition
   without building the product; measures declared interest and willingness to act.
   (c) Concierge — a human manually delivers the value proposition to real customers
   without automation; measures whether customers achieve the desired outcome via the
   underlying service logic, not the technology. (d) Wizard of Oz — the customer
   experiences a product-like interface while a human executes the backend manually;
   tests the full end-to-end experience before engineering automation. (e) Data mining
   — analysis of existing behavioural data (logs, CRM, support tickets) to test an
   assumption without any new customer contact. Select the cheapest rung that can
   meaningfully refute the highest-severity assumption. Never skip rungs to run a
   "more realistic" test at higher cost before cheaper tests have been exhausted
   (Torres, Continuous Discovery Habits, 2021).

4. **Complete the pre-experiment rigour checklist.** Before any test is launched,
   four elements must be documented in writing: (a) Hypothesis — the specific,
   falsifiable belief being tested, in "We believe [X] because [Y]; we will know
   we are right if [Z]" format. (b) Primary metric — the single observable outcome
   that will confirm or refute the hypothesis; never a composite score. (c)
   Counter-metrics — guardrail indicators that, if they move adversely during the
   test, indicate the test itself is causing harm (e.g., a fake door that drives
   a measurable drop in trust or NPS). (d) Minimum Detectable Effect (MDE) — the
   smallest effect size that would be practically meaningful; sets the required
   sample size and prevents calling a null result before the test is powered. No
   test proceeds without all four elements documented.

5. **Run the pre-mortem.** Before launching, enumerate all the ways this test can
   produce a misleading result. At minimum, address three failure modes: (a)
   Simpson's paradox — an aggregate result that masks a reversed pattern within
   a subgroup; specify which segments will be analysed separately. (b) Novelty
   effect — new-user behaviour inflated by curiosity that decays after the first
   week; define the minimum observation window to clear the novelty window. (c)
   Control group contamination from network effects — treated and control users
   interact, so the control is not pure; identify whether the product has network
   structure that makes randomised holdout invalid and specify the alternative
   design (e.g., geo-based or cohort-based split). Document the pre-mortem in the
   same artefact as the rigour checklist. A test launched without a pre-mortem
   is constitutionally incomplete.

6. **Run the test and collect evidence.** Execute the test at the specified sample
   size for the minimum observation window defined in the MDE calculation. Capture
   both quantitative results (primary metric, counter-metrics) and qualitative
   signals (customer words, observed hesitations, unexpected behaviours). Do not
   extend the test window after peeking at results — this inflates false positive
   rates. Quantitative results without qualitative context are insufficient for
   updating the hypothesis tree; both are required.

7. **Issue a go/no-go decision against the pre-stated hypothesis.** Compare the
   primary metric result to the MDE threshold. If the effect meets or exceeds the
   MDE in the predicted direction: the hypothesis node is supported — proceed to
   the next highest-severity assumption. If the effect is below the MDE or in the
   wrong direction: the hypothesis node is refuted — update the OST, descope or
   pivot the solution, and identify the next test target. Never treat an
   inconclusive result as confirmation. A result that is directionally positive but
   below MDE is a signal to redesign the test or revisit the assumption, not to
   proceed.

8. **Update the OST and hand off.** Record the test outcome on the corresponding
   OST hypothesis node. If the full hypothesis tree for a solution is supported
   across all high-severity assumptions, hand off to soldier-opportunity-solution-tree
   (O3/OST) to update the tree and to the O4 officer for solution design progression.
   If the tree is partially refuted, surface the updated node map to O4 and recommend
   the next assumption to test. Never hand off a solution with unresolved
   high-severity (score ≥ 4) assumption nodes.

## Output format

```
ASSUMPTION TEST LADDER — <product / solution / hypothesis>
Context detected: <B2B/B2C · sector · stage · OST node reference>

ASSUMPTION MAP
  OST node:          [specific node in the Opportunity Solution Tree]
  Assumption 1:      [belief] | Type: [desirability/viability/feasibility/usability]
                     Severity: X/5 | Test cost: Y/5 | Priority score: X×Y
  Assumption 2:      [belief] | Type: [...] | Severity: X | Cost: Y | Score: Z
  [continue for all assumptions, ranked by priority score descending]

SELECTED TEST (highest-priority assumption)
  Assumption tested: [the specific belief]
  Test type:         [fake door / smoke test / concierge / Wizard of Oz / data mining]
  Rationale:         [why this is the cheapest test capable of meaningfully refuting this assumption]
  Ladder rung:       [1–5] — cheaper rungs exhausted: [yes/no — list if yes]

PRE-EXPERIMENT RIGOUR CHECKLIST
  Hypothesis:        We believe [X] because [Y]; we will know we are right if [Z]
  Primary metric:    [single observable outcome]
  Counter-metrics:   [guardrail indicators; adverse movement = test harm signal]
  MDE:               [minimum effect size meaningful to the business] → required n = [N]
  Observation window:[minimum duration, cleared of novelty window]

PRE-MORTEM
  Simpson's paradox: [which subgroups will be analysed separately and why]
  Novelty effect:    [minimum window to clear novelty; risk level: low/medium/high]
  Network contamination: [network structure present? yes/no; split design: random / geo / cohort]
  Other failure modes: [additional risks specific to this test design]

TEST RESULTS (if available)
  Primary metric:    [observed result] vs MDE threshold [value] → [met / not met]
  Counter-metrics:   [observed movement] → [no harm / harm detected]
  Qualitative signals: [exact customer words or observed behaviours]

GO / NO-GO DECISION
  Verdict:           [GO — hypothesis supported / NO-GO — hypothesis refuted / INCONCLUSIVE]
  OST node update:   [supported / refuted / requires redesign]
  Next assumption:   [next highest-priority assumption to test]

SO-WHAT / NEXT STEPS
  - [Primary action: proceed / pivot / descope based on verdict]
  - [Next test on the ladder if this result was inconclusive]
  - [Handoff target: soldier-opportunity-solution-tree (O3/OST) or O4 officer]
  - [Any unresolved high-severity assumptions that block solution progression]

SOURCES (every external fact cited; nothing invented)
  - Teresa Torres — Continuous Discovery Habits, Product Talk (2021) — test ladder
    sequence (fake door → smoke test → concierge → Wizard of Oz → data mining);
    OST hypothesis node coupling; Ellis 40% scope constraints
  - Ethan Rasiel / McKinsey & Company — The McKinsey Way (1999) — hypothesis-driven
    consulting methodology; deductive data collection against pre-stated hypothesis tree
```
