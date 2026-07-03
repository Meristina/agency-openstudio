---
role: jurisdiction-context
scope: ops · tech · comms · data · people agents operating in EU/EEA markets
trigger: AK_JURISDICTION=eu  (or detected from goal/dossier context)
---

# EU Jurisdiction — Compliance Context

Load this file when the mission targets EU/EEA operations, customers, or data subjects. Inject into: ops (compliance), tech (security architecture), comms (ESG/disclosure), data (privacy engineering), people (employment law).

---

## Data Protection — GDPR (Regulation 2016/679)

| Requirement | Key articles | Implication |
|---|---|---|
| Lawful basis for processing | Art. 6 | Must document basis per processing activity (Art. 30 register) |
| Data subject rights | Art. 15–22 | Erasure, portability, restriction — pipelines must support |
| DPA / DPO appointment | Art. 37 | Mandatory if large-scale special-category processing |
| Data breach notification | Art. 33 | 72h to supervisory authority; Art. 34 to subjects if high risk |
| Cross-border transfer | Art. 44–49 | SCCs (Commission Decision 2021/914) or adequacy decision |
| Records of processing | Art. 30 | Mandatory for all controllers and processors |

**Sourcing:** cite GDPR article number + OJ L 119/1, 04.05.2016. For supervisory authority guidance, cite the relevant SA opinion (CNIL, BfDI, ICO, etc.) and date.

---

## Cybersecurity — NIS2 Directive (Directive 2022/2555)

**In force:** 17 October 2024 (transposition deadline). Applies to **160,000+ entities** (confirmed by ENISA) across medium and large essential and important entities in 18 sectors. As of November 2024, **23 EU member states** had not transposed — European Commission opened infringement proceedings (EC, Nov 2024).

| Obligation | Scope | Detail |
|---|---|---|
| Risk management measures | Art. 21 | Policies, incident handling, supply chain security, cryptography, MFA, access control |
| Incident reporting | Art. 23 | 24h early warning → 72h notification → 1 month final report to CSIRT/authority |
| Management accountability | Art. 20 | Board-level responsibility; training mandatory |
| Supply chain security | Art. 21(2)(d) | Evaluate ICT suppliers; include security clauses in contracts |
| Sanctions | Art. 34 | Up to €10M or 2% of global turnover (essential entities); €7M / 1.4% (important) |

**NIS2 ↔ DORA:** DORA is *lex specialis* for NIS2 in the financial sector — financial entities satisfy NIS2 via DORA.

**Sourcing:** cite Directive 2022/2555, OJ L 333/80, 27.12.2022. For national transposition, cite implementing law per member state.

---

## AI Systems — AI Act (Regulation 2024/1689)

**Application dates:** Art. 5 (prohibited practices) → **2 February 2025** (in force); GPAI rules → August 2025; high-risk systems → August 2026; other → August 2027.

| Risk level | Examples | Obligations |
|---|---|---|
| Unacceptable | Social scoring, real-time biometric surveillance, manipulation of vulnerable groups, real-time remote biometric ID in public spaces | **Prohibited — Art. 5 in force 2 Feb 2025** |
| High-risk | CV screening, credit scoring, critical infrastructure AI, education access | Conformity assessment, human oversight, transparency, Art. 10 data governance |
| Limited risk | Chatbots, deepfake generation | Transparency disclosure (Art. 50) |
| Minimal | Spam filters, basic recommendation | No specific obligations |

**GPAI models** (Art. 51–53): systemic-risk models (>10^25 FLOPS) → adversarial testing, cybersecurity, incident reporting.

**Sourcing:** cite Regulation (EU) 2024/1689, OJ L 2024/1689, 12.07.2024.

---

## Financial Sector Resilience — DORA ICT (Regulation 2022/2554)

Applies to: banks, insurers, investment firms, payment institutions, crypto-asset service providers, and their critical ICT third-party providers.

| Pillar | Requirement |
|---|---|
| ICT risk management | Board-approved framework, asset inventory, classification |
| Incident reporting | Classify → report to competent authority (major incidents: within 4h initial, 72h intermediate, 1 month final) |
| Digital operational resilience testing | TLPT (threat-led penetration testing) every 3 years for significant entities |
| Third-party risk | Register of ICT contracts; concentration risk; oversight of critical providers |
| Information sharing | Voluntary (Art. 45) but encouraged |

**In force:** 17 January 2025. **Critical ICT third-party providers (CTPPs):** 19 designated by ESAs (EBA + EIOPA + ESMA) in November 2025, including AWS, Google Cloud, and Microsoft.

**Sourcing:** cite Regulation (EU) 2022/2554, OJ L 333/1, 27.12.2022. For CTPP designation: ESA Joint Register.

---

## ESG Reporting — CSRD (Directive 2022/2464) as amended by Omnibus I

**⚠️ Scope drastically reduced — Directive (EU) 2026/470 (OJ, 26 Feb 2026, in force 18 March 2026):**

