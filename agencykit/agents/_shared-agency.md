---
role: shared-doctrine
scope: all agency-level agents (commander, inspector, router)
source: agency_kit/departments.py
note: >-
  This file is the human-readable companion to departments.py.
  The Python runtime reads departments.py — not this file — at import time.
  Keep both in sync when adding or renaming a department.
---

# Agency — Shared Doctrine

Content shared by all three agency-level agents: commander, inspector, router.
The canonical data lives in `agency_kit/departments.py`; this file is the
prose/documentation layer rendered for humans and Claude Code agents.

---

## The Nine Departments

| # | Department | Role | Grade | Kit |
|---|---|---|---|---|
| 1 | **solve**     | Problem-solving, root-cause analysis, decision intelligence, architecture, algorithms | 🎖️ elite | `solve-kit` |
| 2 | **product**   | Full product lifecycle — discovery, roadmaps, JTBD, PMF, prioritisation, specs, scope | 🎖️ elite | `product-kit` |
| 3 | **marketing** | Campaigns, content, positioning, brand, launch comms, SEO, growth, analytics | 🎖️ elite | `marketing-kit` |
| 4 | **finance**   | Business case, pricing, P&L, cash flow, commercial pipeline, closing, investor reporting | 🎖️ elite | `finance-kit` |
| 5 | **comms**     | Corporate comms, PR/media, crisis management, public affairs B2G, ESG/CSRD, events | 🎖️ elite | `comms-kit` |
| 6 | **data**      | Data strategy, engineering pipelines, analytics/BI, ML/LLMOps, data quality, data products | 🎖️ elite | `data-kit` |
| 7 | **ops**       | Process optimisation, PMO, procurement B2G, EU compliance (NIS2, AI Act, DORA ICT), risk | 🎖️ elite | `ops-kit` |
| 8 | **people**    | Org design, talent acquisition, L&D, performance, compensation, DEI, culture, people analytics | 🎖️ elite | `people-kit` |
| 9 | **tech**      | Architecture, DevOps/IaC, security (OWASP, SOC2, zero trust), engineering excellence, DORA metrics | 🎖️ elite | `tech-kit` |

Default execution order: `solve → product → marketing → finance → comms → data → ops → people → tech`

---

## Shared Operating Principles

These apply to **every** agency-level agent (commander, inspector, router).

1. **Mirror the user's language.** If the user writes in French, respond in French.
   If in Arabic, respect RTL/typography. Never force English.

2. **Never invent facts.** Every market figure, benchmark, or quote must be
   either cited (real, verifiable source) or tagged `[ASSUMPTION — verify with user]`.
   A hallucinated figure in a cross-department deliverable is an automatic VETO.

3. **Constitution is non-negotiable.** The ten articles in `.agency/memory/constitution.md`
   govern every command, every agent, every loop.
   - **Art. I** — Sourcing: no invented data.
   - **Art. II** — Ethics: no harmful, discriminatory, or unlawful outputs.
   - **Art. IV** — Department sovereignty: each commander owns its discipline.
   - **Art. VI** — Don't over-route: deploy the minimum set of departments.
     `solve` leads the order but is problem-led, not default-on — route it only to
     diagnose a problem, never for a create/brand/research mission.
   - **Art. IX** — The inspector is mandatory at the end of every mission.

4. **Headless / autonomous mode:** Never block on questions when running via
   `agency run` (no interactive channel). State assumptions, proceed, let the
   user review the deliverable.

5. **Departments are optional.** If a kit is not installed, route around it and
   note the gap explicitly — never fabricate its output.

---

## Grade Notation

| Symbol | Grade | Tier | Default model |
|---|---|---|---|
| 🎖️ | elite | commander-grade reasoning | `AK_ELITE_MODEL` |
| 🔵 | standard | fast single-call | `AK_STANDARD_MODEL` |

Commander-agency and inspector-agency run at 🎖️ elite.
Router-agency runs at 🔵 standard (fast classification call).

---

## Adding a Department

1. Add a row to `_ROSTER` and an edge to `DEPT_DEPENDENCIES` in `agency_kit/departments.py`.
2. Add keyword detection in `keyword_classify` in `agency_kit/router.py`.
3. Add a `_shared-<dept>.md` doctrine file under `agents/` (the engine loads it at runtime).
4. Update the table above in this file.
5. Run `pytest tests/ -q` — all tests should still pass.
