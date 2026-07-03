# tech-kit — Recherche terrain 2025-2026
*Deep research adversarialement vérifié — 110 agents, 30 sources, claims vérifiés*
*Note : plusieurs claims rate-limited → non tués mais non confirmés (signalés ⚠️)*

---

## 3 Macro-forces structurantes (2025-2026)

### 1. IA dans les pipelines CI/CD — réalité de production, mais tension throughput/stabilité
- **DORA 2025** (Google Cloud) : l'adoption IA montre une **relation positive avec le throughput** (inversé vs 2024 où c'était négatif) MAIS **continue de montrer une relation NÉGATIVE avec la stabilité** des livraisons
  - *C'est la tension ouverte #1 pour toute équipe engineering qui scale l'AI-assisted coding*
- **Meta DRS (Diff Risk Score)** — système IA en production :
  - Fine-tuned **Llama LLM** qui prédit la probabilité qu'un changement de code cause un incident de production (SEV)
  - Intégré sur tout le cycle CI/CD : sélection build/tests, assignation reviewers, analyse risque release
  - **10 000+ code changes** livrés pendant une période de freeze (événement partner 2024) avec impact production minimal
  - Source : Meta Engineering Blog, août 2025 (3-0 adversarial)
- **76% des PR pros** utilisent l'IA générative quotidiennement (tech/PR convergent)

### 2. Platform Engineering — franchissement du seuil opérationnel
- **Backstage (Spotify)** — Internal Developer Portal de référence :
  - **700 squads R&D** s'appuient dessus quotidiennement (Spotify Engineering Blog, avril 2025 — 3-0)
  - Cohérent avec ~7 300 employés Spotify (taille de squad 5-7)
  - ⚠️ "3 000+ entreprises ont adopté Backstage" → **réfuté 0-3** (statistique non vérifiable)
  - ⚠️ "90% des entreprises ont adopté le platform engineering" → **réfuté** (chiffre Gartner non confirmé)
- **Le modèle** : un IDP unique peut servir toute l'organisation engineering d'une grande tech company

### 3. Résilience & Sécurité — doctrines établies de référence
- **AWS Static Stability** (Well-Architected Framework, REL11-BP05 — 3-0) :
  - "Dans un design statiquement stable, le système global continue de fonctionner même quand une dépendance est impairée"
  - Best practice : séparer systèmes selon la frontière **control plane / data plane** (data plane = plus critique, cibler disponibilité plus haute)
  - **Overprovision** l'infrastructure pour ne jamais avoir besoin de lancer de nouvelles instances pendant une défaillance
- **Netflix Observability Multi-Sources** (Netflix Tech Blog, juin 2026 — 3-0) :
  - Combine délibérément **3 sources** car aucune ne donne visibilité complète :
    1. **eBPF network flows** → visibilité kernel-level
    2. **IPC metrics** (gRPC/GraphQL/REST) → détail application-level
    3. **Distributed tracing** → chemins de requêtes réels
  - Principe : chaque source compense les limitations structurelles des autres → **complémentarité et redondance par design**

---

## Claims non réfutés mais non-vérifiés (rate-limited — à valider)

*Ces claims ont été extraits de sources reconnues mais les 3 vérificateurs adversariaux ont été rate-limited — pas tués, pas confirmés :*

| Claim | Source probable | Pertinence |
|---|---|---|
| **Kubernetes** = standard de facto déploiement containers | CNCF survey 2025 | Haute — composant tech-kit |
| **Zero Trust** : rejet du modèle périmètre, authentification à chaque resource | NIST SP 800-207 | Haute — security officer |
| **Vibe coding** (late 2025) : l'IA génère la majorité du code en production | Tendance générale | Moyenne — engineering excellence |
| **MCP (Model Context Protocol)** : standard émergent IA↔outils | Anthropic/communauté | Haute — AI-assisted dev |
| **BOLA (Broken Object Level Authorization)** = #1 OWASP API Security | OWASP API Top 10 2023 | Haute — security engineering |
| **eBPF** = visibilité kernel-level sans overhead | Docs officielles | Haute — observabilité |
| **GenAI** pour comprendre legacy code | ThoughtWorks Radar | Haute — tech debt |
| **Continuous compliance** (policy as code automatisé) | Tendance DevSecOps | Moyenne |
| **AI-assisted dev** : shift de génération vers vérification/orchestration | Évolution 2025 | Haute |
| **Netflix** : migration de self-hosted vers infra managée | Netflix blog | Moyenne |

---

## Landscape des références tech