| Criteria | Before Omnibus I | After Omnibus I (Directive 2026/470) |
|---|---|---|
| Scope threshold | >500 employees OR large companies | **>1,000 employees AND >€450M** net turnover |
| Companies in scope | ~50,000 | **~5,000 (-90%)** |
| Listed SMEs | Mandatory FY2026 (opt-out to 2028) | **Exempt** |
| ESRS data points | Full set | **>70% reduction** (EFRAG Dec 2025) |
| CSDDD (supply chain due diligence) | >500 employees / >€150M | **>5,000 employees AND >€1.5B** — implementation delayed to **26 July 2029** |

**For the ~5,000 entities still in scope:**
- Mandatory ESRS reporting under reduced data point set
- Double materiality: financial impact ON the company AND company's impact ON environment/society
- Assurance required

**For the ~45,000 newly exempt entities:**
- No obligation — but voluntary reporting (GRI, B Corp, SBTi, ISO 14001) signals commitment
- **77% of CFOs** maintain or increase sustainability investment regardless of obligation (BDO Survey, Feb 2025, 3-0)
- **78% of investors** say sustainability metrics improve their confidence (PwC Survey 2025, 3-0)

| ESRS standard | Content | Status post-Omnibus |
|---|---|---|
| ESRS E1 | Climate (GHG Scope 1/2/3, TCFD-aligned) | Retained (reduced data points) |
| ESRS S1 | Own workforce | Retained |
| ESRS S2 | Workers in the value chain | Retained (reduced) |
| ESRS G1 | Business conduct | Retained |

**Sourcing:** cite Directive 2022/2464 + Directive (EU) 2026/470, OJ 26.02.2026. For pre-Omnibus delegated acts: Commission Regulation (EU) 2023/2772 (ESRS set 1). Verify current ESRS data point set via EFRAG.

---

## Public Procurement — Directive 2014/24/EU + Reform 2026

| Threshold (2024–2025) | Scope |
|---|---|
| €143,000 | Central government works/supplies/services |
| €221,000 | Sub-central contracting authorities |
| €5,538,000 | Works contracts |

**Current landscape (verified):**
- **55%** of public contracts awarded on lowest-price criterion only (EC Staff Working Document SWD(2025)332, Oct 2025 evaluation of Directives 2014/23-24-25/EU)
- Only **11%** use cooperative/pooled procurement
- Average number of bids per tender declining (confirmed EC trend)

**Reform 2026 — Public Procurement Act** (planned Q2 2026, Art. 114 TFEU):
- Sustainability, resilience, and social criteria entering tender evaluation
- **"Made in Europe" provisions** for strategic sectors
- Source: EC Work Programme 2026 + European Parliament Legislative Train (2-1 confidence — announced, not yet enacted)

**Key principles:** transparency, equal treatment, proportionality, mutual recognition.  
**Sourcing:** cite current Commission Regulation setting thresholds (biennial update — check OJ). For reform: cite EC Work Programme 2026.

---

## Employment — EU Directives (key)

| Directive | Topic | Key detail |
|---|---|---|
| 2019/1152 | Transparent and predictable working conditions | Written statement of terms requirements |
| 2022/2041 | Adequate minimum wages | Process for setting and updating national minimum wages |
| **2023/970** | **Pay transparency and equal pay enforcement** | **Transposition deadline: 7 June 2026** — gender pay gap >5% per job category → mandatory joint assessment with worker representatives |
| 2002/14/EC | Employee information and consultation (works councils) | Consultation rights on strategic decisions |
| 2001/23/EC | Transfer of undertakings (TUPE-equivalent) | Employee rights on business transfer |

**Directive 2023/970 — Pay Transparency (verified 3-0):** companies must disclose salary ranges in job ads; employees have right to request pay benchmarks; gap >5% per job category triggers mandatory joint assessment. Korn Ferry 5-Stage Framework: a solid job architecture (Stage 3) is a structural prerequisite before compensation policy design (Stage 4).

**Sourcing:** cite directive number + OJ reference. For national implementation, cite domestic statute.

---

## Verification Checklist (EU)
- [ ] GDPR Art. 30 processing register updated
- [ ] NIS2 sector classification confirmed (essential / important / not in scope); check if national transposition is in force
- [ ] AI Act: Art. 5 prohibited practices check (in force 2 Feb 2025); risk classification for each AI system
- [ ] DORA applicability check (financial sector entity?); CTPP contract register if applicable
- [ ] CSRD: confirm scope under Directive 2026/470 (>1,000 employees AND >€450M) or confirm exempt status; verify ESRS data point set in force
- [ ] CSDDD: confirm scope under amended thresholds (>5,000 employees AND >€1.5B) — implementation 26 July 2029
- [ ] Public Procurement: thresholds verified against current OJ; flag if Q2 2026 reform enacted
- [ ] Directive 2023/970: salary range disclosure in job postings; pay gap assessment ready
- [ ] Cross-border data transfer mechanism documented (SCC / adequacy decision)
