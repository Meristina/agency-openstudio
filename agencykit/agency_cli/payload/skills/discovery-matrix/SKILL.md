---
name: discovery-matrix
description: >-
  Run a Discovery Matrix (matrice de découverte, Abraham Moles) to map the
  solution space by crossing two dimensions in a double-entry grid — every
  intersection is a candidate option, and the empty cells reveal combinations
  not yet tried. A morphological technique: pick two relevant axes, build the
  grid, mark what exists, then mine the blanks. Use when the option space feels
  under-explored. Sector-agnostic; cells are candidates (not facts), and any
  factual claim must be internet-sourced or flagged to verify.
---

# Discovery Matrix — Field Manual

The Discovery Matrix (Abraham Moles) turns option-finding into reading a table.
Cross two dimensions; each cell is a possible combination. Known solutions occupy
some cells — the **empty cells are unexplored opportunities**, the inventions and
fixes nobody has assembled yet. It is a lightweight morphological analysis: the
structure does the divergence for you.

## When it fits
Use it when the problem has at least two parameters that can each take several
values, and you suspect obvious combinations are being overlooked. If the problem
has no natural two dimensions, prefer brainstorming or SCAMPER instead.

## Procedure

### Step 1 — Pick the two dimensions
Choose two axes that genuinely structure the problem. Common pairings:
- **need × technology/mechanism** (what to achieve × how)
- **audience/segment × channel**
- **function × component** · **user × context of use** · **resource × use**
State in one line why these two axes fit this case.

### Step 2 — List each axis cleanly
Enumerate the values along each axis. Keep the lists tidy — minimal overlap, no
glaring gap — so each cell means something. 4–8 values per axis is a good range
(bigger grids get noisy).

### Step 3 — Build and read the grid
Draw the rows × columns table. For each cell, mark:
- `■` an **existing** combination (known solution/product) — name it briefly;
- `·` an **empty / unexplored** cell.
You may web-search to verify whether a cell is genuinely empty — label borrowed
facts with their source.

### Step 4 — Mine the empty cells
For each promising blank, articulate the **candidate solution** that combination
implies ("axis-A value × axis-B value → we could…"). This is where new options
come from. Don't judge yet — generate.

### Step 5 — Flag the bold ones
Mark the 2–3 most promising unexplored cells worth a serious second look.

## Output format

```
PROBLÈME : <one line>                         (pour Officier 3)
Axe lignes  (X) : <name> = [v1, v2, v3, …]
Axe colonnes(Y) : <name> = [w1, w2, w3, …]
Pourquoi ces axes : <one line>

Grille (■ existe / · inexploré) :
            w1        w2        w3
   v1       ■ <name>  ·         ·
   v2       ·         ■ <name>  ·
   v3       ·         ·         ·

Cases inexplorées → solutions candidates :
   v1×w2 : <candidate>        [candidat | si fait: source/url ou "à vérifier"]
   v3×w1 : <candidate>
   v3×w3 : <candidate>
   …

À CREUSER (cases audacieuses) : <2–3 cells>
SOURCES (faits empruntés) : <numbered list>
À VÉRIFIER : <list>
```

## Guardrails
- Two genuinely structuring axes; keep each list clean (no big overlap/gap).
- The empty cells are the deliverable — concentrate divergence there.
- Generation only — no ranking or rejection here.
- Cells are candidates, never asserted as facts; cite or flag any factual claim.
- Mirror the user's language.
