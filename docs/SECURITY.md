# Sécurité — Agency Studio

Posture non négociable, appliquée **dès la Vague 0**. Elle prend explicitement le
contre-pied des défauts relevés dans les runners locaux existants (notamment
Uncensored-Local-Studio : serveur exposé sur `0.0.0.0` + path traversal).

## Règles dures

| # | Règle | Pourquoi |
|---|---|---|
| 1 | **Bind `127.0.0.1` uniquement** (jamais `0.0.0.0`). | Évite l'exposition silencieuse au réseau local. Un studio « privacy » ne doit pas être pilotable depuis une autre machine du LAN. |
| 2 | **Pas de `Access-Control-Allow-Origin: *`.** Origine locale uniquement. | Empêche un site web tiers d'appeler l'API locale depuis le navigateur. |
| 3 | **`path_inside()` sur 100 % du service de fichiers statiques.** | Bloque le path traversal (`GET /../../etc/passwd`). Résoudre le chemin et vérifier qu'il reste sous `dist/`. |
| 4 | **Valider schéma/host des URLs de download.** | Empêche le téléchargement d'URLs arbitraires (SSRF / contenu non maîtrisé). |
| 5 | **Vérifier les checksums des binaires/modèles téléchargés.** | Garde de chaîne d'approvisionnement avant d'exécuter un binaire local. |
| 6 | **Aucune télémétrie, aucune clé en clair.** | Cohérent avec l'ethos local-first. |

## Test de non-régression (dès Vague 0)

```bash
# Path traversal bloqué
curl --path-as-is http://127.0.0.1:<port>/../../../../etc/passwd   # → 404 attendu

# Le serveur n'écoute QUE sur la loopback
lsof -iTCP -sTCP:LISTEN | grep <port>                              # → 127.0.0.1 only
```

Ces deux vérifications font partie de la définition de « done » de la Vague 0 et doivent
être couvertes par `tests/test_server.py`.

## Implémentation de `path_inside()` (référence)

```python
from pathlib import Path

def path_inside(child: str | Path, parent: str | Path) -> bool:
    """True si `child` résolu reste sous `parent` (anti path-traversal)."""
    parent = Path(parent).resolve()
    try:
        Path(child).resolve().relative_to(parent)
        return True
    except ValueError:
        return False
```
