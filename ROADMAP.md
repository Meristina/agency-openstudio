# Roadmap — Agency Studio

> **Status: Wave 0 implemented; Wave 1 GUI in progress.** The stdlib server, `on_event`
> hook, and React Mission Console are built and tested in a Linux session (the core).
> Waves **2-6**: target Apple Silicon (Metal) + model downloads → deferred to the Mac.

## Context

Local-first agentic studio: stack agency-kit (the *brain*: route → execute → synthesize →
inspect with veto) on top of a local multimodal layer (image / voice / RAG) inspired by
model runners (Uncensored-Local-Studio, GPT4All) — without inheriting Jan's AGPL, without
depending on a closed app (LM Studio), and with **zero marginal reasoning cost** via the
Claude CLI subscription.

Hardware framing: **Apple Silicon Mac, 16 GB**. The heavy LLM stays on **Opus via the
`claude` CLI** (`claude-code` engine); the local layer carries **only** multimodal + RAG,
loaded **mutually exclusively** (image and LLM never co-resident in memory).

### Corrections grounded in agency-kit's actual code

| Initial assumption | Verified reality | Consequence |
|---|---|---|
| "SSE by parsing the `print(...)`" | Parsing stdout would be fragile | **Clean hook (shipped)**: `run_mission_cli` takes an optional `on_event` param and fires `_emit(on_event, …)` at each milestone. Default `None` ⇒ current behavior preserved. |
| Reusing `serve.cjs`, scripts, Uncensored's React components | **Do not exist** in agency-kit (no `app/`, no `package.json`) | **External** ports = new hardened code. |
| `_call` handles HTTP | `_call` is **subprocess/argv-only** | `local` HTTP engine = separate dispatch path (wave 2+), disabled on 16 GB. |
| Server via Flask | agency-kit = **zero runtime dependencies** | Server in **`http.server` stdlib** (ThreadingHTTPServer), native SSE. |

**Non-negotiable**: the veto loop in `run_mission_cli` (MAX_ITERS=3, `_RETRY_VERDICTS`)
and `_short_verdict` do **not** change behavior (Constitution Art. IX). The `on_event`
hook is purely observational.

## Architecture (summary)

