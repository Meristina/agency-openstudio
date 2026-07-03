---
name: scamper
description: >-
  Run a structured SCAMPER session to TRANSFORM an existing baseline (solution,
  product, process, or offer) into many variants by applying seven lenses —
  Substitute, Combine, Adapt, Modify/Magnify, Put to other use, Eliminate,
  Reverse/Rearrange. Use when you already have something concrete to improve or
  reinvent (directed divergence), not a blank page. Sector-agnostic; variants are
  candidates (not facts), and any factual claim must be internet-sourced or
  flagged to verify.
---

# SCAMPER — Field Manual

SCAMPER (Bob Eberle, from Osborn's checklists) forces *directed* divergence: take
one existing thing and interrogate it through seven transformation lenses. Each
lens cracks a different kind of fixation, so the variant spread is broader than
free brainstorming on the same baseline.

## Prerequisite — a baseline
SCAMPER acts on a concrete object: a current solution, product, service, process,
workflow, or offer. State it in one line before you start. No baseline → switch to
`brainstorming` instead.

## The seven lenses (trigger questions)
1. **S — Substitute:** What component, material, rule, person, or step can be
   swapped for something else? What if X were replaced by Y?
2. **C — Combine:** What can be merged — features, steps, audiences, products,
   partners? What pairs into a bundle?
3. **A — Adapt:** What works elsewhere (another industry, nature, a competitor)
   that we can borrow or tune to fit here?
4. **M — Modify / Magnify / Minify:** What can be made bigger, smaller, stronger,
   more frequent, or reshaped? Change scale, attribute, or form.
5. **P — Put to another use:** Who else could use this? What new context, market,
   or job could it serve as-is or slightly altered?
6. **E — Eliminate:** What can be removed, simplified, or stripped to the core?
   What happens if a step/feature/cost is deleted?
7. **R — Reverse / Rearrange:** What if the order, roles, or direction were
   flipped? Reverse the sequence, invert who does what, swap inputs and outputs.

## Procedure

### Step 1 — Anchor the baseline
Write the one-line baseline + the root causes / constraints it must respect.

### Step 2 — Run the seven lenses
For each lens, ask its trigger questions and produce 1–3 concrete variants. Aim for
at least one usable variant per lens; skip a lens only if genuinely N/A and say
why. You may web-search analogous cases (esp. for **Adapt**) as *stimulus* — label
borrowed facts with their source.

### Step 3 — Flag the bold ones
Mark the 2–3 most unconventional variants worth a serious second look.

## Output format

```
BASELINE : <the existing thing being transformed>  (pour Officier 3)
Contraintes : <root causes / constraints to respect>

Variants par lentille :
  S — Substituer
    1. <variant>          [candidat | si fait: source/url ou "à vérifier"]
  C — Combiner
    2. <variant>
  A — Adapter
    3. <variant>          [source si emprunté à un autre secteur]
  M — Modifier/Magnifier
    4. <variant>
  P — Autre usage
    5. <variant>
  E — Éliminer
    6. <variant>
  R — Réorganiser/Inverser
    7. <variant>
  (≥1 par lentille ; N/A justifié si une lentille est sautée)

À CREUSER (audacieuses) : <2–3 ids>
SOURCES (faits empruntés) : <numbered list>
À VÉRIFIER : <list>
```

## Guardrails
- Anchor on a stated baseline; tag every variant with its lens.
- Generation only — no ranking or rejection here.
- Variants are candidates, never asserted as facts; cite or flag any factual claim.
- Mirror the user's language.
