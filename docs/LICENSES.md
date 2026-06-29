# Licences des composants tiers — Agency Studio

**Discipline** : Agency Studio est **MIT**. On ne réemploie/porte que du code
**MIT ou Apache-2.0**. Tout composant **AGPL** est **écarté** (licence virale qui
contaminerait l'ensemble du projet) — on n'en emprunte que les *concepts*, jamais le code.

## Composants évalués

| Composant | Rôle envisagé | Licence | Décision |
|---|---|---|---|
| **agency-kit** | Noyau d'orchestration (réemployé) | MIT | ✅ Cœur du projet |
| **Uncensored-Local-Studio** | Patterns multimodal local (SD/Whisper/Kokoro) | MIT | ✅ Patterns réemployés, **code durci** (pas son serveur troué) |
| **GPT4All** | Pattern LocalDocs / RAG | MIT | ✅ Concept réemployé |
| **microsoft/markitdown** | Ingestion documents → Markdown (Vague 4) | MIT | ✅ Dépendance directe |
| **hyper-extract** | Graphes de connaissances (Vague 6) | Apache-2.0 | ✅ Plug-in optionnel |
| **agency-agents** | Personas de doctrine (Vague 6) | MIT | ✅ Import curé |
| **PixelRAG** | RAG visuel (Vague 6, cloud) | Apache-2.0 | ✅ Mode opt-in |
| **seedance-2.0** | Modalité vidéo (Vague 6, cloud) | MIT | ✅ Mode cloud |
| **awesome-llm-apps** | Catalogue d'inspiration | Apache-2.0 | 📚 Référence, pas une dépendance |
| **Jan** | Runner LLM mûr (MCP, OpenAI-compat) | **AGPL-3.0** | ❌ Concepts seulement, **jamais le code** |
| **chunkr** | OCR/chunking documents | **AGPL-3.0** | ❌ Écarté (AGPL + service Rust/Docker lourd) |
| **LM Studio** | Runner LLM | Propriétaire | ❌ Fermé, non réutilisable |

## Règle pour les contributeurs / agents

Avant d'ajouter une dépendance ou de porter du code tiers : **vérifier la licence**.
Si elle n'est pas MIT/Apache-2.0/BSD/ISC (ou équivalent permissif), ne pas l'intégrer —
ouvrir une discussion. En cas de doute sur de l'AGPL/GPL : **concepts uniquement**.

## Attribution

Les portages de code MIT/Apache conservent leur notice de copyright d'origine dans les
fichiers concernés, conformément aux termes de ces licences.