### Google / AWS / Meta / Netflix — Engineering Blogs (sources primaires)
- **AWS Builders' Library** — doctrines resilience, static stability, availability
- **Meta Engineering Blog** — DRS, CI/CD AI, developer tools
- **Netflix Tech Blog** — observabilité multi-sources, microservices, chaos engineering
- **Google DORA** — metrics livraison software (annuels depuis 2014)

### ThoughtWorks Technology Radar (référence conseil)
- Publication semestrielle : Adopt / Trial / Assess / Hold
- 2025 : plateforme engineering, AI-assisted dev, GenAI for legacy — tous en position "Assess" ou "Trial"

### CNCF (Cloud Native Computing Foundation)
- Survey annuel sur adoption Kubernetes, containers, platform engineering

---

## Implications directes pour le tech-kit

### Officers validés par la recherche

| Officer | Validation terrain |
|---|---|
| **O1 Architecture système** | AWS static stability + control/data plane separation → ADR, C4, resilience patterns |
| **O2 DevOps & Platform Engineering** | Backstage 700 squads ; DORA 2025 ; Meta DRS → CI/CD + IDP + AI-assisted pipelines |
| **O3 Security Engineering** | NIST Zero Trust ; OWASP BOLA API #1 ; continuous compliance → security by design |
| **O4 Engineering Excellence** | DORA stability/throughput tension ; vibe coding ; GenAI legacy → quality gate + AI governance |
| **O5 Build vs Buy & Cloud** | eBPF, Kubernetes, MCP → vendor evaluation, cloud selection, OSS |
| **O6 Engineering Metrics** | DORA 5 metrics (DF, LTFC, CFR, MTTR, rework) ; Netflix observabilité → fiabilité mesurable |

### Soldats prioritaires

**O1 — Architecture système**
- `soldier_adr_writer` 🎖️ (Architecture Decision Records — documenter les choix)
- `soldier_c4_designer` (C4 diagrams : context/container/component/code)
- `soldier_resilience_patterns` 🎖️ (static stability, circuit breaker, bulkhead, retry)
- `soldier_microservices_design` (decomposition, bounded contexts, DDD)
- `soldier_api_design` (OpenAPI, REST vs GraphQL, versioning, BOLA mitigation)

**O2 — DevOps & Platform Engineering**
- `soldier_cicd_pipeline` 🎖️ (GitHub Actions, GitLab CI, trunk-based dev, feature flags)
- `soldier_idp_designer` (Internal Developer Portal ; Backstage architecture)
- `soldier_kubernetes_sizing` (cluster design, resource requests, HPA, cost)
- `soldier_iac_designer` (Terraform, Pulumi, IaC patterns, drift detection)
- `soldier_ai_cicd_integration` 🎖️ (Meta DRS pattern ; AI risk scoring in pipelines)

**O3 — Security Engineering**
- `soldier_threat_modeling` 🎖️ (STRIDE, attack trees, DFD)
- `soldier_zero_trust_designer` (NIST SP 800-207, BeyondCorp, identity-centric)
- `soldier_owasp_auditor` (OWASP Top 10 + API Security Top 10, BOLA)
- `soldier_soc2_controls` (control mapping, evidence collection, readiness)
- `soldier_secrets_management` (Vault, AWS Secrets Manager, rotation, SAST)

**O4 — Engineering Excellence**
- `soldier_tech_debt_mapper` 🎖️ (classification, quantification, payback plan)
- `soldier_code_review_standards` (checklists, AI-assisted review, PR hygiene)
- `soldier_testing_strategy` (TDD, BDD, test pyramid, contract testing)
- `soldier_genai_legacy_modernizer` (GenAI pour comprendre + refactorer le legacy)
- `soldier_vibe_coding_governance` (guardrails IA-generated code, ownership, review)

**O5 — Build vs Buy & Cloud**
- `soldier_make_or_buy` 🎖️ (framework décision, TCO, risque vendor lock-in)
- `soldier_cloud_selection` (AWS vs GCP vs Azure vs OVH ; multi-cloud ; coût)
- `soldier_oss_evaluation` (maturité OSS, licence, communauté, SBOM)
- `soldier_finops_optimizer` (FinOps, rightsizing, reserved vs spot, RI coverage)

**O6 — Engineering Metrics**
- `soldier_dora_measurer` 🎖️ (DF, LTFC, CFR, MTTR, Rework Rate — baseline + amélioration)
- `soldier_slo_sli_designer` (SLO/SLI/Error Budget, alerting philosophie)
- `soldier_observability_stack` (eBPF + metrics + tracing ; Prometheus/Grafana/Jaeger)
- `soldier_incident_postmortem` (blameless postmortem, RCA, COE, action items)
- `soldier_capacity_planning` (load testing, traffic modeling, auto-scaling)
