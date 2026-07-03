---
name: pert
description: >-
  Run a PERT / CPM analysis to schedule a set of dependent tasks: build the
  dependency network, apply three-point estimates (optimistic, most likely,
  pessimistic → expected = (O+4M+P)/6), run the forward and backward pass for
  earliest/latest start-finish and slack, then extract the CRITICAL PATH and a
  realistic project duration. Use on the SCHEDULE side to find what truly drives the
  timeline. Sector-agnostic; durations are evidence-based (internet-sourced or
  flagged) and the arithmetic must be correct.
---

# PERT / CPM — Field Manual

PERT (with the Critical Path Method) answers two questions a task list can't:
**how long will it really take**, and **which tasks can't slip without slipping the
whole project**. It does so by treating the work as a *network* of dependencies and
computing timing through it. The method is only as good as its arithmetic and its
estimates — both must be honest.

## When it fits
Use after the action plan exists (tasks + dependencies + rough durations) and the
timeline matters. To define the tasks, use the action plan; to draw the calendar,
use Gantt. PERT computes the **schedule logic**.

## Procedure

### Step 1 — Build the network
List the tasks; for each, its immediate **predecessors**. This defines the
dependency graph (a task starts only when its predecessors finish, unless an
explicit lead/lag is given). Respect the dependencies you're handed; flag any that
look wrong rather than re-ordering silently.

### Step 2 — Three-point estimate per task
For each task estimate **O** (optimistic), **M** (most likely), **P**
(pessimistic), then:
```
te = (O + 4M + P) / 6          (expected duration)
σ  = (P − O) / 6     σ² = ((P − O)/6)²   (variance, optional)
```
Source the numbers where they lean on facts (lead times, benchmarks); label pure
judgment as "estimate".

### Step 3 — Forward pass (earliest times)
Left to right: `ES` = max(EF of predecessors); `EF = ES + te`. The largest EF is
the **project duration**.

### Step 4 — Backward pass (latest times)
Right to left from the project duration: `LF` = min(LS of successors);
`LS = LF − te`.

### Step 5 — Slack and the critical path
`slack = LS − ES` (= LF − EF) per task. The **critical path** is the chain of
**zero-slack** tasks from start to finish; its length = the project duration. Note
**near-critical** tasks (small slack) — they're the next-to-blow risks.

### Step 6 — Sanity check
Re-verify: every critical task has slack 0; the critical path is continuous start→
finish; the path length equals the largest EF. A wrong critical path is worse than
none — recompute if anything disagrees.

## Output format

```
PROJET : <one line>                              (pour Officier 4)

Réseau & estimations :
  Tâche | Préd. | O | M | P | te=(O+4M+P)/6 | [σ²]
  A     | —     | … | … | … | …             | …
  B     | A     | … | … | … | …             | …
  (durées : source/url, ou "estimation")

Passes (ES/EF/LS/LF/slack) :
  Tâche | ES | EF | LS | LF | Slack
  A     | …  | …  | …  | …  | 0
  …

CHEMIN CRITIQUE : A → B → … (slack 0)   |   DURÉE PROJET : <te totale> [± variance]
QUASI-CRITIQUES (faible marge) : <tâches + slack>
SOURCES : <numbered list>     À VÉRIFIER / estimations : <list>
```

## Guardrails
- te = (O+4M+P)/6; forward then backward pass; slack = LS − ES; critical path = zero-slack chain.
- Re-check the passes — the critical path must be continuous and equal the longest path.
- Respect given dependencies; flag suspicious ones, don't silently re-order.
- Durations sourced or labeled estimates; nothing invented as firm.
- Scheduling logic only — no task authoring (action plan), no calendar bars (Gantt).
- Mirror the user's language.
