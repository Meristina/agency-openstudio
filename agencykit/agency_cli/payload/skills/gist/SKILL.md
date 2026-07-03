---
name: gist
description: >-
  Guides product teams through the GIST planning framework (Goals, Ideas, Steps,
  Tasks) with four enrichment layers: Amazon Single-Threaded Leader audit at the
  Goals layer, McKinsey hypothesis-first kill conditions at the Ideas layer, Spotify
  Bets cadence mapping at the Steps layer, and Grove/Doerr 0.6–0.7 attainment
  calibration. Use when building or auditing a product plan at any horizon. Produces
  a four-layer GIST block with named STL per Goal, falsifiable idea hypotheses with
  pre-declared kill conditions, and quarterly bet assignments.
---

# Skill — GIST Planning (Goals · Ideas · Steps · Tasks)

GIST is a four-layer planning framework originated by Itamar Gilad (Google, 2016)
designed to replace the output-focused roadmap with an evidence-guided prioritization
stack. Each layer operates on a different time horizon: Goals are annual company-level
aspirations; Ideas are experiments or hypotheses that could achieve the Goals; Steps
are short delivery iterations (typically one to six weeks) that test an Idea; Tasks
are the day-to-day activities that compose a Step. The framework's structural advantage
over a feature roadmap is that the Ideas and Steps layers make uncertainty visible and
force teams to kill low-signal bets before they accumulate. Four enrichment layers
strengthen the original framework: Amazon's Single-Threaded Leader (STL) audit
prevents Goal diffusion by requiring a named owner who is 100% dedicated — not matrix
— before a Goal is treated as a real priority (Bryar & Carr, Working Backwards, 2021);
McKinsey hypothesis-first framing requires every Idea to declare a falsifiable kill
condition specifying metric, threshold, and time window before work begins; the Spotify
Bets Framework maps every Step to an explicit quarterly bet laddering toward a tribe
OKR (Spotify Engineering Culture, 2014); and the Grove/Doerr 0.6–0.7 attainment norm
applies to Step targets to prevent rational sandbagging.

> **Doctrine:** Cite Gilad for GIST layers and the evidence-guided principle. Cite
> Bryar & Carr (Working Backwards, 2021) for the STL requirement. Cite the Spotify
> Engineering Culture blog for the bets/tribe-OKR cadence. Cite Grove (1983) and
> Doerr (2018) for the attainment norm. Never cite "50% of features are never used"
> as a universal statistic, NPS as a sole growth driver, or story points as
> productivity signals. Never invent a quote, statistic, or benchmark — research
> every external fact and cite it.

## Procedure

1. **Establish context and horizon.** Identify the team level (company, tribe, squad),
   planning horizon (annual for Goals, quarterly for Steps and Bets), business stage
   (pre-PMF, scaling, mature), and domain. Clarify whether the request is to build a
   new GIST plan, audit an existing one, or diagnose a specific layer. This context
   determines which enrichment layers are most load-bearing.

2. **Define and audit Goals (STL gate).** Write or review the annual Goals: qualitative
   aspirations expressed in outcome language, measurable at period end. For each Goal,
   run the Amazon STL audit: name the Single-Threaded Leader — one person who is 100%
   dedicated to this initiative, not managing it as part of a matrix role. Goals without
   a named, confirmed STL are demoted to candidate status regardless of strategic
   importance score, because distributed ownership predictably degrades execution quality
   (Bryar & Carr, Working Backwards, 2021). Record the STL name and confirmation status.

3. **Formulate Ideas as falsifiable hypotheses with kill conditions.** For each Goal,
   enumerate candidate Ideas. Each Idea must be framed as a testable hypothesis, not a
   feature description: "We believe that [intervention] will produce [measurable outcome]
   for [customer segment], because [assumption]." Then pre-declare the kill condition:
   "If [metric] does not improve by [threshold %] within [time window in days], kill
   this Idea." This McKinsey hypothesis-first structure prevents idea accumulation
   without commitment to evidence-based termination. An Idea without a kill condition
   is not eligible to advance to Steps.

4. **Score and rank Ideas.** Apply an evidence-weighted scoring model to each Idea.
   Gilad recommends an ICE score (Impact, Confidence, Ease) as a starting point
   (Gilad, Evidence-Guided, 2023), but the score is a prompt for discussion, not a
   mechanical ranking. Weight Confidence heavily: an Idea with high theoretical impact
   but zero supporting evidence should be scored lower than a modest Idea with strong
   user research or prior experiment data. Surface assumptions; do not bury them in
   confidence padding.

