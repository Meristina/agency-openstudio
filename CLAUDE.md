# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**Agency Studio** is a **local-first agentic studio**. It stacks
[agency-kit](https://github.com/Meristina/agency-kit) — the orchestration *brain*
(route → execute 9 departments → synthesize → inspect with veto) — on top of a **local
multimodal layer** (image generation, speech-to-text, text-to-speech, document RAG) and
a clean web GUI.

> **Current status: Waves 0-3 shipped; Wave 4 (RAG / LocalDocs) core shipped — GUI
> deferred.** Core (Wave 0-1): the stdlib HTTP/SSE server
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
> endpoints + best-effort mission retrieval injection with a `retrieval` SSE phase. Offline
> suite runs anywhere; the live embedding path needs the Apple Silicon Mac; the **GUI "Docs"
> tab is a tracked follow-up**. **Waves 5-6 remain deferred** (web search, MCP, extensions;
> plus Wave-6 visual RAG / knowledge graphs); see `ROADMAP.md`. Do **not** invent
> implementation that the roadmap/WAVE-PLANs defer.
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
Metal), **Wave 3** (multimodal as a department deliverable), and **Wave 4** (RAG / LocalDocs
core) are **shipped** — their unit/HTTP tests run offline anywhere (backends + network
stubbed), but the live model runs require the Apple Silicon Mac. Wave 4's **GUI "Docs" tab**
is a tracked follow-up. Waves **5-6** (web search, MCP, advanced extensions — plus Wave-6
visual RAG / knowledge graphs) remain deferred.

## Conventions

- Python: stdlib-first for the core; type hints; match agency-kit's style.
- Frontend: React 19 + Vite under `app/studio/`.
- Tests mirror agency-kit's offline pattern (monkeypatch the subprocess boundary; no
  network, no CLI required to run the suite).
- Commits: Conventional Commits. Branch before non-trivial work.
