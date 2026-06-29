# Roadmap — Agency Studio

> **Statut : ROADMAP (plan-only).** Aucune implémentation dans ce repo pour l'instant.
> Vagues **0-1** : constructibles/testables en session Linux (le cœur). Vagues **2-6** :
> ciblent Apple Silicon (Metal) + téléchargements de modèles → exécution différée sur le Mac.

## Contexte

Studio agentique local-first : empiler agency-kit (le *cerveau* : route → execute →
synthesize → inspect avec veto) au-dessus d'une couche multimodale locale (image / voix /
RAG) inspirée des runners de modèle (Uncensored-Local-Studio, GPT4All) — sans hériter de
l'AGPL de Jan, sans dépendre d'une app fermée (LM Studio), coût marginal du raisonnement
**nul** via l'abonnement Claude CLI.

Cadrage matériel : **Mac Apple Silicon 16 Go**. Le LLM lourd reste sur **Opus via le CLI
`claude`** (engine `claude-code`) ; le local ne porte **que** le multimodal + RAG,
chargés **mutuellement exclusifs** (jamais image + LLM en mémoire ensemble).

### Corrections ancrées dans le vrai code d'agency-kit

| Hypothèse initiale | Réalité vérifiée | Conséquence |
|---|---|---|
| « SSE en parsant les `print(...)` » | Progression = `print(..., flush=True)` dans `run_mission_cli` (cli_engine.py:251-275) — parser stdout serait fragile | **Hook propre** : param `on_event` optionnel ; prints mappent 1:1. Défaut `None` ⇒ comportement actuel préservé. |
| Réemploi de `serve.cjs`, scripts, composants React d'Uncensored | **N'existent pas** dans agency-kit (pas de `app/`, pas de `package.json`) | Portages **externes** = code neuf durci. |
| `_call` gère du HTTP | `_call` est **subprocess/argv-only** | Engine `local` HTTP = chemin de dispatch séparé (vague 2+), désactivé sur 16 Go. |
| Serveur via Flask | agency-kit = **zéro dépendance runtime** | Serveur en **`http.server` stdlib** (ThreadingHTTPServer), SSE natif. |

**Non négociable** : la boucle veto de `run_mission_cli` (MAX_ITERS=3, `_RETRY_VERDICTS`)
et `_short_verdict` ne changent **pas** de logique (Art. IX). Le hook `on_event` est
purement observationnel.

## Architecture (résumé)

Voir [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) pour le schéma complet et le flux SSE.

```
GUI React/Vite (app/studio, 127.0.0.1)
   └─HTTP/SSE→ agency_cli/server.py (http.server stdlib, bind 127.0.0.1)
                  └─→ NOYAU agency-kit : run_mission_cli(goal, engine, on_event=…)
                         ├─ outils départements : web search · image/TTS livrable · RAG · MCP
                         └─ inférence locale (Metal, mut. exclusif) : SD · Whisper · Kokoro · embeddings
```

---

## Vagues de construction

