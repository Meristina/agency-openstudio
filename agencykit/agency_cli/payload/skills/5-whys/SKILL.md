---
name: 5-whys
description: >-
  Run a 5 Whys (Les 5 Pourquoi) analysis: ask "why?" in a validated chain from a
  symptom toward its actionable root cause, with evidence at each step and
  branching when several causes exist. Use to verify a problem is real (not a
  symptom) or to drill to root cause. Sector-agnostic; each causal link must be
  evidence-backed and unproven links flagged; facts internet-sourced and cited.
---

# 5 Whys — Field Manual

The 5 Whys moves from *what is observed* to *why it happens*, one validated step
at a time. Five is a guideline, not a rule — stop when you reach an actionable
root cause, branch when causes diverge.

## When to use
- Light (Officer 1): test whether a stated problem is the real problem.
- Full (Officer 2): reach a validated root cause.

## Procedure

### Step 1 — State the symptom
Write the observed problem as a precise, factual statement (ideally with a figure
from the QQOQCP "Combien").

### Step 2 — Ask "why?" and VALIDATE each answer
For each level:
1. Ask "Why does the previous statement happen?"
2. Give the cause.
3. **Validate it:** is there evidence? Cite a web source if it's a factual claim.
   If it's an assumption, label it `[hypothèse]` and note how to verify it.
4. Only descend to the next "why" from a *validated* cause.

### Step 3 — Branch when needed
If a level has several plausible causes, create a branch per cause and continue
each. Do not force a single linear path.

### Step 4 — Stop at an actionable root cause
Stop when the cause is something you can actually act on. Reject dead-ends like
"human error" or "bad luck" — ask why those occurred (missing check, no training,
bad process).

### Step 5 — Verify the logic (read upward)
Read the chain back up using "therefore": each root cause should logically
produce the symptom. If it doesn't, the chain is broken — fix it.

## Output format

```
SYMPTÔME : <precise factual statement>

Pourquoi 1 ? → <cause>            [preuve: <url> | hypothèse: <how to verify>]
  Pourquoi 2 ? → <cause>          [preuve / hypothèse]
    Pourquoi 3 ? → <cause>        [preuve / hypothèse]
      (branche A) Pourquoi 4 ? → <cause>   [...]
      (branche B) Pourquoi 4 ? → <cause>   [...]
        Pourquoi 5 ? → <ROOT CAUSE actionnable>  [preuve / hypothèse]

CAUSE(S) RACINE(S) : <list, actionable>
VÉRIFICATION ASCENDANTE : <"root -> therefore -> symptom" check: OK / broken>
SOURCES : <numbered list>
HYPOTHÈSES À VÉRIFIER / QUESTIONS : <list>
```

## Guardrails
- Every link validated; unproven links labelled `[hypothèse]`, never asserted.
- Branch on multiple causes; don't tunnel into one convenient path.
- Root cause must be actionable; "human error" is a symptom, not a root cause.
- Causes only — no solutions. Mirror the user's language.
