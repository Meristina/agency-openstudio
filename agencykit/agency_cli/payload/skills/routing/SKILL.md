---
name: routing
description: >-
  Classify a mission goal into the minimal ordered set of departments to deploy
  (solve / product / marketing / finance / comms / data / ops / people / tech).
  Used by the agency commander in Phase 0 (Frame) to pick the route, and again
  whenever the commander must reclassify mid-mission after a REDIRECT or a
  direction-check correction. Not a problem-solving method — it is the
  classification logic the whole agency pipeline depends on.
---

# Routing — Field Manual

The routing decision is the first and most consequential call the agency makes. Deploy
the wrong department and the mission either fails or wastes budget. Deploy too many and
focus dissolves. This skill documents the classification logic so the commander can
apply it confidently — both on the first call via `router_agency` and when reclassifying
mid-mission after a REDIRECT.

## The nine departments

| Department | Domain | Canonical keywords |
|---|---|---|
| **product** | Discovery, strategy, prioritisation, JTBD, PMF, spec, roadmap, delivery, measurement | feature, roadmap, JTBD, PMF, spec, user story, scope, build, discovery |
| **marketing** | Research, positioning, content, campaigns, SEO, brand, launch comms, analytics | campaign, content, copy, positioning, messaging, SEO, brand, launch, go-to-market, ads |
| **solve** | Problem-solving, root-cause, decision intelligence, architecture, debugging, implementation | debug, fix, bug, root cause, architect, algorithm, implement, refactor, optimise, decide |
| **finance** | Business case, financial modelling, pricing, P&L, commercial pipeline, closing, reporting | finance, pricing, budget, ROI, P&L, cash flow, pipeline, deal, commercial, investor, business case |
| **comms** | Corporate communications, PR/media, crisis management, public affairs B2G, ESG/CSRD, events | PR, press release, crisis, communiqué, media relations, ESG, CSRD, public affairs, event, réputation |
| **data** | Data strategy, engineering, analytics/BI, ML/LLMOps, data quality, data products | data, pipeline, warehouse, analytics, BI, dashboard, ML, LLM, RAG, dbt, streaming, lakehouse |
| **ops** | Process optimisation, PMO, procurement B2G, EU compliance (NIS2, AI Act, DORA ICT), risk | ops, process, PMO, procurement, NIS2, AI Act, DORA, compliance, conformité, risque, lean, BCP |
| **people** | Org design, talent acquisition, L&D, performance, compensation, culture, people analytics | RH, HR, talent, recrutement, recruiting, org design, onboarding, L&D, compensation, culture, DEI |
| **tech** | Software architecture, DevOps/IaC, security, engineering excellence, build-vs-buy, DORA metrics | architecture, DevOps, infrastructure, cloud, security, Kubernetes, CI/CD, Terraform, SOC2, OWASP |

## Classification rules

### Rule 1 — Single domain first
If the goal points at one discipline, deploy one department. Most missions are
single-domain. Do not inflate the pipeline to look thorough — it wastes budget and
violates Art. VI.

- "Add an export-to-CSV button" → `["product"]`
- "Write a launch email sequence" → `["marketing"]`
- "Our checkout throws a 500 on Safari" → `["solve"]`
- "Define the North Star metric" → `["product"]`
- "Run an SEO audit" → `["marketing"]`
- "Choose between two architectures" → `["solve"]`

### Rule 2 — Multi-domain pipeline (ordered)
Deploy more than one department only when the goal **explicitly spans** those domains.
The order is the execution sequence — each department's output feeds the next.

Default pipeline order when multiple departments are needed:

1. **solve** first (when routed) — frames the problem, isolates the root cause, and sets
   the solution direction. Its diagnosis is the foundational context every downstream
   department builds against (or runs standalone if it is the only routed department).
   **Problem-led, not default-on:** routed only for a genuine problem (root cause, blocker,
   failing process, hard decision) — never for a create/brand/research mission.
2. **product** second — builds against solve's diagnosis: establishes what is being built,
   for whom, and why. Its strategy and outcome targets become ground truth for downstream.
3. **marketing** third — takes the product output as the positioning input. It does not
   re-derive the product strategy; it builds on it.
4. **finance** — evaluates economic viability, pricing, and commercial strategy. Takes
   solve, product, and marketing outputs as inputs; does not re-derive upstream strategy.
5. **comms** — corporate communications, PR/media, crisis, ESG. Runs after
   product/marketing when messaging and narrative are needed externally.
