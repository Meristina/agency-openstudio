---
description: Phase 0 — refine the goal, detect context, classify departments, optional direction check
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.frame — Phase 0 (Commander)

**Constitution check:** `.agency/memory/constitution.md` (Art. III mirror-language,
Art. VI routing doctrine, Art. VIII optional direction check).
`$MISSION` = `$ARGUMENTS`.

## Do

1. **Read in**: `$MISSION/dossier.md` (the goal + any prior facts or assumptions).

2. **Restate** the goal in one sentence and detect the context:
   sector, domain (solve / product / marketing or cross-domain), stage (early idea,
   launched, scaling, …), and any visible constraints.

3. **Ask 2–3 questions that change the plan** — each with a recommended default:
   - What outcome does a successful mission look like?
   - What constraints apply (budget, timeline, team, market, stack, …)?
   - What data / prior work is already available?
   Keep to 2–3; stop when the framing is sharp enough to classify confidently.
   **Wait for the user's answers** unless the user has already said "go" or "auto".

4. **Classify** via `router_agency` / `classify` tool: which departments, in what order.
   - State in one line *why* each routed department is in scope (Art. VI).
   - State in one line *why* each non-routed department is out.
   - Single-domain missions deploy one department. Multi-department routing is justified
     only when the goal genuinely spans those disciplines.

5. **Direction check (Art. VIII):** surface the proposed route (departments + order +
   rationale) and wait for **GO / REDIRECT / ADJUST**.
   - **GO** (or "auto") → record and continue.
   - **REDIRECT** → reclassify with the user's correction; re-surface.
   - **ADJUST** → update the framing assumptions, reclassify, re-surface.
   The direction check is the **only** sanctioned interruption (Art. VIII); skip it
   only when the user has explicitly requested autonomous execution.

6. **Write out** — update `$MISSION/dossier.md`:
   - Set `context` (sector + stage + constraints detected).
   - Set `route` (ordered department list + per-department rationale).
   - Append user answers / defaults as `[ASSUMPTION]`-tagged entries under Decisions.
   - Append the direction-check answer (GO / REDIRECT / ADJUST + note).

## Done when
`$MISSION/dossier.md` has: context, route with rationale, framing assumptions, and the
direction-check outcome. No separate artefact — framing lives in the Dossier.
Mirror the user's language.
