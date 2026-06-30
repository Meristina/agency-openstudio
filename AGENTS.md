# AGENTS.md

Orientation for AI coding agents working in this repo.

- **Read [`CLAUDE.md`](./CLAUDE.md) and [`ROADMAP.md`](./ROADMAP.md) first.** **Wave 0 is
  implemented** (stdlib server `agency_studio/server.py`, `agency-studio` CLI, React Mission
  Console `app/studio/`, `tests/`). Build by waves.
- **Build on Wave 0.** Do not implement deferred waves (2-6) ahead of order.
- **Never change** the behavior of agency-kit's veto loop / `_short_verdict`. The
  `on_event` hook (already wired in agency-kit via `_emit`) is observational only.
- **Security from Wave 0** (`docs/SECURITY.md`): bind `127.0.0.1`, no CORS `*`,
  `path_inside()` on static serving, validate downloads + checksums.
- **License discipline** (`docs/LICENSES.md`): MIT/Apache only. Never copy AGPL code
  (Jan, chunkr) — concepts only.
- **Core = zero runtime dependencies** (stdlib). Extras cover RAG/build/export.
- Tests run fully offline (monkeypatch the subprocess boundary), like agency-kit.
