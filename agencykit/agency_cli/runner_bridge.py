"""runner_bridge — headless mission path.

Drives the local agent CLI engine (`cli_engine.run_mission_cli`), saves the returned
Mission Dossier to the `~/.agency` store (so `agency missions/resume/export` see it),
and serializes it into `missions/<NNN-slug>/` as Markdown (`dossier.md` +
`deliverable.md`) for a project-local human-readable copy.
"""

import json
import re
from pathlib import Path
from typing import Callable, NamedTuple, Optional

from agency_kit.store import slug as _store_slug


class MissionResult(NamedTuple):
    """Result of a headless run: the project-local mission folder + the dossier.

    `dossier` carries `verdicts` so callers (e.g. batch_runner) can record the
    real Inspector verdict instead of assuming success.
    """
    path: Path
    dossier: dict


def _last_verdict(dossier: dict) -> str:
    """The Inspector's final verdict token, or 'DELIVERED' if none was recorded.
    Tolerant of a malformed (non-dict) verdict entry so it can't raise."""
    verdicts = dossier.get("verdicts") or []
    last = verdicts[-1] if verdicts else None
    return last.get("verdict", "DELIVERED") if isinstance(last, dict) else "DELIVERED"


def _resolve_escalation(value):
    from .escalation import EscalationConfig
    if value is None:
        return EscalationConfig()
    if value is False:
        return None
    if isinstance(value, EscalationConfig):
        return value if value.enabled and value.budget > 0 else None
    if not isinstance(value, dict):
        raise ValueError("escalation must be None, False, EscalationConfig, or dict")
    allowed = {"enabled", "budget"}
    if set(value) - allowed:
        raise ValueError("escalation contains unknown keys")
    enabled = value.get("enabled", True)
    budget = value.get("budget", 6)
    if not isinstance(enabled, bool) or not isinstance(budget, int) or isinstance(budget, bool):
        raise ValueError("escalation.enabled must be bool and escalation.budget must be int")
    if not enabled or budget <= 0:
        return None
    return EscalationConfig(enabled=enabled, budget=budget)


def _resolve_verification(value):
    from .verification import VerificationConfig, coerce_config
    if isinstance(value, VerificationConfig):
        return None if value.min_sources == 0 and not value.resolve else value
    try:
        config = coerce_config(value)
    except Exception:
        config = VerificationConfig()
    return None if config.min_sources == 0 and not config.resolve else config


def _next_id(missions: Path) -> str:
    nums = []
    if missions.exists():
        for p in missions.iterdir():
            m = re.match(r"(\d{3})-", p.name)
            if m:
                nums.append(int(m.group(1)))
    return f"{(max(nums) + 1) if nums else 1:03d}"


