---
name: gantt
description: >-
  Build a Gantt chart that lays planned actions on a calendar timeline — each task a
  dated bar (start/end, duration), dependencies drawn, milestones marked, overlaps
  and the critical path made visible. Use on the SCHEDULE side to turn the action
  plan and PERT's critical path into a readable schedule. Sector-agnostic; bars
  respect the given dependencies and durations, and dates are internet-sourced or
  flagged, never invented.
---

# Gantt — Field Manual

A Gantt chart makes a schedule **legible**: time runs along the horizontal axis,
each task is a bar from its start to its end, dependencies and milestones are
marked, and overlaps show what runs in parallel. It doesn't compute timing — it
*renders* the timing the action plan and PERT already established, so a reader sees
the whole rollout at a glance.

## When it fits
Use once you have tasks with durations and a sequence (ideally PERT's critical
path). To define the tasks use the action plan; to compute the critical path use
PERT. Gantt **presents** the schedule.

## Procedure

### Step 1 — Set the timeline axis
Choose the unit (days/weeks/months) and the horizon (start → end date). Use the
project duration from PERT if available.

### Step 2 — Place each task as a bar
For each task draw a bar from its start to its end (start = earliest start honoring
predecessors; length = duration). A task can't begin before its predecessors finish
unless an explicit lead/lag is given. If durations/dependencies conflict, flag it
rather than silently shifting a bar.

### Step 3 — Draw dependencies and milestones
Link predecessor→successor (finish-to-start by default). Mark **milestones** as
dated points (◆) — kickoffs, gates, deliveries, the go-live.

### Step 4 — Highlight the critical path and owners
Highlight the critical-path bars so the eye lands on what can't slip. Put each
task's **owner** on its bar. Make overlaps visible; note where one owner is
double-booked at the same time.

### Step 5 — Back the dates
Dates/durations come from the action plan / PERT or are web-sourced; anything
assumed is flagged `à vérifier` / "estimate". No fabricated firm date.

## Output format

```
PROJET : <one line>   |   Axe : <days/weeks>, <start> → <end>     (pour Officier 4)

Gantt (▰ tâche, ▓ critique, ◆ jalon) :
  Tâche (owner)      | S1   S2   S3   S4   S5
  A  (resp.)         | ▓▓▓▓                        [critique]
  B  (resp.)         |      ▰▰▰▰▰
  C  (resp.)         |           ▰▰▰
  Jalon: Go-live     |                  ◆ (date)
  (dépendances : A→B→…   ; dates : source/url ou "à vérifier")

CHEMIN CRITIQUE (surligné) : A → … 
CHEVAUCHEMENTS / double-booking : <notes>
JALONS CLÉS : <list + dates>
SOURCES : <numbered list>     À VÉRIFIER / estimations : <list>
```

## Guardrails
- Bars respect dependencies and durations; conflicts are flagged, not silently shifted.
- Mark milestones; highlight the critical path; show owners and overlaps.
- Dates sourced or flagged; nothing fabricated as firm.
- Rendering only — no critical-path computation (PERT), no task authoring (action plan).
- Mirror the user's language.
