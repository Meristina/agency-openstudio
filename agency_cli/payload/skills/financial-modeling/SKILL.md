# financial-modeling — Modélisation Financière P&L

## Objectif
Construire un P&L prévisionnel rigoureux sur 3 ans avec 3 scénarios et une analyse de sensibilité.

## Procédure

### Étape 1 — Structurer le P&L
```
Revenus
  - Segment A : volume × prix moyen
  - Segment B : volume × prix moyen
  [...]
COGS (coût des ventes)
  - Coût de production / livraison
  - Marge brute = Revenus - COGS
Charges d'exploitation
  - S&M (Sales & Marketing)
  - R&D
  - G&A (Général & Administration)
EBITDA = Marge brute - Charges d'exploitation
Amortissements / dépréciations
EBIT = EBITDA - A&D
Résultat net = EBIT - Impôts
```

### Étape 2 — Documenter les hypothèses
Pour chaque ligne : source de l'hypothèse (marché, client, analogie, benchmark) ou label `[HYPOTHÈSE]`.
Indiquer la fourchette raisonnable (min-max) pour les variables critiques.

### Étape 3 — Construire les 3 scénarios
- **Base** : hypothèses réalistes (médiane des benchmarks sectoriels)
- **Best** : +20 à +40% sur les variables de croissance (revenus, rétention), -10% sur les coûts variables
- **Worst** : -20 à -40% sur les revenus, +15% sur les coûts, churn accéléré

### Étape 4 — Analyse de sensibilité
Identifier les 3-5 variables à plus fort impact. Tableau croisant les variations de ces variables avec le résultat net.

### Étape 5 — Verdict de viabilité
- À quel scénario l'entreprise est-elle profitable ?
- À partir de quel mois / année dans le scénario base ?
- Quelles hypothèses doivent être vraies pour le worst case ?

## Standards de qualité
- Cohérence arithmétique vérifiée (totaux = somme des lignes)
- Benchmarks sectoriels sourcés
- Pas de chiffre "inventé" — fourchettes ou hypothèses documentées
