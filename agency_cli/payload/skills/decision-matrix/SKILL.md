---
name: decision-matrix
description: >-
  Run a Decision Matrix (weighted-criteria scoring / Pugh-style multi-criteria
  decision analysis) to choose among compared options: define MECE weighted
  criteria, apply knock-outs first, score every option on a consistent scale,
  compute weighted totals, rank, then run a mandatory sensitivity check on whether
  the winner is robust. Use on the CONVERGE side to make the final, defensible pick
  with trade-offs visible. Sector-agnostic; every score is evidence-based
  (internet-sourced or flagged) — no option wins on invented data.
---

# Decision Matrix — Field Manual

A Decision Matrix makes a choice **transparent and defensible**: instead of "I
prefer B", you show *which criteria*, *weighted how*, scored each option *to what
total*, and *how robust* the winner is. The discipline is in the order — criteria
and weights are fixed before scoring, so the analysis can't be quietly tuned to
crown a favorite.

## When it fits
Use when you have ≥2 reasonably-scoped options and several criteria that matter at
different degrees. To *generate* options, use a diverger; to *clean* the set, use
MECE; to zoom on cost-efficiency only, use value analysis. This tool makes the
**pick**.

## Procedure

### Step 1 — Frame the decision and list the options
One line: "choose X among …". List the candidate options (ideally already cleaned by
MECE). 2–7 options keeps it legible.

### Step 2 — Set criteria (MECE) and split out knock-outs
List the criteria that actually drive the decision; keep them non-overlapping and
complete. Separate:
- **Knock-outs (must-haves):** pass/fail constraints (legal, budget ceiling,
  hard requirement). Any option failing one is **eliminated before scoring**.
- **Weighted criteria:** the rest, to be scored by degree.

### Step 3 — Weight the criteria (before scoring) and justify
Assign weights (e.g. summing to 100%, or 1–5 importance). **Write the weights and
the reason for each before you look at option scores** — this is the anti-bias
rule. Note who the weights reflect (the decision-owner's priorities).

### Step 4 — Apply knock-outs
Drop options failing any must-have; record which and why.

### Step 5 — Score on a consistent scale
Pick one scale (e.g. 1–5) and use it for every option × weighted criterion. For
each score, back it: cite a web source for any factual basis, or label it a
**judgment estimate**. Never invent a number to favor an option.

### Step 6 — Compute and rank
Weighted total = Σ(weight × score) per option. Rank them. Show the table.

### Step 7 — Sensitivity check (mandatory)
Test the winner's robustness: does it still win if the top weights shift ±, or if a
contested score moves one notch? Report:
- the **margin** over the runner-up (decisive or narrow),
- the **deciding criteria** (which weights/scores flip the result),
- a verdict: **robust** or **close call** (and what would change it).

### Step 8 — Recommend
State the winner + one-line rationale, the runner-up, what the winner **trades off**,
and any condition under which you'd revisit.

## Output format

```
DÉCISION : <choose … among …>                   (pour Officier 3)
Options : <A, B, C, …>   (éliminées d'office : <option — critère échoué>)

Critères éliminatoires (must-have) : <list> → options recalées : <…>

Critères pondérés (poids fixés AVANT scoring) :
  C1 <name>  poids <w1>  — justification
  C2 <name>  poids <w2>  — justification
  (Σ = 100% ou échelle 1–5)

Matrice (échelle <1–5>) :
  Critère (poids) | Option A | Option B | Option C
  C1 (w1)         |  s  src  |  s  est. |  s  src
  C2 (w2)         |  …       |  …       |  …
  TOTAL pondéré   |   TA     |   TB     |   TC

CLASSEMENT : 1. <gagnant> (TA)  2. <runner-up> (TB)  …
SENSIBILITÉ : marge = <…> ; critères décisifs = <…> ; verdict = robuste | serré (<ce qui changerait>)
RECOMMANDATION : <gagnant> — <raison 1 ligne> ; compromis = <…> ; runner-up = <…>

SOURCES (scores factuels) : <numbered list>
À VÉRIFIER / estimations de jugement : <list>
```

## Guardrails
- Criteria + weights fixed and justified **before** scoring (anti-bias).
- Knock-outs applied before weighted scoring.
- One consistent scale; every factual score sourced, judgment scores labeled.
- Sensitivity check is mandatory — never present a winner without testing its robustness.
- Choosing only — no inventing options.
- Mirror the user's language.
