# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**Agency Studio** is a **local-first agentic studio**. It stacks
[agency-kit](https://github.com/Meristina/agency-kit) — the orchestration *brain*
(route → execute 9 departments → synthesize → inspect with veto) — on top of a **local
multimodal layer** (image generation, speech-to-text, text-to-speech, document RAG) and
a clean web GUI.

> **Current status: Waves 0-4 shipped.** Core (Wave 0-1): the stdlib HTTP/SSE server
> (`agency_studio/server.py`), the `agency-studio` CLI (`agency_studio/cli.py`), the React
> Mission Console (`app/studio/`: live SSE timeline, project-scoped history, PDF export,
> full "Stop mission"), `tests/`, and `pyproject.toml`. **Wave 2 — local multimodal
> (image / STT / TTS) on Apple Silicon (Metal)** — is now built, reviewed, and
> **validated live on the target Mac (M4, 16 GB)**: `agency_studio/engines/local_media.py`
> (warm single-resident `ModelManager`) + `models.py` (integrity-checked model
> resolution), the `POST /api/image|/api/tts|/api/stt` + `GET /api/models` endpoints with
> `/media/` asset serving, and the GUI's **Image/Voice tabs, gallery, and warm-model
> status chip** (the former deferred Wave-1 gallery/ModelManager surface). Models load
> **mutually exclusive** and stay **warm** for fast repeat calls.
> **Wave 3 (multimodal as a department deliverable) is SHIPPED** — tracked in
> `docs/WAVE3-PLAN.md` (which supersedes the naive `ROADMAP.md §Wave 3` sketch): all six
> steps landed/reviewed — `/api/tts` voice allowlist; `assets.py` marker parser;
> agency-kit's additive `asset_clause` engine hook; the best-effort `render_assets` bridge
> hook + `## Assets`; `assets.render`/`rewrite_delivered` + server wiring + SSE `asset`
> phase; and the GUI asset timeline + per-mission gallery (`AssetGallery`) + the PDF
> `/media`→on-disk fix (`exporter._localize_assets`). Its offline suite runs anywhere; the
> live render path needs the Apple Silicon Mac. **Wave 4 — RAG / LocalDocs — core is
> SHIPPED** (offline-first slice), tracked in `docs/WAVE4-PLAN.md`: the `mlx_embedding_models`
> embed engine (`engines/embeddings.py` + `ModelManager.embed`, mutually exclusive with the
> media models), `agency_studio/rag.py` (markitdown → chunk → embed → **`sqlite-vec`** store
> with a pure-Python cosine fallback, behind a pluggable `Retriever`), agency-kit's additive
> **`context_clause`** hook (twin of `asset_clause`), and the `POST/GET/DELETE /api/docs`
> endpoints + best-effort mission retrieval injection with a `retrieval` SSE phase, and the
> **GUI "Docs" tab** (upload / list / delete + the retrieval timeline). Offline suite runs
> anywhere; the live embedding path needs the Apple Silicon Mac. **Wave 5 — local web search +
> MCP — is BUILT** (offline-first slice), tracked in `docs/WAVE5-PLAN.md`: both land as
> *web-RAG* — the studio fetches web results (`websearch.py`, ddgs, `[web]`) and reads MCP
> server resources (`mcp_client.py`, the official MIT `mcp` SDK, `[mcp]`) **itself** and injects
> them through the **same additive `context_clause` hook** as Wave 4 (no new agency-kit surface),
> each **opt-in per mission** (default off — the Claude path already searches / speaks MCP).
> A shared `context_block.format_context_block` + server `_resolve_clause` back RAG/web/MCP alike;
> MCP is read-only **resources-as-context** (tool-calling is the `claude --mcp-config` path,
> deferred). Offline suite runs anywhere; the live web/MCP paths need a network / a real MCP
> server (deferred like Wave 2). **Wave 6 — advanced extensions — is partly BUILT (two bricks, both
> merged to `main`)**, tracked
> in `docs/WAVE6-PLAN.md`: the **knowledge-graph brick** (offline-first slice; studio PR #30) lands as *graph-RAG*,
> the exact parallel of Waves 4/5 — `agency_studio/knowledge.py` extracts `(subject, relation,
> object)` triples from the user's own **docs + mission history** into a pure-stdlib SQLite graph
> (`nodes`/`edges`, upsert-dedup + weight; `rag.LocalRetriever.all_chunks` feeds the doc source),
> then at mission time seeds on the goal → 1-hop **neighbourhood** → injects the subgraph through
> the **same additive `context_clause` hook** (`build_kg_context_clause` + the server's
> `_resolve_kg_clause`, composed after RAG/web/MCP). The `Extractor` seam's live impl wraps
> `hyper-extract` (Apache-2.0, the new **`[kg]`** extra, lazy → `KnowledgeUnavailable`); **querying
> an already-built graph needs no extra**. Opt-in per mission (`knowledge` flag, default off) with
> a `graph` SSE phase, `GET /api/graph` + `POST /api/graph/build`, and the GUI "Use knowledge graph"
> toggle + timeline step. Its offline suite runs anywhere (extractor stubbed); the live extraction
> path needs the Apple Silicon Mac (deferred like Wave 2). The **MCP tool-calling brick** (Brick 2)
> is also BUILT — the first brick that can't ride `context_clause`: it adds a **new additive
> agency-kit engine hook** (`mcp_config_path` / `mcp_allowed_tools` on `run_mission_cli`, spliced by
> `_with_mcp` into the claude **department + synthesis** commands only — never the router/inspector,
> so the Art. IX gate's inputs are unchanged), while the studio builds the `--mcp-config` from the
> enabled `mcp.json` servers (`mcp_client.build_cli_config`), writes a short-lived temp file, emits
> an `mcp_tools` SSE phase, and threads it + the `mcp__*` tools through `runner_bridge.run` under a
> new `mcp_tools` opt-in flag (default off) + GUI toggle. This brick spans **both repos** (the hook
> lands in agency-kit-studio via agency-kit PR #10, like the Wave-4 `context_clause` hook did; the
> studio side is studio PR #32 — both merged to `main`); its live tool-calling path
> needs a real MCP server on the Mac. The **remaining three Wave-6 plug-ins** (persona doctrine,
> visual RAG (PixelRAG), cloud video (seedance)) **remain deferred**; see `ROADMAP.md`. Do **not**
> invent implementation that the roadmap/WAVE-PLANs defer.
>
> **Running Wave 2 (target Mac):** a **Python 3.10+ venv** with the `[media]` extra
> (`pip install -e ".[media]"`), plus **`ffmpeg`** on PATH for speech-to-text
> (`brew install ffmpeg`). The image model defaults to a **non-gated, pre-quantized
> 8-bit FLUX.1-schnell mirror** (`engines/models.py` `IMAGE_MODEL_REPO`) so no Hugging
> Face login is needed; weights (~18 GB total) download once into the OS cache.

## Design principles (do not violate)

- **Brain = Claude CLI subscription.** Heavy reasoning (commander, departments,
  synthesis, inspector) runs on Opus via the `claude` CLI (agency-kit's `claude-code`
  engine). Zero marginal cost. The local layer never carries heavy reasoning.
- **Local = multimodal only, Apple Silicon / Metal.** FLUX (image), Whisper (STT),
  Kokoro (TTS), RAG embeddings — loaded **mutually exclusive** (image and a local LLM
  never co-resident) because the target machine is a **16 GB Mac**.
- **Zero runtime dependencies for the core.** The HTTP server is Python `http.server`
  stdlib (mirrors agency-kit's stdlib-only ethos). Extras cover opt-in features only and
  are **lazily imported** so the core boots without them: `[media]` (Wave 2 — mflux /
  mlx-whisper / kokoro-onnx), `[pdf]` (export), `[studio]` (Wave 4 RAG). A multimodal
  request with `[media]` absent returns a clean **501 + install hint** (the same pattern
  as `[pdf]`).
- **Security is non-negotiable, from Wave 0.** Bind `127.0.0.1` (never `0.0.0.0`), no
  `Access-Control-Allow-Origin: *`, `path_inside()` guard on every static file handler,
  validate download URLs and verify binary checksums. See `docs/SECURITY.md`.
- **License discipline: MIT-compatible only.** Reuse MIT/Apache patterns
  (Uncensored-Local-Studio, GPT4All, markitdown). **Never fork/copy AGPL code**
  (Jan, chunkr) — borrow concepts only. See `docs/LICENSES.md`.

## Relationship to agency-kit

Agency Studio does **not** reimplement agency-kit's mission loop. It wraps it:
- Reuses `run_mission_cli` (route→execute→synth→inspect, veto loop), `runner_bridge`
  (serialize_dossier / run), `store`, `departments`, `exporter`.
- Two sanctioned core hooks on `run_mission_cli`, both additive and default-None
  so standalone agency-kit is byte-identical:
  1. an **observational** `on_event` callback so the GUI can stream live progress;
  2. a **cancel** `should_cancel` predicate (the "Stop mission" feature), polled in
     two places: at **phase boundaries** (after routing, before each department,
     before each synth→inspect iteration) as a no-spend early-exit, **and inside
     `_call`** while a child process is in flight — so a Stop **kills the running
     subprocess tree immediately** (`start_new_session` + `killpg` SIGTERM→SIGKILL,
     so the CLI wrapper's grandchildren die too) instead of waiting up to the
     per-call timeout. Either way `run_mission_cli` raises `MissionCancelled`
     **before** any persistence.
  The veto loop and `_short_verdict` logic must **never** change behavior
  (agency-kit Constitution Art. IX). The in-flight kill preserves this: an aborted
  mission yields **no dossier at all**, so no verdict is ever altered and no
  un-inspected result is ever delivered — `MissionCancelled` cancels the whole run,
  it does not let a synthesis skip its inspection and ship. The veto loop's *logic*
  is untouched; only an abort can now happen mid-call rather than only between calls.

## Build order

Follow `ROADMAP.md` exactly. Waves **0-1** (stdlib server + event hook + React/Vite
Mission Console) are buildable and testable on Linux. **Wave 2** (FLUX/Whisper/Kokoro on
Metal), **Wave 3** (multimodal as a department deliverable), **Wave 4** (RAG / LocalDocs,
incl. the GUI "Docs" tab), **Wave 5** (local web search + MCP resources-as-context), and the
first two **Wave 6** bricks (knowledge graphs + MCP tool-calling — both merged to `main`) are
**shipped** — their unit/HTTP/GUI tests run offline anywhere (backends + network stubbed), but
the live model / web / MCP-server runs require the Apple Silicon Mac. The **remaining three
Wave-6 plug-ins** (persona doctrine, visual RAG (PixelRAG), cloud video (seedance)) remain
deferred.

## Conventions

- Python: stdlib-first for the core; type hints; match agency-kit's style.
- Frontend: React 19 + Vite under `app/studio/`.
- Tests mirror agency-kit's offline pattern (monkeypatch the subprocess boundary; no
  network, no CLI required to run the suite).
- Commits: Conventional Commits. Branch before non-trivial work.
