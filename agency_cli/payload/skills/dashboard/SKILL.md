---
name: dashboard
description: >-
  Build a Dashboard (tableau de bord de pilotage) that defines the vital-few
  indicators tracking whether a solution meets its Phase-4 success criteria — each
  KPI with a data source, target, RAG thresholds (green/amber/red), frequency, owner,
  and a leading/lagging tag, shown as at-a-glance status. Use on the MEASURE side of
  monitoring to decide what to track and display standing vs target. Sector-agnostic;
  status reflects real readings (internet-sourced or flagged), never invented.
---

# Dashboard — Field Manual

A dashboard answers one question fast: **is the solution working?** It does that by
turning each success criterion into a measurable indicator with a target and a
colour, so a glance separates on-track from off-track. Its discipline is restraint —
a few decision-driving indicators beat a wall of vanity metrics.

## When it fits
Two uses, same tool: **baseline** (Officer 1 — quantify the current problem state,
the "from what?") and **monitoring** (Officer 5 — track whether the solution meets
its success criteria). To collect the raw readings, use the check sheet; to rank the
deviations, use Pareto; to decide, that's the officer. This tool **defines and
displays** the indicators.

## Procedure

### Step 1 — Anchor on the reference
- **Baseline (O1):** anchor on the problem; derive 1–2 indicators that quantify its
  current state, with the reference = a sourced benchmark or the as-is value over a
  recent window.
- **Monitoring (O5):** anchor on the Phase-4 success criteria of the chosen solution;
  derive 1–2 indicators that show whether each is met.
Either way, don't invent the reference or the readings.

### Step 2 — Specify each indicator fully
- **Name** + **what it measures** (one line).
- **Data source / formula** — where the number comes from and how it's computed.
- **Target** — the value that means "met".
- **RAG thresholds** — green (on target) / amber (drifting) / red (off target).
- **Frequency** — how often it's read (daily/weekly/monthly).
- **Owner** — who watches it.

### Step 3 — Keep the vital few; mix leading & lagging
Aim for ~5–9 indicators. Tag each **leading** (predicts the outcome early, e.g.
activity/adoption) or **lagging** (confirms the outcome, e.g. result/defect rate).
Cut any metric that wouldn't change a decision.

### Step 4 — Show status at a glance
Fill current values from real readings and colour each RAG. Summarize: how many
green / amber / red. Flag any indicator with no data yet — don't colour it.

### Step 5 — Source the readings
Every current value is web-sourced and cited, or flagged `à vérifier` / "no data
yet". No green cell on an imagined number.

## Output format

```
SOLUTION suivie : <one line>                     (pour Officier 5)
Critères de réussite (Phase 4) : <list>

Tableau de bord (vital few) :
  Indicateur | Critère servi | Source/Formule | Cible | Seuils V/A/R | Fréquence | Responsable | Avance/Retard(L/L) | Statut actuel
  <KPI 1>    | <crit>        | <…>            | <…>   | <…>/<…>/<…>  | <…>       | <owner>     | leading            | 🟢 <val> [source]
  <KPI 2>    | <crit>        | <…>            | <…>   | …            | …         | <owner>     | lagging            | 🔴 <val> [à vérifier]
  …  (viser 5–9)

SYNTHÈSE RAG : 🟢 <n>  🟡 <n>  🔴 <n>
LEADING vs LAGGING : <split>   |   SANS DONNÉE encore : <flagged>
SOURCES (relevés actuels) : <numbered list>     À VÉRIFIER : <list>
```

## Guardrails
- Every indicator traces to a Phase-4 success criterion — no vanity metrics.
- Fully specify each: source, target, RAG thresholds, frequency, owner.
- Vital few (~5–9); mix leading and lagging.
- Status from real readings only — sourced or flagged; never colour an imagined number.
- Defining/displaying only — no raw data collection (check sheet), no steering decision (officer).
- Mirror the user's language.
