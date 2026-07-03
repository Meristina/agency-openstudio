---
name: value-analysis
description: >-
  Run a Value Analysis / Value Engineering (analyse de la valeur, L. D. Miles) to
  maximize Value = Function / Cost — express a solution as the functions it must
  deliver (verb + noun), estimate each function's worth and cost, then improve the
  ratio by cutting or cheapening over-engineered functions and reinforcing
  under-served needs. Use on the CONVERGE side when budget matters and you want
  every unit of cost to buy needed function. Sector-agnostic; costs and worths are
  evidence-based (internet-sourced or flagged), never invented.
---

# Value Analysis — Field Manual

Value Analysis (Lawrence D. Miles) shifts the question from "what does it cost?" to
"what function does each cost buy, and is that function worth it?". The governing
equation:

```
Value = Function (worth of what it does) / Cost (of delivering it)
```

You raise value four ways: deliver the function cheaper, drop functions nobody
needs, add a missing needed function, or do more function for the same cost — never
by removing a primary function.

## When it fits
Use after a solution (or a short list) is on the table and cost-efficiency is a key
criterion. To *generate* options, use a diverger; to choose across *many weighted
criteria*, use the decision matrix. Value analysis zooms on one thing: function per
cost.

## Procedure

### Step 1 — Functional analysis (functions, not features)
List what the solution must **do** as functions in **verb + noun** form ("retain
heat", "guide the user", "reassure the buyer"). Classify each:
- **Use vs Esteem** — does it perform, or does it please/signal?
- **Primary vs Secondary** — is it the core reason the thing exists, or support?
Features are only the *means*; name the function each feature serves.

### Step 2 — Estimate worth and cost
For each function estimate:
- **Worth** — how much the need justifies spending on it (the value to the user).
- **Cost** — what delivering it currently costs (money, effort, time, complexity).
Use real figures where possible (web-sourced, cited). Where you must estimate
relatively, say so and use a consistent scale (e.g. 1–5).

### Step 3 — Compute the value ratio
Per function, compare worth vs cost. Flag two pathologies:
- **Over-engineered** (cost ≫ worth) — paying for function nobody needs at that level.
- **Under-served** (worth ≫ spend) — a valued need that's starved.

### Step 4 — Optimize
Recommend concrete moves: eliminate or downgrade low-value secondary functions,
find a cheaper means for a needed function, reallocate freed cost to an under-served
high-worth function. Keep every **primary** function intact. State the net value
gain.

## Output format

```
SOLUTION analysée : <one line>                  (pour Officier 3)
Contrainte budget : <budget/constraints>

Fonctions (verbe + nom) :
  F1 <verb+noun>   [usage|estime] [primaire|secondaire]
  F2 …

Table de valeur :
  Fonction | Valeur(worth) | Coût | Ratio | Diagnostic
  F1       | <…>           | <…>  | <…>   | sur-dimensionné / sous-servi / ok
  F2       | …             | …    | …     | …
  (chiffres : source/url, ou "à vérifier", ou "estimation relative 1–5")

Recommandations (↑ valeur) :
  - Couper/alléger : <…>
  - Moins cher : <…>
  - Renforcer (besoin sous-servi) : <…>
  GAIN DE VALEUR net attendu : <…>   (aucune fonction PRIMAIRE supprimée)

SOURCES (chiffres) : <numbered list>
À VÉRIFIER / estimations relatives : <list>
```

## Guardrails
- Functions (verb + noun) before features; classify use/esteem & primary/secondary.
- Optimize the ratio; never remove a primary function to save cost.
- Every figure is sourced or flagged; relative estimates labeled as such.
- Evaluation/optimization only — no inventing options, no final multi-criteria pick.
- Mirror the user's language.
