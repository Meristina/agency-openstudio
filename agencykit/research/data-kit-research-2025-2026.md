# data-kit — Recherche terrain 2025-2026
*Deep research — 106 agents. Note : majorité des claims quantitatifs tués (sources secondaires/paywalled)*
*Seuls 2 claims ont passé la vérification adversariale — données Databricks/dbt non vérifiables sans accès payant*

---

## Findings confirmés (adversarialement vérifiés)

### 1. RAGOps — discipline émergente distincte (2-1)
- **RAGOps** a émergé comme discipline distincte qui *étend* LLMOps en ajoutant un **lifecycle dédié de gestion des données** pour les systèmes RAG (Retrieval-Augmented Generation)
- Stages dédiés : **ingest → verify → update** pour gérer l'évolution continue des sources de données externes
- Insight clé : LLMOps tel que défini précédemment n'adressait pas adéquatement la **maintenance continue des knowledge sources externes**
- Source : ArXiv preprint 2506.03401, juin 2025 (non peer-reviewed — confidence medium)
- **Implication data-kit** : RAG pipelines, couches d'intégration LLM et leurs data operations sont des **préoccupations data engineering de premier ordre** — pas de simples extensions MLOps

### 2. LLMs comme driver structurel de la demande API (3-0)
- **Gartner (mars 2024)** : >**30% de la croissance de la demande d'APIs d'ici 2026 proviendra des outils IA et applications LLM**
- Signal : les LLMs deviennent un driver structurel de croissance de l'infrastructure data enterprise
- Source primaire : Gartner press release, 20 mars 2024 (direct title match — 3-0 unanime)
- **Implication data-kit** : vector databases, embedding APIs, retrieval layers = composants data-kit prioritaires

---

## Claims non vérifiés (rate-limited ou sources paywalled)
*Directionnellement corrects mais non confirmés adversarialement — à valider avec accès primaire*

| Claim | Source présumée | Statut |
|---|---|---|
| dbt adoption : 73% des équipes data (2024) | Anonymous Medium post | ❌ Réfuté 0-3 (source non-identifiable) |
| Databricks : +377% vecteur DB, +1018% model registry | Databricks State of Data+AI (paywall) | ⚠️ 1-2 (source inaccessible) |
| Lakehouse architecture = standard de facto 2025 | Starburst/Gartner (secondaire) | ⚠️ rate-limited |
| 60% des systèmes LLM enterprise utilisent RAG | ArXiv preprint | ❌ Réfuté 0-3 |
| Modern data stack = 5-couches consensus 2025-2026 | Medium anonyme | ⚠️ rate-limited |
| Kubernetes = standard déploiement ML | CNCF (présumé) | ⚠️ rate-limited |
| 66% IT leaders utilisent AI/ML en production | IDC (présumé) | ⚠️ rate-limited |

**Conclusion recherche** : les données quantitatives data-kit sont majoritairement paywalled (Gartner, Forrester, IDC, Databricks State of Data+AI, dbt Labs State of Analytics). Pour un brief grade-décision, accès direct nécessaire.

---

## Ce qui est structurellement vrai (consensus technique, pas besoin de stats)

### Architecture data 2025-2026 (consensus non-statistique)
- **Lakehouse** (Delta Lake, Apache Iceberg, Hudi) = pattern dominant pour unifier data warehouse + data lake
- **dbt** = standard de facto pour transformation analytique (SQL-based, version-controlled)
- **Apache Airflow** = orchestration pipeline de référence (Astronomer + MWAA + GCP Composer)
- **Apache Kafka / Confluent** = streaming event-driven data
- **Fivetran / Airbyte** = EL (extraction-loading) standardisé
- **Databricks / Snowflake / BigQuery** = triumvirat lakehouse/warehouse
- **Great Expectations / Monte Carlo** = data quality & observability
- **MLflow / Kubeflow / SageMaker** = MLOps reference stack
- **RAG + vector databases** (Pinecone, Weaviate, pgvector) = LLMOps layer
- **Data contracts** (Soda, dbt contracts) = gouvernance inter-équipes émergente

