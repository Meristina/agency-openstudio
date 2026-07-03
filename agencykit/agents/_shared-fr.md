---
role: jurisdiction-context
scope: ops · tech · comms · data · people agents operating in French / FR-specific context
trigger: AK_JURISDICTION=fr  (or detected from goal/dossier context)
---

# FR Jurisdiction — Compliance Context

Load this file when the mission targets French operations, French legal entities, or French employees. **FR stacks on EU**: always load `_shared-eu.md` first (GDPR, NIS2, AI Act, DORA), then this file for France-specific transpositions and additional obligations. Inject into: ops (regulatory), tech (ANSSI, hébergement), comms (presse FR, lobbying), data (CNIL, HDS), people (droit du travail FR).

---

## Données personnelles — RGPD + transposition FR (Loi Informatique et Libertés modifiée)

| Obligation | Base légale | Référence |
|---|---|---|
| RGPD transposé en droit FR | LIL révisée (Loi n° 78-17, modifiée par Ordonnance n° 2018-1125) | JORF n° 0267 du 17 nov. 2018 |
| Autorité de contrôle | CNIL (Commission Nationale de l'Informatique et des Libertés) | cnil.fr |
| Données de santé | HDS — Hébergeur de Données de Santé (certification obligatoire) | Art. L.1111-8 CSP |
| Délégué à la Protection des Données (DPD) | Obligatoire si traitement à grande échelle de données sensibles | Art. 37 RGPD + CNIL guidance |
| Transfert hors UE | CACI (Clauses Contractuelles Types) ou décision d'adéquation | CNIL référentiel transferts |

**Délais de notification de violation:** 72h à la CNIL (Art. 33 RGPD) → notification CNIL via notification.cnil.fr.

**Sourcing:** Citer LIL (Loi n° 78-17 modifiée) + article RGPD correspondant + guide CNIL et date.

---

## Cybersécurité — NIS2 transposition FR + ANSSI

**Transposition NIS2 FR:** Ordonnance attendue fin 2024 / début 2025 — vérifier l'état au JORF.

| Cadre | Portée | Détail |
|---|---|---|
| ANSSI — Agence Nationale de la Sécurité des Systèmes d'Information | OIV / OSE / entités NIS2 | Doctrine ANSSI, guides techniques (anssi.gouv.fr) |
| SecNumCloud | Hébergement cloud souverain | Qualification ANSSI obligatoire pour certains services OIV et OES |
| Opérateurs d'Importance Vitale (OIV) | 12 secteurs définis par arrêté | Obligation de mise en conformité sur systèmes d'information d'importance vitale (SIIV) |
| Opérateurs de Services Essentiels (OSE) | NIS1 → NIS2 scope élargi | Mesures de sécurité + déclaration incidents à l'ANSSI |
| PSSIE | Politique de Sécurité des SI de l'État | Applicable aux administrations FR |

**Référentiels clés ANSSI:** Guide EBIOS Risk Manager · Référentiel général de sécurité (RGS) v2 · PAMO (Plan d'Amélioration de la Maturité Opérationnelle).

**Sourcing:** Citer référence ANSSI + numéro de version + date. Pour les décrets OIV, citer l'arrêté sectoriel et l'article du Code de la Défense (L1332-1 et suivants).

---

## Intelligence Artificielle — AI Act transposition FR

L'AI Act est d'application directe en tant que règlement UE. Spécificités FR :

| Acteur | Rôle |
|---|---|
| Autorité de surveillance des marchés (IA à haut risque, sauf secteur financier) | Direction Générale de la Concurrence, de la Consommation et de la Répression des Fraudes (DGCCRF) |
| Autorités sectorielles pour IA haut-risque | AMF (finance), ACPR (assurance/banque), ANSSI (cybersécurité IA) |
| Incitations FR | Programme France 2030 — IA ; PIA (investissement ADEME/BPI) |

**Sourcing:** Référencer Règlement (UE) 2024/1689 + désignation des autorités nationales compétentes par ordonnance FR.

---

## Droit du travail FR (Code du travail)

### Contrats et ruptures

| Acte | Régime | Référence |
|---|---|---|
| CDI (Contrat à Durée Indéterminée) | Résiliation : faute / cause réelle et sérieuse / accord | Art. L1232-1 s. CT |
| CDD (Contrat à Durée Déterminée) | Motifs limitatifs ; requalification si abus | Art. L1242-1 s. CT |
| Rupture conventionnelle | Accord amiable homologué DREETS ; délai de rétractation 15 jours | Art. L1237-11 s. CT |
| Plan de Sauvegarde de l'Emploi (PSE) | ≥10 licenciements sur 30 jours dans entreprise ≥50 salariés | Art. L1233-61 s. CT |
| Portage salarial | Cadre légal depuis 2015 (Ord. 2015-380) | Art. L1254-1 s. CT |

### Représentation du personnel

| Instance | Seuil | Attributions |
|---|---|---|
| CSE (Comité Social et Économique) | ≥11 salariés (délégués) ; ≥50 salariés (plénitude) | Information-consultation obligatoire sur décisions stratégiques |
| BDES → BDESE (Base de Données Économiques, Sociales et Environnementales) | ≥50 salariés | Mis à disposition du CSE : emploi, rémunérations, formations, environnement |
| Accord d'entreprise | Négociation obligatoire annuelle (NAO) sur salaires, égalité F/H, télétravail | Art. L2242-1 s. CT |

**Consultation CSE obligatoire pour:** licenciements ≥10 salariés, cession/fusion, introduction d'outils de surveillance numérique (DUERP numérique), déménagement de site, modification substantielle des conditions de travail.

### Temps de travail

- Durée légale : **35h/semaine** (Art. L3121-27 CT)
- Heures supplémentaires : majorées à 25% (8 premières h/sem) puis 50%
- Forfait jours : cadres autonomes — 218 jours max ; accord collectif obligatoire
- Congés payés : **5 semaines** (25 jours ouvrables ou 30 jours ouvrés)

### Égalité et non-discrimination

- Index égalité professionnelle F/H obligatoire (≥50 salariés) — publication annuelle
- Obligation de formation continue (CPF — Compte Personnel de Formation)

**Sourcing:** Citer Code du travail (Legifrance) article + version en vigueur. Pour circulaires DREETS, citer référence ministérielle et date.

---

## Fiscalité et droit des sociétés FR

| Cadre | Points clés |
|---|---|
| SAS / SASU | Société par actions simplifiée — forme la plus utilisée pour les startups FR ; grande liberté statutaire |
| Crédit Impôt Recherche (CIR) | 30% des dépenses R&D (jusqu'à 100 M€), 5% au-delà ; déclaration 2069-A |
| Jeune Entreprise Innovante (JEI) | Exonérations sociales + fiscales si ≤250 salariés, ≤8 ans, ≥15% charges R&D |
| TVA | Taux normal 20% ; réduit 5,5% / 10% selon catégorie |
| IS | 25% standard ; taux réduit 15% pour PME (jusqu'à 42 500 € de bénéfices) |
| Loi Sapin II (n° 2016-1691) | Anticorruption — plan de vigilance si CA >100 M€ ou effectif >500 ; code de conduite obligatoire |

**Sourcing:** Citer BOFIP (Bulletin Officiel des Finances Publiques) + article CGI ou BOI-référence.

---

## Commande publique FR (marchés publics)

| Seuil 2024 | Procédure |
|---|---|
| < 40 000 € HT | Procédure adaptée allégée (bon de commande) |
| 40 000 € – 221 000 € HT | MAPA — Marché à Procédure Adaptée |
| > 221 000 € HT (fournitures/services) / 5 538 000 € HT (travaux) | Procédure formalisée (appel d'offres ouvert/restreint, dialogue compétitif) |

**Référence:** Code de la commande publique (CCP) — CCP art. L2124-2. Seuils révisés tous les 2 ans par décret.

**Plates-formes:** PLACE (Profil Acheteur de l'État) · AWS Marchés · Marchés Sécurisés (MSS)

---

## Communications & Presse FR

| Règle | Référence |
|---|---|
| Loi sur la presse (29 juillet 1881) | Diffamation, injure, droit de réponse obligatoire (72h) |
| Loi Sapin II — publicité, médias | Transparence sur achats d'espace publicitaire (Art. 23 Loi Sapin) |
| LCEN (Loi n° 2004-575) | E-commerce, mentions légales obligatoires, hébergeur/éditeur |
| Registre des représentants d'intérêts (HATVP) | Obligation d'inscription si activité de lobbying auprès d'agents publics FR |
| CSRD transposition FR | Transposée par Ordonnance n° 2023-1142 + décrets 2024 — rapport de durabilité obligatoire |

**Sourcing:** Citer texte de loi (Legifrance), numéro d'article, version consolidée.

---

## Vérification (checklist FR)
- [ ] RGPD + LIL : registre des traitements (CNIL Art. 30), DPD nommé si requis
- [ ] HDS certification si traitement de données de santé
- [ ] Qualification NIS2 FR confirmée (OIV / OSE / entité importante / hors scope)
- [ ] SecNumCloud requis si hébergement de données OIV ou administration FR
- [ ] CSE consulté si décision déclenchant obligation légale (≥50 salariés)
- [ ] BDESE mise à jour et accessible au CSE
- [ ] Index égalité F/H publié (≥50 salariés)
- [ ] CIR/JEI éligibilité vérifiée pour R&D en cours
- [ ] Loi Sapin II — code de conduite et plan de vigilance si seuils atteints
- [ ] Registre HATVP si activité de lobbying auprès des autorités FR
- [ ] Seuils marchés publics CCP vérifiés (décret en vigueur)
