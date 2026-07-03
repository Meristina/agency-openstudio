---
name: ishikawa
description: >-
  Build an Ishikawa / fishbone (cause-and-effect) diagram to organize all candidate
  causes of an effect across the 5M categories (Main-d'œuvre, Méthode, Matériel,
  Matière, Milieu; extensible to 6M/7M with Management, Monnaie). Use to map the
  full breadth of possible causes before drilling and ranking. Sector-agnostic;
  causes are hypotheses until evidenced; factual claims sourced or flagged.
---

# Ishikawa (Fishbone) — Field Manual

The fishbone organizes possible causes of one effect by *family*, so the team
sees the whole cause space and no category is forgotten. It maps breadth; it does
not prove, drill, or rank (other soldiers do that).

## The 5M categories (extensible)
| M | Catégorie | Couvre |
|---|-----------|--------|
| 1 | **Main-d'œuvre** (People) | skills, training, workload, communication, motivation |
| 2 | **Méthode** (Process) | procedures, workflow, rules, standards |
| 3 | **Matériel** (Machine/Equipment) | tools, systems, software, infrastructure |
| 4 | **Matière** (Materials/Inputs) | raw inputs, data, supplies, quality of inputs |
| 5 | **Milieu** (Environment) | physical/market/cultural/regulatory context |
| (6) | **Management** | decisions, priorities, governance |
| (7) | **Monnaie** (Money) | budget, cost constraints, pricing |

## Procedure

### Step 1 — State the effect
Write the problem/effect at the "fish head" — one precise statement (ideally with
the QQOQCP figure).

### Step 2 — Populate each M
For every category, ask "what here could cause the effect?" List candidate causes.
Add sub-causes (a cause behind a cause) as smaller bones. Use 6M/7M if Management
or Money are relevant. If a category yields nothing, write "RAS / aucune cause
identifiée" — never leave it silently blank.

### Step 3 — Label evidence
Mark each cause `[hypothèse]` or attach a source. Search the web for facts that
support/refute a candidate where it matters.

### Step 4 — Spot the promising branches
Flag the 3–5 candidate causes most worth drilling (hand to the 5 Whys soldier) or
ranking (hand to the relations-diagram soldier).

## Output format

```
EFFET (tête) : <precise statement>

🐟 Main-d'œuvre : - cause … [hypothèse | source]   - sous-cause …
🐟 Méthode      : - cause …                         - sous-cause …
🐟 Matériel     : - cause …
🐟 Matière      : - cause …
🐟 Milieu       : - cause …
🐟 (Management) : - cause …   (si pertinent)
🐟 (Monnaie)    : - cause …   (si pertinent)

CATÉGORIES VIDES : <list, explicit>
BRANCHES À CREUSER : <3–5 candidates for 5 Whys / relations diagram>
SOURCES : <numbered list>   |   HYPOTHÈSES : <list>
```

## Guardrails
- Check all 5M; note empty categories explicitly, never silently.
- Causes are hypotheses until evidenced; cite or flag — never assert as fact.
- Breadth only — no drilling to root (5 Whys), no ranking (relations), no solutions.
- Mirror the user's language.
