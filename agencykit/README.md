# Agency-Kit

The **meta-orchestrator** of the AI Agency. Agency-Kit routes a mission goal across nine departments — **solve**, **product**, **marketing**, **finance**, **comms**, **data**, **ops**, **people**, and **tech** — and has a local agent CLI engine (Claude Code / Codex / Gemini) play each one in turn. It runs single-department missions as well as cross-department pipelines (e.g. *solve → product → marketing*) behind a single CLI, so you describe the outcome once and the agency figures out who does what, in what order. No API key, no SDK.

---

## Architecture

```
Agency Commander  (one engine model plays every role, guided by agents/ doctrine)
 ├─ router        🔵  classifies the goal → ordered department list
 ├─ solve         🎖️  problem-solving · root-cause · architecture · decisions
 ├─ product       🎖️  discovery · roadmap · JTBD · prioritisation · specs
 ├─ marketing     🎖️  positioning · content · campaigns · launch · SEO
 ├─ finance       🎖️  business case · pricing · P&L · commercial pipeline
 ├─ comms         🎖️  PR/media · crisis · public affairs · ESG/CSRD · events
 ├─ data          🎖️  data strategy · engineering · analytics/BI · ML/LLMOps
 ├─ ops           🎖️  process · PMO · procurement B2G · EU compliance · risk
 ├─ people        🎖️  org design · talent · L&D · performance · culture
 ├─ tech          🎖️  architecture · DevOps · security · engineering excellence
 └─ inspector     🎖️  cross-department consistency check (veto power)
```

There are no installable kits and no `commander_<dept>` symbols. Every role —
router, each of the nine departments, and the inspector — is played by the single
**engine model** you choose with `--engine` (Claude Code / Codex / Gemini), guided
by the doctrine files in `agents/`. The router classifies the goal to the minimum
ordered department set; the engine then plays only those departments, in order. The
engine uses its own model selection and auth.

---

## Routing

The router reads the goal and returns an **ordered** list of departments (earlier department runs first). It deploys the *minimum* set the goal actually requires — a pricing question is `["finance"]`, not all nine.

### Single-department

| Goal mentions… | → Department |
|---|---|
| `product` · `feature` · `roadmap` · `jtbd` · `pmf` · `discovery` · `prioritization` | **product** |
| `campaign` · `content` · `launch` · `positioning` · `seo` · `brand` | **marketing** |
| `debug` · `architect` · `algorithm` · `implement` · `solve` · `fix` | **solve** |
| `finance` · `pricing` · `budget` · `roi` · `p&l` · `pipeline` · `commercial` | **finance** |
| `pr` · `press release` · `crisis` · `esg` · `csrd` · `public affairs` · `events` | **comms** |
| `data` · `pipeline` · `analytics` · `bi` · `ml` · `llm` · `rag` · `warehouse` | **data** |
| `ops` · `process` · `pmo` · `nis2` · `ai act` · `compliance` · `procurement` | **ops** |
| `hr` · `talent` · `recruiting` · `org design` · `l&d` · `culture` · `compensation` | **people** |
| `architecture` · `devops` · `security` · `cloud` · `kubernetes` · `ci/cd` · `soc2` | **tech** |

### Cross-department pipelines

| Goal | → Route (in order) |
|---|---|
| "launch a product" | **product → marketing** |
| "build and market" | **product → marketing** |
| "solve and explain" | **solve → marketing** |
| "pitch investors" | **product → finance** |
| "launch with financial model" | **product → marketing → finance** |
| "end-to-end" / "full agency" | minimum set the goal needs (never all nine reflexively) |

The router outputs a small JSON object (`{"departments": [...], "rationale": "..."}`). If parsing fails it falls back to a keyword heuristic, and ultimately to `["product"]`.

---

## Installation

agency-kit has **no runtime dependencies and needs no API key**. Missions run
through a local agent CLI engine via subprocess.

```bash
pip install -e .                 # the agency CLI (pure stdlib)
pip install -e ".[dev]"          # + pytest (offline tests)
pip install -e ".[pdf]"          # + PDF export
pip install -e ".[tui]"          # + terminal UI
```

Then install **at least one** agent CLI engine and authenticate it once:

