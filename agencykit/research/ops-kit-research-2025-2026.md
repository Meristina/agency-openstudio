# ops-kit — Recherche terrain 2025-2026
*Deep research adversarialement vérifié — 116 agents, claims EU réglementaires 3-0*

---

## 3 Dynamiques structurantes (2025-2026)

### 1. Stack réglementaire EU dense et délibérément chevauchante
Cinq directives/règlements créent simultanément des obligations sur legal, compliance ET technique :

| Réglementation | Scope | Entrée en vigueur | Sanctions |
|---|---|---|---|
| **NIS2** (Directive 2022/2555) | >160 000 entités (énergie, transport, santé, finance, digital) | Oct 2024 (EC a ouvert des procédures contre 23 États membres pour non-transposition) | Essential : €10M ou 2% CA mondial ; Important : €7M ou 1,4% CA |
| **DORA** (Règlement 2022/2554) | ~22 000 entités financières + CTPPs | 17 janvier 2025 (compliance) | Secteur financier ; Lead Overseer ESAs |
| **AI Act** | Systèmes IA par niveau de risque | Art. 5 (pratiques interdites) : 2 février 2025 | |
| **Cyber Resilience Act** | Produits hardware/software avec éléments digitaux | 2027 (progressif) | |
| **Critical Entities Resilience (CER)** | Entités critiques (énergie, eau, transport) | | |

**Faits vérifiés (3-0 adversarial) :**
- **NIS2** : 160 000+ entités confirmées par ENISA ; transposition octobre 2024 ; 23 États membres en infraction (EC, nov 2024) ; pénalités Article 34 text législatif direct
- **DORA** :
  - Entrée en vigueur 16 jan 2023 ; compliance requise 17 jan 2025
  - TLPT (Threat-Led Penetration Testing) **tous les 3 ans minimum** sur systèmes de production
  - Lead Overseer model (EBA + EIOPA + ESMA) pour CTPPs critiques — **19 CTPPs désignés nov 2025** (dont AWS, Google Cloud, Microsoft)
  - DORA = *lex specialis* sur NIS2 pour le secteur financier
- **AI Act Art. 5** : pratiques interdites (manipulation comportementale, exploitation vulnérabilités, identification biométrique temps réel, social scoring) en application depuis 2 février 2025
- **EC Digital Omnibus** : initiative de simplification lancée nov 2025 — reconnaissance officielle de la convergence réglementaire et de la surcharge compliance

### 2. Marchés publics B2G — sous-performance structurelle + réforme 2026
*(3-0 pour les stats, 2-1 pour la réforme)*
- **55%** des contrats publics attribués sur **critère prix le plus bas uniquement**
- Seulement **11%** utilisent les achats coopératifs/groupés
- **Baisses du nombre moyen d'offres par appel d'offres** (tendance confirmée EC)
- Source : EC Staff Working Document SWD(2025)332 — évaluation oct 2025 des directives 2014/23/EU, 2014/24/EU, 2014/25/EU

**Réforme 2026 confirmée :**
- **Public Procurement Act** prévu Q2 2026 (Article 114 TFEU)
- Critères entrant dans les AO : durabilité, résilience, critères sociaux
- **Provisions "Made in Europe"** pour secteurs stratégiques
- Source : EC Work Programme 2026 + European Parliament Legislative Train

### 3. IA dans les opérations — acquisitions process intelligence par les grands éditeurs
*(claims Celonis/UiPath rate-limited — tendance confirmée directionnellement)*
- **SAP** (Signavio), **Microsoft**, **ServiceNow** acquièrent des sociétés de process mining pour alimenter leurs agents IA en données de processus réels
- **Celonis** : Orchestration Engine → convergence process mining + agents IA (non vérifié adversarialement faute de temps)
- **Convergence émergente** : process intelligence (données de flux réels) + agentic AI (exécution autonome) = nouveau standard ops

---

## Landscape des référentiels méthodes

### Lean / Six Sigma / BPM
- **Lean** : Toyota Production System → élimination gaspillages (Muda/Muri/Mura)
- **Six Sigma DMAIC** : Define → Measure → Analyze → Improve → Control
- **BPM (Business Process Management)** : notation BPMN 2.0 standard
- **VSM (Value Stream Mapping)** : cartographie flux de valeur end-to-end

### Gestion de projet / PMO
- **PRINCE2** : standard B2G UK/Europe (prince2.com)
- **PMP / PMBoK** : standard global Project Management Institute
- **SAFe** : Scaled Agile Framework pour enterprise Agile
- **ISO 21500** : guidance on project management

