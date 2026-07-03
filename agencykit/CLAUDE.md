# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo does

agency-kit is a thin routing and orchestration layer over nine departments (solve, product, marketing, finance, comms, data, ops, people, tech — the **solve-first** canonical order of `DEPT_NAMES`). It reads a mission goal, classifies which departments are needed and in what order, runs them sequentially (each reads the previous dept's output), synthesises one cross-department deliverable, and inspects it.

Missions execute through a **local agent CLI engine** (Claude Code / Codex / Gemini) via subprocess — **no API key, no SDK, no `pip` dependencies**. Each CLI uses its own authenticated session and its own live web search. There are no installable department "kits"; every department is played by the engine model, guided by the doctrine files in `agents/`.

## Commands

```bash
# Install (dev) — agency-kit has NO runtime dependencies
pip install -e ".[dev]"         # core + pytest
pip install -e ".[pdf]"         # PDF export extra
pip install -e ".[tui]"         # terminal UI extra

# Test  (fully offline; engine subprocess is monkeypatched)
pytest tests/ -q
pytest tests/test_structure.py -q   # structural invariants only
pytest tests/test_engine.py -q      # engine path
pytest tests/test_router.py -q      # keyword router

# Health check (constitution present + at least one engine CLI on PATH)
agency check

# CLI — pick the engine with --engine (default: claude-code)
# Only VALIDATED engines run missions: claude-code is validated; codex/gemini are
# registered but refused (EngineNotValidated) until validated end-to-end.
agency init [path] [--agent claude|codex|cursor|copilot|gemini|opencode]
agency run "goal" [--dry-run] [--engine claude-code]   # codex/gemini refused until validated
agency missions
agency resume <mission_id> [--engine ...]    # re-runs the saved goal via the engine
agency sync [--strict]
agency batch add "goal" / run [--engine ...] / status / clear
agency export <mission_id>      # requires pip install -e ".[pdf]"
agency tui                      # requires pip install -e ".[tui]"
```

## Architecture

### Mission loop (`agency_cli/engines/cli_engine.py` → `run_mission_cli`)

```
run_mission_cli(goal, engine)
  ROUTE      → _route_via_cli asks the engine CLI for the dept list (JSON array);
               falls back to router.keyword_classify on unparseable output
  EXECUTE    → for each routed dept (in order): subprocess _call(engine, prompt)
               prompt = goal + prior dept outputs + agents/_shared-<dept>.md doctrine
  SYNTHESIZE → _call(engine, commander-agency.md + all dept outputs)
  INSPECT    → _call(engine, inspector-agency.md + deliverable) → verdict text
  → returns a dossier dict (goal, route, dept_outputs, delivered, verdicts)
```

`runner_bridge.run` wraps this: it assigns a `mission_id`, saves to the `~/.agency`
store (so `agency missions/resume/export` see it), and writes the project-local
`missions/<id>/{dossier,deliverable}.md`. The engine is single-shot — there is no
quota/rate-limit checkpoint; `agency resume` re-runs the saved goal.

### Cross-department dossier

Carried as a JSON block through every brief:
```python
{
  "goal": str,
  "route": list,            # ["product", "marketing"]
  "context": str | None,
  "dept_outputs": dict,     # {"product": "<full text>", ...}
  "decisions": list,
  "sources": list,
  "open_to_verify": list,
  "direction_check": dict | None,
  "verdicts": list,
  "iteration": int,
}
```

Departments are sovereign (Art. IV): the engine passes the full previous output forward unchanged — never summarises or rewrites a department's deliverable.

### Engine wiring (`agency_cli/engines/cli_engine.py`)

`ENGINE_SPECS` is the single source of truth for engine wiring: command argv, validation status, web-search capability, and per-call timeouts. (`kill_tree_on_cancel` is declared for the contract; `_call` always terminates the whole process group today, so it records that guarantee rather than toggling behavior.) `ENGINES` and `_ROUTE_CMD` are derived compatibility views (mutated in place, never rebound, so a held reference stays live) for CLI choices and older readers; the mission loop reads `ENGINE_SPECS` directly. Construction (`EngineSpec.__post_init__`) rejects an inconsistent spec — e.g. `validated=True` without `web_search_headless` — so `register_engine` fails fast instead of deferring to mission time.

```python
ENGINE_SPECS = {
    "claude-code": EngineSpec(..., web_search_headless=True, validated=True),
    "codex":       EngineSpec(..., web_search_headless=True, validated=False),
    "gemini":      EngineSpec(..., web_search_headless=True, validated=False),
}
```

`_call(cmd, prompt)` shells out through the subprocess boundary. Adding an engine = one `EngineSpec` plus contract tests; the engine must guarantee headless web search, and it stays `validated=False` until it passes end-to-end validation. Registered but unvalidated engines (`codex`, `gemini`) refuse production missions with `EngineNotValidated`.

### Single source of truth for department names

`agency_kit/departments.py` exports `DEPT_NAMES` (ordered tuple, **solve-first**), `VALID_DEPTS` (frozenset), `DEPT_DEPENDENCIES` + `dependency_layers()` (the canonical ordering model), and `dept_list_text()`. The keyword router and the engine import from here. Adding a department means updating only this file (one `_ROSTER` row + one `DEPT_DEPENDENCIES` entry).

### Payload (`agency_cli/payload/`)

`agency init` installs from the bundled payload — no internet required:
- `payload/agency/` ← `.agency/` (commands, constitution, templates; `plans/` excluded)
- `payload/agents/` ← merged from agency-kit `agents/` + all 9 dept kit `agents/` dirs
- `payload/skills/` ← merged skill dirs

`agency sync` regenerates from sibling repos. A pre-flight check verifies all sibling repos exist before wiping anything (silent wipe + missing repo = permanent loss of committed agent files).

### Shared doctrine files (`agents/`)

| Pattern | Files |
|---|---|
| Agency-level doctrine | `commander-agency.md`, `router-agency.md`, `inspector-agency.md`, `_shared-agency.md` |
| Per-department doctrine | `_shared-product.md` … `_shared-tech.md` (× 9) |
| Jurisdiction context | `_shared-eu.md` · `_shared-us.md` · `_shared-fr.md` |

All source files under `agents/` are mirrored to `payload/agents/`. The drift guard test (`test_payload_agent_matches_source`) catches divergence — run `agency sync` to fix.

## Key files

| File | Role |
|---|---|
| `agency_cli/engines/cli_engine.py` | `run_mission_cli()` + `ENGINE_SPECS` — the whole route→execute→synthesize→inspect loop via subprocess |
| `agency_cli/runner_bridge.py` | `run()` / `resume()` — drive the engine, save to store + serialize `missions/<id>/` |
| `agency_cli/cli.py` | All CLI subcommands + the `--engine` flag |
| `agency_cli/batch_runner.py` | `agency batch` queue — runs each goal through the engine |
| `agency_cli/scaffolder.py` | `agency init` + `agency check` (constitution + engine-on-PATH) |
| `agency_cli/sync_payload.py` | Payload regeneration logic + pre-flight safety guard |
| `agency_kit/router.py` | `keyword_classify()` — dependency-free fallback router (solve-first) |
| `agency_kit/departments.py` | Single source of truth: `DEPT_NAMES`, `DEPT_DEPENDENCIES`, `dependency_layers()` |
| `agency_kit/store.py` | `save()`, `load()`, `list_missions()`, atomic `new_mission_id()` |
| `.agency/memory/constitution.md` | 10 articles — every command re-reads this before acting |
| `docs/ARCHITECTURE.md` | Full routing table, pipeline diagram, design decisions |

## Environment / configuration

agency-kit reads **no** environment variables for execution. Each engine CLI handles its own auth and model selection:
- **claude-code** — `claude` CLI session (run `claude` once to authenticate)
- **codex** — `codex` CLI session
- **gemini** — `gemini` CLI session

Pick the engine per run with `--engine` (default `claude-code`). Only `claude-code` is validated and will run a mission; `codex`/`gemini` are registered but refused (`EngineNotValidated`) until validated end-to-end.

## Test architecture

`tests/conftest.py` is intentionally minimal — there is no SDK to stub. The suite runs fully offline:
- `test_engine.py` — monkeypatches `cli_engine._call` (the subprocess wrapper) to exercise the mission loop without any CLI installed.
- `test_engine_contract.py` — the Engine-contract suite: registry/views, `EngineSpec` invariants, and the Art. II refusal guards (all offline); plus subprocess/kill-tree tests that spawn real fake binaries on a temp `PATH` (no network, no real CLI, no Node) and are `@requires_posix` (skipped on Windows).
- `test_router.py` — the pure keyword classifier.
- `test_structure.py` — import spine, the `dependency_layers` ordering model, and the payload drift guards.
- `test_cli.py` — CLI dispatch with `runner_bridge`/`batch_runner` monkeypatched.

## Constitution

`.agency/memory/constitution.md` — 10 articles. Critical ones:
- **Art. I** — Never invent data, citations, or outputs
- **Art. II** — No dark patterns, no misleading outputs
- **Art. IV** — Department sovereignty: don't override a kit's internal logic
- **Art. VI** — Don't over-route: deploy the minimum set the goal requires
- **Art. IX** — Inspector always runs; VETO triggers another iteration, not a skip