5. **Map Steps to the Spotify Bets cadence.** For the top-ranked Ideas, decompose each
   into Steps — short delivery iterations of one to six weeks that produce a testable
   increment. Map every Step to a quarterly bet: an explicit outcome hypothesis that
   ladders toward a tribe-level OKR. The Spotify Bets Framework treats each Step as a
   commitment to learn, not to ship (Spotify Engineering Culture, 2014). State the bet
   in the form: "We bet that [Step output] will move [tribe OKR metric] from [baseline]
   toward [target] by [date]." A Step that cannot be expressed as a bet is an activity,
   not a prioritization decision.

6. **Calibrate Step targets against the 0.6–0.7 attainment norm.** Review the numeric
   targets embedded in each Step bet. Consistent 1.0 attainment is a diagnostic signal
   of excessive conservatism — a norm established by Andrew Grove at Intel (High Output
   Management, 1983) and propagated by John Doerr at Google (Measure What Matters, 2018).
   The appropriate ambition range for a stretch Step target is 0.6–0.7; recalibrate any
   target where the team is confident of full attainment under normal execution.

7. **Define Tasks and ownership.** For the active Step, enumerate the Tasks: specific,
   assignable work items with clear definitions of done. Each Task must have a single
   named owner. Flag any Task with two or more co-owners — split it or assign a
   decision-maker. Tasks are the execution layer; their quality depends on the clarity
   of the Step above them.

8. **Produce the output block, flag governance gap, and cite all sources.** Format
   the result using the output template below. Flag the GIST governance gap explicitly:
   GIST defines what to prioritize but not who has authority to finalize the decision.
   Recommend handoff to soldier-rapid-decision (Bain RAPID Framework, O3) for
   decision-authority assignment. End with a SOURCES section citing every external fact.

## Output format

```
GIST PLAN — <product / context>
Context detected: <B2B/B2C · sector · stage>
Planning horizon: <Annual Goals / Q[N] YYYY Steps & Bets>
Team level: <Company | Tribe | Squad>

GOALS  (annual · outcome language · STL required)
  [G1] <Qualitative outcome-oriented aspiration>
       STL: <Name, Role — [Confirmed 100% dedicated | DEMOTED: no STL named]>
  [G2] <Goal>
       STL: <...>

IDEAS  (hypothesis-first · kill condition mandatory)
  [I1 → G1] Hypothesis: "We believe [intervention] will [outcome] for [segment]"
             Kill condition: if [metric] does not improve by [threshold]% in [N] days → kill
             ICE score: Impact [1-10] · Confidence [1-10] · Ease [1-10] = [avg]
             Evidence: <prior data, user research, analogues>
  [I2 → G1] ...

STEPS  (quarterly bets · 1–6 week iterations)
  [S1 → I1] Bet: "We bet [Step output] moves [tribe OKR metric] from [X] toward [Y] by [date]"
             Duration: <N weeks>
             Attainment target: <0.6–0.7 calibrated; 1.0 = sandbagging signal>
             Tribe OKR ladder: <OKR label it supports>
  [S2 → I1] ...

TASKS  (active Step only · single named owner per Task)
  [T1 → S1] <Specific work item>   Owner: <Name>   Done-when: <definition>
  [T2 → S1] ...

GOVERNANCE GAP ALERT
  GIST defines what to prioritize; it does not assign decision authority (who can say
  yes/no and finalize). Recommend: invoke soldier-rapid-decision (Bain RAPID Framework,
  O3 · Prioritization) to assign a named Decide role per Goal before execution begins.

SO-WHAT / NEXT STEPS
  - <Goals with no STL → demote or assign before treating as active>
  - <Ideas missing kill conditions → block from Steps until declared>
  - <Steps without tribe OKR ladder → reclassify as activity, not a bet>
  - <Calibration action: any Step target where team is confident of 1.0 → recalibrate>

SOURCES (every external fact cited; nothing invented)
  - Gilad, Itamar. "GIST Planning." itamargilad.com, 2016.
    https://itamargilad.com/gist-framework/
  - Gilad, Itamar. Evidence-Guided: Creating High Impact Products. 2023.
  - Bryar, Colin & Carr, Bill. Working Backwards: Insights, Stories, and Secrets from
    Inside Amazon. St. Martin's Press, 2021. [STL / single-threaded ownership]
  - Spotify Engineering Culture. "Spotify's Agile Methodology." 2014.
    https://engineering.atspotify.com/2014/03/spotify-engineering-culture-part-1/
  - Grove, Andrew. High Output Management. Random House, 1983. [0.6–0.7 OKR norm]
  - Doerr, John. Measure What Matters. Portfolio/Penguin, 2018. [attainment calibration]
  - [Additional sources as needed — author, title, year, URL or [assumption — verify]]
```
