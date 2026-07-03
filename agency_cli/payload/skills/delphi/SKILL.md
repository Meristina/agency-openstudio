---
name: delphi
description: >-
  Run a Delphi process (RAND) to converge expert judgment when hard data is scarce
  — an anonymous panel answers in iterative rounds, each round fed back the group's
  distribution and reasons (no attribution), revising until the answer stabilizes,
  surfacing reasoned dissent rather than forcing false consensus. Use on the
  CONVERGE side to estimate, rank, or forecast under uncertainty. Sector-agnostic;
  a panel's output is a labeled estimate (never empirical fact), simulated experts
  are flagged, and factual anchors are internet-sourced.
---

# Delphi — Field Manual

The Delphi method (Dalkey & Helmer, RAND) produces a *defensible group estimate*
where measurement fails. Its power comes from three design choices: **anonymity**
(so the loudest voice doesn't win), **iteration with controlled feedback** (so
people update on reasons, not status), and **statistical group response** (so the
output carries its own spread and dissent).

## When it fits
Use when a needed input can't be measured or sourced — feasibility odds, an effort
or adoption estimate, a ranking under deep uncertainty. If clean evidence exists,
score it with the decision matrix instead. If you still need to *generate* options,
use a diverger. Delphi **converges judgment**, it doesn't invent or measure.

## Panel — real or simulated (label it)
- **Preferred:** real domain experts with diverse vantage points.
- **If none available:** *simulate* a panel of N (≈3–6) personas, each with a
  **distinct, stated** vantage point (e.g. practitioner, skeptic, economist,
  end-user). State clearly that this is a simulated panel and the result is a
  **structured estimate, not empirical data**. Anchor personas with web-sourced
  context where possible.

## Procedure

### Step 1 — Frame the question
State the single question to converge (a number, a probability, a ranking) and why
Delphi (data scarce). Define the answer format and scale.

### Step 2 — Round 1 (independent, anonymous)
Each panelist answers **independently** with a short rationale. No cross-talk, no
attribution. Collect the raw answers.

### Step 3 — Feedback
Summarize the **anonymized** group response: central tendency + spread (e.g. median
and interquartile range, or the vote split) and the **key reasons** on each side —
without names.

### Step 4 — Subsequent rounds (revise on reasons)
Show each panelist the anonymized distribution and reasons; they may revise or hold
(if holding against the group, they give a reason). Re-summarize.

### Step 5 — Convergence test
Stop when the answer **stabilizes** (little movement between rounds) or after a set
max (e.g. 3 rounds). Do **not** pressure outliers into line — keep **reasoned
dissent**; a stable split is a legitimate result.

### Step 6 — Report with caveats
Give the converged estimate + its dispersion, the consensus level, the retained
dissent, and a confidence caveat. Source any factual anchors.

## Output format

```
QUESTION : <one line>   |   Pourquoi Delphes : <data scarce because…>   (pour Officier 3)
Panel : <réel | SIMULÉ — estimation structurée, pas un fait empirique>
  P1 <vantage point>   P2 <vantage point>   P3 …            (points de vue distincts)
Format de réponse / échelle : <…>

Tour 1 :  réponses → médiane <…>  écart <…>   ; raisons clés : <pour / contre>
Tour 2 :  révisions → médiane <…>  écart <…>   ; ce qui a bougé : <…>
Tour 3 :  … (jusqu'à stabilité ou max)

ESTIMATION CONVERGÉE : <valeur/intervalle>  (dispersion <…>)
CONSENSUS : <fort | modéré | partagé>
DISSENSUS RAISONNÉ retenu : <position minoritaire + sa raison>
MISE EN GARDE (confiance) : <…>
SOURCES (ancrages factuels) : <numbered list>   |   À VÉRIFIER : <list>
```

## Guardrails
- Anonymity + controlled feedback every round; no attribution, no dominance.
- Iterate to stability; keep reasoned dissent — never force false consensus.
- Simulated panels are labeled estimates, not empirical facts; factual anchors sourced.
- Converging judgment only — not generating options, not overriding real evidence.
- Mirror the user's language.
