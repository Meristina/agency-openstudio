"""Budget-controlled department escalation.

The mission loop stays route -> department -> synthesize -> inspect. This module only
expands one department call into a bounded commander/officer/soldier chain when the
caller explicitly passes an active EscalationConfig.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Callable, Optional


@dataclass(frozen=True)
class EscalationConfig:
    enabled: bool = True
    budget: int = 6


@dataclass(frozen=True)
class AgentRef:
    name: str
    file: Path
    summary: str


@dataclass(frozen=True)
class PhaseRef:
    name: str
    directive: str
    virtual: bool = True


@dataclass(frozen=True)
class SpecialistRoster:
    commanders: dict[str, AgentRef]
    officers: dict[str, list[AgentRef]]
    virtual_officers: dict[str, list[PhaseRef]]
    soldiers: list[AgentRef]


DEPT_COMMANDERS = {
    "marketing": "commander-marketing",
    "product": "commander-product",
    "solve": "commander-problem-solving",
    "finance": "commander-finance",
    "comms": "commander-comms",
    "data": "commander-data",
    "ops": "commander-ops",
    "people": "commander-people",
    "tech": "commander-tech",
}

DEPT_OFFICERS = {
    "marketing": (
        "officer-1-research",
        "officer-2-strategy",
        "officer-3-brand",
        "officer-4-demand",
        "officer-5-lifecycle",
        "officer-6-measurement",
    ),
    "product": (
        "officer-1-discovery",
        "officer-2-pricing",
        "officer-3-prioritization",
        "officer-4-design",
        "officer-5-delivery",
    ),
    "solve": (
        "officer-1-define-problem",
        "officer-2-root-cause",
        "officer-3-solution",
        "officer-4-launch-actions",
        "officer-5-monitor",
    ),
    "finance": (
        "officer-1-business-case",
        "officer-2-pricing",
        "officer-3-commercial",
        "officer-4-pipeline",
        "officer-5-accounts",
        "officer-6-reporting",
    ),
}

WEBSEARCH_CLAUSE = (
    "CRITICAL: Use WebSearch to find current, real data. Never invent statistics, "
    "market sizes, or citations. Every factual claim must come from a real source "
    "you have searched and verified."
)

__all__ = [
    "AgentRef",
    "DEPT_COMMANDERS",
    "DEPT_OFFICERS",
    "EscalationConfig",
    "PhaseRef",
    "SpecialistRoster",
    "build_roster",
    "run_department",
]


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    return text[end + 4 :].lstrip() if end != -1 else text


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    lines = text[3:end].splitlines()
    out: dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"')
        if value in (">-", "|-"):
            block = []
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            out[key] = " ".join(p for p in block if p)
            continue
        out[key] = value
        i += 1
    return out


def _summary(text: str) -> str:
    first = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return first[:200]


def _agent_ref(path: Path) -> Optional[AgentRef]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    fm = _frontmatter(raw)
    name = fm.get("name")
    desc = fm.get("description")
    if not name or not desc:
        return None
    return AgentRef(name=name, file=path, summary=_summary(desc))


def _load_body(ref: AgentRef) -> Optional[str]:
    try:
        return _strip_frontmatter(ref.file.read_text(encoding="utf-8"))
    except OSError:
        return None


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "phase"


def _virtual_phases(dept: str, commander: AgentRef) -> list[PhaseRef]:
    body = _load_body(commander) or ""
    refs = []
    for m in re.finditer(r"^\s*\d+\.\s+\*\*(O\d+[^*]+)\*\*\s*(?:\([^)]+\))?\s*[—-]\s*(.+)$", body, re.M):
        title = " ".join(m.group(1).split())
        directive = " ".join(m.group(2).split())
        refs.append(PhaseRef(name=f"{dept}/{_slug(title)}", directive=f"{title} - {directive}"))
    return refs


def build_roster(payload_agents_dir: Path) -> SpecialistRoster:
    refs: dict[str, AgentRef] = {}
    for path in payload_agents_dir.glob("*.md"):
        ref = _agent_ref(path)
        if ref:
            refs[ref.name] = ref
    commanders = {dept: refs[name] for dept, name in DEPT_COMMANDERS.items() if name in refs}
    officers = {
        dept: [refs[name] for name in names if name in refs]
        for dept, names in DEPT_OFFICERS.items()
    }
    virtual = {
        dept: _virtual_phases(dept, commander)
        for dept, commander in commanders.items()
        if not officers.get(dept)
    }
    soldiers = [ref for name, ref in sorted(refs.items()) if name.startswith("soldier-")]
    return SpecialistRoster(commanders=commanders, officers=officers, virtual_officers=virtual, soldiers=soldiers)


def _emit(on_event: Optional[Callable[[dict], None]], event: dict) -> None:
    if on_event is None:
        return
    try:
        on_event(event)
    except Exception:
        pass


def _check_cancel(should_cancel: Optional[Callable[[], bool]], cancelled: type[Exception]) -> None:
    if should_cancel is not None and should_cancel():
        raise cancelled()


def _est(prompt: str, output: str = "") -> int:
    return (len(prompt) + len(output) + 3) // 4


def _prior_outputs(dept_outputs: dict) -> str:
    if not dept_outputs:
        return "(no prior department output)"
    return "\n\n".join(f"### {dept.upper()}\n{str(output)[:4000]}" for dept, output in dept_outputs.items())


def _compact_roster(dept: str, roster: SpecialistRoster) -> str:
    parts = ["COMMANDER:", roster.commanders[dept].name]
    dept_officers = roster.officers.get(dept) or roster.virtual_officers.get(dept) or []
    parts.append("\nOFFICERS:")
    for ref in dept_officers:
        parts.append(f"- {ref.name}: {getattr(ref, 'summary', getattr(ref, 'directive', ''))}")
    parts.append("\nSOLDIERS:")
    for ref in roster.soldiers:
        parts.append(f"- {ref.name}: {ref.summary}")
    return "\n".join(parts)


def _extract_json_object(text: str) -> Optional[dict]:
    match = re.search(r"\{.*\}", text or "", re.S)
    if not match:
        return None
    try:
        obj = json.loads(match.group())
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def _validate_selection(dept: str, raw: Optional[dict], roster: SpecialistRoster) -> tuple[dict, bool]:
    if not raw:
        return {"fallback": "selection-unparseable"}, False
    valid_officers = {r.name for r in roster.officers.get(dept, [])}
    valid_officers.update(r.name for r in roster.virtual_officers.get(dept, []))
    valid_soldiers = {r.name for r in roster.soldiers}
    # LLMs sometimes emit null instead of [] — .get(key, default) does not
    # cover a present-but-null key, so coerce anything non-list to []
    raw_officers = raw.get("officers") if isinstance(raw.get("officers"), list) else []
    raw_soldiers = raw.get("soldiers") if isinstance(raw.get("soldiers"), list) else []
    officers = [n for n in raw_officers if isinstance(n, str) and n in valid_officers]
    soldiers = [n for n in raw_soldiers if isinstance(n, str) and n in valid_soldiers]
    rationale = raw.get("rationale") if isinstance(raw.get("rationale"), dict) else {}
    selection = {
        "officers": officers,
        "soldiers": soldiers,
        "rationale": {n: str(rationale.get(n) or "(no rationale returned)") for n in officers + soldiers},
    }
    return selection, bool(officers or soldiers)


def _selection_prompt(dept: str, goal: str, dept_outputs: dict, roster: SpecialistRoster, budget: int) -> str:
    commander = _load_body(roster.commanders[dept]) or ""
    return (
        f"{commander}\n\nMISSION GOAL:\n{goal}\n\n"
        f"PRIOR DEPARTMENT OUTPUTS:\n{_prior_outputs(dept_outputs)}\n\n"
        f"BUDGET: {budget} total escalation calls including this selection.\n\n"
        f"COMPACT SPECIALIST ROSTER:\n{_compact_roster(dept, roster)}\n\n"
        "Select only the officers and soldiers needed. Output ONLY JSON like "
        '{"officers":["officer-2-strategy"],"soldiers":["soldier-stp"],'
        '"rationale":{"officer-2-strategy":"why"}}.'
    )


def _specialist_prompt(
    dept: str,
    role: str,
    name: str,
    doctrine: str,
    goal: str,
    dept_outputs: dict,
    commander_output: str = "",
    prior_specialist_outputs: list[dict] = None,
    *,
    asset_clause: Optional[str],
    context_clause: Optional[str],
    persona_doctrine: Optional[dict],
    directive: str = "",
) -> str:
    persona = (persona_doctrine or {}).get(dept)
    # commander is already surfaced via COMMANDER BRIEF and selection is
    # orchestration meta — including either here would duplicate prompt text
    prior = "\n\n".join(
        f"### {i['role'].upper()} {i['name']}\n{i.get('output', '')}"
        for i in (prior_specialist_outputs or [])
        if i.get("output") and i.get("role") not in ("commander", "selection")
    )
    return (
        f"You are {name}, acting as the {role} for the {dept} department.\n\n"
        f"MISSION GOAL:\n{goal}\n\n"
        f"PRIOR DEPARTMENT OUTPUTS:\n{_prior_outputs(dept_outputs)}\n\n"
        + (f"COMMANDER BRIEF:\n{commander_output}\n\n" if commander_output else "")
        + (f"PRIOR SPECIALIST OUTPUTS:\n{prior}\n\n" if prior else "")
        + (f"PHASE DIRECTIVE:\n{directive}\n\n" if directive else "")
        + (f"DOCTRINE:\n{doctrine}\n\n" if doctrine else "")
        + (f"PERSONA DOCTRINE:\n{persona}\n\n" if persona else "")
        + "Produce your scoped department deliverable.\n"
        + WEBSEARCH_CLAUSE
        + (f"\n\n{context_clause}" if context_clause else "")
        + (f"\n\n{asset_clause}" if asset_clause else "")
    )


def _fallback_prompt(dept: str, goal: str, dept_outputs: dict, doctrine: str, reason: str) -> str:
    return (
        f"You are the {dept} department commander for an AI agency.\n\n"
        f"MISSION GOAL:\n{goal}\n\nPRIOR DEPARTMENT OUTPUTS:\n{_prior_outputs(dept_outputs)}\n\n"
        f"ESCALATION FALLBACK REASON: {reason}\n\n"
        f"DEPARTMENT DOCTRINE:\n{doctrine}\n\n"
        "Produce a complete, detailed deliverable for this department.\n"
        + WEBSEARCH_CLAUSE
    )


def _record(role: str, name: str, prompt: str, output: str, **extra) -> dict:
    rec = {
        "role": role,
        "name": name,
        "task": prompt[:2000],
        "output": output,
        "est_tokens": _est(prompt, output),
    }
    rec.update(extra)
    return rec


def _skip(role: str, name: str, reason: str, **extra) -> dict:
    rec = {"role": role, "name": name, "task": "", "skipped": reason, "est_tokens": 0}
    rec.update(extra)
    return rec


def _assemble(commander: str, invocations: list[dict]) -> str:
    parts = [f"## Commander Brief\n\n{commander}"] if commander else []
    for inv in invocations:
        # commander is already seeded above as the brief — re-appending its
        # record would duplicate it verbatim in every escalated dept output
        if inv.get("role") in ("selection", "commander") or inv.get("skipped") or not inv.get("output"):
            continue
        parts.append(f"## {inv['role'].title()}: {inv['name']}\n\n{inv['output']}")
    return "\n\n".join(parts)


def run_department(
    dept: str,
    goal: str,
    dept_outputs: dict,
    *,
    config: EscalationConfig,
    roster: SpecialistRoster,
    call: Callable[..., str],
    base_cmd: list,
    exec_cmd: list,
    run_timeout: int,
    should_cancel: Optional[Callable[[], bool]] = None,
    on_event: Optional[Callable[[dict], None]] = None,
    asset_clause: Optional[str] = None,
    context_clause: Optional[str] = None,
    persona_doctrine: Optional[dict] = None,
    cancelled: type[Exception] = Exception,
) -> tuple[str, dict]:
    commander = roster.commanders[dept]
    commander_doc = _load_body(commander) or ""
    budget = max(0, int(config.budget))
    trace = {"budget": budget, "consumed": 0, "est_tokens": 0, "selection": {}, "invocations": []}

    def spend(role: str, name: str, prompt: str, cmd: list, **extra) -> Optional[str]:
        if trace["consumed"] >= budget:
            trace["invocations"].append(_skip(role, name, "budget-exhausted", **extra))
            _emit(on_event, {"phase": "escalation", "dept": dept, "step": role, "name": name, "status": "skipped"})
            return None
        _check_cancel(should_cancel, cancelled)
        _emit(on_event, {"phase": "escalation", "dept": dept, "step": role, "name": name, "status": "start"})
        try:
            output = call(cmd, prompt, timeout=run_timeout, should_cancel=should_cancel)
        except cancelled:
            raise
        except Exception:
            trace["invocations"].append(_skip(role, name, "call-failed", **extra))
            _emit(on_event, {"phase": "escalation", "dept": dept, "step": role, "name": name, "status": "skipped"})
            return None
        rec = _record(role, name, prompt, output, **extra)
        trace["invocations"].append(rec)
        trace["consumed"] += 1
        trace["est_tokens"] += rec["est_tokens"]
        _emit(on_event, {"phase": "escalation", "dept": dept, "step": role, "name": name, "status": "done"})
        return output

    selection_text = spend("selection", f"{commander.name}-selection", _selection_prompt(dept, goal, dept_outputs, roster, budget), base_cmd)
    selection, selected_any = _validate_selection(dept, _extract_json_object(selection_text or ""), roster)
    trace["selection"] = selection
    if not selected_any:
        reason = selection.get("fallback") or "router-selected-none"
        prompt = _fallback_prompt(dept, goal, dept_outputs, commander_doc, reason)
        output = call(exec_cmd, prompt, timeout=run_timeout, should_cancel=should_cancel)
        trace["finalized_by"] = "doctrine-fallback"
        trace["fallback_reason"] = reason
        return output, trace

    commander_prompt = _specialist_prompt(
        dept,
        "commander",
        commander.name,
        commander_doc,
        goal,
        dept_outputs,
        asset_clause=asset_clause,
        context_clause=context_clause,
        persona_doctrine=persona_doctrine,
    )
    commander_output = spend("commander", commander.name, commander_prompt, exec_cmd)

    officer_refs = {r.name: r for r in roster.officers.get(dept, [])}
    virtual_refs = {r.name: r for r in roster.virtual_officers.get(dept, [])}
    soldier_refs = {r.name: r for r in roster.soldiers}
    for name in selection["officers"]:
        ref = officer_refs.get(name)
        virtual = virtual_refs.get(name)
        if not ref and not virtual:
            trace["invocations"].append(_skip("officer", name, "missing-file"))
            continue
        doctrine = _load_body(ref) if ref else commander_doc
        if doctrine is None:
            trace["invocations"].append(_skip("officer", name, "missing-file"))
            continue
        prompt = _specialist_prompt(
            dept,
            "officer",
            name,
            doctrine,
            goal,
            dept_outputs,
            commander_output or "",
            trace["invocations"],
            asset_clause=asset_clause,
            context_clause=context_clause,
            persona_doctrine=persona_doctrine,
            directive=virtual.directive if virtual else "",
        )
        spend("officer", name, prompt, exec_cmd, **({"virtual": True} if virtual else {}))

    for name in selection["soldiers"]:
        ref = soldier_refs.get(name)
        doctrine = _load_body(ref) if ref else None
        if doctrine is None:
            trace["invocations"].append(_skip("soldier", name, "missing-file"))
            continue
        prompt = _specialist_prompt(
            dept,
            "soldier",
            name,
            doctrine,
            goal,
            dept_outputs,
            commander_output or "",
            trace["invocations"],
            asset_clause=asset_clause,
            context_clause=context_clause,
            persona_doctrine=persona_doctrine,
        )
        spend("soldier", name, prompt, exec_cmd)

    output = _assemble(commander_output or "", trace["invocations"])
    if not output.strip():
        output = call(exec_cmd, _fallback_prompt(dept, goal, dept_outputs, commander_doc, "budget-exhausted-before-assembly"), timeout=run_timeout, should_cancel=should_cancel)
        trace["finalized_by"] = "doctrine-fallback"
        trace["fallback_reason"] = "budget-exhausted-before-assembly"
    else:
        trace["finalized_by"] = "escalation"
    return output, trace