### Vague 0 — Socle serveur + hook d'événements + sécurité *(Linux-OK)*
1. **Refactor minimal** (`cli_engine.py`) : param `on_event: Callable | None = None` sur
   `run_mission_cli`. À chaque jalon (un `print` aujourd'hui), appeler aussi `on_event` :
   - 251/253 → `{"phase":"route","status":"done","route":[...]}`
   - 257/259 → `{"phase":"dept","dept":dept,"status":"start"|"done"}`
   - 268/270 → `{"phase":"synth","iteration":n,"status":...}`
   - 272/275 → `{"phase":"inspect","iteration":n,"verdict":token}`
   **Ne pas toucher** la boucle veto ni `_short_verdict`. Défaut `None` ⇒ tests verts.
   Threader `on_event` dans `runner_bridge.run`.
2. **`agency_cli/server.py`** : `ThreadingHTTPServer` + `BaseHTTPRequestHandler` (stdlib).
   **bind `127.0.0.1`**. `POST /api/mission` (SSE) · `GET /api/missions` · `/api/mission/{id}`.
   Static handler GUI avec garde `path_inside()`. CORS local uniquement (pas de `*`).
3. **Sous-commande `agency studio`** (`cli.py`) : calquer `_cmd_tui` + parser `tui`.
   `--port` (8765), `--host` (`127.0.0.1`). `ImportError` → `pip install -e ".[studio]"`.
4. **`pyproject.toml`** : extra `studio`. Serveur = stdlib (rien). Extra réserve les deps des vagues 4+.
5. **`tests/test_server.py`** : mirror de `test_engine.py` (monkeypatch `_call` + `shutil.which`),
   asserte le flux SSE (route/dept/synth/inspect/done) + écriture `missions/<id>/`.
   Sécurité : `GET /../../etc/passwd` → 404.

### Vague 1 — GUI Mission Console (React + Vite) *(Linux-OK)*
- **`app/studio/`** : Vite + React 19. Build → `app/studio/dist/`, servi par `server.py`.
- **Mission Console** : goal → Run → SSE → timeline live (route, dept start/done, synth iter,
  inspect+verdict) → rendu Markdown dossier + livrable. Historique via `GET /api/missions`.
- **Export PDF** : `exporter.export_pdf(mission_id)` via `GET /api/mission/{id}/pdf` (extra `[pdf]`).
- Composants riches (Sidebar, gallery, ModelManager) = **réécrits neufs**.

### Vague 2 — Inférence locale multimodale, durcie *(Mac/Metal — différé)*
- **`agency_cli/engines/local_media.py`** : spawn SD/Whisper/Kokoro, **Metal only**,
  chargement **mutuellement exclusif** image↔LLM.
- Setup backends Mac arm64 ; modèles **git-ignored** ; valider URLs + **checksums**.
- Endpoints `POST /api/image` · `/api/tts` · `/api/stt`. GUI : onglets Image/Voix.
- Engine `local` HTTP optionnel (désactivé 16 Go) : chemin de dispatch séparé.

### Vague 3 — Multimodal comme *livrable de département* *(Mac/Metal — différé)*
- Hook dans `_dept_prompt` (cli_engine.py:182) + post-traitement détectant une demande
  d'asset (image campagne, narration TTS) → `local_media`. Assets dans `missions/<id>/assets/`.

### Vague 4 — RAG / LocalDocs *(téléchargements modèles — différé)*
- **Ingestion via `microsoft/markitdown`** (MIT) → Markdown. Dans l'extra `[studio]`.
- **`agency_cli/rag.py`** : markitdown → chunking → embeddings (nomic-embed via llama.cpp)
  → **store vectoriel SQLite**. Endpoint `/api/docs` + injection des chunks dans `_dept_prompt`.
- ❌ Pas `chunkr` (AGPL + Rust/Docker trop lourd).

### Vague 5 — Web search local + MCP *(différé)*
- **`agency_cli/websearch.py`** (DuckDuckGo, code neuf) : sourcing pour le chemin local
  optionnel (le chemin Claude a déjà WebSearch). Satisfait Art. I hors-ligne.
- **`agency_cli/mcp_client.py`** : client MCP, MIT, inspiré de Jan **sans réutiliser son code**.

### Vague 6 — Extensions avancées (plug-ins derrière flags, MIT/Apache) *(différé)*
- `hyper-extract` (Apache-2.0) → `agency_cli/knowledge.py` : graphes de connaissances sur docs + historique.
- `agency-agents` (MIT) : import **curé** de personas comme doctrine additionnelle (respecter `DEPT_NAMES` + garde de drift payload).
- `PixelRAG` (Apache-2.0) : RAG visuel **cloud/opt-in** (Qwen3-VL via API).
- `seedance-2.0` (MIT) : modalité **vidéo cloud** comme tool de département.
- 📚 `awesome-llm-apps` : catalogue d'inspiration, pas une dépendance.

---

## Fichiers (lors de l'implémentation)

**À créer** : `agency_cli/server.py` · `app/studio/` · `tests/test_server.py` · (différés)
`engines/local_media.py` · `rag.py` · `websearch.py` · `mcp_client.py` · `knowledge.py`.

**À modifier dans agency-kit** : `cli_engine.py` (param `on_event`) · `runner_bridge.py`
(threader `on_event`) · `cli.py` (`_cmd_studio` + parser) · `pyproject.toml` (extra `[studio]`).

**À réemployer tel quel** : `runner_bridge.serialize_dossier`/`run`/`MissionResult` ·
`store.{list_missions,load,save,new_mission_id}` · `departments.{DEPT_NAMES,dependency_layers}` ·
`exporter.export_pdf`.

## Vérification

**Vagues 0-1 (testable, Linux) :**
1. `pip install -e ".[studio]"` puis `agency check`.
2. `pytest tests/ -q` reste **vert** (défaut `on_event=None`) + `tests/test_server.py`.
3. `agency studio` → goal → timeline SSE en direct → `missions/<id>/{dossier,deliverable}.md`.
4. Sécurité : `curl --path-as-is http://127.0.0.1:<port>/../../../../etc/passwd` → 404 ;
   `lsof -iTCP -sTCP:LISTEN | grep <port>` → **127.0.0.1 only**.

**Vagues 2+ (différé, Mac) :**
5. `POST /api/image|/api/tts|/api/stt` produisent des assets ; image et LLM jamais chargés ensemble.
6. RAG : ingérer un doc, lancer une mission, extraits **sourcés** du doc dans un livrable.