6. **data** — data strategy, pipelines, analytics/BI, ML/LLMOps. Runs when the mission
   involves building or scaling data infrastructure or intelligence.
7. **ops** — process optimisation, PMO, EU compliance (NIS2, AI Act), risk. Runs when
   the mission involves operational delivery, regulatory fit, or scaling ops.
8. **people** — org design, talent, L&D, performance, culture. Runs when the mission
   involves the organisation's human capital.
9. **tech** last (or standalone) — architecture, DevOps, security, engineering excellence.
   Runs when the mission involves technology decisions or delivery.

Common multi-domain patterns:
- "Launch a new product" → `["product", "marketing"]`
- "Build a feature and write the launch copy" → `["product", "marketing"]`
- "Debug a problem and explain it to stakeholders" → `["solve", "marketing"]`
- "Launch with a financial model" → `["product", "marketing", "finance"]`
- "Pitch investors" → `["product", "finance"]`
- "End-to-end engagement" / "full agency" → minimum set the goal needs (never all nine reflexively — Art. VI)

**Solve is problem-led, not default-on.** Solve leads the order and feeds every department,
but only as "foundational *when in scope*." Route it only to diagnose or resolve a problem —
never for greenfield creation, branding, or pure research, where there is nothing to diagnose:
- "Market study to launch an app" → `["product"]` (discovery — NOT solve)
- "Build our brand on a tight budget" → `["marketing"]` (NOT solve; budget is a marketing
  constraint, not finance)
- "End-to-end build of a new app" → `["product", "marketing", "finance"]` (NOT solve — creation, not repair)
- "Our app is losing users — diagnose and relaunch" → `["solve", "product", "marketing"]` (solve leads: a real problem)

### Rule 3 — Classify by dominant intent
When a goal mixes signals, pick the **dominant intent** — the discipline that owns the
primary outcome. Secondary concerns handled inside the primary department do not justify
adding another department to the route.

- "Pricing question with a bit of copy" → `["product"]` (pricing is product; copy is
  secondary, product can note it)
- "Campaign brief that needs a spec" → `["marketing"]` (the campaign is the deliverable;
  the spec is an input)
- "Architecture decision + a blog post about it" → `["solve", "marketing"]` (both are
  primary deliverables — justified multi-domain)

### Rule 4 — Never classify more than needed (Art. VI)
A pure positioning question is not `["product", "marketing", "solve"]`. A root-cause
investigation may need only `["solve"]`. Extra departments that are not needed:
- Waste the user's time and token budget.
- Dilute accountability (who owns the answer?).
- Violate Art. VI and the HARD RULE of the router doctrine.

## Output format

Every routing decision must record, in the dossier:

```
route     : ["department", ...]  ← ordered execution list
rationale : one line per department — why it is IN (or OUT)
```

Example:
```
route     : ["product", "marketing"]
rationale :
  product  → IN: goal requires scoping the feature and defining the pricing model
  marketing → IN: launch copy and channel plan are explicit deliverables
  solve    → OUT: no debugging, architecture, or decision-intelligence task present
  finance  → OUT: no financial modelling, pricing, or commercial pipeline task present
```

Rationale for **out** departments is as important as rationale for in — it makes the
classification auditable and revisable.

## Reclassification (REDIRECT / mid-mission)

The route is a decision, not a fixed rail. Reclassify when:
- The user sends a **REDIRECT** at the direction-check gate.
- A department's deliverable reveals that an upstream assumption was wrong.
- A new constraint surfaces that changes the dominant intent.

When reclassifying:
1. Read the updated dossier — include any `dept_outputs` already produced.
2. Run `router_agency` / `classify` again with the revised brief.
3. Do not discard completed `dept_outputs` from departments that remain in the new route.
4. Record the reclassification decision in the dossier → Decisions (with why).
5. **Do not restart from scratch** unless the mission goal itself has fundamentally
   changed; carry forward what was produced.

## Guardrails

- **Classify before you deploy.** No department runs until the route is set and recorded
  in the dossier (Art. VI).
- **The route is a recorded decision.** Always write `route` + `rationale` to the dossier
  before execution — the Inspector will check it.
- **Single-department missions are correct.** Not a shortfall; not a sign of insufficient
  analysis. The agency's quality bar is precision, not coverage.
- **REDIRECT ≠ restart.** A corrected route reuses all prior `dept_outputs` that still
  apply; only re-runs the departments affected by the change.
- Mirror the user's language (Art. III).
