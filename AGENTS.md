# AGENTS.md

Orientation for AI coding agents working in this repo.

- **Read [`CLAUDE.md`](./CLAUDE.md), [`ROADMAP.md`](./ROADMAP.md), and
  [`docs/WAVE3-PLAN.md`](./docs/WAVE3-PLAN.md) first.** **Waves 0-3 are shipped** — the stdlib
  server (`agency_studio/server.py`), the `agency-studio` CLI, the React Mission Console
  (`app/studio/`), `tests/`, the local multimodal layer (FLUX/Whisper/Kokoro,
  `agency_studio/engines/`), and multimodal-as-a-department-deliverable (`agency_studio/assets.py`,
  the asset render/rewrite pipeline + GUI gallery). Build by waves.
- **Build on Waves 0-3.** Do not implement deferred waves (4-6: RAG, web search, MCP,
  advanced extensions) ahead of order.
- **Never change** the behavior of agency-kit's veto loop / `_short_verdict`. The
  `on_event` hook (already wired in agency-kit via `_emit`) is observational only.
- **Security from Wave 0** (`docs/SECURITY.md`): bind `127.0.0.1`, no CORS `*`,
  `path_inside()` on static serving, validate downloads + checksums.
- **License discipline** (`docs/LICENSES.md`): MIT/Apache only. Never copy AGPL code
  (Jan, chunkr) — concepts only.
- **Core = zero runtime dependencies** (stdlib). Extras cover RAG/build/export.
- Tests run fully offline (monkeypatch the subprocess boundary), like agency-kit.
