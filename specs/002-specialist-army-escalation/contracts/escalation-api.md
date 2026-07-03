# Contract: Escalation Library API

The externally observable surface this feature adds. Anything not listed here is
internal and may change freely.

## 1. `run_mission_cli` — one new keyword parameter

```python
def run_mission_cli(
    goal: str,
    engine: str = "claude-code",
    # ... all existing hooks unchanged ...
    escalation: Optional["EscalationConfig"] = None,   # NEW
) -> dict: ...
```

**Contract**:
- `escalation=None` (default) ⇒ every subprocess command and every prompt is
  **byte-identical** to the pre-feature implementation on the same inputs
  (regression-tested by capturing `_call` args). The returned dossier has NO
  `escalation` key.
- `escalation=EscalationConfig(enabled=False)` or `budget <= 0` ⇒ same as `None`.
- Active escalation touches ONLY the department-execution phase: the router call, the
  synthesis call, the inspector call, the veto loop, `MAX_ITERS`, `_short_verdict`,
  checkpoint/resume invariants, and cancellation semantics are unchanged.
- The selection call runs on the base command (never MCP-spliced); commander/officer/
  soldier calls run on `exec_cmd` (MCP-spliced when configured), mirroring the existing
  department/inspector split.
- All escalation calls respect `spec.run_timeout`, `should_cancel` (kill-in-flight), and
  the engine refusal guards (`ensure_production_engine` runs before anything).

## 2. `agency_cli/escalation.py` — module surface

```python
@dataclass(frozen=True)
class EscalationConfig:
    enabled: bool = True
    budget: int = 6

def build_roster(payload_agents_dir: Path) -> SpecialistRoster: ...
    # Raises nothing: unreadable/malformed files are skipped (logged to stderr).

def run_department(
    dept: str,
    goal: str,
    dept_outputs: dict,
    *,
    config: EscalationConfig,
    roster: SpecialistRoster,
    call: Callable[..., str],        # cli_engine._call, injected (testability)
    base_cmd: list, exec_cmd: list,
    run_timeout: int,
    should_cancel: Optional[Callable[[], bool]] = None,
    on_event: Optional[Callable[[dict], None]] = None,
    asset_clause: Optional[str] = None,
    context_clause: Optional[str] = None,
    persona_doctrine: Optional[dict] = None,
) -> tuple[str, dict]:               # (department_output, DeptEscalationTrace)
```

**Contract**:
- Never raises on specialist failure: a failed/missing specialist is recorded as skipped
  (`FR-007`); only `MissionCancelled` propagates.
- `consumed <= config.budget` always (`SC-002`).
- Department output is a deterministic assembly (commander brief + labeled specialist
  sections in execution order) — no extra subprocess call for assembly.
- Prompts embed the WebSearch/no-invention clause and thread `asset_clause` /
  `context_clause` / `persona_doctrine[dept]` exactly as `_dept_prompt` does.

## 3. `runner_bridge.run` — product default resolution

```python
def run(goal, engine="claude-code", ..., escalation=None): ...
```

- `escalation=None` ⇒ resolves to `EscalationConfig()` (ON, budget 6) — the clarified
  product default.
- `escalation=False` or `EscalationConfig(enabled=False)` / budget 0 ⇒ passes `None`
  down (byte-identical off).
- `escalation=EscalationConfig(...)` / a valid `{"enabled":…, "budget":…}` dict ⇒ passed
  through (dict coerced, types checked, `ValueError` on junk).

## 4. `agency` CLI flags

```text
agency run  "goal" [--no-escalation] [--escalation-budget N]
agency batch run    [--no-escalation] [--escalation-budget N]
agency resume <id>  [--no-escalation] [--escalation-budget N]
```

`--escalation-budget 0` ≡ `--no-escalation`. Defaults: escalation on, budget 6.

**Precedence**: `--no-escalation` ALWAYS wins when both flags are given — an explicit
disable beats a budget tune, whatever `N` says (`--no-escalation --escalation-budget 8`
⇒ disabled). The studio parser applies the same rule (below).

## 5. Studio mission request (HTTP, additive field)

`POST` mission-start payload gains an optional field:

```json
{ "escalation": { "enabled": true, "budget": 6 } }
```

- Absent ⇒ product default (on, budget 6). Both keys optional: missing `enabled` ⇒
  `true`, missing `budget` ⇒ `6`. Types strictly validated (bool / int, `400` on junk).
- Same precedence as the CLI: `"enabled": false` wins over any `budget` value;
  `"budget": 0` ≡ `"enabled": false`.
- Forwarded to `runner_bridge.run` ONLY if its signature accepts `escalation`
  (existing `inspect.signature` degradation pattern — an older agencykit ignores it).
- No new endpoint, no bind/CORS/path change (Principle VI untouched).

## 6. Events (observational)

```python
{"phase": "escalation", "dept": str, "step": "selection|commander|officer|soldier",
 "name": str, "status": "start|done|skipped"}
```

Same swallow-exceptions contract as every `_emit` event; consumers must tolerate
unknown fields.
