# Agency-Kit — Roadmap 360 B2B / B2G / B2C

## Exécution — v0.2.0 · engine-only (juin 2026) ✅

Le chemin **SDK / clé API a été supprimé**. Les missions tournent désormais via un
**moteur CLI local** (Claude Code / Codex / Gemini) en subprocess — **pas de clé API,
zéro dépendance runtime**. Chaque moteur utilise sa propre authentification + sa
recherche web live.

- `agency run "<goal>" --engine claude-code|codex|gemini` (défaut : `claude-code`).
- **Boucle inspecteur réelle (Art. IX)** : sur VETO / PASS-WITH-FIXES, re-synthèse avec
  les correctifs injectés, jusqu'à `MAX_ITERS = 3`, puis livraison avec `residual_risk`
  si pas de PASS. → *validé en vrai : PASS-WITH-FIXES → iter 2 → PASS.*
- **Routage solve-first** : solve est le diagnostic fondamental, routé uniquement pour
  un vrai problème (Art. VI) — jamais pour créer / brander / étudier un marché.
- `agency check` vérifie un moteur CLI sur le PATH ; `agency sync` est en mode preserve
  par défaut (`--strict` pour un rebuild complet avec les 9 repos kits).

> Les 9 kits ne sont plus des packages Python installables : leur **doctrine est
> bundlée dans le payload** (`agency init`) et jouée par le moteur. Le build-out des
> armées internes ci-dessous reste le même objectif produit — il est orthogonal au
> moteur d'exécution.

## Kits câblés dans agency-kit (9/9)

| # | Kit | Question métier | Statut |
|---|---|---|---|
| 1 | **product-kit** | Quoi construire ? | ✅ Done — 31 soldats |
| 2 | **marketing-kit** | Comment vendre & construire la marque ? | ✅ Done — 31 soldats |
| 3 | **solve-kit** | Comment résoudre un problème ? | ✅ Done — 25 soldats |
| 4 | **finance-kit** | Viable ? Comment signer et piloter le revenu ? | ✅ Done — 45 soldats |
| 5 | **comms-kit** | Comment communiquer et protéger la réputation ? | ⚙️ Wired — armée interne à compléter |
| 6 | **data-kit** | Comment collecter, structurer, analyser et valoriser les données ? | ⚙️ Wired — armée interne à compléter |
| 7 | **ops-kit** | Comment optimiser les opérations, les achats et la conformité ? | ⚙️ Wired — armée interne à compléter |
| 8 | **people-kit** | Qui recruter, comment organiser, comment faire grandir ? | ⚙️ Wired — armée interne à compléter |
| 9 | **tech-kit** | Comment construire, faire tourner et sécuriser ? | ⚙️ Wired — armée interne à compléter |

## Armées internes à compléter (5/9)

| # | Kit | Question métier | Officers | Soldats est. | Priorité |
|---|---|---|---|---|---|
| 5 | **comms-kit** | Comment communiquer, protéger la réputation et naviguer le secteur public ? | 6 | ~26 | 🔴 En cours |
| 6 | **tech-kit** | Comment construire, faire tourner et sécuriser ? | 6 | ~30 | ⬜ À venir |
| 7 | **ops-kit** | Comment optimiser les opérations, les achats et la conformité ? | 6 | ~28 | ⬜ À venir |
| 8 | **people-kit** | Qui recruter, comment organiser, comment faire grandir ? | 6 | ~25 | ⬜ À venir |
| 9 | **data-kit** | Comment collecter, structurer, analyser et valoriser les données ? | 6 | ~28 | ⬜ À venir |

---

## comms-kit — Détail (next)

**Question :** Comment communiquer en externe, gérer la réputation et naviguer le secteur public ?

| Officer | Domaine |
|---|---|
| O1 | Corporate Communications (narrative CEO, thought leadership, messaging) |
| O2 | PR & Media Relations (presse, journalistes, communiqués, tribunes) |
| O3 | Crisis Communications (cellule de crise, dark site, porte-parole) |
| O4 | Public Affairs / B2G (lobbying, AO, financement public, institutionnel) |
| O5 | RSE / ESG (stratégie CSRD/GRI, labels, engagements climatiques) |
| O6 | Événements & Expériences (roadshow, salons, conférences, influenceurs) |

---

## tech-kit — Détail

| Officer | Domaine |
|---|---|
| O1 | Architecture système (C4, ADR, DDD, monolith vs microservices) |
| O2 | DevOps & Platform (CI/CD, containers, IaC, observability, SRE) |
| O3 | Security Engineering (STRIDE, OWASP, SOC2, secrets management) |
| O4 | Engineering Excellence (TDD/BDD, code review, tech debt, API design) |
| O5 | Build vs Buy & Vendor (make-or-buy, OSS evaluation, cloud selection) |
| O6 | Engineering Metrics (DORA 5, SLO/SLI, incident management) |

---

## ops-kit — Détail

| Officer | Domaine |
|---|---|
| O1 | Process Optimization (Lean, Six Sigma DMAIC, BPM, VSM) |
| O2 | Project & Program Management (PMO, Agile, PRINCE2, portefeuille) |
| O3 | Procurement & Supply Chain (sourcing, SRM, logistique, contrats) |
| O4 | Legal & Compliance (droit contrats, RGPD, IP, réglementation) |
| O5 | Risk Management (cartographie, RCSA, continuité, audit interne) |
| O6 | Operational KPIs (dashboards ops, lean metrics, OKRs opérationnels) |

---

## people-kit — Détail

| Officer | Domaine |
|---|---|
| O1 | Org Design & Workforce Planning (team topologies, spans/ratios) |
| O2 | Talent Acquisition (JD, sourcing, interview design, offer) |
| O3 | Onboarding & L&D (90-day plan, skill matrix, career ladders) |
| O4 | Performance & Compensation (OKR cascading, calibration, equity/comp) |
| O5 | Culture & Engagement (valeurs, rituels, eNPS, DEI, safety) |
| O6 | People Analytics (headcount, attrition, time-to-hire, perf distribution) |

---

## data-kit — Détail

| Officer | Domaine |
|---|---|
| O1 | Data Strategy & Governance (data mesh vs lakehouse, GDPR/CCPA) |
| O2 | Data Engineering (ELT, dbt, Airflow, Spark, CDC) |
| O3 | Analytics & BI (dashboards, semantic layer, self-serve) |
| O4 | Machine Learning & AI (MLOps, feature store, model registry, LLMOps) |
| O5 | Data Quality & Observability (Great Expectations, lineage, SLAs) |
| O6 | Data Monetization & Products (data products, APIs, embeddings) |

---

## Vision architecture finale (9 kits)

```
                ┌──────────────────────────────────────────────────┐
                │                 AGENCY-KIT (méta)                │
                │  Moteur CLI : Route → Execute → Synth → Inspect ⟲│
                │      (claude-code / codex / gemini · web live)   │
                └───────────────────────┬──────────────────────────┘
                                        │
   ┌─────────┬──────────┬──────────┬────┴────┬──────────┬─────────┬─────────┐
   │         │          │          │         │          │         │         │
 solve    product   marketing   finance     tech      comms     ops
(diag.→   (quoi)    (vendre)   (viable)   (build)   (réputa)  (process)
 1er, VI)                                                  data    people
                                                        (données) (talent)
```

*Solve mène (diagnostic fondamental, Art. VI) ; l'inspecteur reboucle sur VETO (Art. IX).*
