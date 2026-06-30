# Roadmap — Agency Studio

> **Status: Waves 0-2 shipped.** Core (0-1): the stdlib server + `on_event`/
> `should_cancel` hooks and the React Mission Console (live SSE timeline, project-scoped
> history, PDF export, full "Stop mission"). **Wave 2 — local multimodal (image / STT /
> TTS) on Apple Silicon (Metal)** is built, reviewed, and **validated live on the target
> Mac (M4, 16 GB)** end-to-end through the HTTP server: the `local_media` warm
> `ModelManager`, integrity-checked `models` resolution, the `/api/image|/api/tts|/api/stt`
> + `/api/models` endpoints with `/media/` asset serving, and the GUI's Image/Voice tabs +
> gallery + warm-model chip (the former deferred gallery/ModelManager surface).
> Waves **3-6** (multimodal-as-deliverable, RAG, web search, MCP, extensions) remain
> deferred. Setup for Wave 2: Python 3.10+ venv + `[media]` extra + system `ffmpeg` (STT);
> image defaults to a non-gated 8-bit FLUX.1-schnell mirror (no HF login).

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
                         └─ local inference (Metal, mutually exclusive): FLUX · Whisper · Kokoro · embeddings
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
- **PDF export**: `exporter.export_pdf(mission_id)` via `GET /api/mission/{id}/pdf` (`[pdf]` extra). ✅
- Rich components: the **History sidebar** is built ✅. The **gallery** (generated
  assets) and a **warm-model status chip** (the lightweight ModelManager surface) shipped
  in **Wave 2** ✅ alongside the FLUX/Whisper/Kokoro layer they front.

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
  button (formerly "Stop watching") triggers a server-side cancel. Aborting the
  fetch closes the SSE connection; the server sets a `cancel_event` that the worker
  polls via a `should_cancel` predicate on `run_mission_cli`, checked at **phase
  boundaries** (after routing, before each department, before each synth→inspect
  iteration) as a no-spend early-exit. On cancel it raises `MissionCancelled`
  **before** any persistence, so a stopped mission leaves no trace and the
  abandoned-worker leak is fixed.
- ✅ **v2 — immediate subprocess kill** *(closes the best-effort window — shipped)*:
  `should_cancel` is now also polled **inside `_call`**, which runs the child under
  a reader thread (`communicate` drains both pipes) and, the moment a cancel lands,
  kills the child's **whole process group** (`start_new_session=True` +
  `killpg` SIGTERM→SIGKILL — so the `claude` node wrapper's child tree dies too, not
  just the direct child) and raises `MissionCancelled`. A Stop no longer waits up to
  the per-call timeout. The server makes the kill reachable during a long,
  event-silent call by emitting a periodic SSE-comment **heartbeat**
  (`_write_heartbeat`): a failed write is the reliable "client gone" signal (the GUI
  aborted the fetch), which sets `cancel_event`. **Art. IX holds**: an aborted
  mission yields **no dossier**, so no verdict is altered and no un-inspected result
  ships — the veto loop's logic is byte-identical; only an abort can now happen
  mid-call. Trade-off (by design): a Stop landing in the *final* synth→inspect window
  now discards that nearly-finished run instead of persisting it — the deliberate
  cost of an immediate, no-trace cancel.
- ✅ **v3 — explicit cancel endpoint with a run-id** *(shipped)*: each run is
  registered under an ephemeral `run_id` (uuid4) in an in-memory registry on the
  server, announced as the first SSE frame `{"phase":"run","run_id":…}`.
  `POST /api/mission/{run_id}/cancel` sets that run's `cancel_event` (202) — an
  unknown/finished/malformed id is a 404 — so the GUI can stop a run **without
  relying on the connection drop**. When a cancel lands while the client is still
  connected, the stream ends with a `{"phase":"cancelled"}` terminal frame. The
  Mission Console's "Stop mission" now calls the endpoint (falling back to aborting
  the fetch if the run-id hasn't arrived yet or the call fails — the heartbeat path
  then cancels the same way), and the notice is honest: *stopped — cancelled before
  saving*. With the immediate kill + no-persist, the only window that could still
  persist is the microsecond after the final step returns.
  Remaining future work: none for Stop — the loop is closed. (A natural next
  extension, if ever needed: surface in-flight runs in the GUI so a run can be
  cancelled from another tab/device.)

### Wave 2 — Local multimodal inference, hardened *(Mac/Metal)* — **shipped**
Built, reviewed (high-effort `/code-review` per brick), and **validated live on the
target Mac (M4, 16 GB, Python 3.12)** end-to-end through the HTTP server.

