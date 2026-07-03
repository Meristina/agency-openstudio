---
name: action-plan
description: >-
  Build an Action Plan that turns a chosen solution into a concrete, owned, testable
  list of actions — each with an owner, the resources it needs, a deadline, a
  success criterion, a dependency note, and a status. The execution-side cousin of
  QQOQCP (who/what/when/how applied to actions). Use on the PLAN side of rollout,
  before sequencing (PERT) and scheduling (Gantt). Sector-agnostic; dates, costs and
  resources are realistic and internet-sourced or flagged, never invented.
---

# Action Plan — Field Manual

An Action Plan makes a solution **doable**: it answers, for every piece of work,
*what, who, with what, by when, and how we'll know it's done*. Its discipline is
that **no action is an orphan** — every line has an accountable owner and a
visible finish test, so nothing falls through and progress is checkable.

## When it fits
Use right after a solution is chosen, to define the work before timing it. To find
the critical path, hand the result to PERT; to draw the calendar, hand it to Gantt.
This tool **defines the work**; it doesn't sequence or schedule.

## Lane boundaries
- **Upstream (Officer 3's tree diagram):** that tool decomposed the solution into a
  means→ends *logic*. You turn that logic into owned, dated, testable *actions* —
  you don't re-derive the structure.
- **Downstream (Officer 5's monitoring):** you do **not** keep a live status/
  progress column. Set owner, date and success test; tracking happens in Phase 5.

## Procedure

### Step 1 — Decompose the solution into actions
Break the chosen solution into concrete, verb-led steps ("draft X", "configure Y",
"train Z"). Keep each atomic enough that one owner can carry it. Split anything too
big to own or verify.

### Step 2 — Fill the five fields for each action
- **Owner** — one accountable person (a role if no name yet). Never "the team".
- **Resources** — people, budget, tools, inputs the action needs.
- **Deadline** — a date or relative target ("D+5").
- **Success criterion** — the observable test that it's done ("PR merged",
  "sign-off received", "error rate < 2%").
- **Depends-on** — predecessor actions ("after #3"), so PERT can build the network.

### Step 3 — SMART check
Each action should be Specific, Measurable-enough, Assigned, Realistic, Time-bound.
Fix or flag any line that fails (e.g. no owner, vague finish, impossible date).

### Step 4 — Sort and spot the poles
Separate **quick wins** (do now, cheap) from **long poles** (start early, they gate
the end). Flag any action still missing an owner or date.

### Step 5 — Back the numbers
Any duration, cost, or capacity figure is web-sourced and cited, or flagged
`à vérifier` / "estimate". No invented dates or costs presented as firm.

## Output format

```
SOLUTION à déployer : <one line>                 (pour Officier 4)
Contraintes : <deadline / budget / resources>

Plan d'action :
  # | Action (verbe) | Responsable | Ressources | Échéance | Critère de réussite | Dépend de
  1 | <…>            | <owner>     | <…>        | <date>   | <observable test>   | —
  2 | <…>            | <owner>     | <…>        | <date>   | <…>                 | #1
  …
  (dates/coûts : source/url, ou "à vérifier", ou "estimation")
  (pas de colonne « statut » — le suivi d'exécution est l'affaire de l'Officier 5)

QUICK WINS : <#…>     LONG POLES (gating) : <#…>
ACTIONS INCOMPLÈTES (sans owner/date) : <flagged>
SOURCES : <numbered list>     À VÉRIFIER / estimations : <list>
```

## Guardrails
- No orphan actions: owner + resources + deadline + success criterion on every line.
- Atomic, verb-led, SMART-ish actions; name dependencies (don't resolve them here).
- Dates/costs sourced or flagged; nothing invented as firm.
- Defining only — no critical-path computation (PERT), no calendar (Gantt), no live
  status tracking (Officer 5).
- Mirror the user's language.
