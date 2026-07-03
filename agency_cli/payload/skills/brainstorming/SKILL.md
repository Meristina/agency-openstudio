---
name: brainstorming
description: >-
  Run a structured Brainstorming (Osborn) session to generate many diverse ideas
  before any evaluation — problem framings, candidate causes, or candidate
  solutions depending on the phase. Use when you need breadth of options and want
  to avoid premature convergence. Sector-agnostic; ideas are candidates (not
  facts), and any factual claim must be internet-sourced or flagged to verify.
---

# Brainstorming — Field Manual

Brainstorming maximizes the *number and diversity* of ideas by separating
generation from judgment. Evaluation happens later, by someone else.

## The four rules (Osborn)
1. **Defer judgment** — no criticism during generation.
2. **Go for quantity** — more ideas → better odds of a great one.
3. **Welcome wild ideas** — bold/unconventional are encouraged; tame later.
4. **Build on ideas** — combine and improve others' ideas (1 + 1 = 3).

## Procedure

### Step 1 — Set the target
State precisely what you're generating and for whom:
"framings of <problem>" / "causes of <symptom>" / "solutions to <root cause>".

### Step 2 — Diverge (no filtering)
Generate widely (aim 15–30 items). Use prompts to break fixation:
- Reversal ("what if the opposite?"), analogy ("how does nature/another industry
  solve this?"), extremes ("if budget were infinite / zero"), combination
  ("merge idea 3 and 7").
- Optionally search the web for analogous cases/precedents as *stimulus* — but
  label borrowed facts with their source.

### Step 3 — Light clustering
Group the raw ideas into 3–6 themes. Do **not** rank or reject — just organize.

### Step 4 — Flag the bold ones
Mark the 2–3 most unconventional ideas worth a serious second look.

## Output format

```
CIBLE : <framings | causes | solutions> de <…>  (pour Officier <n>)

Idées (brutes, non jugées) :
  Thème A — <name>
    1. <idea>            [candidat | si fait: source/url ou "à vérifier"]
    2. <idea>
  Thème B — <name>
    3. <idea>
    …  (viser 15–30 au total)

À CREUSER (audacieuses) : <2–3 ids>
SOURCES (faits empruntés) : <numbered list>
À VÉRIFIER : <list>
```

## Guardrails
- Generation only — no evaluation, ranking, or rejection here.
- Quantity + diversity; include wild cards.
- Ideas are candidates, never asserted as facts; cite or flag any factual claim.
- Mirror the user's language.
