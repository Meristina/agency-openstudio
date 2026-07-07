# Phase 1 Data Model — Real Multi-CLI (Brick 9)

The "data" here is the in-code engine registry plus two documentation artifacts. No persistence changes.

## Entity: EngineSpec (existing, unchanged shape)

Frozen dataclass in `agencykit/agency_cli/engines/cli_engine.py`. Fields (from Brick 1):

| Field | Type | Meaning | Invariant |
|---|---|---|---|
| `name` | str | registry key / `--engine` value | non-empty |
| `run_cmd` | tuple[str, …] | argv prefix for research/synthesis/inspect (`_call` appends the prompt) | non-empty |
| `route_cmd` | tuple[str, …] | argv prefix for routing (cheap JSON-array classification) | non-empty; must be non-interactive |
| `web_search_headless` | bool | engine guarantees live web search headlessly | if `validated` ⇒ must be `True` (`__post_init__`) |
| `validated` | bool | may drive a production mission | flip only on a passing live-test |
| `run_timeout` | int | seconds for a research call | > 0 (default 900) |
| `route_timeout` | int | seconds for a routing call | > 0 (default 60) |
| `kill_tree_on_cancel` | bool | cancel/timeout kills the whole process group | default `True`; `_call`/`_signal_tree` always honor it |

**No new fields.** The permissive `web_search_headless` rule (D4) is a *declaration policy*, not a schema change — the invariant already enforces `validated ⇒ web_search_headless`.

## Registry state: ENGINE_SPECS after this brick

Baseline committed offline (validation flips are separate, live-test-gated tasks — shown as the post-live-test target in the last column).

| name | run_cmd | route_cmd | web_search_headless (baseline → after live-test) | validated (baseline → target) |
|---|---|---|---|---|
| `claude-code` | `claude --allowedTools WebSearch -p` | `claude -p` | `True` → `True` | `True` → `True` (unchanged) |
| `codex` | `codex --search exec --color never --sandbox read-only --skip-git-repo-check --` | `codex exec --color never --sandbox read-only --skip-git-repo-check --` | `True` → `True` | `False` → **`True`** (on passing live-test) |
| `antigravity` | `agy --print` | `agy --print` | `False` → `True` iff live-test proves tool-driven search (likely needs `--dangerously-skip-permissions`) | `False` → `True` iff proven |
| `opencode` | `opencode run` | `opencode run` | `False` → `True` iff live-test proves Exa search under `OPENCODE_ENABLE_EXA` | `False` → `True` iff proven |

Removed: `gemini` (no row). Selecting it → `ValueError` (unknown engine), listing current engines.

**State transition (per engine)**: `registered (validated=False)` → *[live-test PASS: mission completes with resolvable, verified sources]* → `validated=True`. No other transition promotes an engine. A live-test FAIL leaves it registered-but-refused and is recorded in the report.

## Artifact: Compatibility Matrix (`agencykit/README.md`)

One row per registered engine. Columns and their source of truth:

| Column | Source | Notes |
|---|---|---|
| Engine (`--engine`) | `EngineSpec.name` | the value passed to `--engine` |
| Run / Route | `run_cmd` / `route_cmd` | the corrected/added argv |
| Headless web search | `web_search_headless` + config note | `✅` guaranteed by our flag (claude WebSearch, codex `--search`); `✅ via OPENCODE_ENABLE_EXA` / `⚠️ tool-driven` for config-gated; never a bare ✓ that hides setup |
| MCP `--mcp-config` | code (`_with_mcp` gates on `--allowedTools`) | only `claude-code` today |
| Kill-tree on cancel | `kill_tree_on_cancel` | `True` for all (POSIX process group) |
| Validation status | `validated` | `validated` / `candidate (unvalidated)` |

**Consistency invariant (test-enforced, FR-011)**: for every engine, the matrix's name and validation status equal `ENGINE_SPECS[name].validated`; no matrix row exists without a registry entry and vice-versa; no row marked `validated` shows a non-affirmative headless-web-search cell.

## Artifact: Live-Test Report (`docs/legacy/…` alongside archived reports)

Per-engine end-to-end record; the evidence that authorizes a `validated=True` flip (FR-016).

| Field | Meaning |
|---|---|
| engine | which engine was exercised |
| mission goal | the single representative mission run on every engine (same goal → comparability, SC-001) |
| outcome | `PASS` (mission completed) / `FAIL` (+ reason: no headless search, hang, auth, etc.) |
| dossier shape | route, dept_outputs keys, delivered present, inspector verdict — comparable to `claude-code` |
| source verification | per-department cited-source count ≥ min; sampled URLs resolve (Brick 3 postcondition, SC-002) |
| config used | e.g. `OPENCODE_ENABLE_EXA=1`, `--dangerously-skip-permissions` — the documented configuration behind a config-gated declaration |
| decision | flip `validated`/`web_search_headless` → `True`, or keep refused |