See [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for the full diagram and SSE flow.

```
React/Vite GUI (app/studio, 127.0.0.1)
   └─HTTP/SSE→ agency_studio/server.py (http.server stdlib, bind 127.0.0.1)
                  └─→ agency-kit CORE: run_mission_cli(goal, engine, on_event=…)
                         ├─ department tools: web search · image/TTS deliverable · RAG · MCP
                         └─ local inference (Metal, mutually exclusive): SD · Whisper · Kokoro · embeddings
```

---

## Build waves

### Wave 0 — Server foundation + event hook + security *(Linux-OK)* — **implemented**
1. **Minimal refactor** (`cli_engine.py`, **shipped in agency-kit**): `run_mission_cli`
   takes `on_event: Callable | None = None` and fires `_emit(on_event, …)` at each
   milestone, mapping 1:1 to events:
   - route done → `{"phase":"route","status":"done","route":[...]}`
   - dept start/done → `{"phase":"dept","dept":dept,"status":"start"|"done"}`
   - synth start/done → `{"phase":"synth","iteration":n,"status":...}`
   - inspect → `{"phase":"inspect","iteration":n,"verdict":token}`
   The veto loop and `_short_verdict` are **untouched**. Default `None` ⇒ tests stay green.
   `on_event` is threaded through `runner_bridge.run`.
2. **`agency_studio/server.py`**: `ThreadingHTTPServer` + `BaseHTTPRequestHandler` (stdlib).
   **bind `127.0.0.1`**. `POST /api/mission` (SSE) · `GET /api/missions` · `/api/mission/{id}`.
   Static GUI handler with a `path_inside()` guard. CORS local-only (no `*`).
3. **`agency-studio` entry point**: a standalone `agency_studio` package with its own
   `build_parser()`/`main()` (`agency_studio/cli.py`), registered as the `agency-studio`
   console script in `pyproject.toml`. It **imports** agency-kit (it does not modify
   agency-kit's `cli.py`). `--port` (8765), `--host` (`127.0.0.1`). `ImportError` →
   `pip install -e ".[studio]"`.
4. **`pyproject.toml`**: `studio` extra. Server = stdlib (nothing). The extra reserves the
   deps for waves 4+.
5. **`tests/test_server.py`**: mirror of `test_engine.py` (monkeypatch `_call` +
   `shutil.which`), assert the SSE stream (route/dept/synth/inspect/done) + that
   `missions/<id>/` is written. Security: `GET /../../etc/passwd` → 404.

### Wave 1 — Mission Console GUI (React + Vite) *(Linux-OK)*
- **`app/studio/`**: Vite + React 19. Build → `app/studio/dist/`, served by `server.py`.
- **Mission Console**: goal → Run → SSE → live timeline (route, dept start/done, synth
  iter, inspect+verdict) → Markdown render of dossier + deliverable. History via
  `GET /api/missions`.
- **PDF export**: `exporter.export_pdf(mission_id)` via `GET /api/mission/{id}/pdf` (`[pdf]` extra).
- Rich components (Sidebar, gallery, ModelManager) = **written fresh**.

**Post-review refinements (shipped):**
- **GUI polish**: cited sources rendered as safe (`noopener noreferrer`) links,
  history verdict badges, ⌘/Ctrl+Enter submit, live elapsed timer.
- **Server hardening** (`server.py`): request-body reads bounded by size **and** a
  socket read-timeout (slowloris); rejects close the socket with `Connection:
  close` (no keep-alive desync); chunked bodies refused; PDF render error → clean
  500; SPA fallback 404s a missing hashed asset instead of returning `index.html`
  as JS. Mission-folder allocation made atomic in agency-kit `serialize_dossier`
  (TOCTOU).
- ✅ **Project-scoped history** *(was deferred — done)*: each mission is stamped
  with its `project_root`; `store.list_missions(project_root=…)` and the server's
  GET-by-id / PDF scope to the launched `--path`, so the GUI shows only this
  project's missions (pre-feature unstamped missions stay visible). The
  `agency missions` CLI still lists all (unchanged).
- ✅ **Mission "Stop mission"** *(real server-side cancellation — shipped)*: the
  button (formerly "Stop watching") now triggers a **cooperative** server-side
  cancel. Aborting the fetch drops the SSE connection; the server sets a
  `cancel_event` that the worker polls via a new `should_cancel` predicate on
  `run_mission_cli`, checked at **phase boundaries only** (after routing, before
  each department, before each synth→inspect iteration — **never** inside a started
  synth→inspect cycle, so the veto loop is byte-identical and Art. IX holds). On
  cancel it raises `MissionCancelled` **before** any persistence, so a stopped
  mission usually leaves no trace, and the abandoned-worker leak is fixed.
  It is **best-effort, not a kill**: an in-flight engine call and the *final*
  synth→inspect cycle complete first, so a stop that lands in that last window still
  finishes and persists — the GUI notice says so honestly (Refresh + check History).
  Remaining future work: immediate subprocess termination (kill the in-flight
  `Popen`) and an explicit cancel endpoint with a run-id, to close the best-effort
  window.

### Wave 2 — Local multimodal inference, hardened *(Mac/Metal — deferred)*
- **`agency_studio/engines/local_media.py`**: spawn SD/Whisper/Kokoro, **Metal only**,
  **mutually exclusive** image↔LLM loading.
- Mac arm64 backend setup; models **git-ignored**; validate URLs + **checksums**.
- Endpoints `POST /api/image` · `/api/tts` · `/api/stt`. GUI: Image/Voice tabs.
- Optional `local` HTTP engine (disabled on 16 GB): separate dispatch path.

### Wave 3 — Multimodal as a *department deliverable* *(Mac/Metal — deferred)*
- Hook in agency-kit's `_dept_prompt` + post-processing that detects an asset
  request (campaign image, TTS narration) → `local_media`. Assets in `missions/<id>/assets/`.

### Wave 4 — RAG / LocalDocs *(model downloads — deferred)*
- **Ingestion via `microsoft/markitdown`** (MIT) → Markdown. In the `[studio]` extra.
- **`agency_studio/rag.py`**: markitdown → chunking → embeddings (nomic-embed via llama.cpp)
  → **SQLite vector store**. Endpoint `/api/docs` + inject relevant chunks into `_dept_prompt`.
- ❌ Not `chunkr` (AGPL + Rust/Docker too heavy).

### Wave 5 — Local web search + MCP *(deferred)*
- **`agency_studio/websearch.py`** (DuckDuckGo, fresh code): sourcing for the optional local
  path (the Claude path already has WebSearch). Satisfies Art. I offline.
- **`agency_studio/mcp_client.py`**: MCP client, MIT, inspired by Jan **without reusing its code**.

### Wave 6 — Advanced extensions (plug-ins behind flags, MIT/Apache) *(deferred)*
- `hyper-extract` (Apache-2.0) → `agency_studio/knowledge.py`: knowledge graphs over docs + history.
- `agency-agents` (MIT): **curated** import of personas as additional doctrine (respect
  `DEPT_NAMES` + the payload drift guard).
- `PixelRAG` (Apache-2.0): visual RAG **cloud/opt-in** (Qwen3-VL via API).
- `seedance-2.0` (MIT): **cloud video** modality as a department tool.
- 📚 `awesome-llm-apps`: inspiration catalog, not a dependency.

---

## Files (during implementation)

**Built (Wave 0)**: `agency_studio/server.py` · `agency_studio/cli.py` · `app/studio/` ·
`tests/` · `pyproject.toml` (`agency-studio` script + `[studio]` extra).
**Deferred** (will live under `agency_studio/`): `engines/local_media.py` · `rag.py` ·
`websearch.py` · `mcp_client.py` · `knowledge.py`.

**As-built launcher**: `agency_studio` is a **standalone package** with its own
`build_parser()`/`main()` and a separate `agency-studio` console script. It **imports**
agency-kit (`cli_engine`/`runner_bridge`/`store`/…); agency-kit's `cli.py` is **not**
modified — there is no `_cmd_studio` in agency-kit.

**Reused from agency-kit (already shipped)**: `cli_engine.run_mission_cli` (`on_event`
param via `_emit`) · `runner_bridge.run` (threads `on_event`).

**To reuse as-is**: `runner_bridge.serialize_dossier`/`run`/`MissionResult` ·
`store.{list_missions,load,save,new_mission_id}` · `departments.{DEPT_NAMES,dependency_layers}` ·
`exporter.export_pdf`.

## Verification

**Waves 0-1 (testable now, Linux):**
1. `pip install -e ".[studio]"` then `agency check`.
2. `pytest tests/ -q` stays **green** (default `on_event=None`) + `tests/test_server.py`.
3. `agency-studio` → goal → live SSE timeline → `missions/<id>/{dossier,deliverable}.md`.
4. Security: `curl --path-as-is http://127.0.0.1:<port>/../../../../etc/passwd` → 404 ;
   `lsof -iTCP -sTCP:LISTEN | grep <port>` → **127.0.0.1 only**.

**Waves 2+ (deferred, Mac):**
5. `POST /api/image|/api/tts|/api/stt` produce assets; image and LLM never loaded together.
6. RAG: ingest a doc, run a mission, **sourced** excerpts from the doc appear in a deliverable.
