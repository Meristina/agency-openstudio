---
name: user-interview
description: >-
  Runs a structured qualitative user interview using three interrogation techniques
  (context-setting probe, naïve probe, ask-the-opposite) and documents in-session
  observations via the IDEO POEMS framework. Use when a product team needs to surface
  tacit user rationale, mental models, or situational context that cannot be captured
  through surveys or analytics. Produces a structured POEMS brief plus a ranked
  so-what / next-steps block ready to feed an Opportunity-Solution Tree.
---

# Skill — Structured User Interview

A structured qualitative user interview is a one-on-one conversation designed to surface
the tacit knowledge, situational context, and unarticulated rationale that users cannot
easily self-report in surveys. The method draws on Steve Portigal's interrogation repertoire
(Interviewing Users, Rosenfeld Media, 2013) — context-setting probe, naïve probe, and
ask-the-opposite — and pairs them with IDEO's POEMS in-session documentation protocol
(People, Objects, Environments, Messages, Services) to produce structured observational
data alongside the spoken narrative. For product managers, the interview is not a validation
instrument; it is a discovery instrument. Its job is to widen the problem space, not close
it. Teresa Torres (Product Talk / Continuous Discovery Habits, 2021) sets the minimum viable
cadence at one interview per week per product team via automated recruitment pipelines —
a rhythm, not a quarterly sprint.

> **Doctrine:** Cite every external framework by author, source, and year. Do NOT cite
> "50% of features are never used" (untraceable origin, no peer-reviewed source). Do NOT
> treat a single interview as statistically representative; it is a signal, not a proof.
> Never invent a participant quote, a benchmark figure, or an industry standard.
> Unknown → say "unknown". Flag GDPR/CCPA consent obligations at recruitment and recording.

## Procedure

1. **Scope and recruit.** Define the target segment (role, context, frequency of the
   behaviour under study). Use an automated recruitment pipeline (e.g., Calendly +
   Respondent or UserInterviews.com) to maintain the Torres cadence of one session per week
   per product team. Obtain explicit informed consent for recording and data use; flag GDPR
   Art. 6 / CCPA opt-in requirements before any session is confirmed. Prepare a lightweight
   screener — three to five criteria maximum — to protect session quality without narrowing
   the sample so tightly that only power users qualify.

2. **Prepare the guide — context first.** Write the guide in three sections: warm-up
   (background, role, typical day), core topic (the behaviour or situation under study),
   and closing (anything the participant wants to add). Apply Portigal's context-setting
   probe structure: the first substantive question must anchor the participant in a specific
   recent situation — "Walk me through the last time you [behaviour]" — before any probing
   begins. Avoid asking about hypotheticals or preferences until after the situational
   context is fully established.

3. **Open the session with a POEMS frame.** At the start of each session, activate the IDEO
   POEMS documentation template (People, Objects, Environments, Messages, Services). Assign
   a note-taker the explicit job of capturing POEMS observations in real time, separately
   from the spoken transcript. These in-session observations capture environmental and
   artefactual details the participant may not volunteer verbally.

4. **Apply the naïve probe.** Throughout the session, deploy Portigal's naïve probe
   deliberately: respond to any described behaviour or workaround with "Why do you do it
   like that?" or "Help me understand why that's the way you do it." Feigned ignorance is
   the mechanism — the interviewer already has a hypothesis, but suppresses it so the
   participant must articulate the tacit rationale in their own words. This is the primary
   technique for surfacing mental models that would be invisible in a survey.

5. **Apply the ask-the-opposite.** When a participant expresses a clear preference or
   assumption ("I always do X because Y"), probe the implicit opposite: "Is there ever a
   situation where you'd do the reverse?" or "What would have to be true for you NOT to do
   X?" This Portigal technique challenges the embedded assumption in the participant's
   framing and surfaces the boundary conditions of their mental model.

6. **Complete the POEMS documentation block.** Before closing the session, review and
   complete the five POEMS dimensions based on the note-taker's real-time observations.
   Flag any dimension where observation was impossible (e.g., remote session where the
   physical environment was not visible) as "not observed — [reason]" rather than leaving
   it blank or inferring.

7. **Debrief immediately.** Within 30 minutes of the session, the interviewer and note-taker
   align on: the single most surprising finding, the single strongest signal of unmet need,
   and any POEMS dimension that contradicted the team's prior assumptions. Record these three
   items before memory degrades. Do not wait for a synthesis sprint.

8. **Synthesise into the output block.** Aggregate observations across sessions into the
   structured output below. In B2B contexts, follow the AIM Institute's New Product
   Blueprinting protocol: conduct separate sessions with at minimum four distinct stakeholder
   roles — economic buyer (ROI and risk), technical evaluator (integration and reliability),
   end user (ergonomics and efficiency), and purchasing (compliance and supplier risk) — each
   with a separate interview guide. Collapsing these roles into a single session produces
   data that conflates incommensurable success criteria.

## Output format

```
USER INTERVIEW — <product / context>
Context detected: <B2C / B2B · sector · discovery stage>
Sessions conducted: <N> | Roles covered: <list>

POEMS OBSERVATIONS
  People:       <who was present or referenced; roles, relationships, workarounds observed>
  Objects:      <tools, devices, documents, physical artefacts in use or described>
  Environments: <physical/digital spaces; constraints imposed by the environment>
  Messages:     <communications observed — notifications, labels, instructions, errors>
  Services:     <support structures, platforms, human services the participant relies on>

KEY SIGNALS
  Context-setting probe findings:
    - <Situation 1: the specific context the participant described>
    - <Situation 2>
  Naïve probe findings (tacit rationale surfaced):
    - <"I do X because Y" — the why that the survey would never have captured>
    - ...
  Ask-the-opposite findings (boundary conditions):
    - <The exception or reversal that redraws the mental model>
    - ...

UNMET NEEDS (ranked by recurrence across sessions)
  1. <Need — supporting quote or behavioural signal>
  2. <Need>
  3. <Need>

B2B ROLE DELTA (if applicable)
  Economic buyer:      <distinct success criteria / concerns observed>
  Technical evaluator: <distinct success criteria / concerns observed>
  End user:            <distinct success criteria / concerns observed>
  Purchasing:          <distinct success criteria / concerns observed>

SO-WHAT / NEXT STEPS
  - <Opportunity node candidate for the Opportunity-Solution Tree>
  - <Assumption to test before building>
  - <Follow-on session needed? If yes: who, why>
  - <Handoff: feed findings to O1 OST soldier or O3 opportunity-scoring soldier>

SOURCES (every external fact cited; nothing invented)
  - Steve Portigal, Interviewing Users, Rosenfeld Media, 2013 — context-setting probe,
    naïve probe, ask-the-opposite
  - IDEO, POEMS Framework — in-session observational documentation protocol
  - Teresa Torres, Continuous Discovery Habits, Product Talk / Rosenfeld Media, 2021 —
    one interview per week per product team, automated recruitment standard
  - AIM Institute, New Product Blueprinting — B2B VoC multi-role protocol (economic
    buyer, technical evaluator, end user, purchasing)
  - [Any additional citations for claims made in this output]
```
