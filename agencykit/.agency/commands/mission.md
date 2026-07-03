---
description: Start & orchestrate a full Agency mission (classify → execute → synthesize → audit) from a goal
argument-hint: "<one-line mission goal>"
---

# /agency.mission — orchestrator (the full loop)

**Constitution check:** read `.agency/memory/constitution.md`. You may not skip
Articles I (sourcing), III (mirror-language), IV (dept sovereignty), VI (routing),
VII (cross-dept pipeline), IX (inspector).

## Input
`$ARGUMENTS` = the mission goal in one line.

## Steps

1. **Scaffold** the mission directory.
   - Pick the next available mission number; create `missions/<NNN-<slug>>/dossier.md`.
   - Seed the dossier: `goal` (= `$ARGUMENTS`), blank `route`, blank `dept_outputs`,
     blank `synthesis`, blank `verdicts`, blank `decisions`, blank `sources`,
     blank `open_to_verify`.
   - Use that path as `$MISSION` for everything below.

2. **Frame** (Phase 0) — run `/agency.frame $MISSION`.
   - Detect context, ask 2–3 plan-changing questions, **wait for answers** (unless the
     user said "go" or "auto").
   - Classify departments via `router_agency`. Record `route` + per-department rationale
     in the dossier. State explicitly why each non-routed department is out (Art. VI).
   - **Direction check (Art. VIII):** surface the proposed route and wait for
     **GO / REDIRECT / ADJUST**. On REDIRECT, reclassify; on GO or "auto", continue.

3. **Execute** (Phase 1) — run each routed department in order (Art. VII):
   - `/agency.product $MISSION`   — if `product` is in the route.
   - `/agency.marketing $MISSION` — if `marketing` is in the route.
   - `/agency.solve $MISSION`     — if `solve` is in the route.
   - `/agency.finance $MISSION`   — if `finance` is in the route.
   - `/agency.comms $MISSION`     — if `comms` is in the route.
   - `/agency.data $MISSION`      — if `data` is in the route.
   - `/agency.ops $MISSION`       — if `ops` is in the route.
   - `/agency.people $MISSION`    — if `people` is in the route.
   - `/agency.tech $MISSION`      — if `tech` is in the route.
   Each department receives the goal **plus all prior `dept_outputs`** as context.
   If a department is not installed, record the gap in the dossier and continue —
   never fabricate its output (Art. I, Art. IV).

4. **Synthesize** (Phase 2).
   - Combine all `dept_outputs` into one cross-department deliverable: reconcile overlaps,
     surface contradictions, produce one agency voice (Art. VII).
   - A synthesis is **not** a stack of reports — it reads as the agency speaking with one
     voice, each claim traceable to its source department.
   - Write the result into `$MISSION/dossier.md` → `synthesis`.

5. **Audit** (Phase 3) — run `/agency.inspect $MISSION` (FINAL mode, Art. IX).
   - On VETO / PASS-WITH-FIXES: re-enter only the responsible department(s), re-synthesize,
     then re-audit. Loop capped at `MAX_ITERS = 3`.
   - After the cap, deliver the best available result with **residual risk explicitly
     stated** — never loop silently.

## Done when
`$MISSION/dossier.md` holds: the goal, route, all `dept_outputs` (or gap notes), the
synthesis, and an inspector verdict of PASS (or the capped-iteration best-effort with
residual risk). Mirror the user's language throughout.