def _dossier_md(mission_id: str, d: dict) -> str:
    """Render the dossier dict as Markdown."""
    lines = [f"# Mission Dossier — {mission_id}", ""]
    for key in ("goal", "route", "context", "iteration", "direction_check"):
        lines.append(f"- **{key}**: {d.get(key)}")
    dept_keys = list((d.get("dept_outputs") or {}).keys())
    if dept_keys:
        lines.append(f"- **departments run**: {', '.join(dept_keys)}")
    lines.append("\n## Decisions")
    for dec in d.get("decisions", []) or []:
        lines.append(f"- {dec}")
    lines.append("\n## Sources")
    for i, s in enumerate(d.get("sources", []) or [], 1):
        lines.append(f"{i}. {s}")
    verification = d.get("verification")
    if isinstance(verification, dict) and isinstance(verification.get("final"), dict):
        lines.extend(_verification_md(verification))
    lines.append("\n## Open to verify")
    for o in d.get("open_to_verify", []) or []:
        lines.append(f"- {o}")
    lines.append("\n## Verdicts")
    for v in d.get("verdicts", []) or []:
        lines.append(f"- {json.dumps(v, ensure_ascii=False)}")
    if d.get("residual_risk"):
        lines.append(f"\n## Residual risk\n{d['residual_risk']}")
    # Escalation trace addendum. Keyed on `escalation` so a run without it (the key
    # is absent — escalation off or pre-feature) is byte-identical, mirroring `assets`.
    escalation = d.get("escalation")
    if escalation and isinstance(escalation, dict):
        lines.append("\n## Escalation")
        for dept, trace in escalation.items():
            if not isinstance(trace, dict):
                lines.append(f"- {dept}: {json.dumps(trace, ensure_ascii=False)}")
                continue
            lines.append(f"\n### {dept}")
            lines.append(
                f"- budget: {trace.get('budget')}, consumed: {trace.get('consumed')}, "
                f"est_tokens: {trace.get('est_tokens')} (advisory)"
            )
            if trace.get("finalized_by"):
                reason = f" ({trace['fallback_reason']})" if trace.get("fallback_reason") else ""
                lines.append(f"- finalized by: {trace['finalized_by']}{reason}")
            sel = trace.get("selection") or {}
            if sel.get("fallback"):
                lines.append(f"- selection fallback: {sel['fallback']}")
            elif sel.get("officers") or sel.get("soldiers"):
                lines.append(
                    f"- selection: officers={sel.get('officers')}, soldiers={sel.get('soldiers')}"
                )
                for name, why in (sel.get("rationale") or {}).items():
                    lines.append(f"  - {name}: {why}")
            for inv in trace.get("invocations") or []:
                if not isinstance(inv, dict):
                    continue
                if inv.get("skipped"):
                    lines.append(f"- {inv.get('role')} {inv.get('name')}: SKIPPED ({inv['skipped']})")
                else:
                    lines.append(
                        f"- {inv.get('role')} {inv.get('name')} (est_tokens: {inv.get('est_tokens', 0)})"
                    )
    # Studio multimodal addendum. Keyed on `assets` so a non-studio run (the key is
    # absent) is byte-identical to the pre-Wave-3 output. Each entry is a render
    # manifest dict ({type, status, url|reason, model, seconds}); a non-dict entry
    # falls back to a JSON line, mirroring the Verdicts section.
    assets = d.get("assets")
    if assets:
        lines.append("\n## Assets")
        for a in assets if isinstance(assets, list) else [assets]:
            if isinstance(a, dict):
                ref = a.get("url") or a.get("reason") or ""
                meta = []
                if a.get("model"):
                    meta.append(str(a["model"]))
                if a.get("seconds") is not None:
                    meta.append(f"{a['seconds']}s")
                suffix = f" ({', '.join(meta)})" if meta else ""
                lines.append(
                    f"- {a.get('type', 'asset')} [{a.get('status', '?')}] {ref}{suffix}".rstrip()
                )
            else:
                lines.append(f"- {json.dumps(a, ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def _verification_md(verification: dict) -> list[str]:
    final = verification.get("final") or {}
    lines = ["\n## Source verification"]
    sources = final.get("sources") or []
    rate = final.get("rate")
    if rate is None:
        # `rate` is None for distinct reasons — resolution off, total network outage,
        # or zero checkable sources. Never claim "not enabled" for an enabled run.
        # final.resolve (the cycle that produced this rate) is the driver; the
        # mission-level config is only the fallback for records lacking the field.
        reason = (
            "resolution not enabled"
            if not final.get("resolve", verification.get("resolve"))
            else "network unavailable or no checkable sources"
        )
        lines.append(
            f"- Verified-source rate: unverified ({reason}) — counted {len(sources)} cited sources"
        )
    else:
        checkable = sum(1 for s in sources if s.get("status") in {"resolved", "ambiguous", "unresolved"})
        resolved = sum(1 for s in sources if s.get("status") == "resolved")
        lines.append(f"- Verified-source rate: {round(rate * 100)}% ({resolved} of {checkable} checkable)")
    lines.append(f"- Minimum per department: {verification.get('min_sources')}")
    per_dept = final.get("per_dept") or {}
    if per_dept:
        lines.append("\n| Department | Counted | Min | OK |")
        lines.append("|---|---:|---:|---|")
        for dept, item in per_dept.items():
            ok = "yes" if item.get("ok") else "no"
            lines.append(f"| {dept} | {item.get('counted', 0)} | {item.get('min', 0)} | {ok} |")
    unresolved = [s for s in sources if s.get("status") == "unresolved"]
    for src in unresolved:
        lines.append(f"- Unresolved: {src.get('url')} ({src.get('detail')})")
    for claim in final.get("missing") or []:
        lines.append(f"- Missing sources: {claim}")
    truncated = int(final.get("truncated") or 0)
    if truncated:
        lines.append(f"- {truncated} sources not checked — cap reached")
    return lines


def serialize_dossier(dossier: dict, project_root) -> Path:
    """Write the dossier + deliverable into a fresh missions/<NNN-slug>/ folder."""
    project_root = Path(project_root)
    missions = project_root / "missions"
    missions.mkdir(parents=True, exist_ok=True)
    slug = _store_slug(dossier.get("goal", ""), max_words=6)
    # _next_id() then mkdir() is a TOCTOU race: two concurrent missions can read the
    # same highest number and collide. mkdir() (no exist_ok) is the atomic claim —
    # on FileExistsError, recompute the next id and retry rather than aborting.
    for _ in range(100):
        mission_id = f"{_next_id(missions)}-{slug}"
        out = missions / mission_id
        try:
            out.mkdir()
            break
        except FileExistsError:
            continue
    else:
        raise RuntimeError(f"could not allocate a mission folder under {missions}")
    (out / "dossier.md").write_text(_dossier_md(mission_id, dossier), encoding="utf-8")
    delivered = dossier.get("delivered") or "(no deliverable)"
    (out / "deliverable.md").write_text(
        f"# Deliverable — {mission_id}\n\n{delivered}\n", encoding="utf-8"
    )
    return out


def _run_and_persist(
    goal: str,
    project_root: str,
    engine: str,
    on_event: Optional[Callable[[dict], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
    asset_clause: Optional[str] = None,
    render_assets: Optional[Callable[[dict], None]] = None,
    context_clause: Optional[str] = None,
    mcp_config_path: Optional[str] = None,
    mcp_allowed_tools: Optional[list] = None,
    persona_doctrine: Optional[dict] = None,
    on_checkpoint: Optional[Callable[[dict], None]] = None,
    resume_state: Optional[dict] = None,
    escalation=None,
    verification=None,
) -> MissionResult:
    """Drive the engine for `goal`, persist to the ~/.agency store (so
    `agency missions/resume/export` see it) AND serialize the project-local
    missions/<id>/ copy. Shared by run() and resume() so both persist identically.

    `on_event` is an optional observational progress callback threaded straight
    through to `run_mission_cli` (used by the Studio server to stream SSE). Default
    None ⇒ unchanged behaviour.

    `should_cancel` is an optional cooperative-cancel predicate. When it fires,
    `run_mission_cli` raises `MissionCancelled` BEFORE returning — so the store.save
    and serialize_dossier below never run, and a cancelled mission leaves no trace.

    `asset_clause` / `render_assets` are the Studio's multimodal hook (default None
    ⇒ unchanged). `asset_clause` is threaded to `run_mission_cli` (it lets a
    department/synthesis emit fenced `asset` markers). `render_assets` is invoked
    AFTER the engine returns but BEFORE persistence, so both the store copy and the
    serialized missions/<id>/ copy carry the manifest it writes into
    `dossier['assets']` (and the cosmetic rewrite it makes to `dossier['delivered']`).
    It is gated strictly on a clean Inspector PASS and is best-effort.

    `context_clause` is the Studio's Wave-4 RAG hook — sourced excerpts from the user's
    uploaded documents, threaded to `run_mission_cli` and appended to the department +
    synthesis prompts. Default None ⇒ unchanged; same additive contract as `asset_clause`.

    `mcp_config_path` / `mcp_allowed_tools` are the Studio's Wave-6 MCP tool-calling hook —
    a `--mcp-config` file (built from the user's MCP servers) and the `mcp__*` tools to allow,
    threaded to `run_mission_cli` so departments + synthesis can invoke those tools. Default
    None ⇒ unchanged; same additive contract as `context_clause`.

    `persona_doctrine` is the Studio's Wave-6 persona-doctrine hook — a dict keyed by
    department (+ the reserved `"commander"` key) → a curated persona string, threaded to
    `run_mission_cli` where it augments the DEPARTMENT DOCTRINE (departments) and commander
    doctrine (synthesis) prompt text only. Default None ⇒ unchanged; same additive contract.

    `on_checkpoint` / `resume_state` are the Studio's crash-recovery hook — an observational
    snapshot callback fired at each phase boundary, and a prior snapshot to resume an interrupted
    mission from mid-flight (skip routing + completed departments, re-enter the veto loop at the
    saved iteration). Threaded straight to `run_mission_cli`. Default None ⇒ unchanged. Note a
    resumed mission persists under a FRESH mission_id (line below) exactly like a first run — the
    checkpoint is transient crash-recovery, not the durable dossier.
    """
    from agency_kit import store
    from .engines.cli_engine import run_mission_cli
    import inspect
    engine_kwargs = dict(
        engine=engine,
        on_event=on_event,
        should_cancel=should_cancel,
        asset_clause=asset_clause,
        context_clause=context_clause,
        mcp_config_path=mcp_config_path,
        mcp_allowed_tools=mcp_allowed_tools,
        persona_doctrine=persona_doctrine,
        on_checkpoint=on_checkpoint,
        resume_state=resume_state,
        escalation=_resolve_escalation(escalation),
    )
    if "verification" in inspect.signature(run_mission_cli).parameters:
        engine_kwargs["verification"] = _resolve_verification(verification)
    dossier = run_mission_cli(goal, **engine_kwargs)
    dossier["mission_id"] = store.new_mission_id(goal)
    # Stamp the canonical project root so store.list_missions can scope history to
    # this project (the Studio GUI launched with --path), not the global store.
    dossier["project_root"] = store.canonical_project_root(project_root)
    # Best-effort multimodal render. Gate on the EXACT 'PASS' token: a VETO at the
    # iteration cap still returns a populated `delivered` (with residual_risk), and
    # an unrecognized verdict breaks the loop with neither a PASS nor residual_risk —
    # so `_last_verdict(dossier) == 'PASS'` is the only correct gate (never "no
    # residual_risk"). mission_id is already set so the renderer can scope its output
    # dir. Never destructive: any failure (MediaUnavailable when [media] is absent, a
    # Metal crash) is swallowed so the already-inspected deliverable is still persisted.
    if render_assets is not None and _last_verdict(dossier) == "PASS":
        try:
            render_assets(dossier)
        except Exception:
            pass
    store.save(dossier)
    path = serialize_dossier(dossier, Path(project_root))
    return MissionResult(path=path, dossier=dossier)


def run(
    goal: str,
    project_root: str = ".",
    engine: str = "claude-code",
    on_event: Optional[Callable[[dict], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
    asset_clause: Optional[str] = None,
    render_assets: Optional[Callable[[dict], None]] = None,
    context_clause: Optional[str] = None,
    mcp_config_path: Optional[str] = None,
    mcp_allowed_tools: Optional[list] = None,
    persona_doctrine: Optional[dict] = None,
    on_checkpoint: Optional[Callable[[dict], None]] = None,
    resume_state: Optional[dict] = None,
    escalation=None,
    verification=None,
) -> MissionResult:
    """Headless run: drive a local agent CLI engine, then serialize the dossier.

    engine="claude-code" — `claude -p "..." --allowedTools WebSearch`  (default, validated)
    engine="codex" / "gemini" — registered but NOT validated: run_mission_cli refuses them
        with EngineNotValidated until they are validated end-to-end (no silent substitution).
    No API key required: each CLI uses its own authenticated session + web search.

    `on_event` is an optional observational progress callback (route/dept/synth/
    inspect events) used by the Studio server to stream live SSE progress.

    `should_cancel` is an optional cooperative-cancel predicate polled at phase
    boundaries; if it fires the mission stops and nothing is persisted.

    `asset_clause` / `render_assets` are the Studio's optional multimodal hook (see
    `_run_and_persist`); default None ⇒ unchanged behaviour. `context_clause` is the
    Wave-4 RAG hook (sourced excerpts from the user's docs); default None ⇒ unchanged.
    `mcp_config_path` / `mcp_allowed_tools` are the Wave-6 MCP tool-calling hook (a
    `--mcp-config` file + allowed `mcp__*` tools for department/synthesis calls); default
    None ⇒ unchanged.

    `on_checkpoint` / `resume_state` are the crash-recovery hook (a snapshot callback fired at
    phase boundaries, and a prior snapshot to continue an interrupted mission from mid-flight);
    default None ⇒ unchanged. NB this is distinct from `resume(mission_id)` below, which re-runs a
    COMPLETED mission's goal from scratch — `resume_state` continues an interrupted one.

    Returns a MissionResult (path + dossier) so callers can read the real verdict.
    """
    return _run_and_persist(
        goal, project_root, engine,
        on_event=on_event, should_cancel=should_cancel,
        asset_clause=asset_clause, render_assets=render_assets,
        context_clause=context_clause,
        mcp_config_path=mcp_config_path, mcp_allowed_tools=mcp_allowed_tools,
        persona_doctrine=persona_doctrine,
        on_checkpoint=on_checkpoint, resume_state=resume_state,
        escalation=escalation,
        verification=verification,
    )


def resume(
    mission_id: str,
    project_root: str = ".",
    engine: str = "claude-code",
    on_event: Optional[Callable[[dict], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
    asset_clause: Optional[str] = None,
    render_assets: Optional[Callable[[dict], None]] = None,
    context_clause: Optional[str] = None,
    mcp_config_path: Optional[str] = None,
    mcp_allowed_tools: Optional[list] = None,
    persona_doctrine: Optional[dict] = None,
    on_checkpoint: Optional[Callable[[dict], None]] = None,
    escalation=None,
    verification=None,
) -> MissionResult:
    """Re-run a COMPLETED mission's goal through the engine, from scratch.

    NB this is a DIFFERENT operation from the `resume_state` kwarg on `run` /
    `run_mission_cli`: this loads a saved (finished) dossier, takes only its `goal`, and re-runs
    the whole mission fresh — route, departments, and synthesis all execute again, producing a
    new result under a fresh mission id. `resume_state`, by contrast, continues an INTERRUPTED
    mission from its last checkpoint without re-paying the completed phases. The engine is
    single-shot (no quota checkpoint), which is why goal-re-run is all this can offer.

    The multimodal hook (`asset_clause` / `render_assets`) is forwarded too, so a re-run
    regenerates assets under its fresh mission id exactly as a first run would. `on_checkpoint`
    is forwarded as well (the re-run is a normal mission and can be checkpointed); `resume_state`
    is intentionally NOT accepted here — a mission_id re-run and a checkpoint-continue are
    mutually exclusive.
    """
    from agency_kit import store
    saved = store.load(mission_id)
    goal = saved.get("goal", "")
    return _run_and_persist(
        goal, project_root, engine,
        on_event=on_event, should_cancel=should_cancel,
        asset_clause=asset_clause, render_assets=render_assets,
        context_clause=context_clause,
        mcp_config_path=mcp_config_path, mcp_allowed_tools=mcp_allowed_tools,
        persona_doctrine=persona_doctrine,
        on_checkpoint=on_checkpoint,
        escalation=escalation,
        verification=verification,
    )
