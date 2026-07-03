---
name: catwoe
description: >-
  Run a CATWOE analysis (Customers, Actors, Transformation, Weltanschauung,
  Owner, Environment) from Soft Systems Methodology to surface every stakeholder
  and the worldview that frames a situation as a problem. Use when a problem
  involves several parties, conflicting interests, unclear ownership, or when you
  need a shared "root definition" before analysis. Sector-agnostic; facts must be
  internet-sourced and cited.
---

# CATWOE — Field Manual

CATWOE exposes the human system around a problem: who it serves, who acts, what
change is at stake, the worldview that justifies it, who can stop it, and the
constraints around it. It frames the problem; it does not solve it.

## When to use
- Multi-stakeholder problems, conflicting interests, unclear sponsorship.
- Before writing a problem statement, to ensure all perspectives are accounted for.

## Procedure

### Step 1 — State the situation
One neutral sentence describing the situation under study.

### Step 2 — Fill the six elements
Research real actors/context on the web and cite sources. Mark unknowns
`À vérifier`.

| Letter | Element | Guiding question |
|--------|---------|------------------|
| **C** | Customers | Who are the beneficiaries or victims of the system/outcome? |
| **A** | Actors | Who carries out the activities (operators, staff, executors)? |
| **T** | Transformation | What input is converted into what output? (the core change) |
| **W** | Weltanschauung | What worldview/belief makes this transformation meaningful? |
| **O** | Owner | Who can start, stop, or veto the system? (authority/sponsor) |
| **E** | Environment | What external constraints apply? (rules, market, tech, culture, budget) |

### Step 3 — Write the root definition
One sentence of the form:
> *A system to **[T: transform X into Y]**, operated by **[A]**, serving **[C]**,
> owned by **[O]**, under constraints **[E]**, because **[W]**.*

### Step 4 — Flag conflicts & gaps
List any conflicting worldviews (W) between stakeholders, and all `À vérifier`
items.

## Output format

```
SITUATION : <one neutral sentence>

| Élément          | Réponse                         | Source            |
|------------------|---------------------------------|-------------------|
| C — Customers    | …                               | <url / "À vérifier"> |
| A — Actors       | …                               | …                 |
| T — Transformation | … (X -> Y)                    | …                 |
| W — Weltanschauung | …                             | …                 |
| O — Owner        | …                               | …                 |
| E — Environment  | …                               | …                 |

ROOT DEFINITION : <one sentence>
CONFLITS DE VISION : <list, if any>
SOURCES : <numbered list>
À VÉRIFIER / QUESTIONS OUVERTES : <list>
```

## Guardrails
- Framing only: no root-cause diagnosis, no solutions.
- Real, sourced stakeholders/context; unknowns = `À vérifier`, never invented.
- Always surface conflicting worldviews — that's where the real problem hides.
- Mirror the user's language in the table and root definition.
