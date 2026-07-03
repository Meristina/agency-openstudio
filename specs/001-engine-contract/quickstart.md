# Quickstart: The Engine Contract

**Feature**: 001-engine-contract

## Run the suites (all offline — no CLI, no network, no Node, no GPU)

```bash
# The fork's suite, including the new contract tests
cd agencykit && pytest tests/ -q

# Just the contract suite
cd agencykit && pytest tests/test_engine_contract.py -q

# The studio suite (must stay green, untouched by this feature)
pytest tests/ -q
```

## Inspect the registry

```python
from agency_cli.engines.cli_engine import ENGINE_SPECS

for name, spec in ENGINE_SPECS.items():
    print(name, "validated" if spec.validated else "UNVALIDATED",
          "web_search" if spec.web_search_headless else "NO-SEARCH")
# claude-code validated web_search
# codex UNVALIDATED web_search
# gemini UNVALIDATED web_search
```

## See the Art. II refusal

```bash
cd agencykit && agency run "any goal" --engine codex
# → EngineNotValidated: engine 'codex' is registered but NOT validated for
#   production missions. Validated engine(s): claude-code.
```

The validated path is unchanged:

```bash
agency run "any goal" --engine claude-code   # runs exactly as before
```

## Add a new engine (Brick 9 preview)

```python
from agency_cli.engines.cli_engine import EngineSpec, register_engine

register_engine(EngineSpec(
    name="opencode",
    run_cmd=("opencode", "run", "--search"),      # must guarantee headless web search
    route_cmd=("opencode", "run"),
    web_search_headless=True,
    validated=False,   # stays False until end-to-end validation (human decision)
))
```

Then add its fake-binary tests in `agencykit/tests/test_engine_contract.py`.
No other file changes — `--engine opencode` appears in the CLI choices via the
`ENGINES` view, and the mission loop needs zero edits.

## Verify byte-identity of the claude path

```bash
cd agencykit && pytest tests/test_engine.py -q   # existing suite, one incidental
                                                 # test updated (see plan.md
                                                 # Complexity Tracking), everything
                                                 # else unmodified
```
