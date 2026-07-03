# Library API Contract: Engine Contract

**Module**: `agencykit/agency_cli/engines/cli_engine.py` (the fork)
**Consumers**: mission loop (same module), `runner_bridge.py`, `cli.py`, studio server, offline suites

## Public surface (post-feature)

### New

```python
@dataclass(frozen=True)
class EngineSpec:
    name: str
    run_cmd: tuple            # argv prefix, web search enabled
    route_cmd: tuple          # argv prefix, classification only
    web_search_headless: bool
    validated: bool
    run_timeout: int = 900
    route_timeout: int = 60
    kill_tree_on_cancel: bool = True

ENGINE_SPECS: dict           # name -> EngineSpec; single source of truth

class EngineNotValidated(RuntimeError): ...

def register_engine(spec: EngineSpec) -> None:
    """Insert/replace a spec and refresh the ENGINES/_ROUTE_CMD views."""
```

### Preserved unchanged (behavioral contract)

```python
ENGINES: dict      # derived view {name: run_cmd list} — same keys/values as today
_ROUTE_CMD: dict   # derived view {name: route_cmd list} — same keys/values as today

def _call(cmd_prefix, prompt, timeout=900, should_cancel=None) -> str
    # THE subprocess boundary and monkeypatch seam. Signature, semantics,
    # error messages, cancel/kill-tree behavior: all unchanged.

class MissionCancelled(Exception)   # unchanged

def run_mission_cli(goal, engine="claude-code", on_event=None, should_cancel=None,
                    asset_clause=None, context_clause=None, mcp_config_path=None,
                    mcp_allowed_tools=None, persona_doctrine=None,
                    on_checkpoint=None, resume_state=None) -> dict
    # Signature unchanged. New guard behavior documented below.
```

## Guard contract of `run_mission_cli` (evaluated in order, before any subprocess)

| # | Condition | Raises | Message contract |
|---|---|---|---|
| 1 | `engine not in ENGINE_SPECS` | `ValueError` | UNCHANGED: `Unknown engine '<e>'. Available: <names>` |
| 2 | `not spec.validated` | `EngineNotValidated` | names the engine, its unvalidated status, and the validated alternative(s); self-contained (no host-repo article/brick numbers baked into the fork-level message) |
| 3 | `not spec.web_search_headless` | `EngineNotValidated` | names the missing web-search capability (defense-in-depth; registry invariant makes this unreachable when 2 passes) |
| 4 | `shutil.which(spec.run_cmd[0]) is None` | `RuntimeError` | UNCHANGED: `engine '<e>' needs the '<bin>' CLI on PATH — install it and authenticate first. Check availability with: agency check` |

Refusals are hard stops: no silent engine substitution, ever (spec clarification
2026-07-03).

## Byte-identity contract (claude-code path)

For `engine="claude-code"` with all optional hooks at their defaults, every
observable is identical to the pre-feature module:

- argv of every subprocess call (route, department, synthesis, inspection)
- prompt text of every call
- timeout values (60 route / 900 others)
- cancellation semantics (poll cadence, SIGTERM→SIGKILL grace, process-group kill)
- error types and messages for unknown engine / missing binary / timeout / non-zero exit / empty output
- the veto loop: `MAX_ITERS`, `_RETRY_VERDICTS`, `_short_verdict`, checkpoint/resume invariants — untouched
- the returned dossier shape

## Extension contract (Brick 9 forward-compatibility)

Adding an engine =

1. construct an `EngineSpec` (`validated=False` until end-to-end validation),
2. `register_engine(spec)` — or add the literal to the initial registry,
3. add its fake-binary contract tests.

Zero changes to `run_mission_cli`, the veto loop, `runner_bridge`, `cli.py`
(choices pick up the new name via the `ENGINES` view), or the studio.

## Test contract (offline, Art. VII)

`agencykit/tests/test_engine_contract.py` MUST cover, per registered engine, using
a fake binary on a temp `PATH` (no network / real CLI / Node / GPU):

- research-grade run: canned stdout returned verbatim
- classification: route prompt answered, JSON parsed
- cancel mid-call: `MissionCancelled` raised, process tree dead
- kill-tree: fake binary spawns a child; after cancel/timeout BOTH pids are gone
- missing binary: guard-4 `RuntimeError` with the unchanged message
- refusal matrix: guard-2 `EngineNotValidated` for every `validated=False` spec; no refusal for `claude-code`
- registry invariant: every spec with `validated=True` has `web_search_headless=True`
- views: `ENGINES` / `_ROUTE_CMD` agree with `ENGINE_SPECS` after `register_engine`
