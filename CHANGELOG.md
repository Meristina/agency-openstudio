# Changelog

All notable changes to agency-kit are documented here.

## [0.2.0] — 2026-06-28

### Changed — BREAKING: engine-only execution

The OpenAI-agents **SDK execution path was removed entirely**. Missions now run
through a **local agent CLI engine** (Claude Code / Codex / Gemini) via subprocess.
agency-kit has **no runtime dependencies and needs no API key** — each engine CLI
uses its own authenticated session and its own live web search.

- `agency run "<goal>" --engine claude-code|codex|gemini` (default: `claude-code`).
- The inspector is a real gate again: on `VETO` / `PASS-WITH-FIXES` the synthesis is
  re-run with the inspector's findings injected, up to `MAX_ITERS = 3` (Art. IX); the
  best result is delivered with a `residual_risk` note if it never PASSes.
- `agency run` / `resume` now print the store `mission_id` (the id `resume`/`export`
  take) alongside the project path and the verdict.
- `agency check` verifies the constitution is present **and at least one engine CLI is
  on PATH** (no longer checks for the SDK or installed kits).
- `agency sync` defaults to **preserve mode** (regenerates agency-level files, keeps the
  committed kit-derived payload snapshot). Use `agency sync --strict` only when all nine
  sibling kit repos are cloned. (`--allow-missing` is gone — preserve is the default.)
- `DEPT_NAMES` is **solve-first**: solve is the foundational diagnosis routed only for a
  real problem (root cause / blocker / failing process / hard decision), never for a
  create / brand / research mission (Art. VI).

### Removed

- `agency_kit/` SDK modules: `mission.py`, `parallel.py`, `commander.py`, `inspector.py`,
  `models.py`, `web.py` (and the SDK half of `router.py` — now just `keyword_classify`).
- The `openai-agents` runtime dependency.
- The `--engine api` choice and the `--parallel` / `--steer` flags on `agency run`.
- The `agency-kit-mission` console script.
- The department-kit install extras (`.[product]` … `.[tech]`, `.[all]`) and the
  search-backend / `litellm` extras. Remaining extras: `dev`, `pdf`, `tui`.

### Migration

If you used the old API path (`--engine api` + `OPENAI_API_KEY`):

1. Install one agent CLI engine and authenticate it once: Claude Code (`claude`),
   Codex CLI (`codex`), or Gemini CLI (`gemini`).
2. `pip install -e .` (no extras needed — there are no runtime deps).
3. Drop `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `AK_ELITE_MODEL`, `AK_STANDARD_MODEL`,
   `AK_SEARCH`, `AK_HTTP_TIMEOUT` — none are read anymore. Model choice and auth belong
   to the engine CLI.
4. Run `agency run "<goal>"` (add `--engine codex|gemini` to switch engine).
5. Verify with `agency check`.

## [0.1.0]

Initial release — SDK-based meta-orchestrator over nine optional department kits.
