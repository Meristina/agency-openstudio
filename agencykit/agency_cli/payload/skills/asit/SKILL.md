---
name: asit
description: >-
  Run an ASIT (Advanced Systematic Inventive Thinking) session to invent solution
  variants inside the "Closed World" — using only components already in or near the
  problem, no new external resources. Applies five tools (Unification,
  Multiplication, Division, Breaking Symmetry, Object Removal) under two principles
  (Closed World, Qualitative Change). Use when resources are tight or a clever
  reframe beats adding more. Sector-agnostic; variants are candidates (not facts),
  and any factual claim must be internet-sourced or flagged to verify.
---

# ASIT — Field Manual

ASIT (Roni Horowitz, a streamlined heir of TRIZ) generates inventive solutions by
*restricting* the search space instead of widening it. Constraint breeds
creativity: forbidding new resources forces non-obvious recombinations of what is
already there.

## The two principles

### 1. Closed World (CW)
The solution may use only objects/components already present **in or near** the
problem — no brand-new external resource. Before generating, list that inventory;
it is your entire toolbox.

### 2. Qualitative Change (QC)
Aim for solutions where the **harmful or problematic factor becomes the source of
the benefit** — not merely reduced. Litmus test: "the worse this factor gets, the
better the solution works." These are the strongest ASIT outcomes.

## The five tools (trigger questions)
1. **Unification (task unification):** Give an *existing* component an *additional*
   task. "What element already here could also do the job we'd add a new part for?"
2. **Multiplication:** Add a *copy* of an existing component, then change one
   attribute of the copy. "Duplicate X — but make the copy different how?"
3. **Division:** Cut an existing component and **rearrange the parts** in space or
   time. "Split X and redistribute it — separate in place, sequence, or order?"
4. **Breaking Symmetry:** Turn a symmetric/uniform situation into an asymmetric
   one. "Where we treat things equally/uniformly — what if one side differed (in
   time, space, condition, audience)?"
5. **Object Removal (subtraction):** Remove an existing component entirely and find
   how the remaining system still delivers — or delivers a new value. "Delete X —
   who/what covers its role now?"

## Procedure

### Step 1 — Define the Closed World
State the problem in one line, then list the components/resources already in or
near it (objects, actors, steps, signals, constraints). This is the only material
you may use.

### Step 2 — Run the five tools
For each tool, ask its trigger questions and produce 1–3 closed-world variants.
Reject (or flag out-of-scope) any idea that needs a new external resource. You may
web-search analogous precedents as *stimulus* — label borrowed facts with their
source.

### Step 3 — Hunt for Qualitative Change
Mark any variant where the problematic factor itself becomes the benefit — these
get priority for the officer's second look.

### Step 4 — Flag the bold ones
Mark the 2–3 most unconventional variants worth a serious second look.

## Output format

```
PROBLÈME : <one line>                        (pour Officier 3)
MONDE CLOS (composants disponibles) : <inventory list>
Contraintes : <constraints to respect>

Variants par outil (tous en monde clos) :
  Unification
    1. <variant>           [candidat | QC? | si fait: source/url ou "à vérifier"]
  Multiplication
    2. <variant>
  Division
    3. <variant>
  Rupture de symétrie
    4. <variant>
  Soustraction (retrait d'objet)
    5. <variant>
  (≥1 par outil ; N/A justifié si un outil est sauté)

CHANGEMENT QUALITATIF (le facteur nuisible devient le bénéfice) : <ids, le cas échéant>
À CREUSER (audacieuses) : <2–3 ids>
SOURCES (faits empruntés) : <numbered list>
À VÉRIFIER : <list>
```

## Guardrails
- Closed World is hard: no new external resource; out-of-scope ideas are flagged out.
- Generation only — no ranking or rejection here.
- Variants are candidates, never asserted as facts; cite or flag any factual claim.
- Mirror the user's language.
