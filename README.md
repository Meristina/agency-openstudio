# Agency OpenStudio — l'agence 360 ultime

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](./LICENSE)

**Une agence multimédia, B2B et événementielle complète, pilotée par des agents CLI sur
abonnement mensuel — zéro coût marginal par mission.** L'utilisateur entre dans une
« boîte magique » : il décrit ce qu'il veut (une recherche, une stratégie, une campagne,
une vidéo, un événement…) et l'agence recherche sur internet, décide, produit et exporte
le livrable — du brief à la vidéo finale.

## Les trois piliers (un seul dépôt, autonome)

| Pilier | Répertoire | Rôle |
|---|---|---|
| **agency-kit** (fork studio) | [`agencykit/`](./agencykit/) | Le cerveau : route → 9 départements métiers (solve, product, marketing, finance, comms, data, ops, people, tech) → synthèse → inspecteur avec veto. Multi-moteurs : claude-code / codex / gemini. Recherche internet obligatoire, sources citées. |
| **OpenMontage** | [`openmontage/`](./openmontage/) | La production : 122 outils (locaux gratuits / GPU / API payantes), 13 pipelines vidéo, rendu Remotion + HyperFrames. |
| **Le studio** | [`agency_studio/`](./agency_studio/) + [`app/studio/`](./app/studio/) | Le serveur local (Python stdlib, zéro dépendance), les moteurs multimodaux locaux (image, voix, RAG, vidéo) et l'interface web. |

## Démarrage

```bash
# 1. Le venv + le cerveau (le fork agency-kit vendored) + le studio
python3 -m venv .venv && source .venv/bin/activate
pip install -e ./agencykit
pip install -e .

# 2. Un agent CLI sur PATH (le moteur v1 validé est claude)
#    claude / codex / gemini — voir agencykit/README.md

# 3. Lancer
agency-studio          # (alias : agency-openstudio) → http://127.0.0.1:8765
```

Extras optionnels (chargés paresseusement ; absents ⇒ 501 propre + hint) :
`[media]` image/STT/TTS Apple Silicon · `[studio]` RAG · `[web]` recherche web ·
`[mcp]` ressources MCP · `[visual]` RAG visuel · `[pdf]` export. La vidéo locale
(OpenMontage/Remotion) demande Node 18+ et un `npm install` unique dans
`openmontage/remotion-composer/` (`AGENCY_STUDIO_VIDEO_BACKEND=openmontage-remotion`).

## La feuille de route

Le développement suit **[`PLAN.md`](./PLAN.md)** — bricks 0 à 9, chacun un cycle
**spec-kit** complet (constitution → specify → plan → tasks → implement). Gouvernance :
la constitution spec-kit (`.specify/memory/constitution.md`) ; contexte agents :
[`AGENTS.md`](./AGENTS.md) (canonique — `CLAUDE.md` est un symlink).

## Licence

**AGPL-3.0-only** (l'œuvre combinée, depuis la fusion OpenMontage). Le code
agency-studio pré-fusion reste disponible sous MIT ([`LICENSE.MIT`](./LICENSE.MIT)).
Composants tiers : [`docs/LICENSES.md`](./docs/LICENSES.md). Décision de fusion :
[`docs/OPENMONTAGE-FUSION.md`](./docs/OPENMONTAGE-FUSION.md). Historique pré-fusion
(Waves 0–6) : [`docs/legacy/`](./docs/legacy/).