### Procurement / Supply Chain
- **SRM (Supplier Relationship Management)** : segmentation, évaluation, développement fournisseurs
- **CIPS** (Chartered Institute of Procurement & Supply) : référentiel procurement
- **ISO 28000** : supply chain security management

### Risk Management
- **ISO 31000** : principes et lignes directrices risk management
- **COSO ERM** : enterprise risk management framework
- **RCSA** : Risk Control Self-Assessment (standard bancaire/financier)
- **ISO 22301** : business continuity management (PCA/PRA)

---

## Implications pour le ops-kit

### Officers validés par la recherche

| Officer | Validation terrain |
|---|---|
| **O1 Process Optimization** | Lean/Six Sigma classiques + IA process mining (SAP/Celonis convergence) |
| **O2 Project & Program Management** | PMO B2G (PRINCE2) + enterprise Agile (SAFe) + portfolio |
| **O3 Procurement & Supply Chain B2G** | 55% prix-seul → réforme 2026 ; "Made in Europe" ; marchés publics durabilité |
| **O4 Legal & Compliance EU** | NIS2 (3-0) + DORA (3-0) + AI Act Art.5 (3-0) + convergence réglementaire |
| **O5 Risk & Business Continuity** | RCSA + ISO 22301 + TLPT DORA (tous les 3 ans) |
| **O6 Operational Intelligence** | Process mining + IA agents ; Celonis/SAP convergence ; KPIs opérationnels |

### Soldats prioritaires

**O1 — Process Optimization**
- `soldier_vsm_lean` 🎖️ (Value Stream Mapping + élimination gaspillages)
- `soldier_dmaic_six_sigma` (DMAIC : Define → Measure → Analyze → Improve → Control)
- `soldier_bpmn_modeler` (cartographie processus BPMN 2.0)
- `soldier_process_mining` 🎖️ (Celonis/SAP Signavio ; process discovery depuis logs)
- `soldier_kaizen_facilitator` (amélioration continue ; ateliers Kaizen)

**O2 — Project & Program Management**
- `soldier_pmo_designer` 🎖️ (setup PMO : gouvernance, reporting, portfolio)
- `soldier_prince2_planner` (PRINCE2 pour B2G : stages, business case, tolerances)
- `soldier_safe_coach` (SAFe PI Planning, ARTs, team topologies agile)
- `soldier_gantt_critical_path` (PERT/CPM, chemin critique, gestion dépendances)
- `soldier_portfolio_governance` (priorisation portefeuille projets, RAG status)

**O3 — Procurement & Supply Chain**
- `soldier_ao_strategy` 🎖️ (réponse AO B2G post-réforme 2026 ; durabilité + résilience)
- `soldier_supplier_qualification` (SRM : segmentation Kraljic, évaluation, audit)
- `soldier_contract_writer` 🎖️ (rédaction contrats fournisseurs, SLAs, pénalités)
- `soldier_supply_chain_risk` (cartographie risques fournisseurs, single-sourcing, BCP)
- `soldier_made_in_europe` (critères "Made in Europe" provisions 2026 AO stratégiques)

**O4 — Legal & Compliance EU**
- `soldier_nis2_compliance` 🎖️ (NIS2 : scope, mesures Article 21, notification, pénalités)
- `soldier_dora_ict_risk` 🎖️ (DORA : ICT risk framework, TLPT, registre tiers, CTPP)
- `soldier_ai_act_classifier` (AI Act : classification risque, Art.5 interdits, conformité)
- `soldier_gdpr_dpo` (RGPD : DPO, DPIA, bases légales, transferts internationaux)
- `soldier_regulatory_horizon` (veille NIS2/DORA/CRA/AI Act/CER — convergence)

**O5 — Risk & Business Continuity**
- `soldier_risk_mapper` 🎖️ (cartographie risques : probabilité × impact, RCSA)
- `soldier_bcp_designer` (ISO 22301 : PCA/PRA, RTOs/RPOs, tests, plans de reprise)
- `soldier_tlpt_coordinator` (DORA TLPT : scope, prestataires, résultats, remédiation)
- `soldier_audit_internal` (programme d'audit interne : scope, sampling, rapport)
- `soldier_crisis_ops` (cellule de crise opérationnelle, RETEX, plan de communication)

**O6 — Operational Intelligence**
- `soldier_ops_kpi_dashboard` 🎖️ (OEE, OTIF, lead time, NPS ops, coûts opérationnels)
- `soldier_process_intelligence_ai` (process mining + AI agents : détection déviations)
- `soldier_capacity_planner` (modélisation charge, simulation, goulots d'étranglement)
- `soldier_ops_automation` (RPA, hyper-automation, workflows no-code/low-code)
- `soldier_continuous_improvement_tracker` (backlog amélioration, ROI mesures, RETEX)
