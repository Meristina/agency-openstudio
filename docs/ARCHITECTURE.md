# Architecture — Agency Studio

> Target state. Waves 0-3 are implemented: the stdlib server + `on_event` hook, the React
> Mission Console, the **local multimodal layer (image / STT / TTS on Metal)** — validated
> live on an M4 — and **multimodal as a department deliverable** (assets rendered into the
> dossier + gallery + PDF). **Wave 4 (RAG / LocalDocs) core is implemented** — `/api/docs`
> ingestion, `rag.py` (markitdown → embeddings → `sqlite-vec`), and the `context_clause`
> retrieval hook (GUI "Docs" tab deferred). The remaining layers (Waves 5-6: web search, MCP,
> extensions; plus Wave-6 visual RAG / knowledge graphs) are still deferred. See `ROADMAP.md`.

## Stacked view

Agency Studio is not one more model runner — it's the **orchestration layer** placed on
top. Three layers:

```
┌─ app/studio/ — React 19 + Vite (served on 127.0.0.1) ──────────────┐
│  Mission Console: goal → live timeline (SSE) → dossier + deliverable│
│  + Image gallery · TTS player · Model Manager · Docs/RAG            │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼  HTTP / SSE
┌─ agency_studio/server.py — http.server stdlib, bind 127.0.0.1 ─────┐
│  POST /api/mission · GET /api/missions · /api/mission/{id} (+ /pdf) │
│  Wave 2 (shipped): POST /api/{image,tts,stt} · GET /api/models      │
│                    · /media/<asset> (path_inside-guarded)           │
│  Wave 4 (shipped): POST/GET/DELETE /api/docs (RAG) + context_clause │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼
┌─ agency-kit CORE — logic UNCHANGED ────────────────────────────────┐
│  run_mission_cli(goal, engine, on_event=…) route→exec→synth→inspect │
│  runner_bridge: serialize_dossier · store.save                      │
└──────────┬───────────────────────┬─────────────────────────────────┘
           ▼                       ▼
   department tools         LOCAL INFERENCE (multimodal only, Metal)
   • web search (Claude       • FLUX · Whisper · Kokoro · embeddings (warm, mutually excl.) ✅
     WebSearch already wired) • rag.py: markitdown → MLX embeddings → sqlite-vec (Wave 4) ✅
   • image/TTS = deliverable  • mcp_client (Jan ideas, fresh MIT code) (Wave 5)
     (Wave 3)
```

## Layer 1 — Brain (agency-kit, reused)

The core stays agency-kit, **logic unchanged**:
- `run_mission_cli(goal, engine)`: route → execute (9 departments) → synthesize →
  inspect (veto loop, `MAX_ITERS=3`).
- Default engine `claude-code` → Opus via the Claude CLI subscription (zero cost).
- `runner_bridge.serialize_dossier` / `run` persist the mission; `store` lists/loads it.

**The only extension**: an **observational** `on_event` callback on `run_mission_cli`, to
stream progress to the GUI. It is already implemented in agency-kit — `_emit(on_event, …)`
fires at each milestone (route / dept / synth / inspect). Default `None` ⇒ behavior
identical to today. The veto loop and `_short_verdict` do **not** change.

## Layer 2 — Server (new, stdlib)

`agency_studio/server.py` = `ThreadingHTTPServer` (Python stdlib, **zero dependencies**).
Strict **`127.0.0.1`** bind. Serves the API + the built GUI (`app/studio/dist/`) with a
`path_inside()` guard on the static handler.

## Layer 3 — Local inference (Wave 2, Metal — shipped)

`agency_studio/engines/local_media.py` — a warm single-resident `ModelManager` over
MLX-native back-ends: **FLUX.1-schnell** (mflux, image), **Whisper large-v3-turbo**
(mlx-whisper, STT), **Kokoro-82M** (kokoro-onnx, TTS). At most one model is resident; a
model is kept **warm** for fast repeats and **evicted** (freeing the Metal buffer cache)
only when switching modality — so image and a local LLM are never co-resident (the 16 GB
constraint; the local LLM engine stays off). Weights resolve through `models.py` with the
URL-allowlist + SHA-256 / content-addressed-cache integrity guards (see `docs/SECURITY.md`).
All back-ends are lazy-imported behind the `[media]` extra; absent ⇒ a clean 501.

## Streaming flow (the centerpiece)

```
Browser ──POST /api/mission──▶ server.py
                                 │ run_mission_cli(goal, engine, on_event=push)
                                 │   route done ─────────────▶ event "route"
                                 │   dept start/done (×N) ───▶ events "dept"
                                 │   synth (×iter) ──────────▶ events "synth"
                                 │   inspect verdict ────────▶ events "inspect"
                                 ▼ at the end
                              serialize_dossier + store.save
                                 └─▶ event "done" {mission_id, verdict, path, residual_risk}
Browser ◀──SSE (text/event-stream)──┘  (live timeline, then dossier+deliverable render)
```

## Why this split

- **Cost**: reasoning on the subscription (free at the margin), local only for multimodal
  → fits in 16 GB.
- **Security**: a single network entry point, on `127.0.0.1`, hardened from the start.
- **Reuse**: we don't rewrite agency-kit; we wrap it.
- **License**: everything MIT/Apache (see `docs/LICENSES.md`).
