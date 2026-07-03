# agency-kit — Architecture

## Overview

agency-kit is a thin routing and orchestration layer. It does not reimplement
department logic — it routes a goal across nine departments (solve, product,
marketing, finance, comms, data, ops, people, tech) and has a local agent CLI
engine (Claude Code / Codex / Gemini) play each one in turn, guided by the
per-department doctrine files in `agents/`. The router deploys the minimum set
the goal needs — most missions are single-department.

## Execution model

Missions run through a local agent CLI **engine** (Claude Code / Codex / Gemini)
selected with `--engine`. There is no SDK and no API key: the engine model plays
every role — router, each department, and the inspector — guided by the doctrine
files in `agents/`. Each CLI brings its own auth and its own live web search.

```
agency run "<goal>" --engine claude-code|codex|gemini
  └─ agency_cli/engines/cli_engine.run_mission_cli(goal, engine)
       ROUTE → EXECUTE (per dept) → SYNTHESIZE → INSPECT   (all via subprocess _call)
```

## Mission loop

```
run_mission_cli(goal, engine)
  ROUTE       _route_via_cli(engine, goal) -> dept list (JSON array)
              fallback: router.keyword_classify(goal) on unparseable output
  EXECUTE     for each routed dept (in order):
              _call(engine, goal + prior outputs + agents/_shared-<dept>.md)
  SYNTHESIZE  _call(engine, commander-agency.md + all dept outputs)
  INSPECT     _call(engine, inspector-agency.md + deliverable) -> verdict
  -> dossier {goal, route, dept_outputs, delivered, verdicts}
```

runner_bridge.run then assigns a mission_id, saves to the ~/.agency store, and
writes missions/<id>/{dossier,deliverable}.md. Single-shot — no quota checkpoint.

## Routing table

| Goal keywords | Departments invoked | Order |
|---|---|---|
| product / feature / roadmap / jtbd / pmf / discovery / prioriti | product | 1 |
| market / campaign / content / launch / position / seo / brand | marketing | 1 |
| solve / debug / fix / architect / algorithm / technical / implement | solve | 1 |
| finance / pricing / budget / roi / p&l / pipeline / commercial / deal | finance | 1 |
| comms / pr / press release / crisis / esg / event / réputation | comms | 1 |
| data / pipeline / analytics / bi / ml / llm / rag / warehouse | data | 1 |
| ops / process / pmo / nis2 / ai act / compliance / procurement | ops | 1 |
| people / hr / talent / recruiting / org design / l&d / culture | people | 1 |
| tech / architecture / devops / security / cloud / kubernetes / soc2 | tech | 1 |
| "launch a product" / "go to market" | product → marketing | 1 → 2 |
| "build and market" / "product launch" | product → marketing | 1 → 2 |
| "launch with financial model" / "pitch investors" | product → marketing → finance | 1 → 2 → 3 |
| "launch with PR" | product → marketing → comms | 1 → 2 → 3 |
| "build a data product" | product → data | 1 → 2 |
| "scale engineering team" | tech → people | 1 → 2 |
| "solve and communicate" / "fix and explain" | solve → marketing | 1 → 2 |
| "end-to-end" / "full agency" | minimum set the goal needs (never all nine reflexively) | router decides |

Default ordering when multiple departments are co-deployed:
solve → product → marketing → finance → comms → data → ops → people → tech.
When solve is routed it runs first: its problem definition and root cause are the
foundational context every other department builds against. Solve is problem-led,
not default-on — it is routed only to diagnose a real problem (root cause, blocker,
failing process, hard decision), never for a create/brand/research mission (Art. VI).
Each department evaluates upstream outputs; it does not re-derive upstream strategy.

The router outputs JSON `{"departments": [...], "rationale": "..."}`.
Keyword fallback in `keyword_classify()` handles parse errors gracefully.

## Cross-department dossier

Carried across the whole mission (passed as JSON block in every brief):

```python
{
  "goal": str,
  "route": list,            # ["product", "marketing"]
  "context": str | None,    # detected audience / stage / constraints
  "dept_outputs": dict,     # {"product": "...", "marketing": "..."}
  "decisions": list,
  "sources": list,
  "open_to_verify": list,
  "direction_check": dict | None,  # DC result: {"iteration", "choice", "note"}
  "verdicts": list,         # Inspector verdicts per iteration
  "iteration": int,
}
```

