# Quickstart — Real Multi-CLI (Brick 9)

How to run, validate, and extend the multi-engine roster. All commands run from the `agencykit/` fork unless noted.

## 1. Run the offline contract suite (no CLI / network / Node needed)

```bash
cd agencykit
pip install -e ".[dev]"
pytest tests/test_engine_contract.py -q      # registry shape, refusal, argv parse, matrix-vs-registry
pytest tests/ -q                              # full offline suite stays green
```

The suite spawns fake binaries on a temp `PATH`; it never touches a real engine or the network. It proves the registry is well-formed, unvalidated engines are refused, `gemini` is an unknown-engine error, and the README matrix matches `ENGINE_SPECS`.

## 2. See the roster and what's on your machine

```bash
agency check            # lists validated engines available on PATH (derives from ENGINE_SPECS)
agency run --help       # --engine choices derive from the registry
```

## 3. Live-validate an engine (produces the report that gates a `validated=True` flip)

Only needed to promote codex / antigravity / opencode. Requires the real CLI installed + authenticated. Run the SAME representative mission on each engine for comparability (SC-001):

```bash
# codex — has a real live-search flag; expected to pass
agency run --engine codex --min-sources 3 --resolve-sources "<representative mission goal>"

# antigravity (agy) — tool-driven search; try with tool auto-approval
#   if the offline entry is agy --print and search doesn't fire, the live-test determines
#   whether adding --dangerously-skip-permissions yields genuine headless web search
agency run --engine antigravity --min-sources 3 --resolve-sources "<same goal>"

# opencode — Exa search is env-gated; enable it for the run
OPENCODE_ENABLE_EXA=1 agency run --engine opencode --min-sources 3 --resolve-sources "<same goal>"
```

Note: codex/antigravity/opencode are **refused** (`EngineNotValidated`) until their flip lands — so the very first live run of each is done by temporarily flipping `validated=True` in a working branch to exercise it, OR via a dedicated validation harness. Record each engine's outcome (PASS/FAIL, dossier shape, per-department source count, resolved URLs, config used) in the Brick-9 live-test report under `docs/legacy/`.

**Flip rule**: only after a PASS with resolvable, verified sources do you set `validated=True` (and, for antigravity/opencode, `web_search_headless=True`) in `ENGINE_SPECS`. A FAIL stays refused and is documented.

## 4. Read the compatibility matrix

`agencykit/README.md` holds the authoritative engines × capabilities matrix (run/route, headless web search + config note, MCP `--mcp-config`, kill-tree, validation status). The root `README.md` points to it. A test fails if the matrix drifts from the registry.

## 5. Add another engine later (the Brick 1 property)

1. Add one `EngineSpec(...)` to `ENGINE_SPECS` (or call `register_engine(...)` at runtime), `validated=False`.
2. Add its per-engine cases to `test_engine_contract.py` (refusal + fake-binary argv parse).
3. Add its row to the README matrix.
4. Live-validate → author the report → flip `validated=True`.

No mission-loop edits. `cli.py`/`scaffolder.py` update automatically (they derive from `ENGINE_SPECS`).
