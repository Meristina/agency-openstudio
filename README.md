# Agency Studio

> **Status: Waves 0-3 shipped.** Core (0-1): the stdlib HTTP/SSE server + `on_event`
> hook and the React Mission Console (`app/studio/`). **Wave 2** — local multimodal
> (image / speech-to-text / text-to-speech) on Apple Silicon (Metal) — is built and
> **validated live on an M4**: `POST /api/image|/api/tts|/api/stt` + Image/Voice GUI
> tabs, gallery, and a warm-model chip. **Wave 3** — multimodal as a department
> deliverable (assets rendered into the dossier + gallery + PDF) — is shipped. Setup: a
> Python 3.10+ venv with the `[media]` extra + system `ffmpeg` (for STT); the image model
> defaults to a non-gated 8-bit FLUX.1-schnell mirror (no Hugging Face login). Waves
> **4-6** (RAG, web search, MCP, extensions) remain deferred — see [`ROADMAP.md`](./ROADMAP.md).

**Agency Studio** is a **local-first agentic studio**. It stacks
[agency-kit](https://github.com/Meristina/agency-kit) (the *brain* that orchestrates
9 departments — route → execute → synthesize → inspect with veto) on top of a **local
multimodal layer** (image generation, speech-to-text, text-to-speech, document RAG).

The point is not to build yet another model runner (LM Studio, Jan, GPT4All,
Uncensored-Local-Studio already do that) — it's to add the **orchestration layer** on top,
with a clean GUI and a sound security posture.

## Guiding principle

- 🧠 **Brain = Opus via the Claude CLI subscription** (the `claude-code` engine already
  wired into agency-kit) → strong reasoning at **zero marginal cost**.
- 🦾 **Hands = local models** (FLUX image, Whisper STT, Kokoro TTS — shipped; RAG
  embeddings in Wave 4), targeting **Apple Silicon / Metal**, loaded **mutually
  exclusively** (16 GB constraint).
- 🖥️ **Screen = a React/Vite GUI** served locally, with a live mission timeline (SSE).
- 🔒 **Security first**: bind `127.0.0.1`, no `*` CORS, anti path-traversal guard
  (the inverse of the flaws found in existing runners).
- ⚖️ **MIT-compatible licensing**: reuse MIT/Apache patterns, **rule out AGPL**
  (Jan, chunkr) so nothing contaminates the project.

## What it will do (once implemented)

```
agency-studio        # launches the local server + opens the Mission Console
→ type a goal        # "launch a campaign for X in Morocco"
→ watch departments run live (route → depts → synth → inspect)
→ get the dossier + deliverable, with generated images and a spoken summary
```

## Usage

```
agency-studio                       # serve the Mission Console on 127.0.0.1:8765
agency-studio --port 9000           # custom port
agency-studio --path /some/project  # project dir where missions/ + studio_assets/ live
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--host` | `127.0.0.1` | Bind host — **loopback only**; a non-loopback host is refused (see `docs/SECURITY.md`). |
| `--port` | `8765` | Bind port. |
| `--path` | `.` | Project dir where mission history (`missions/`) and generated assets (`studio_assets/`) are written. |
| `--static-root` | `<path>/app/studio/dist` if built | Path to the built GUI (the API still serves without it). |
| `--media-budget-mb` | `2048` | Cap `studio_assets/` size in MB; oldest generated assets are evicted first. `0` disables the cap. |
| `--version` | — | Print the version and exit. |

## Documentation

- 🗺️ [`ROADMAP.md`](./ROADMAP.md) — the full build plan (waves 0-6).
- 🏛️ [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — target architecture + streaming flow.
- 🔐 [`docs/SECURITY.md`](./docs/SECURITY.md) — the non-negotiable security guard.
- 📜 [`docs/LICENSES.md`](./docs/LICENSES.md) — third-party component inventory and licenses.
- 🤖 [`CLAUDE.md`](./CLAUDE.md) — guidance for Claude Code in this repo.

## License

MIT — see [`LICENSE`](./LICENSE).