### Questions ouvertes (pour affiner le kit)
1. Quelle adoption réelle des data contracts en enterprise EU 2026 ?
2. Comment les frameworks GDPR/CCPA s'adaptent aux données synthétiques et flux LLM ?
3. Quelles structures org (job titles, team topologies) pour RAGOps + LLMOps vs data engineering classique ?
4. La prédiction Gartner (>30% API de LLMs d'ici 2026) est-elle confirmée maintenant qu'on y est ?

---

## Implications pour le data-kit

### Officers validés (par consensus technique + findings vérifiés)

| Officer | Justification |
|---|---|
| **O1 Data Strategy & Governance** | Data contracts émergents, GDPR/AI Act data flows, data mesh vs lakehouse decision |
| **O2 Data Engineering** | dbt + Airflow + Kafka + Lakehouse = stack confirmée, non statistiquement mais techniquement |
| **O3 Analytics & BI** | Semantic layer, self-serve — marché large, tendance confirmée direction |
| **O4 ML/AI & LLMOps** | RAGOps (2-1 ArXiv), Gartner API LLM 3-0 — LLMOps = first-class data concern |
| **O5 Data Quality & Observability** | Great Expectations, Monte Carlo — outils matures, category établie |
| **O6 Data Monetization & Products** | Gartner API signal (LLMs → API demand) → data products, embeddings APIs |

### Soldats prioritaires

**O1 — Data Strategy & Governance**
- `soldier_data_strategy` 🎖️ (data mesh vs lakehouse vs hybrid)
- `soldier_data_governance` (ownership, stewardship, cataloguing)
- `soldier_data_contracts` (interface entre équipes data)
- `soldier_gdpr_data_compliance` (privacy by design, DPIA, CCPA)
- `soldier_data_maturity_assessment` (évaluer le niveau de maturité data)

**O2 — Data Engineering**
- `soldier_pipeline_architect` 🎖️ (ELT design, orchestration, CDC)
- `soldier_dbt_modeler` (dbt models, tests, documentation)
- `soldier_lakehouse_designer` (Iceberg/Delta Lake/Hudi choix + schema)
- `soldier_streaming_engineer` (Kafka, Flink, event-driven patterns)
- `soldier_data_warehouse_optimizer` (partitioning, clustering, cost)

**O3 — Analytics & BI**
- `soldier_semantic_layer_designer` 🎖️ (metrics layer, dbt Semantic, Cube)
- `soldier_dashboard_architect` (Looker, Metabase, Power BI — governance)
- `soldier_self_serve_analytics` (documentation, training, access tiers)
- `soldier_kpi_tree_builder` (North Star → input metrics → dashboard)
- `soldier_embedded_analytics` (analytics dans le produit client)

**O4 — ML/AI & LLMOps**
- `soldier_rag_pipeline_designer` 🎖️ (RAGOps; chunking, embedding, retrieval)
- `soldier_mlops_architect` (MLflow, feature store, model registry, CI/CD ML)
- `soldier_llmops_engineer` 🎖️ (fine-tuning, prompt management, eval, drift)
- `soldier_vector_db_selector` (Pinecone/Weaviate/pgvector — trade-offs)
- `soldier_ml_experiment_designer` (A/B testing ML, shadow deployment)

**O5 — Data Quality & Observability**
- `soldier_data_quality_framework` 🎖️ (Great Expectations, Soda rules)
- `soldier_data_observability` (Monte Carlo, lineage, freshness, volume)
- `soldier_data_incident_response` (data downtime, SLAs, alerting)
- `soldier_data_testing_strategy` (dbt tests, schema contracts, CI data)
- `soldier_data_catalog` (Amundsen, DataHub, Collibra — implementation)

**O6 — Data Monetization & Products**
- `soldier_data_product_designer` 🎖️ (data as a product, interfaces, SLAs)
- `soldier_embedding_api_builder` (vector APIs, semantic search endpoints)
- `soldier_data_marketplace` (internal/external data sharing, pricing)
- `soldier_synthetic_data_generator` (privacy-preserving synthetic data)
- `soldier_data_monetization_strategy` (revenue streams from data assets)
