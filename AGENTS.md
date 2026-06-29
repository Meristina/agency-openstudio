# AGENTS.md

Orientation for AI coding agents working in this repo.

- **Read [`CLAUDE.md`](./CLAUDE.md) and [`ROADMAP.md`](./ROADMAP.md) first.** This repo
  is a **scaffold** — docs + config only, no application code yet. Build by waves.
- **Start with Wave 0** (ROADMAP). Do not implement deferred waves (2-6) ahead of order.
- **Never change** the behavior of agency-kit's veto loop / `_short_verdict`. The planned
  `on_event` hook is observational only.
- **Security from Wave 0** (`docs/SECURITY.md`): bind `127.0.0.1`, no CORS `*`,
  `path_inside()` on static serving, validate downloads + checksums.
- **License discipline** (`docs/LICENSES.md`): MIT/Apache only. Never copy AGPL code
  (Jan, chunkr) — concepts only.
- **Core = zero runtime dependencies** (stdlib). Extras cover RAG/build/export.
- Tests run fully offline (monkeypatch the subprocess boundary), like agency-kit.
