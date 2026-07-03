---
name: qqoqcp
description: >-
  Run a QQOQCP analysis (Qui, Quoi, Où, Quand, Comment, Combien, Pourquoi —
  Who/What/Where/When/How/How-much/Why; a.k.a. 5W1H / 5W2H / Quintilian method)
  to fully and factually characterize a problem, situation, or brief before any
  cause or solution work. Use when you need to scope facts, write a complete
  situation brief, or make sure nothing about a problem is left undefined.
  Sector-agnostic; every fact must be internet-sourced and cited.
---

# QQOQCP — Field Manual

QQOQCP characterizes a situation along **seven dimensions** so the problem is
described completely and factually, with no blind spots. It answers *what is*,
not *why* or *what to do*.

## When to use
- First factual pass on any problem, before root-cause or solution work.
- Writing a situation brief, scoping a request, or completing an information gap.

## Procedure

### Step 1 — Restate the subject
Write the situation/problem in one neutral sentence (no causes, no judgment).

### Step 2 — Answer the seven dimensions
For each dimension, answer the lead question and the sub-questions. **Search the
web for every factual element and cite the source.** If a fact is unavailable,
write `À vérifier` — never invent.

| # | Dimension | Lead question | Sub-questions to cover |
|---|-----------|---------------|------------------------|
| 1 | **Qui / Who** | Who is involved/affected? | Actors, stakeholders, decision-makers, victims, responsible parties |
| 2 | **Quoi / What** | What is happening exactly? | Nature of the problem, symptoms, objects/processes concerned |
| 3 | **Où / Where** | Where does it occur? | Place, scope, channel, which sites/markets/systems |
| 4 | **Quand / When** | When does it occur? | Start, frequency, duration, trend, key dates |
| 5 | **Comment / How** | How does it manifest? | Mechanism, process, conditions, how it's observed/measured |
| 6 | **Combien / How much** | What is the magnitude? | Quantities, cost, %, volume, severity — figures with sources |
| 7 | **Pourquoi / Why** | Why is it a problem now? | Stakes, consequences, why it matters (NOT root cause — that's Phase 2) |

> Tip: "Combien / How much" is what turns QQOQCP into 5W2H — always quantify when
> data exists; it feeds the Pareto soldier later.

### Step 3 — Synthesize
Write a 2–3 sentence factual summary of the situation from the table.

### Step 4 — Flag gaps
List every `À vérifier` cell and open question for the officer.

## Output format

```
SUJET : <one-sentence neutral statement>

| Dimension      | Réponse                          | Source            |
|----------------|----------------------------------|-------------------|
| Qui            | …                                | <url / "À vérifier"> |
| Quoi           | …                                | …                 |
| Où             | …                                | …                 |
| Quand          | …                                | …                 |
| Comment        | …                                | …                 |
| Combien        | …                                | …                 |
| Pourquoi       | …                                | …                 |

SYNTHÈSE : <2–3 sentences>
SOURCES : <numbered list of cited URLs>
À VÉRIFIER / QUESTIONS OUVERTES : <list>
```

## Guardrails
- Facts only; no diagnosis (causes) and no recommendations (solutions).
- One source per factual claim; unsourced = `À vérifier`, never invented.
- Cover all 7 dimensions; flag missing data instead of hiding it.
- Mirror the user's language in the filled table and synthesis.
