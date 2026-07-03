# Data Model: The Engine Contract

**Feature**: 001-engine-contract | **Date**: 2026-07-03

## EngineSpec (frozen dataclass)

The single contract entity. One instance per registered engine.

| Field | Type | Constraints | Meaning |
|---|---|---|---|
| `name` | `str` | non-empty; unique registry key; matches its `ENGINE_SPECS` key | Engine identifier (`claude-code`, `codex`, `gemini`) — existing names preserved |
| `run_cmd` | `tuple[str, ...]` | non-empty; `run_cmd[0]` is the binary | Argv prefix for research-grade execution (web search enabled) — current `ENGINES` values |
| `route_cmd` | `tuple[str, ...]` | non-empty; `route_cmd[0]` is the binary | Argv prefix for classification (no web search) — current `_ROUTE_CMD` values |
| `web_search_headless` | `bool` | — | Guaranteed headless web search (Constitution Art. II precondition) |
| `validated` | `bool` | invariant: `validated ⇒ web_search_headless` (spec clarification) | May run production missions; changed only by explicit human decision |
| `run_timeout` | `int` | > 0; default `900` | Seconds budget per research-grade call (current `_call` default) |
| `route_timeout` | `int` | > 0; default `60` | Seconds budget per classification call (current route call site value) |
| `kill_tree_on_cancel` | `bool` | always `True` for subprocess engines | Cancellation terminates the whole process group (documents `_signal_tree` behavior) |

Frozen (immutable): tests substitute whole instances via `monkeypatch.setitem`,
never mutate shared state — same discipline as `_with_mcp`'s copy-not-mutate rule.

### Validation rules (enforced where)

- Unknown `name` at mission start → `ValueError` (existing message) — `run_mission_cli` guard 1.
- `validated is False` at production-mission start → `EngineNotValidated` — guard 2 (FR-003).
- `web_search_headless is False` for research-grade work → `EngineNotValidated`-family refusal — guard 3, defense-in-depth (FR-004).
- Binary (`run_cmd[0]`) absent from `PATH` → `RuntimeError` (existing message) — guard 4 (FR-008).
- Registry consistency `validated ⇒ web_search_headless` → asserted by the contract test suite over every registered spec (not at runtime — the runtime check is guard 3).

## ENGINE_SPECS (registry)

`dict[str, EngineSpec]` — the single source of truth.

Initial contents:

| name | validated | web_search_headless | notes |
|---|---|---|---|
| `claude-code` | ✅ True | ✅ True | the only validated v1 engine (FR-002) |
| `codex` | ❌ False | ✅ True | registered, refused for production until Brick 9 validation |
| `gemini` | ❌ False | ✅ True | registered, refused for production until Brick 9 validation |

Derived views (rebuilt by `register_engine`, never hand-edited):

- `ENGINES: dict[str, list]` = `{name: list(spec.run_cmd)}` — read by `cli.py:_engine_choices`, `tests/test_engine.py`, docs.
- `_ROUTE_CMD: dict[str, list]` = `{name: list(spec.route_cmd)}` — read by `tests/test_engine.py`.

`register_engine(spec: EngineSpec) -> None` — inserts/replaces the spec and
refreshes both views atomically; the only mutation path (used by the contract
suite's fake engine and by Brick 9 additions).

## State transitions

```text
                 (human decision after end-to-end validation — Brick 9)
  unvalidated ────────────────────────────────────────────────────────▶ validated
      │                                                                    │
      │ production mission attempt                                        │ production mission attempt
      ▼                                                                    ▼
  EngineNotValidated refusal                                          mission runs
  (before any department work;                                        (guards pass; behavior
   no silent engine substitution)                                      byte-identical for claude-code)
```

There is no runtime transition: `validated` changes only by editing the registry
in code (an explicit, reviewed human decision per the constitution's governance).

## Relationships

- `run_mission_cli` → reads exactly one `EngineSpec` from `ENGINE_SPECS` (guards + argv + timeouts); never reads the view dicts.
- `_route_via_cli` → reads `route_cmd`/`route_timeout` from the spec (with the preserved claude-code fallback, research.md D6).
- `_call` → unchanged; receives argv + timeout as plain arguments (remains the monkeypatch seam).
- `cli.py` / docs / structure tests → read the derived views only.
- Contract test suite → iterates `ENGINE_SPECS`, generating one fake binary per spec (FR-009).
