# Architecture — Agency Studio

> Cible. Aucun de ces fichiers n'existe encore (repo en scaffold). Voir `ROADMAP.md`
> pour l'ordre de construction.

## Vue empilée

Agency Studio n'est pas un runner de modèle de plus — c'est **l'étage d'orchestration**
posé au-dessus. Trois couches :

```
┌─ app/studio/ — React 19 + Vite (servi sur 127.0.0.1) ──────────────┐
│  Mission Console : goal → timeline live (SSE) → dossier + livrable  │
│  + Gallery images · Lecteur TTS · Model Manager · Docs/RAG          │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼  HTTP / SSE
┌─ agency_cli/server.py — http.server stdlib, bind 127.0.0.1 ────────┐
│  POST /api/mission (SSE) · GET /api/missions · /api/mission/{id}    │
│  /api/image · /api/tts · /api/stt · /api/docs · /api/models         │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼
┌─ NOYAU agency-kit — logique INCHANGÉE ─────────────────────────────┐
│  run_mission_cli(goal, engine, on_event=…) route→exec→synth→inspect │
│  runner_bridge: serialize_dossier · store.save                      │
└──────────┬───────────────────────┬─────────────────────────────────┘
           ▼                       ▼
   OUTILS départements      INFÉRENCE LOCALE (multimodal only, Metal)
   • web search (Claude       • SD · Whisper · Kokoro (mut. exclusif)
     WebSearch déjà câblé)    • rag.py: markitdown → embeddings → SQLite
   • image/TTS = livrable     • mcp_client (idées Jan, code neuf MIT)
```

## Couche 1 — Cerveau (agency-kit, réemployé)

Le cœur reste agency-kit, **inchangé dans sa logique** :
- `run_mission_cli(goal, engine)` : route → execute (9 départements) → synthesize →
  inspect (boucle veto, `MAX_ITERS=3`).
- Engine par défaut `claude-code` → Opus via l'abonnement Claude CLI (coût nul).
- `runner_bridge.serialize_dossier` / `run` persistent la mission ; `store` la liste/charge.

**Seule extension** : un callback **observationnel** `on_event` sur `run_mission_cli`,
pour streamer la progression vers la GUI. Les `print(..., flush=True)` actuels
(cli_engine.py:251-275) mappent 1:1 vers des events. Défaut `None` ⇒ comportement
identique à aujourd'hui. La boucle veto et `_short_verdict` ne changent **pas**.

## Couche 2 — Serveur (neuf, stdlib)

`agency_cli/server.py` = `ThreadingHTTPServer` (Python stdlib, **zéro dépendance**).
Bind **`127.0.0.1`** strict. Sert l'API + la GUI buildée (`app/studio/dist/`) avec une
garde `path_inside()` sur le static handler.

## Couche 3 — Inférence locale (neuf, Metal, différé)

Wrappers subprocess autour de stable-diffusion.cpp / whisper.cpp / Kokoro, ciblés
Apple Silicon. Chargement **mutuellement exclusif** image↔LLM (contrainte 16 Go).

## Flux de streaming (la pièce maîtresse)

```
Browser ──POST /api/mission──▶ server.py
                                 │ run_mission_cli(goal, engine, on_event=push)
                                 │   route done ─────────────▶ event "route"
                                 │   dept start/done (×N) ───▶ events "dept"
                                 │   synth (×iter) ──────────▶ events "synth"
                                 │   inspect verdict ────────▶ events "inspect"
                                 ▼ à la fin
                              serialize_dossier + store.save
                                 └─▶ event "done" {mission_id, path}
Browser ◀──SSE (text/event-stream)──┘  (timeline live, puis rendu dossier+livrable)
```

## Pourquoi ce découpage

- **Coût** : raisonnement sur abonnement (gratuit à la marge), local seulement pour le
  multimodal → tient sur 16 Go.
- **Sécurité** : un seul point d'entrée réseau, en `127.0.0.1`, durci dès le départ.
- **Réemploi** : on ne réécrit pas agency-kit ; on l'enveloppe.
- **Licence** : tout MIT/Apache (voir `docs/LICENSES.md`).