## Department sovereignty (Art. IV)

The agency commander delegates fully to each department's internal logic. It does
not short-circuit, summarise, or rewrite a department's output before passing it
to the next — it carries the full output forward as context. The inspector checks
CROSS-DEPARTMENT consistency, not the individual kit's internal quality (each kit's
own inspector handles that).

## Inspector — 3 cross-department checks

1. **SOURCES** — same never-cite list as individual kits; cross-referenced facts must
   be consistent across departments (e.g., market size cited in product ≠ marketing).
2. **ETHICS & COMPLIANCE** — no dark patterns; coherent compliance posture
   (e.g., product says privacy-first but marketing recommends tracking → VETO).
3. **CROSS-DEPARTMENT CONSISTENCY** — strategy ↔ positioning ↔ delivery alignment:
   - Product North Star ↔ Marketing KPIs
   - Product spec ↔ Solve deliverables (builds what was designed)
   - No orphaned handoffs (discover → position → deliver, no gaps)

## CLI subcommands

| Command | Description |
|---|---|
| `agency init [path] [--agent claude\|codex\|cursor\|copilot\|gemini\|opencode]` | Scaffold `.agency/` + harness slash commands |
| `agency run "goal" [--engine claude-code\|codex\|gemini] [--dry-run]` | Headless mission via the engine — routes, executes, inspects |
| `agency missions` | List all saved missions from `~/.agency/missions/` |
| `agency resume <mission_id> [--engine ...]` | Re-run a saved mission's goal through the engine |
| `agency check [path]` | Health check — constitution present + at least one engine CLI on PATH |
| `agency sync [--strict]` | Regenerate payload (default preserve mode; `--strict` requires all kit repos) |
| `agency batch add "goal"` | Add a goal to the sequential batch queue |
| `agency batch run [--retry-failed] [--limit N] [--engine ...]` | Execute pending queue goals |
| `agency batch status` | Show queue + run state |
| `agency batch clear [--status done]` | Remove entries from the queue by status |
| `agency export <mission_id>` | Export deliverable to PDF (optional: `pip install -e ".[pdf]"`) |
| `agency tui` | Terminal UI — Pipeline / Viewer / Analytics (optional: `pip install -e ".[tui]"`) |

## Slash commands (installed by `agency init`)

| Command | Description |
|---|---|
| `/agency.mission` | Full cross-department mission with Direction Check |
| `/agency.frame` | Frame a goal before running: clarify constraints, audience, context |
| `/agency.inspect` | Inspect a deliverable: 3-check cross-department audit |
| `/agency.product` | Deploy the product department directly |
| `/agency.marketing` | Deploy the marketing department directly |
| `/agency.solve` | Deploy the solve department directly |
| `/agency.finance` | Deploy the finance department directly |
| `/agency.comms` | Deploy the comms department directly |
| `/agency.data` | Deploy the data department directly |
| `/agency.ops` | Deploy the ops department directly |
| `/agency.people` | Deploy the people department directly |
| `/agency.tech` | Deploy the tech department directly |

## Engine wiring

`agency_cli/engines/cli_engine.py` maps each engine to its headless CLI invocation:

```python
ENGINES = {
    "claude-code": ["claude", "--allowedTools", "WebSearch", "-p"],
    "codex":       ["codex", "--search", "exec", "--color", "never", "--sandbox", "read-only", "--"],
    "gemini":      ["gemini", "-p"],
}
```

`_call(cmd, prompt)` shells out via `subprocess.run`; per-department doctrine is loaded
from `agents/_shared-<dept>.md`. Adding an engine is one row in `ENGINES` + `_ROUTE_CMD`,
but only if it can do live web search headlessly — without it a mission would fabricate
data (Art. I). The inspector's output is stored as `verdicts: [{engine, verdict, detail}]`
— `verdict` is a short token (PASS / PASS-WITH-FIXES / VETO, via `_short_verdict`) for
listing, `detail` keeps the full inspector text. The engine is single-shot: there is no
programmatic loop-back on a VETO.
