---
name: tree-diagram
description: >-
  Build a Tree Diagram (diagramme en arbre / systematic diagram, one of the 7
  management tools) to break a chosen objective or solution into a logical
  means→ends tree — "by what means?" downward, "to what end / why?" upward —
  until the leaves are concrete and actionable, with each level kept MECE. Use on
  the CONVERGE side to detail HOW a selected solution decomposes, or to verify a
  goal is fully covered before action. Sector-agnostic; the structure is logical
  (not factual), and any factual leaf must be internet-sourced or flagged to
  verify.
---

# Tree Diagram — Field Manual

The Tree Diagram (a.k.a. systematic diagram / arbre des moyens) decomposes a single
goal into the means that achieve it, level by level, until each branch ends in
something concrete enough to do. It converts a chosen solution into a complete,
checkable skeleton — the bridge from "what we'll do" to "how it breaks down".

## When it fits
Use after an option is selected (or a goal is set) and you need its full
structure: sub-objectives, work packages, actionable steps. If you still need to
*generate* options, use a diverger; if you need to *choose* between options, use
the decision matrix. This tool **structures**, it does not score.

## The core logic — means↔ends, both ways
- **Downward ("by what means?"):** each node expands into the means that realize it.
- **Upward ("to what end / why?"):** each node must be a genuine means to its
  parent. If a child doesn't answer "why?" with its parent, the branch is wrong.
Run the upward test on every level — it is what keeps the tree honest.

## Procedure

### Step 1 — Set the root
State the objective or chosen solution to decompose, in one line. This is the trunk.

### Step 2 — Expand level by level
For each node ask "by what means is this achieved?" and list its children. Then ask
the children "to what end?" to confirm they point back at the parent. Keep going
branch by branch.

### Step 3 — Keep each level MECE
The children of a node should cover the parent **without gaps** and **without
overlap**. If a sibling set leaves a hole, add the missing branch; if two siblings
overlap, merge or re-split. Mark any residual gap/overlap you can't fully resolve.

### Step 4 — Stop at actionable leaves
Decompose each branch until its leaves are concrete enough to assign or act on
(a step, a deliverable, a decision). Don't leave a branch hanging on an abstraction.
Mark leaves as `[action]`.

### Step 5 — Source factual leaves
Any leaf that asserts a fact (a figure, a named constraint, a requirement) is
web-sourced and cited, or flagged `à vérifier`. The tree's *logic* is yours; its
*facts* must be backed.

## Output format

```
RACINE (objectif/solution) : <one line>          (pour Officier 3)

Arbre (moyens → fins) :
  1. <means level-1>
     1.1 <means level-2>
         1.1.1 <means level-3>            [action]
         1.1.2 <means level-3>            [action | si fait: source/url ou "à vérifier"]
     1.2 <means level-2>
         1.2.1 …                          [action]
  2. <means level-1>
     2.1 …
  (descend chaque branche jusqu'à des feuilles actionnables)

COMPLÉTUDE (MECE) : <gaps/overlaps found and how closed, or "ras">
SOURCES (feuilles factuelles) : <numbered list>
À VÉRIFIER : <list>
```

## Guardrails
- Means→ends must hold in both directions; run the upward "why?" test per level.
- MECE per level — flag any gap or overlap you can't close.
- Stop at actionable leaves, not abstractions.
- Structuring only — no scoring, no choosing the winner.
- Logical structure is yours; factual leaves are cited or flagged.
- Mirror the user's language.
