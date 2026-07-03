---
name: check-sheet
description: >-
  Build a Check Sheet (feuille de relevés, one of the 7 basic quality tools) — a
  structured form designed BEFORE collection to record observations consistently:
  MECE categories with an operational definition each, stratified columns
  (time/shift/location), tally cells, and context metadata (who/when/where, sample
  size). Use on the MEASURE side of monitoring to gather real, comparable readings
  that feed the dashboard. Sector-agnostic; tallies are real observations
  (provided/sourced) or the form is delivered blank — never invented.
---

# Check Sheet — Field Manual

A check sheet is the simplest of the 7 quality tools and the one everything else
depends on: if the raw data isn't captured consistently, every chart built on it
lies. Its whole job is to make recording an observation **fast, uniform, and
countable** — so the numbers feeding the dashboard and Pareto are trustworthy.

## When it fits
Use when you need to collect data on the ground — the **current problem** (Officer 1
baseline) or the **solution's** results (Officer 5 monitoring). The dashboard says
*which* indicators matter; the check sheet is *how you capture* the readings. Pareto
then ranks the tallies. This tool **captures data**.

## Check-sheet types (pick the fit)
- **Tally / frequency:** count occurrences per category (defect types, reasons).
- **Defect-location:** marks on a diagram/map where issues occur.
- **Cause-by-factor:** tallies cross a factor (shift, machine, operator) to spot
  patterns.
- **Confirmation / checklist:** tick that each required step was done (process
  adherence).

## Procedure

### Step 1 — Define what's recorded + the categories
State the event being counted (tie it to the dashboard indicator it feeds). List the
categories — **MECE**, with an explicit **`Other`** to catch the unforeseen.

### Step 2 — Write an operational definition per category
One line per category, precise enough that two observers tally the same event
identically (e.g. "Late = delivered > 24h after due"). This is what makes the data
comparable.

### Step 3 — Design the form (stratify)
Rows = categories; columns = **strata** (time bucket, shift, location, batch) so
patterns show. Cells hold tallies. Add a **context header**: collector, dates/window,
location, sample size, unit of measure.

### Step 4 — Collect (or hand over blank)
If real readings are provided or web-sourceable, tally them in and total. If not,
deliver the **blank form + a short collection protocol** (who records, when, how) and
mark data as pending. **Never invent tallies.**

### Step 5 — Note data quality
Flag small samples, ambiguous categories, missing strata, or gaps. Honest data beats
a full-looking sheet.

## Output format

```
À MESURER : <event>  (indicateur servi : <dashboard KPI>)        (pour Officier 5)
Type : <tally | location | cause-by-factor | checklist>
Contexte : collecteur <…> · période <…> · lieu <…> · taille d'échantillon <…> · unité <…>

Définitions opérationnelles :
  Cat A = <one-line definition>
  Cat B = <…>
  Autre = <catch-all>

Feuille de relevés (catégories × strates) :
  Catégorie | Strate1 | Strate2 | Strate3 | Total
  Cat A     | ||| (3) | | (1)   |         | 4
  Cat B     | …       | …       | …       | …
  Autre     | …       | …       | …       | …
  TOTAL     |         |         |         | <n>
  (cellules remplies UNIQUEMENT à partir de relevés fournis/sourcés ; sinon FORMULAIRE VIERGE)

QUALITÉ DES DONNÉES : <sample size, ambiguïtés, strates manquantes>
DONNÉES EN ATTENTE / À VÉRIFIER : <flagged>     SOURCES : <numbered list>
```

## Guardrails
- Design the form and operational definitions before collecting; categories MECE + `Other`.
- Always record context (who/when/where/sample size) — data without it isn't comparable.
- Fill tallies only from real provided/sourced observations; else deliver blank + protocol.
- Never fabricate a count; flag every gap.
- Capturing only — no indicator definition (dashboard), no ranking (Pareto), no decision (officer).
- Mirror the user's language.
