---
description: Final cross-department quality gate (Inspector FINAL mode — sources, coherence, ethics; veto)
argument-hint: "<mission dir, e.g. missions/001-...>"
---

# /agency.inspect — final gate (Inspector, FINAL mode, veto power)

**Constitution check:** `.agency/memory/constitution.md` (Art. I sourcing, Art. II
ethics, Art. IX inspector). `$MISSION` = `$ARGUMENTS`.

## Do

1. **Read** the full `$MISSION/dossier.md`: goal, route, all `dept_outputs`, synthesis,
   decisions, sources, open_to_verify.

2. **Confirm prerequisites**: every routed department has a `dept_outputs.<dept>` entry
   that is not `not_installed` and not blank. If a department ran but produced no entry,
   stop and flag it before inspecting — the Inspector audits what was produced, not
   what should have been.

3. **Delegate to the `inspector_agency` subagent** (Agent tool — runs elite grade; else
   adopt its role inline) in **FINAL mode** — the three-check cross-department pass:

   **Check 1 — SOURCES (Art. I)**
   Every factual claim in the combined output (metric, market size, benchmark, quote,
   figure) must cite a real, verifiable source. Spot-check the riskiest claims by web
   search. Any hallucinated or uncited fact → automatic **VETO** until cited or removed.
   Any fact shared across departments must be **identical and double-cited**: if product
   cites a $4 B market and marketing cites $7 B for the same segment → **flag as conflict**.

   **Check 2 — ETHICS & COMPLIANCE (Art. II)**
   Name the detected product/market/sector context. Flag dark patterns, privacy-law gaps
   (GDPR, CCPA, HIPAA, COPPA, loi 09-08/CNDP…), and any compliance risk **laundered
   across departments** (e.g. privacy-first product strategy paired with tracking-heavy
   marketing execution → contradiction → VETO).

   **Check 3 — CROSS-DEPARTMENT CONSISTENCY (Art. IX)**
   Read departments against each other:
   - **Same customer & value prop?** Product strategy ↔ marketing positioning — same
     target, same job-to-be-done, same core value proposition.
   - **Consistent metrics?** Marketing KPIs ladder up to the product North Star; no metric
     the product doesn't count as success.
   - **Spec ↔ delivery match?** Solve deliverables match the product spec; no scope drift.
   - **No cross-constraint contradiction.** A constraint declared in one department is
     binding on the others (timeline, pricing, privacy model, …).
   - **No orphaned handoffs.** Trace discover → position → deliver: every stage has an
     owner; every output is consumed downstream.

4. **Verdict**:
   - **PASS** — the agency ships as one coherent output.
   - **PASS WITH FIXES** — ships after the listed concrete reconciliations (each fix names
     the departments, the conflict, and a checkable resolution).
   - **VETO** — must not ship; list the blocking cross-department issues and exactly what
     clears each one.

5. **Log**: append the verdict + findings (with both-sides evidence for every
   cross-department finding) to `$MISSION/dossier.md` → Verdicts.

## On PASS-WITH-FIXES / VETO
Re-enter only the **responsible department(s)** to reconcile — do not restart
classification. Re-run `/agency.inspect` to verify the seam closed. Loop capped at
`MAX_ITERS = 3`; after the cap, deliver the best available result with **residual risk
explicitly stated**. The Inspector audits only — it never authors the fix. Mirror the
user's language.
