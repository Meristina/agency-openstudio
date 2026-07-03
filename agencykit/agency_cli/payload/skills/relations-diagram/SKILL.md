---
name: relations-diagram
description: >-
  Build an Interrelationship Digraph (diagramme des relations): map which factors
  influence which among a set of causes, count in/out arrows per node, and identify
  the driving causes (high out-degree, highest leverage) versus outcomes (high
  in-degree). Use to find the highest-leverage root causes once candidates are
  known. Sector-agnostic; every link justified; factual links sourced or flagged.
---

# Interrelationship Digraph — Field Manual

When causes influence each other, a flat list hides which one is really driving
the system. This tool maps the influence network and uses arrow counts to separate
*drivers* (act here) from *outcomes* (symptoms).

## When to use
- After Ishikawa/Brainstorming have produced candidate causes.
- When causes seem tangled and you need the highest-leverage point.

## Procedure

### Step 1 — List the factors
Take 5–12 candidate causes/factors (label them A, B, C…). Too many → cluster first.

### Step 2 — Compare each pair for influence
For every pair (X, Y) ask: "Does X cause/influence Y, Y cause/influence X, or
neither?" Choose ONE dominant direction (or mark bidirectional + dominant side).
**Write a one-line reason for each arrow.** Cite a source if the link is factual;
else flag `[hypothèse]`.

### Step 3 — Count in/out degree
For each factor: out-degree = arrows leaving (it influences others); in-degree =
arrows arriving (others influence it).

### Step 4 — Classify
- **Driver / root cause:** highest out-degree (and relatively low in-degree) — the
  leverage point; fixing it cascades.
- **Outcome / symptom:** highest in-degree — a result, not a cause to attack
  directly.

### Step 5 — Rank by leverage
Order the drivers; these are what Phase 3 should target.

## Output format

```
FACTEURS : A=… B=… C=… (5–12)

LIENS (A → B = A influence B) :
  A → C   [raison ; source/url | hypothèse]
  B → C   [raison]
  D → A   [raison]
  …

DEGRÉS :
  | Facteur | Sortant (out) | Entrant (in) | Rôle           |
  |---------|---------------|--------------|----------------|
  | A       | 3             | 1            | MOTEUR         |
  | C       | 0             | 4            | RÉSULTAT/symptôme |
  | …       |               |              |                |

CAUSES MOTRICES (par levier) : <ranked list>
RÉSULTATS CLÉS : <list>
SOURCES : <numbered>   |   HYPOTHÈSES / QUESTIONS : <list>
```

## Guardrails
- Every arrow justified in one line; factual links cited or flagged.
- Pick a deliberate direction per pair; mark genuine bidirectionals + dominant side.
- Drivers/outcomes come from the degree counts, not intuition — show the numbers.
- Find drivers only — no new causes, no solutions. Mirror the user's language.
