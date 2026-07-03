---
role: jurisdiction-context
scope: ops · tech · comms · data · people agents operating in US markets
trigger: AK_JURISDICTION=us  (or detected from goal/dossier context)
---

# US Jurisdiction — Compliance Context

Load this file when the mission targets US operations, customers, or data subjects. Inject into: ops (compliance), tech (security architecture), comms (SEC/FTC disclosure), data (privacy engineering), people (employment law).

---

## Cybersecurity — NIST CSF 2.0 (2024)

Six functions (updated from five in CSF 1.1):

| Function | Core activities |
|---|---|
| **Govern** (new) | Cybersecurity strategy, roles, policies, risk tolerance — board-level accountability |
| Identify | Asset inventory, risk assessment, supply chain risk |
| Protect | Access control, awareness training, data security, platform security |
| Detect | Continuous monitoring, anomaly detection |
| Respond | Response planning, communications, mitigation |
| Recover | Recovery planning, improvements, communications |

**Tiers:** Partial (1) → Risk-Informed (2) → Repeatable (3) → Adaptive (4).  
**Sourcing:** cite NIST CSF 2.0 (February 2024). SP 800-53 Rev 5 for control catalogue.

---

## Security Audit — SOC 2 (AICPA Trust Services Criteria)

| Criterion | Scope |
|---|---|
| Security (CC) | Common criteria — mandatory for all SOC 2 |
| Availability (A) | System uptime commitments |
| Processing Integrity (PI) | Complete, valid, accurate, timely processing |
| Confidentiality (C) | Information designated as confidential |
| Privacy (P) | Personal information lifecycle |

**Type I** — design effectiveness at a point in time.  
**Type II** — operating effectiveness over a period (typically 12 months). Preferred by enterprise buyers.

**Sourcing:** cite AICPA Trust Services Criteria (2017, updated 2022) + specific control reference.

---

## Data Privacy — State Laws (no federal omnibus yet)

| Law | State | In force | Key scope |
|---|---|---|---|
| CCPA / CPRA | California | CCPA 2020; CPRA 2023 | Consumer rights (access, deletion, opt-out of sale/sharing), sensitive PI, data minimisation |
| VCDPA | Virginia | 2023 | Similar to CCPA; no private right of action |
| CPA | Colorado | 2023 | Universal opt-out mechanism required |
| TDPSA | Texas | 2024 | Data brokers; no revenue threshold |
| MHMDA | Washington | 2024 | Consumer health data — very broad definition |

**Federal sector laws:** HIPAA (health), FERPA (education), GLBA (financial), COPPA (children under 13).

**Sourcing:** cite state statute by code reference and effective date. Federal laws: cite USC/CFR section.

---

## AI Governance — Federal & State

| Framework | Status |
|---|---|
| Executive Order 14110 (AI Safety, Oct 2023) | Active — agencies implementing; NIST AI RMF required |
| NIST AI RMF 1.0 (2023) | Voluntary framework; increasingly referenced in contracts |
| EU AI Act equivalence | No federal equivalent — sector-specific rules apply |
| State AI laws | Illinois BIPA (biometric), NYC Local Law 144 (automated hiring), Colorado AI insurance |

**Sourcing:** cite EO number + Federal Register; NIST AI RMF DOI 10.6028/NIST.AI.100-1.

---

## SEC Cyber Disclosure (2023 Final Rule)

Applies to public companies (registrants).

| Requirement | Timing |
|---|---|
| Material cybersecurity incident disclosure | Form 8-K, Item 1.05 — within **4 business days** of materiality determination |
| Annual cybersecurity risk management disclosure | Form 10-K — governance, material risks, strategy |
| Board cybersecurity expertise | Disclose if any director has expertise (not require it) |

**Materiality test:** would a reasonable investor consider it important? Apply qualitative + quantitative analysis.

**Sourcing:** cite 17 CFR Parts 229 and 249; Release Nos. 33-11216, 34-97989 (2023).

---

## FTC — Advertising, Privacy & Endorsements

| Rule / Guidance | Scope |
|---|---|
| FTC Guides (16 CFR Part 255) — Endorsements & Testimonials | Disclose material connections; no fake reviews |
| Section 5 FTC Act | Unfair or deceptive acts or practices |
| FTC Health Breach Notification Rule | Non-HIPAA health apps — breach notification |
| Gramm-Leach-Bliley Safeguards Rule | Financial institution data security (2023 update) |

**Sourcing:** cite 16 CFR part/section and FTC guidance URL with date.

---

## Employment Law — Federal (key)

| Law | Scope |
|---|---|
| Title VII (Civil Rights Act 1964) | Prohibits discrimination by race, color, religion, sex, national origin |
| ADA (1990) | Disability discrimination and reasonable accommodation |
| ADEA (1967) | Age discrimination (40+) |
| FLSA | Minimum wage, overtime, exempt/non-exempt classification |
| NLRA | Protected concerted activity; union rights |
| FMLA | 12 weeks unpaid leave (50+ employee threshold) |

**State note:** at-will employment modified by state — check California (near-total for-cause), Montana (for-cause after probation), and 12+ states with expanded protected classes.

**Sourcing:** cite USC section. For EEOC guidance, cite EEOC document number + date.

---

## Public Procurement — Federal (FAR / DFARS)

| Threshold | Requirement |
|---|---|
| Micro-purchase (≤$10,000) | Simplified; no competition required |
| Simplified acquisition ($10K–$250K) | Competitive; fewer formalities |
| > $250,000 | Full & open competition; FAR Part 15 |

**Cyber for federal:** CMMC (Cybersecurity Maturity Model Certification) required for DoD contracts handling CUI. CMMC Level 2 → NIST SP 800-171 (110 controls).

**Sourcing:** cite FAR clause number; CMMC Final Rule 32 CFR Part 170 (2024).

---

## Verification Checklist (US)
- [ ] State privacy law applicability mapped (CCPA/CPRA, VCDPA, CPA, etc.) by customer/data subject location
- [ ] SOC 2 Type II report current (< 12 months) or remediation plan in place
- [ ] NIST CSF tier documented and gap assessment complete
- [ ] SEC registrant status confirmed (8-K / 10-K disclosure obligations)
- [ ] FTC endorsement compliance checked for any marketing materials
- [ ] EEOC/Title VII — hiring process reviewed for disparate impact
- [ ] At-will status confirmed per key employee states (esp. California)
- [ ] Federal contracting: FAR/DFARS applicability checked; CMMC level if DoD
