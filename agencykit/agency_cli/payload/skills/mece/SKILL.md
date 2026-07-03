---
name: mece
description: >-
  Apply MECE (Mutually Exclusive, Collectively Exhaustive) to structure or audit a
  breakdown: ensure categories don't overlap (ME) and nothing is missing (CE),
  using a single organizing principle per level. Use as a quality gate on any
  breakdown (causes, options, segments) or to build a clean structure from scratch.
  Sector-agnostic; exhaustiveness claims must be evidenced, not assumed.
---

# MECE — Field Manual

MECE is the logic of a clean breakdown: every item fits exactly one category
(Mutually Exclusive) and every item fits some category (Collectively Exhaustive).
It is the backbone of clear analysis and a powerful audit on others' structures.

## Procedure

### Step 1 — State the whole + the organizing principle
What is being divided, and by which **single** principle at this level (by cause
family? by stage? by stakeholder? by time?). One principle per level — never mix.

### Step 2 — ME test (no overlap)
Check every pair of categories: can one item belong to two? If yes, that's an
overlap → redefine boundaries or merge/split. List each overlap found and the fix.

### Step 3 — CE test (no gap)
Could a real item belong to *none* of the categories? Probe the edges and corner
cases. Research the domain's standard categories (web) if useful to be sure. List
each gap and what you add. If you can't guarantee completeness, add "Autre / à
compléter" and mark coverage **uncertain** — never claim exhaustive on optimism.

### Step 4 — Verdict
State: MECE ✅, or not-yet-MECE with the residual issues.

## Output format

```
TOUT DÉCOMPOSÉ : <subject>   (Officier <n>)
PRINCIPE D'ORGANISATION (un seul) : <by …>

STRUCTURE (MECE) :
  1. <catégorie>
  2. <catégorie>
  3. <catégorie>
  (… one organizing principle only)

TEST ME (recouvrements) :
  - <overlap found> → <résolution>     (ou "aucun recouvrement")
TEST CE (trous) :
  - <gap found> → <ajouté>             (ou "aucun trou identifié")
  - couverture : certaine | incertaine (+ "Autre / à compléter")

VERDICT : MECE ✅  |  NON-MECE ⚠ (+ issues restantes)
SOURCES (couverture domaine) : <list, si utilisé>
```

## Guardrails
- Run BOTH tests explicitly; report findings, don't just assert "MECE".
- One organizing principle per level — catch mixed principles.
- Exhaustiveness needs evidence; flag uncertain coverage, never fake completeness.
- Structure only — no content generation, no decision. Mirror the user's language.
