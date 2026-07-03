---
name: usability-testing
description: >-
  Runs the full usability-testing lifecycle: heuristic evaluation by 3–5 expert
  reviewers against Nielsen's 10 heuristics before any participant is recruited,
  then moderated participant sessions using Portigal probing techniques, followed
  by rainbow spreadsheet synthesis to identify cross-session issue patterns. Use
  when validating a new interface, auditing an existing flow, or preparing a design
  for a launch-readiness gate. Produces a severity-ranked issue log, a rainbow
  spreadsheet, and a prioritised fix list with owners.
---

# Skill — Usability Testing (Heuristic Evaluation → Sessions → Rainbow Synthesis)

Usability testing is the structured process of exposing real (or simulated) users to a
product in order to identify friction, comprehension failures, and task-completion barriers
that cannot be inferred from analytics alone. The method rests on three sequential layers:
(1) heuristic evaluation, where 3–5 independent expert reviewers apply Jakob Nielsen's 10
usability heuristics (Nielsen Norman Group, 1994) to the interface before any participant
is recruited — this step captures approximately 65% of usability problems at a cost-per-
defect far below any session-based method (Nielsen, "Why You Only Need to Test with 5
Users," NNg, 2000); (2) moderated participant sessions, where 5 participants per target
segment complete realistic task scenarios while a facilitator applies Steve Portigal's
probing techniques (Portigal, Interviewing Users, Rosenfeld Media, 2013) to surface
reasoning and mental models the observer cannot infer from behaviour alone; (3) rainbow
spreadsheet synthesis, where every observed issue is logged across sessions in a shared
matrix, revealing cross-participant patterns and severity gradients for prioritisation.
The cognitive walkthrough (Wharton et al., 1994) serves as a structured complement to
heuristic evaluation, applying three questions at each task step to surface learnability
failures specifically. This skill operationalises the O4 doctrine mandate: heuristic
evaluation precedes participant sessions — teams that skip to participants waste recruits
and budget on defects any trained practitioner would find in two hours.

> **Doctrine:** The 65% issue detection figure (Nielsen, 2000) applies to heuristic
> evaluation with 3–5 evaluators; it is not a claim about participant sessions or any
> single evaluator alone. Never cite "50% of features are never used" (untraceable).
> Never use NPS as a usability severity proxy. Portigal's probing techniques are
> facilitation aids, not validated diagnostic instruments — label participant inference
> [assumption — verify] unless corroborated across sessions. Biometric signals (Tobii Pro
> eye-tracking, iMotions affect analysis) supplement but do not replace task-completion
> observation; treat fixation data as hypothesis-generating, not confirmatory. Research
> every external fact; invent nothing.

## Procedure

1. **Heuristic evaluation gate.** Before recruiting a single participant, assemble 3–5
   independent expert reviewers (UX practitioners or domain-knowledgeable PMs). Each
   reviewer independently walks every screen and flow against Nielsen's 10 heuristics:
   visibility of system status; match between system and the real world; user control and
   freedom; consistency and standards; error prevention; recognition rather than recall;
   flexibility and efficiency of use; aesthetic and minimalist design; help users recognise,
   diagnose, and recover from errors; help and documentation. Log every issue with: heuristic
   violated, screen/component, severity (0–4 on Nielsen's scale), and reviewer ID. Do not
   discuss findings before all reviews are complete — cross-contamination degrades
   independence. The 3–5 evaluator threshold is the sweet spot for ROI: fewer misses issues;
   more produces rapidly diminishing returns (Nielsen Norman Group, 1994).

2. **Cognitive walkthrough at critical paths.** Apply the cognitive walkthrough method
   (Wharton, Rieman, Lewis, Polson, 1994) to the 2–3 highest-stakes task flows identified
   in Step 1. At each step in the task, ask three questions: (a) Will the user know what
   action to take next? (b) Will the user notice the correct control or affordance? (c) Will
   the user correctly interpret feedback after the action? Document failures per step. This
   targets learnability failures — the subset of heuristic issues most predictive of first-
   session abandonment — before any live participant attempts the flow.

3. **Issue consolidation and severity ranking.** Merge all heuristic evaluation and cognitive
   walkthrough findings into a single issue log. Deduplicate issues raised by multiple
   reviewers (record all reviewer IDs as confirming instances). Apply Nielsen's 0–4 severity
   scale: 0 = not a problem; 1 = cosmetic; 2 = minor; 3 = major; 4 = catastrophic (must fix
   before launch). Separate Severity 3–4 issues as a blocking fix list; triage Severity 1–2
   into a backlog. Any Severity 4 issue triggers a design hold — participant sessions proceed
   only after Severity 4 fixes are verified. This is the O4 doctrine gate: do not bring a
   broken prototype to participants.

4. **Participant recruitment and task design.** Recruit 5 participants per primary target
   segment. Nielsen's 5-user rule (NNg, 2000) states that 5 participants reveal approximately
   85% of a product's usability problems for a homogeneous user group; a second round of 5
   after iteration finds diminishing marginal issues. Exclude internal employees and anyone
   familiar with the product. Write 3–6 realistic scenario tasks — not instructions ("you
   want to check your order status; show me what you'd do"), not leading questions. Each task
   must have a measurable completion criterion. Document any GDPR/CCPA consent obligations
   before sessions begin: session recording requires explicit informed consent; biometric
   data (eye-tracking, affect analysis) is sensitive personal data requiring heightened
   consent and data-minimisation controls under GDPR Art. 9 [assumption — verify jurisdiction
   applicability].

5. **Moderated session facilitation (Portigal techniques).** Open each session with a
   context-setting probe: ask the participant to narrate their current experience with similar
   products or workflows before touching the prototype — this calibrates their mental model
   and avoids anchoring. During task execution, use the think-aloud protocol: invite the
   participant to narrate continuously. Apply Portigal's naïve probe when behaviour diverges
   from expectation: "Why do you do it that way?" — never "Why didn't you click X?" Use
   ask-the-opposite to surface hidden assumptions: if the participant says a feature is clear,
   ask "Is there anything about this that might confuse someone encountering it for the first
   time?" Use the five-whys sequence to move from surface behaviour to underlying mental-model
   mismatch. Never correct errors during the task; observe and log. End each session with a
   debrief: "What would you change about this, and why?" (Steve Portigal, Interviewing Users,
   Rosenfeld Media, 2013).

6. **Biometric and implicit signal capture (optional layer).** For flows where self-report is
   insufficient — e.g., emotional response to trust signals, cognitive load on dense screens
   — deploy eye-tracking (Tobii Pro) for fixation heat maps and area-of-interest dwell-time
   analysis, or iMotions for multi-signal affect capture. These tools surface signals users
   cannot self-report: attention blind spots, confusion micro-expressions, and fixation on
   non-interactive elements. Treat all biometric outputs as hypothesis-generating — correlate
   with task-completion data and verbal protocol before drawing conclusions. Flag any
   biometric finding not corroborated by at least one other signal as [assumption — verify].
   Reference Google's Search Quality Rater system as a model for scaled human evaluation
   where A/B testing cannot capture quality dimensions such as trustworthiness and potential
   for harm (Google Search Quality Evaluator Guidelines, public edition).

7. **Rainbow spreadsheet synthesis.** After all sessions, populate a rainbow spreadsheet:
   rows = observed issues; columns = participants (P1–P5, colour-coded by session). For each
   issue, mark which participants encountered it. Issues appearing in 4+ of 5 sessions are
   systemic (fix immediately). Issues in 2–3 sessions are significant (schedule for next
   sprint). Issues in 1 session are worth logging but low priority absent corroborating
   heuristic evidence. Add a severity column (cross-referenced from Step 3) and an issue-
   owner column. The rainbow spreadsheet is the primary artefact for stakeholder
   communication — it makes pattern frequency visually self-evident without requiring
   statistical expertise to interpret.

8. **Prioritised fix list and handoff.** Produce a prioritised fix list: Severity 4 + systemic
   (top priority, design hold); Severity 3 + significant (fix before next usability round);
   Severity 2 + significant (backlog with owner); all others (log and monitor). Assign a
   named owner and target sprint to every top-priority item. Document residual risks:
   participant sample representativeness, task realism constraints, biometric data quality
   gaps. Hand off to soldier-prototyping for iteration, or to soldier-launch-readiness for
   gate sign-off if the fix list is clear.

## Output format

```
USABILITY TESTING — <product / feature / context>
Test date: <YYYY-MM-DD>   |   Participants: <n per segment>   |   Segments: <list>
Context detected: <B2B/B2C · sector · stage · device>

HEURISTIC EVALUATION SUMMARY (pre-session gate)
  Evaluators: <n>   |   Heuristics applied: Nielsen 10 (NNg, 1994)
  Issue count by severity:
    Severity 4 (catastrophic): <n>  — DESIGN HOLD until resolved
    Severity 3 (major):        <n>
    Severity 2 (minor):        <n>
    Severity 1 (cosmetic):     <n>
  Top blocking issues:
    - [SEV-4] <heuristic violated>: <screen/component> — <description>
    - [SEV-3] <heuristic violated>: <screen/component> — <description>
  Cognitive walkthrough findings (critical paths):
    - Task <n>, Step <n>: <question failed> — <description>

PARTICIPANT SESSION LOG
  P1 (<segment>): Tasks completed <n/n> | Key issues: <list>
  P2 (<segment>): Tasks completed <n/n> | Key issues: <list>
  ...
  P5 (<segment>): Tasks completed <n/n> | Key issues: <list>
  Notable Portigal probes (naïve / ask-the-opposite findings): <list>

RAINBOW SPREADSHEET (cross-session pattern matrix)
  Issue                          | P1 | P2 | P3 | P4 | P5 | Freq | Severity | Owner
  -------------------------------|----|----|----|----|-----|------|----------|------
  <issue description>            | X  | X  | X  | X  |  X  | 5/5  | SEV-3    | <name>
  <issue description>            | X  |    | X  | X  |     | 3/5  | SEV-2    | <name>
  <issue description>            |    |    | X  |    |     | 1/5  | SEV-1    | log
  Biometric flags (if applicable): <fixation blind spots, AOI anomalies>

PRIORITISED FIX LIST
  IMMEDIATE (Sev 4 / systemic — design hold):
    - <issue>: owner <name>, target <sprint/date>
  NEXT SPRINT (Sev 3 / significant):
    - <issue>: owner <name>, target <sprint/date>
  BACKLOG (Sev 2 / minor or isolated):
    - <issue>: owner <name>

SO-WHAT / NEXT STEPS
  - <Design iteration action, owner, deadline>
  - <Follow-up test round trigger: segment gap, scenario gap, post-fix validation>
  - <Handoff: soldier-prototyping for iteration / soldier-launch-readiness for gate>
  - <GDPR/CCPA: data retention and deletion schedule for session recordings>

SOURCES (every external fact cited; nothing invented)
  - Jakob Nielsen, "Why You Only Need to Test with 5 Users," Nielsen Norman Group, 2000
    https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/
  - Jakob Nielsen, "10 Usability Heuristics for User Interface Design," Nielsen Norman Group,
    1994 — https://www.nngroup.com/articles/ten-usability-heuristics/
  - Steve Portigal, Interviewing Users: How to Uncover Compelling Insights, Rosenfeld Media,
    2013 — ISBN 978-1-933820-11-8
  - Cathleen Wharton, John Rieman, Clayton Lewis, Peter Polson, "The Cognitive Walkthrough
    Method: A Practitioner's Guide," in Usability Inspection Methods, Wiley, 1994
  - Google Search Quality Evaluator Guidelines (public edition) — https://guidelines.raterhub.com
    [assumption — verify current edition date]
  - Tobii Pro eye-tracking — https://www.tobii.com/products/eye-trackers (product documentation)
  - iMotions biometric research platform — https://imotions.com [assumption — verify version
    and AOI methodology documentation]
```
