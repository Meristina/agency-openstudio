# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**Agency Studio** is a **local-first agentic studio**. It stacks
[agency-kit](https://github.com/Meristina/agency-kit) — the orchestration *brain*
(route → execute 9 departments → synthesize → inspect with veto) — on top of a **local
multimodal layer** (image generation, speech-to-text, text-to-speech, document RAG) and
a clean web GUI.

> **Current status: Wave 0 implemented** (commit 954c070). The stdlib HTTP/SSE server
> (`agency_studio/server.py`), the `agency-studio` CLI (`agency_studio/cli.py`), the React
> Mission Console (`app/studio/`), `tests/`, and `pyproject.toml` exist. The build happens
> in waves; see `ROADMAP.md`. Do **not** invent implementation that the roadmap defers
> (Waves 2-6). Build on Wave 0; Wave 1 GUI polish continues next.

## Design principles (do not violate)

- **Brain = Claude CLI subscription.** Heavy reasoning (commander, departments,
  synthesis, inspector) runs on Opus via the `claude` CLI (agency-kit's `claude-code`
  engine). Zero marginal cost. The local layer never carries heavy reasoning.
- **Local = multimodal only, Apple Silicon / Metal.** Stable Diffusion, Whisper,
  Kokoro, RAG embeddings — loaded **mutually exclusive** (image and LLM never co-resident)
  because the target machine is a **16 GB Mac**.
- **Zero runtime dependencies for the core.** The HTTP server is Python `http.server`
  stdlib (mirrors agency-kit's stdlib-only ethos). Extras (`[studio]`, `[pdf]`) cover
  RAG/build/export only.
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
- The **only** core change planned is an **observational** `on_event` callback on
  `run_mission_cli` so the GUI can stream live progress. The veto loop and
  `_short_verdict` logic must **never** change behavior (agency-kit Constitution Art. IX).

## Build order

Follow `ROADMAP.md` exactly. Waves **0-1** (stdlib server + event hook + React/Vite
Mission Console) are buildable and testable on Linux. Waves **2-6** (SD/Whisper/Kokoro
on Metal, RAG with model downloads, web search, MCP, advanced extensions) target the
Apple Silicon Mac and are deferred.

## Conventions

- Python: stdlib-first for the core; type hints; match agency-kit's style.
- Frontend: React 19 + Vite under `app/studio/`.
- Tests mirror agency-kit's offline pattern (monkeypatch the subprocess boundary; no
  network, no CLI required to run the suite).
- Commits: Conventional Commits. Branch before non-trivial work.
