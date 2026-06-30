# Architecture — Agency Studio

> Target state. Wave 0 (the stdlib server, `on_event` hook, and React Mission Console) is
> implemented; the local-inference layer (Waves 2-6) is still deferred. See `ROADMAP.md`
> for the build order.

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
│  Wave 2+ (deferred): /api/{image,tts,stt,docs,models}               │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼
┌─ agency-kit CORE — logic UNCHANGED ────────────────────────────────┐
│  run_mission_cli(goal, engine, on_event=…) route→exec→synth→inspect │
│  runner_bridge: serialize_dossier · store.save                      │
└──────────┬───────────────────────┬─────────────────────────────────┘
           ▼                       ▼
   department tools         LOCAL INFERENCE (multimodal only, Metal)
   • web search (Claude       • SD · Whisper · Kokoro (mutually exclusive)
     WebSearch already wired) • rag.py: markitdown → embeddings → SQLite
   • image/TTS = deliverable  • mcp_client (Jan ideas, fresh MIT code)
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

## Layer 3 — Local inference (new, Metal, deferred)

Subprocess wrappers around stable-diffusion.cpp / whisper.cpp / Kokoro, targeting Apple
Silicon. **Mutually exclusive** image↔LLM loading (16 GB constraint).

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
