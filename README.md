# Agency Studio

> **Status: scaffold (docs + roadmap).** No application code yet — this repo holds the
> vision, architecture, and build plan. Implementation will land in waves (see
> [`ROADMAP.md`](./ROADMAP.md)).

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
- 🦾 **Hands = local models** (Stable Diffusion, Whisper, Kokoro, RAG embeddings),
  targeting **Apple Silicon / Metal**, loaded **mutually exclusively** (16 GB constraint).
- 🖥️ **Screen = a React/Vite GUI** served locally, with a live mission timeline (SSE).
- 🔒 **Security first**: bind `127.0.0.1`, no `*` CORS, anti path-traversal guard
  (the inverse of the flaws found in existing runners).
- ⚖️ **MIT-compatible licensing**: reuse MIT/Apache patterns, **rule out AGPL**
  (Jan, chunkr) so nothing contaminates the project.

## What it will do (once implemented)

```
agency studio        # launches the local server + opens the Mission Console
→ type a goal        # "launch a campaign for X in Morocco"
→ watch departments run live (route → depts → synth → inspect)
→ get the dossier + deliverable, with generated images and a spoken summary
```

## Documentation

- 🗺️ [`ROADMAP.md`](./ROADMAP.md) — the full build plan (waves 0-6).
- 🏛️ [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — target architecture + streaming flow.
- 🔐 [`docs/SECURITY.md`](./docs/SECURITY.md) — the non-negotiable security guard.
- 📜 [`docs/LICENSES.md`](./docs/LICENSES.md) — third-party component inventory and licenses.
- 🤖 [`CLAUDE.md`](./CLAUDE.md) — guidance for Claude Code in this repo.

## License

MIT — see [`LICENSE`](./LICENSE).
