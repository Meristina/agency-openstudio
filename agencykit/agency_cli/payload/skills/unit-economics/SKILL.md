# unit-economics — Économie Unitaire

## Objectif
Calculer et analyser LTV, CAC, payback period et contribution margin pour évaluer la santé économique unitaire.

## Métriques clés

### LTV (Lifetime Value)
```
LTV = ARPU mensuel × Marge brute (%) / Churn mensuel (%)
ou
LTV = ARPU × Durée de vie client moyenne (mois) × Marge brute (%)
```

### CAC (Customer Acquisition Cost)
```
CAC = (Dépenses S&M sur période) / (Nouveaux clients sur période)
CAC Blended vs CAC par canal
```

### Payback Period
```
Payback = CAC / (ARPU mensuel × Marge brute %)
Cible : < 12 mois (B2C) / < 18 mois (B2B SMB) / < 24 mois (B2B Enterprise)
```

### LTV:CAC Ratio
```
Cible : > 3:1 pour un SaaS sain
> 5:1 = sous-investissement en acquisition
< 2:1 = problème d'économie unitaire
```

### Contribution Margin
```
CM = Revenus - COGS - Coûts variables S&M
CM% = CM / Revenus
```

## Procédure
1. Collecter les données (ARPU, churn, dépenses S&M, nouveaux clients)
2. Calculer les métriques avec les formules ci-dessus
3. Comparer aux benchmarks sectoriels (SaaStr, OpenView, KeyBanc surveys)
4. Identifier les leviers d'amélioration (réduire CAC, augmenter LTV, accélérer payback)
5. Simuler l'impact d'améliorations (+10% rétention, -20% CAC, etc.)

## Benchmarks SaaS (sourcés)
- LTV:CAC médian Series A : 3-5x (OpenView 2024)
- Payback médian : 15-24 mois (SaaStr)
- Churn acceptable : < 5% annuel net pour B2B enterprise