- ✅ **`agency_studio/engines/local_media.py`** — warm single-resident `ModelManager`.
  The heavy LLM runs remotely (Claude CLI), so it never occupies local RAM; only the
  multimodal models compete, and they stay **warm** for fast repeats. At most one model
  is resident — switching modality (image ↔ voice) **evicts** the previous and frees the
  Metal buffer cache. A cheap import **probe before eviction** means a request for an
  uninstalled modality never destroys a working warm model. A lock serialises Metal use.
  - **image** — a **selectable** model (registry in `models.py`, GUI dropdown): **FLUX.1-
    schnell** (default, 8-bit mirror) and **FLUX.2-klein-4B** (modern, distilled, 8-bit) —
    both mflux-native, non-gated, Apache-2.0, and **live-validated on the 16 GB M4** — plus
    an **experimental Boogu-Image-0.1** entry on a separate `"boogu"` backend (the
    `[boogu]` extra: a git-installed community MLX port + a Qwen3-VL-8B conditioner;
    highest quality but slow, minutes/image). The backend dispatch is a pluggable
    `(probe, load, run)` triple, so mflux and non-mflux engines coexist.
    *(Z-Image-Turbo was evaluated and **dropped** — it crashes with a Metal GPU timeout
    on the 16 GB M4 even quantized at 256²/4 steps; not viable here.)*
    **STT** — Whisper large-v3-turbo
    via **mlx-whisper** (MIT); **TTS** — Kokoro-82M via **kokoro-onnx** (MIT). All
    lazy-imported behind the `[media]` extra; `MediaUnavailable` (an `ImportError`) →
    clean **501**.
- ✅ **`agency_studio/engines/models.py`** — integrity-checked model resolution. Hub
  models (mflux/whisper) ride HF's content-addressed cache; the two direct Kokoro files
  are pinned by URL (https + host **allowlist**, re-validated on **every redirect hop**)
  and **SHA-256**, verified on **every load** (cache hits included). Weights live in the
  OS cache (~18 GB), never in the repo.
- ✅ **Endpoints** `POST /api/image` (optional `model` id) · `/api/tts` · `/api/stt` ·
  `GET /api/models` (lists `image_models` + the warm `resident`), with generated assets
  served read-only under `/media/` (`path_inside()`-guarded). Image params are
  range-checked per-model (`steps_max`; no unbounded-compute OOM); STT streams the upload to disk in
  bounded chunks; back-end/model-fetch failures are 5xx, input errors 400.
- ✅ **GUI** — Image/Voice **tabs**, a session **gallery**, and a warm-model **status
  chip** (the former deferred Wave-1 gallery/ModelManager surface). Full ARIA tab
  pattern; views stay mounted so a tab switch never tears down a running mission.
- **Model access**: the official `black-forest-labs/FLUX.1-schnell` HF repo is **gated**
  (license + login). The default is therefore a **non-gated, pre-quantized 8-bit mflux
  mirror** (`dhairyashil/FLUX.1-schnell-mflux-8bit`, Apache-2.0 — the repo mflux's own
  docs point to). 8-bit keeps quality visibly on par with full precision; 4-bit deviates.
- **System dependency**: STT needs **`ffmpeg`** on PATH (`mlx-whisper` shells out to it).
- **Deferred (by design)**: the optional `local` HTTP **LLM** engine stays off on 16 GB
  (image and a local LLM would be co-resident) — only multimodal runs locally here.

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

**Built (Wave 0-1)**: `agency_studio/server.py` · `agency_studio/cli.py` · `app/studio/` ·
`tests/` · `pyproject.toml` (`agency-studio` script + extras).
**Built (Wave 2)**: `agency_studio/engines/local_media.py` · `engines/models.py` ·
the media endpoints + `/media/` serving in `server.py` · the Image/Voice tabs, gallery,
and model-status chip in `app/studio/src/` · `[media]` extra · `tests/test_local_media.py`
+ `tests/test_server_media.py`.
**Deferred** (will live under `agency_studio/`): `rag.py` · `websearch.py` ·
`mcp_client.py` · `knowledge.py`.

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

**Wave 2 (shipped — offline tests anywhere; live runs need the Mac):**
5. Offline: `pytest tests/ -q` covers `local_media` (mutual exclusion, warm reuse,
   URL/checksum guards) + the media endpoints (501-when-absent, 400/500 mapping,
   `/media` traversal → 404), all with backends + network stubbed.
6. Live (Mac): `python3.12 -m venv` + `pip install -e ".[media]"` + `brew install ffmpeg`,
   then `agency-studio` and exercise `POST /api/image|/api/tts|/api/stt` — validated
   end-to-end (a TTS clip transcribed back verbatim; real FLUX images served via
   `/media`). Image and a local LLM are never co-resident (the local LLM engine stays off).

**Waves 3+ (deferred, Mac):**
7. RAG: ingest a doc, run a mission, **sourced** excerpts from the doc appear in a deliverable.
