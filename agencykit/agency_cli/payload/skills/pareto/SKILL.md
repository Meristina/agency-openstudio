---
name: pareto
description: >-
  Run a Pareto (20/80) analysis: rank items by a quantified effect, compute
  cumulative percentages, and identify the ~20% of causes driving ~80% of the
  effect (the vital few). Use to prioritize problems, focus effort, or target a
  control loop. Sector-agnostic; EVERY figure must be sourced or excluded — never
  invented.
---

# Pareto (20/80) — Field Manual

The Pareto principle: a small share of causes usually produces most of the effect.
Ranking by magnitude tells you where effort pays off most. The math is trivial;
the integrity is entirely in the **data**.

## When to use
- Prioritizing which problems/items to tackle first (Officer 1).
- Focusing a monitoring/control loop on the biggest drivers (Officer 5).

## Procedure

### Step 1 — Define metric, unit, scope
State exactly what you measure (count, €, hours, defects…), the unit, and the
data's scope + date. Name which officer you serve.

### Step 2 — Collect sourced values
For each item, get its value WITH a source (web-cited or user-provided). Any item
whose value can't be obtained is marked `à vérifier` and **excluded** from the
computation (listed separately) — never estimated to fill the chart.

### Step 3 — Sort and compute
Sort descending by value. Compute each item's % of total and the running
**cumulative %**.

### Step 4 — Find the 20/80 cut
Identify where cumulative % crosses ~80%. The items above the line are the
**vital few**. (The exact split varies — report the real numbers, don't force 20/80.)

### Step 5 — Read the priority
One line: which few items to focus on, and what share of the effect they cover.

## Output format

```
MÉTRIQUE : <what> · UNITÉ : <unit> · PÉRIMÈTRE/DATE : <scope, date>  (Officier <n>)

| Rang | Item | Valeur | % du total | % cumulé | Source |
|------|------|--------|-----------|----------|--------|
| 1 | … | … | …% | …% | <url / fourni> |
| 2 | … | … | …% | …% | … |
| … |   |   |    |    |    |

VITAL FEW (≈80% de l'effet) : <items au-dessus du seuil> — couvrent <X%> de l'effet
LECTURE PRIORITÉ : <one line>
EXCLUS / À VÉRIFIER : <items sans donnée sourçable>
```

## Guardrails
- No invented figures — sourced or excluded (`à vérifier`), never estimated to fill.
- Report the real split; don't force an exact 20/80.
- If data is too sparse, say so and give a qualitative ranking labeled as such.
- Prioritize only — no cause diagnosis, no fix decision. Mirror the user's language.
