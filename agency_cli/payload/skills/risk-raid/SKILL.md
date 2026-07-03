---
name: risk-raid
description: >-
  Build a Risk register and RAID log (Risks, Assumptions, Issues, Dependencies) to
  anticipate what can break a launch — score each risk by probability × impact,
  assign a response (avoid/reduce/transfer/accept), an owner and a trigger, and log
  the surrounding assumptions, known issues, and external dependencies. Use on the
  SECURE side of rollout to harden the action plan. Sector-agnostic; risks are
  candidate future events (not facts), and any factual basis is internet-sourced or
  flagged.
---

# Risk & RAID — Field Manual

A plan lists what should happen; a RAID log lists what could go wrong and what
you're betting on. The risk register turns vague worry into managed exposure:
each threat gets a **likelihood**, an **impact**, a **response**, and an **owner**,
so attention goes where severity is highest instead of where anxiety is loudest.

## When it fits
Use once an action plan (and ideally a schedule) exists, to secure it before and
during launch. Internal task dependencies belong to PERT; tracking issues as they
unfold belongs to Officer 5. Here you **anticipate and assign**.

## RAID — the four registers
- **R — Risks:** uncertain *future* events that would hurt the plan. Phrased
  "if … then …". The scored core of this tool.
- **A — Assumptions:** things taken as true for the plan to work; if false, they
  become risks. Each needs a way to validate.
- **I — Issues:** problems already true *now* at launch time (not future). Each
  needs an action and owner.
- **D — Dependencies:** **external** reliances (vendor, other team, permit,
  upstream system). Internal task order → PERT, not here.

## Procedure

### Step 1 — Surface the risks
Brainstorm what could break the plan across angles: scope, schedule, resource,
technical, external/market, people, compliance. Phrase each "if <cause> then
<effect>".

### Step 2 — Score probability × impact
Pick one scale (e.g. 1–5 each). **Severity = probability × impact.** State the scale.
Back any score that leans on a fact (a base rate, a failure frequency, a vendor SLA)
with a web source; label pure judgment "estimate".

### Step 3 — Assign a response, an owner, a trigger
For each material risk choose a response — **avoid / reduce / transfer / accept** —
with a concrete mitigation action. Name the **owner** and the **trigger** (the
early-warning signal that activates the response). No owner ⇒ not managed.

### Step 4 — Log Assumptions, Issues, Dependencies
List the A/I/D. For each Assumption, how to check it; for each Issue, the action +
owner; for each Dependency, who/what and the fallback if it slips.

### Step 5 — Rank and recommend
Sort risks by severity; call out the top few to watch and any change they force on
the action plan or schedule.

## Output format

```
PLAN sécurisé : <one line>                       (pour Officier 4)
Échelle : probabilité 1–5 × impact 1–5 = sévérité

Registre des risques :
  id | Risque (« si…alors… ») | Prob | Impact | Sév | Réponse(éviter/réduire/transférer/accepter) | Responsable | Déclencheur
  R1 | <…>                    | …    | …      | …   | réduire: <mitigation>                         | <owner>     | <signal>
  R2 | …                      | …    | …      | …   | …                                            | …           | …
  (scores factuels : source/url, ou "à vérifier", ou "estimation")

Journal RAID :
  Hypothèses (A) : <hypothèse → comment la valider>
  Problèmes (I)  : <connu maintenant → action + owner>
  Dépendances (D, externes) : <qui/quoi → repli si ça glisse>

TOP RISQUES à surveiller : <ids> + impact sur le plan/planning
SOURCES : <numbered list>     À VÉRIFIER / estimations : <list>
```

## Guardrails
- Risks are candidate future events ("if…then…"), never asserted as facts.
- Severity = probability × impact on a stated scale; every material risk gets a
  response + owner + trigger.
- Dependencies here = external only (internal order → PERT); Issues = known now
  (ongoing tracking → Officer 5).
- Factual basis sourced or flagged; judgment scores labeled estimates.
- Mirror the user's language.