| Engine (`--engine`) | CLI | Web search |
|---|---|---|
| `claude-code` (default) | [Claude Code](https://code.claude.com) (`claude`) | ✅ `--allowedTools WebSearch` |
| `codex` | [Codex CLI](https://developers.openai.com/codex/cli) (`codex`) | ✅ `--search` |
| `gemini` | [Gemini CLI](https://github.com/google-gemini/gemini-cli) (`gemini`) | ✅ built-in |

Each CLI uses its own authenticated session and its own live web search — agency-kit
never sees a key. Live web search is required (Art. I: never invent data), which is
why only web-search-capable CLIs are wired.

---

## Configuration

agency-kit itself reads **no environment variables** for execution. Model choice and
auth belong to the engine CLI you pick:

```bash
claude          # authenticate Claude Code once (interactive)
agency run "Launch our new B2B analytics product"            # uses claude-code
agency run --engine gemini "Diagnose our churn and relaunch" # uses gemini
```

`agency check` verifies the constitution is present and at least one engine CLI is on
your `PATH`.

---

## Usage

### CLI

```bash
# Scaffold .agency/ + slash commands for your harness
agency init
# installs: /agency.mission /agency.frame   /agency.inspect
#           /agency.product  /agency.marketing /agency.solve
#           /agency.finance  /agency.comms   /agency.data
#           /agency.ops      /agency.people  /agency.tech
#           (12 commands total)

# Run a headless mission (router decides the route, then runs each dept via the engine)
agency run "Launch our new B2B analytics product"

# Pick a different engine
agency run --engine codex "Take this feature end-to-end"
agency run --engine gemini "Full go-to-market plan"

# Classify the goal and show the planned route — no engine call
agency run --dry-run "Pitch investors for Series A"

# List saved missions
agency missions

# Re-run a saved mission's goal through the engine
agency resume 20260627-123000-launch-b2b-analytics

# Add goals to the batch queue and run them sequentially
agency batch add "Build a data strategy"
agency batch run
agency batch run --retry-failed     # also re-run goals that errored
agency batch status

# Export a mission deliverable to PDF (needs pip install -e ".[pdf]")
agency export 20260627-123000-launch-b2b-analytics

# Launch the terminal UI — Pipeline / Viewer / Analytics (needs pip install -e ".[tui]")
agency tui

# Prerequisite / health check
agency check

# Regenerate the bundled payload after editing .agency/ or agents/
agency sync
```

### Python

```python
from agency_cli.engines.cli_engine import run_mission_cli

dossier = run_mission_cli("Launch our new B2B analytics product", engine="claude-code")
print(dossier["route"])       # e.g. ["product", "marketing"]
print(dossier["delivered"])   # the synthesised cross-department deliverable

# Full headless path (saves to ~/.agency + writes missions/<id>/):
from agency_cli import runner_bridge
out = runner_bridge.run("Take this feature end-to-end", engine="gemini")
```

The mission loop is `ROUTE → EXECUTE (per dept) → SYNTHESIZE → INSPECT`, all run
through the chosen engine CLI via subprocess. The inspector's output is stored in
`verdicts` as a short token (`PASS` / `PASS-WITH-FIXES` / `VETO`) plus the full text.
The engine is single-shot — no retry loop.

---

## The nine departments

Each department is a role the engine model plays, guided by its doctrine file in
`agents/_shared-<dept>.md`. They are not installable packages.

| Department | Focus |
|---|---|
| Solve | Problem-solving · root-cause · architecture · implementation |
| Product | Discovery · strategy · prioritisation · design · delivery · measurement |
| Marketing | Research · positioning · content · campaigns · analytics |
| Finance | Business case · pricing · P&L · commercial pipeline · closing · reporting |
| Comms | Corporate comms · PR/media · crisis · public affairs · ESG/CSRD · events |
| Data | Data strategy · engineering · analytics/BI · ML/LLMOps · data products |
| Ops | Process optimisation · PMO · EU compliance (NIS2, AI Act) · risk |
| People | Org design · talent · L&D · performance · culture · people analytics |
| Tech | Architecture · DevOps · security · engineering excellence · build-vs-buy |

---

## Why nine departments + one orchestrator

- **One source of truth per department.** Each department's behaviour lives in a single
  doctrine file (`agents/_shared-<dept>.md`) the engine loads at runtime — no installable
  package, no conditional import wiring, nothing to drift out of sync.
- **The router deploys the minimum set (Art. VI).** A department that the goal does not
  need is simply not routed, so it never runs and never appears in the deliverable — the
  route, not an install state, decides who plays.
- **Department sovereignty (Art. IV).** The agency orchestrates *between* departments; it
  passes each department's full deliverable forward unchanged and never rewrites another
  department's work. Each department remains the sole authority over how its work is done.

---

## Tests

```bash
pip install -e ".[dev]"
pytest
# offline — the engine subprocess is monkeypatched: no API key, no network,
# and no installed engine CLI required
```

---

## More

**`GUIDE.md`** — full usage manual: pipeline walkthrough, slash-command catalogue, skills reference, and the repeatable pattern to wire a new department kit.
