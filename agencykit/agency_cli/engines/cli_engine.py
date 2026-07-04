"""cli_engine — run missions via a local agent CLI (Claude Code / Codex / Gemini).

Uses subprocess instead of any LLM SDK or API key: each CLI tool uses its own
authenticated session and its own live web search.

Registered engines (all declare live headless web search — facts must come from real
searched sources, never invented). Only VALIDATED engines may drive a production
mission; unvalidated ones stay registered but are refused (EngineNotValidated) until
they pass end-to-end validation:
  claude-code   claude --allowedTools WebSearch -p "<prompt>"     [validated]
  codex         codex --search exec --color never --sandbox read-only -- "<prompt>"  [unvalidated]
  gemini        gemini -p "<prompt>"        (google_web_search built-in)  [unvalidated]

Extension point: other agent CLIs (cursor-agent, opencode, copilot) can be added
via register_engine(EngineSpec(...)), but only once they can guarantee live web
search headlessly — without it a mission would fabricate data. A new engine stays
validated=False until it is validated end-to-end.
"""

from dataclasses import dataclass
import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from agency_kit.departments import DEPT_NAMES, VALID_DEPTS


@dataclass(frozen=True)
class EngineSpec:
    """One engine's contract: how to invoke it, what it guarantees, and whether
    it may drive a production mission.

    ``kill_tree_on_cancel`` records the guarantee that cancelling or timing out a
    call terminates the engine's whole process group (``_call`` always does this
    today, via ``_signal_tree``); it is declared here so the capability is part of
    the contract. Construction enforces the invariants below (fail fast at
    registration, not deep inside a mission)."""

    name: str
    run_cmd: tuple[str, ...]
    route_cmd: tuple[str, ...]
    web_search_headless: bool
    validated: bool
    run_timeout: int = 900
    route_timeout: int = 60
    kill_tree_on_cancel: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("EngineSpec.name must be non-empty")
        if not self.run_cmd or not self.route_cmd:
            raise ValueError(
                f"EngineSpec '{self.name}': run_cmd and route_cmd must be non-empty argv tuples"
            )
        if self.validated and not self.web_search_headless:
            raise ValueError(
                f"EngineSpec '{self.name}': a validated engine MUST guarantee headless web "
                "search (the engine-neutrality precondition) — set web_search_headless=True "
                "or leave the engine validated=False"
            )
        if self.run_timeout <= 0 or self.route_timeout <= 0:
            raise ValueError(f"EngineSpec '{self.name}': timeouts must be positive")


class EngineNotValidated(RuntimeError):
    """A known, registered engine refused because it may not drive a production mission.

    Raised when the selected engine is unvalidated, or (defence in depth) declares no
    guaranteed headless web search. Messages name the engine, the reason, and the
    validated alternative(s) so callers can surface an actionable refusal — with no
    silent substitution of a different engine.
    """


ENGINE_SPECS: dict[str, EngineSpec] = {
    "claude-code": EngineSpec(
        name="claude-code",
        run_cmd=("claude", "--allowedTools", "WebSearch", "-p"),
        route_cmd=("claude", "-p"),
        web_search_headless=True,
        validated=True,
    ),
    "codex": EngineSpec(
        name="codex",
        run_cmd=("codex", "--search", "exec", "--color", "never", "--sandbox", "read-only", "--"),
        route_cmd=("codex", "--color", "never", "--sandbox", "read-only", "--"),
        web_search_headless=True,
        validated=False,
    ),
    "gemini": EngineSpec(
        name="gemini",
        run_cmd=("gemini", "-p"),
        route_cmd=("gemini", "-p"),
        web_search_headless=True,
        validated=False,
    ),
}


# Compatibility views over ENGINE_SPECS for older readers (CLI --engine choices,
# `agency check`). Mutated IN PLACE by _refresh_engine_views so a consumer that did
# `from cli_engine import ENGINES` keeps a live reference after register_engine —
# never rebound, or such a reference would go stale. ENGINE_SPECS is the sole source
# of truth; the mission loop reads it directly, not these views.
ENGINES: dict = {}
_ROUTE_CMD: dict = {}


def _refresh_engine_views() -> None:
    ENGINES.clear()
    ENGINES.update({name: list(spec.run_cmd) for name, spec in ENGINE_SPECS.items()})
    _ROUTE_CMD.clear()
    _ROUTE_CMD.update({name: list(spec.route_cmd) for name, spec in ENGINE_SPECS.items()})


def register_engine(spec: EngineSpec) -> None:
    """Insert or replace an engine spec and refresh the compatibility views.

    The single supported way to add an engine at runtime (Brick 9). Writing
    ENGINE_SPECS directly skips the view refresh and drifts the CLI/`agency check`
    surfaces, so always go through here."""
    ENGINE_SPECS[spec.name] = spec
    _refresh_engine_views()


_refresh_engine_views()


def _validated_engine_names() -> str:
    names = [name for name, spec in ENGINE_SPECS.items() if spec.validated]
    return ", ".join(names) if names else "none"


def ensure_production_engine(engine: str) -> "EngineSpec":
    """Resolve an engine and enforce the Art. II production preconditions, returning its spec.

    The single gate for "may this engine run a production mission?": unknown name →
    ``ValueError``; registered-but-unvalidated → ``EngineNotValidated``; validated without
    guaranteed headless web search → ``EngineNotValidated`` (defence in depth — the EngineSpec
    invariant makes this state unconstructible through the public API, so it can only arise
    from a hand-built object). No engine is ever silently substituted for the one requested.

    Shared by ``run_mission_cli`` (its opening guard) and any caller that must pre-flight an
    engine before doing work (e.g. the batch runner, so one bad ``--engine`` refuses the whole
    queue up front instead of failing every goal in turn)."""
    spec = ENGINE_SPECS.get(engine)
    if spec is None:
        raise ValueError(
            f"Unknown engine '{engine}'. Registered: {', '.join(ENGINE_SPECS)} "
            f"(validated for production: {_validated_engine_names()})."
        )
    if not spec.validated:
        raise EngineNotValidated(
            f"engine '{engine}' is registered but NOT validated for production missions. "
            f"Validated engine(s): {_validated_engine_names()}. "
            "Select a validated engine, or validate this one end-to-end before use — "
            "no other engine is substituted for the one you chose."
        )
    if not spec.web_search_headless:
        raise EngineNotValidated(
            f"engine '{engine}' cannot run production missions because "
            "web_search_headless=False; guaranteed headless web search is required for "
            f"research-grade work. Validated engine(s): {_validated_engine_names()}."
        )
    return spec


def _with_mcp(
    cmd: list,
    mcp_config_path: Optional[str] = None,
    mcp_allowed_tools: Optional[list] = None,
) -> list:
    """Return ``cmd`` with MCP tool-calling flags spliced in, or ``cmd`` unchanged when no MCP
    config is given — an additive, default-None studio hook.

    Only the ``claude-code`` engine speaks ``--mcp-config`` (it is the ``--allowedTools``
    family), so the splice is gated on that flag being present; every other engine's command
    is byte-identical. The allowed ``mcp__*`` tool patterns are appended to the existing
    ``--allowedTools`` value, and ``--mcp-config <path> --strict-mcp-config`` is inserted before
    the trailing ``-p`` prompt flag — so the studio's configured MCP servers' tools become
    available to the model on the calls this is used for. ``--strict-mcp-config`` makes the CLI
    use ONLY the studio-supplied config (never the user's global ``.mcp.json``), so the server
    set is exactly what the studio wrote from ``mcp.json``.

    Returns a NEW list; the shared ``ENGINES`` entry is never mutated."""
    if not mcp_config_path or "--allowedTools" not in cmd:
        return cmd
    out = list(cmd)
    if mcp_allowed_tools:
        after_value = out.index("--allowedTools") + 2   # past the flag and its first value
        out[after_value:after_value] = [str(t) for t in mcp_allowed_tools]
    before_prompt = out.index("-p") if "-p" in out else len(out)
    out[before_prompt:before_prompt] = ["--mcp-config", str(mcp_config_path), "--strict-mcp-config"]
    return out


# ── helpers ───────────────────────────────────────────────────────────────────

def _agents_dir() -> Path:
    here = Path(__file__).resolve()
    candidate = here.parents[2] / "agents"
    if candidate.is_dir():
        return candidate
    candidate = here.parents[1] / "payload" / "agents"
    if candidate.is_dir():
        return candidate
    raise RuntimeError("agents/ directory not found — run `agency sync` first.")


def _load(name: str) -> str:
    """Load an agents/*.md doctrine file, stripping its YAML frontmatter so it
    isn't parsed as CLI flags."""
    from agency_kit.store import split_frontmatter
    try:
        raw = (_agents_dir() / f"{name}.md").read_text(encoding="utf-8")
        fm, body = split_frontmatter(raw)
        return body.lstrip() if fm else raw
    except FileNotFoundError:
        return ""


# How often a blocked `_call` wakes to poll `should_cancel`, and how long it waits
# after SIGTERM before escalating to SIGKILL. Small enough that a Stop feels
# immediate; large enough not to busy-spin.
_CANCEL_POLL_SECONDS = 0.5
_TERMINATE_GRACE = 5.0


def _signal_tree(proc: "subprocess.Popen", sig: int) -> None:
    """Signal the child's whole process GROUP, not just the direct child.

    The engine CLIs are wrappers (the ``claude`` node process spawns its own child
    tree); signalling only ``proc`` would leave grandchildren alive holding the
    stdout/stderr pipes open, so ``communicate`` would never return and a Stop would
    hang. ``Popen(start_new_session=True)`` makes ``proc`` a group leader, so one
    ``killpg`` reaches the whole tree. Falls back to the direct child if the group
    lookup fails (already reaped), and is a no-op once everything is gone."""
    try:
        os.killpg(os.getpgid(proc.pid), sig)
    except OSError:  # group already gone / not found → try the direct child
        try:
            proc.send_signal(sig)
        except OSError:
            pass


def _terminate(proc: "subprocess.Popen", reader: threading.Thread) -> None:
    """Stop an in-flight child tree: SIGTERM, then SIGKILL if it ignores the grace
    window. Joins the reader (bounded) so ``communicate`` finishes reaping the pipes
    before we return — no zombie, no leaked descriptors, and never an unbounded hang
    even if a stubborn grandchild lingers."""
    _signal_tree(proc, signal.SIGTERM)
    reader.join(_TERMINATE_GRACE)
    if reader.is_alive():
        _signal_tree(proc, signal.SIGKILL)
        reader.join(_TERMINATE_GRACE)


def _call(
    cmd_prefix: list,
    prompt: str,
    timeout: int = 900,
    should_cancel: Optional[Callable[[], bool]] = None,
) -> str:
    """Invoke the CLI with a prompt; return stdout. Raises RuntimeError on failure.

    The child runs under a reader thread (``communicate`` drains both pipes, so a
    large deliverable can't deadlock on a full pipe) while this thread polls
    ``should_cancel`` every ``_CANCEL_POLL_SECONDS``. When a cancel fires mid-call
    the child's whole process group is terminated (SIGTERM, then SIGKILL after
    ``_TERMINATE_GRACE``) and ``MissionCancelled`` is raised — so a Stop no longer
    waits up to ``timeout``. With ``should_cancel=None`` the poll never fires,
    so standalone behaviour is byte-identical to the old blocking ``subprocess.run``.
    """
    binary = cmd_prefix[0]
    try:
        proc = subprocess.Popen(
            cmd_prefix + [prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,  # own process group → a cancel can kill the whole tree
        )
    except FileNotFoundError:
        raise RuntimeError(
            f"engine CLI '{binary}' not found on PATH — install it and authenticate "
            f"(e.g. Claude Code / Codex CLI / Gemini CLI)."
        )

    streams: dict = {}

    def _drain() -> None:
        streams["out"], streams["err"] = proc.communicate()

    reader = threading.Thread(target=_drain, daemon=True)
    reader.start()

    deadline = time.monotonic() + timeout
    try:
        while True:
            reader.join(_CANCEL_POLL_SECONDS)
            if not reader.is_alive():
                break
            if should_cancel is not None and should_cancel():
                _terminate(proc, reader)
                raise MissionCancelled()
            if time.monotonic() > deadline:
                _terminate(proc, reader)
                raise RuntimeError(f"engine CLI '{binary}' timed out after {timeout}s.")
    except KeyboardInterrupt:
        # `start_new_session` detaches the child from our process group, so a
        # terminal Ctrl-C no longer reaches it — kill the tree ourselves, then
        # re-raise so the CLI exits as the user asked (no orphaned engine process).
        _terminate(proc, reader)
        raise

    stdout = streams.get("out") or ""
    stderr = streams.get("err") or ""
    if proc.returncode != 0:
        # Claude Code / Codex often write the real error to stdout in -p/exec mode,
        # so surface whichever stream has content (stderr first) instead of a bare code.
        detail = (stderr.strip() or stdout.strip())[:800]
        raise RuntimeError(
            f"CLI engine '{binary}' exited {proc.returncode}"
            + (f": {detail}" if detail else " (no output on stdout or stderr)")
        )
    out = stdout.strip()
    if not out:
        raise RuntimeError(f"engine CLI '{binary}' returned empty output.")
    return out


def _route_via_cli(
    engine: str, goal: str, should_cancel: Optional[Callable[[], bool]] = None
) -> list:
    """Route via the CLI, driven by the canonical router doctrine (router-agency.md).

    Loads the same routing doctrine the whole agency uses — solve-first canonical
    order, the problem-led guardrail, Art. VI, and the routing examples — then forces
    a JSON-array answer for easy parsing. Falls back to keyword_classify() if the
    model returns unparseable output, or to a minimal prompt if the doctrine file is
    absent.
    """
    spec = ENGINE_SPECS.get(engine, ENGINE_SPECS["claude-code"])
    route_cmd = list(spec.route_cmd)
    doctrine = _load("router-agency")
    header = doctrine if doctrine else (
        "You are an agency mission router. Deploy the MINIMUM set of departments the "
        "goal needs (Art. VI). Canonical order is solve-first; solve is problem-led — "
        "route it only to diagnose a real problem, never for a create/brand/research mission.\n"
        f"Available departments: {', '.join(DEPT_NAMES)}"
    )
    prompt = (
        header
        + "\n\n---\n\n"
        + f"MISSION GOAL:\n{goal}\n\n"
        + "Apply the routing doctrine above. Output ONLY a JSON array of the department "
        + 'names to deploy, in execution order (solve-first). No prose, no rationale, no '
        + 'markdown fences. Example: ["solve", "product", "marketing"].'
    )

    try:
        response = _call(route_cmd, prompt, timeout=spec.route_timeout, should_cancel=should_cancel)
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            depts = json.loads(match.group())
            valid = [d for d in depts if d in VALID_DEPTS]
            if valid:
                return valid
    except (RuntimeError, ValueError):
        # CLI call failed or returned unparseable JSON — fall back to keywords.
        pass

    # Fallback: keyword heuristic (no model call)
    from agency_kit.router import keyword_classify
    return keyword_classify(goal)


_MAX_DEPT_CHARS = 4000  # per department, to keep prompts manageable


def _short_verdict(text: str) -> str:
    """Pull a short verdict token (PASS / PASS-WITH-FIXES / VETO) from inspector text.

    Used so `agency missions` / `batch status` show a clean token instead of the
    inspector's full prose. Whole-token, severity-ordered: VETO > PASS-WITH-FIXES >
    PASS. Matching by severity (not by last position) avoids the substring flip-case
    where a bare "PASS" in prose AFTER a "PASS-WITH-FIXES" conclusion would otherwise
    downgrade the reported verdict. Word boundaries stop "PASS" inside "BYPASS" /
    "COMPASS" or the "PASS" inside "PASS-WITH-FIXES" from being read as a bare PASS.

    Cases the heuristic must cover:
      "VERDICT: PASS"                              -> PASS
      "... — VETO"                                 -> VETO
      "VERDICT: PASS-WITH-FIXES, see notes"        -> PASS-WITH-FIXES
      "PASS-WITH-FIXES. It would PASS once fixed." -> PASS-WITH-FIXES (no downgrade)
      "no verdict word here"                       -> DELIVERED
    """
    upper = (text or "").upper()
    if re.search(r"\bVETO\b", upper):
        return "VETO"
    if re.search(r"\bPASS[\s-]WITH[\s-]FIXES\b", upper):
        return "PASS-WITH-FIXES"
    if re.search(r"\bPASS\b", upper):
        return "PASS"
    return "DELIVERED"


def _extract_sources(text: str) -> list:
    """Surface the source URLs cited in a deliverable, de-duplicated in first-seen
    order, for the dossier's structured ``sources`` field.

    The synthesis prompt asks for "all sources cited with URLs and dates", so the
    URLs live in the delivered markdown (typically a "Sources cited" table). Pulling
    them by URL shape is format-agnostic — it works for tables, lists, or inline
    links — and additive: text with no URL yields ``[]``. Delegates to THE canonical
    matcher in ``agency_cli.verification`` (Brick 3) so this list and the source-
    verification gate can never extract different URL sets — see the Complexity
    Tracking entry in specs/003-verifiable-sources/plan.md for the justified
    edge-case delta vs the pre-Brick-3 pattern (markdown-backtick artifacts are no
    longer captured). ``decisions`` / ``open_to_verify`` are deliberately NOT
    auto-extracted: their layout (prose vs table vs list) is model-dependent, so a
    heuristic parser would risk injecting markdown noise rather than reliable items.
    """
    from agency_cli.verification import extract_urls
    return extract_urls(text)


def _fmt_dept_outputs(dept_outputs: dict, limit: Optional[int] = _MAX_DEPT_CHARS) -> str:
    if not dept_outputs:
        return "(no prior department output)"
    parts = []
    for dept, output in dept_outputs.items():
        if limit is not None and len(output) > limit:
            body = output[:limit] + f"\n... [truncated — {len(output) - limit} chars omitted]"
        else:
            body = output
        parts.append(f"### {dept.upper()}\n{body}")
    return "\n\n".join(parts)


# ── prompt builders (one per mission phase) ─────────────────────────────────────

def _dept_prompt(
    dept: str, goal: str, dept_outputs: dict,
    asset_clause: Optional[str] = None, context_clause: Optional[str] = None,
    persona_doctrine: Optional[dict] = None,
) -> str:
    shared = _load(f"_shared-{dept}")
    persona = (persona_doctrine or {}).get(dept)
    doctrine = "\n\n".join(p for p in (shared, persona) if p)
    return (
        f"You are the {dept} department commander for an AI agency.\n\n"
        f"MISSION GOAL:\n{goal}\n\n"
        f"PRIOR DEPARTMENT OUTPUTS:\n{_fmt_dept_outputs(dept_outputs)}\n\n"
        + (f"DEPARTMENT DOCTRINE:\n{doctrine}\n\n" if doctrine else "")
        + "Produce a complete, detailed deliverable for this department.\n"
        "CRITICAL: Use WebSearch to find current, real data (today's date, live sources). "
        "Never invent statistics, market sizes, or citations. "
        "Every factual claim must come from a real source you have searched and verified."
        + (f"\n\n{context_clause}" if context_clause else "")
        + (f"\n\n{asset_clause}" if asset_clause else "")
    )


def _synth_prompt(
    goal: str,
    route: list,
    dept_outputs: dict,
    fixes: str = None,
    asset_clause: Optional[str] = None,
    context_clause: Optional[str] = None,
    persona_doctrine: Optional[dict] = None,
) -> str:
    commander_doc = _load("commander-agency")
    persona = (persona_doctrine or {}).get("commander")
    commander_doc = "\n\n".join(p for p in (commander_doc, persona) if p)
    fixes_block = (
        "PREVIOUS INSPECTOR FINDINGS — the prior synthesis did NOT pass; resolve every "
        f"item before re-presenting:\n{fixes}\n\n" if fixes else ""
    )
    return (
        (f"{commander_doc}\n\n" if commander_doc else "")
        + f"MISSION GOAL:\n{goal}\n\n"
        f"ROUTE: {route}\n\n"
        # Synthesis is the ONE place that must see each department's FULL deliverable —
        # with escalation on, a department is a multi-specialist assembly (commander +
        # officers + soldiers), and truncating it here (as the prior-dept context does)
        # would silently drop the specialist depth escalation exists to add. limit=None.
        f"DEPARTMENT OUTPUTS:\n{_fmt_dept_outputs(dept_outputs, limit=None)}\n\n"
        + fixes_block
        + "Synthesise all department outputs into a final cross-department mission dossier. "
        "List decisions taken, open items to verify, and all sources cited with URLs and dates."
        + (f"\n\n{context_clause}" if context_clause else "")
        + (f"\n\n{asset_clause}" if asset_clause else "")
    )


def _inspect_prompt(goal: str, delivered: str, verification_report: Optional[dict] = None) -> str:
    inspector_doc = _load("inspector-agency")
    verification_block = ""
    if verification_report:
        verification_block = (
            "\n\nSOURCE VERIFICATION REPORT:\n"
            f"{_format_verification_report(verification_report)}\n\n"
            "If any factual claims in the deliverable lack a cited source, list them under "
            "`UNSOURCED CLAIMS:` as bullet points. If none are clear, omit that section."
        )
    return (
        (f"{inspector_doc}\n\n" if inspector_doc else "")
        + f"MISSION GOAL:\n{goal}\n\n"
        f"DELIVERABLE:\n{delivered}\n\n"
        + (f"{verification_block}\n\n" if verification_block else "")
        + "Use WebSearch to spot-check at least 3 sources cited. "
        "Issue a verdict: PASS, PASS-WITH-FIXES, or VETO. "
        "Flag any invented data, outdated figures, or unverifiable claims."
    )


def _format_verification_report(report: dict) -> str:
    rows = []
    for dept, item in sorted((report.get("per_dept") or {}).items()):
        rows.append(f"- {dept}: {item.get('counted', 0)}/{item.get('min', 0)} counted")
    bad = [
        f"- {s.get('url')} ({s.get('detail')})"
        for s in report.get("sources", [])
        if s.get("status") in {"unresolved", "unverifiable"}
    ]
    if bad:
        rows.append("Unresolved/unverifiable sources:\n" + "\n".join(bad))
    return "\n".join(rows) if rows else "(no cited URLs found)"


# "No unsourced claims" phrasings a model may emit under the UNSOURCED CLAIMS heading
# despite the omit-if-none instruction. Filtered so an all-clear never reads as a
# claim and spuriously fails the cycle's verification signal.
_NON_CLAIMS = frozenset({"none", "n/a", "no unsourced claims", "no unsourced claims found"})


def _parse_unsourced_claims(verdict_text: str) -> list[str]:
    claims = []
    capture = False
    for line in (verdict_text or "").splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("UNSOURCED CLAIMS"):
            capture = True
            continue
        if capture and not stripped:
            break
        if capture:
            claims.append(stripped.lstrip("-* ").strip())
    return [c for c in claims if c and c.lower().rstrip(".") not in _NON_CLAIMS]


def _verification_fix_block(report: dict) -> str:
    bad = [
        f"{dept}: {item.get('counted', 0)}/{item.get('min', 0)} counted"
        for dept, item in (report.get("per_dept") or {}).items()
        if not item.get("ok")
    ]
    missing = [f"- {m}" for m in report.get("missing", [])]
    parts = ["Source verification failed; fix every item before re-presenting."]
    if bad:
        parts.append("Departments below source minimum:\n" + "\n".join(f"- {b}" for b in bad))
    if missing:
        parts.append("Unsourced claims named by inspector:\n" + "\n".join(missing))
    return "\n\n".join(parts)


# ── main entry point ──────────────────────────────────────────────────────────

MAX_ITERS = 3                      # synthesise→inspect cap (Art. IX: VETO loops, never skips)
_RETRY_VERDICTS = ("VETO", "PASS-WITH-FIXES")


class MissionCancelled(Exception):
    """Cancellation requested — the mission is aborted before any persistence.

    Raised by ``run_mission_cli`` BEFORE it returns a dossier, so a cancelled
    mission is never persisted (``runner_bridge`` only saves after the call
    returns). Two layers raise it: ``_check_cancel`` at clean phase boundaries
    (a no-spend early-exit between calls), and ``_call`` itself when a cancel
    lands while a child process is in flight — it kills the child and raises,
    so a Stop no longer waits up to the per-call timeout.

    Art. IX still holds: an aborted mission yields NO dossier, so no verdict is
    ever altered and no un-inspected result is ever delivered. The veto loop's
    logic is unchanged; only an abort can now happen faster (mid-call), and an
    abort produces nothing at all rather than a result that skipped the gate.
    """


def _check_cancel(should_cancel: Optional[Callable[[], bool]]) -> None:
    """Raise ``MissionCancelled`` if a cancel has been requested. No-op when
    ``should_cancel`` is None, so default behaviour is byte-identical."""
    if should_cancel is not None and should_cancel():
        raise MissionCancelled()


def _emit(on_event: Optional[Callable], event: dict) -> None:
    """Fire the optional progress callback, swallowing any error.

    The hook is purely observational (GUI live progress): a misbehaving callback
    must never abort or alter a live mission. When on_event is None this is a
    no-op, so the default behaviour — and the existing test suite — is unchanged.
    """
    if on_event is None:
        return
    try:
        on_event(event)
    except Exception:  # observational only — never let the GUI break the mission
        pass


def _checkpoint(
    on_checkpoint: Optional[Callable],
    phase: str,
    goal: str,
    engine: str,
    route: list,
    dept_outputs: dict,
    escalation: Optional[dict] = None,
    delivered: str = "",
    verdicts: tuple = (),
    verifications: tuple = (),
    iteration: int = 0,
    fixes: Optional[str] = None,
) -> None:
    """Fire the optional checkpoint callback with a JSON-serializable snapshot of the mission's
    completed state, swallowing any error.

    Like ``_emit`` this is purely observational — the studio persists the snapshot so a crashed
    mission can be resumed (``resume_state``), but a misbehaving callback must never abort or alter
    a live mission. When ``on_checkpoint`` is None this is a no-op, so default behaviour — and the
    existing suite — is byte-identical.

    ``phase`` is the boundary just completed: ``"route"`` (route decided, no dept run yet),
    ``"dept"`` (a department finished), or ``"cycle"`` (a synth→inspect cycle completed). The
    snapshot's invariants — relied on by ``_validate_resume_state`` — are: ``iteration ==
    len(verdicts)``; ``delivered`` is always the output of an ALREADY-INSPECTED cycle (checkpoints
    fire only AFTER a verdict is recorded, never mid-synthesis); and ``fixes`` is non-None iff the
    last verdict was a retry verdict (it feeds the NEXT synthesis). ``route`` / ``dept_outputs`` /
    ``verdicts`` are copied so a later phase mutating them can't corrupt an already-emitted
    snapshot."""
    if on_checkpoint is None:
        return
    try:
        snapshot = {
            "version": 1,
            "phase": phase,
            "goal": goal,
            "engine": engine,
            "route": list(route),
            "dept_outputs": dict(dept_outputs),
            "delivered": delivered,
            "verdicts": [dict(v) for v in verdicts],
            "iteration": iteration,
            "fixes": fixes,
        }
        if verifications:
            snapshot["verifications"] = [dict(v) for v in verifications]
        # Guarded exactly like the dossier's `escalation` key: only present when at least
        # one department escalated, so an escalation-off / pre-feature checkpoint envelope
        # stays byte-identical to before (Principle X).
        if escalation:
            snapshot["escalation"] = dict(escalation)
        on_checkpoint(snapshot)
    except Exception:  # observational only — never let the studio's persistence break the mission
        pass


def _validate_resume_state(state: dict) -> dict:
    """Validate a checkpoint snapshot before a mission resumes from it, raising ``ValueError`` on
    anything malformed or already-completed. FAIL LOUD by design: a silently-ignored bad resume
    would re-run the whole mission from scratch and invisibly re-spend the very work the checkpoint
    exists to save — so this mirrors the fail-fast ``ValueError`` on an unknown engine, not the
    graceful degradation of the context hooks.

    A valid resume snapshot must satisfy the invariants ``_checkpoint`` writes (see its docstring):
    a non-empty string ``route`` list; ``dept_outputs`` keys ⊆ ``route``; an int ``iteration`` in
    ``0..MAX_ITERS`` equal to ``len(verdicts)``; a non-empty ``delivered`` once any cycle ran; and,
    when a cycle ran, a last verdict still in ``_RETRY_VERDICTS`` (a PASS — or any non-retry
    verdict — means the mission had already finished, so its checkpoint should have been deleted;
    resuming it is a stale-state error). A checkpoint at ``iteration == MAX_ITERS`` is a VALID
    resume target (it finalises instantly with the standard residual_risk, zero engine calls).
    Returns the state unchanged so callers can use it inline."""
    if not isinstance(state, dict):
        raise ValueError("resume_state must be a dict")
    route = state.get("route")
    if not isinstance(route, list) or not route or not all(isinstance(d, str) and d for d in route):
        raise ValueError("resume_state.route must be a non-empty list of department names")
    dept_outputs = state.get("dept_outputs") or {}
    if not isinstance(dept_outputs, dict) or not set(dept_outputs).issubset(set(route)):
        raise ValueError("resume_state.dept_outputs keys must be a subset of route")
    escalation = state.get("escalation") or {}
    if not isinstance(escalation, dict) or not set(escalation).issubset(set(route)):
        raise ValueError("resume_state.escalation must be a dict keyed by departments in route")
    verdicts = state.get("verdicts") or []
    if not isinstance(verdicts, list):
        raise ValueError("resume_state.verdicts must be a list")
    verifications = state.get("verifications", [])
    if verifications is None:
        verifications = []
    if verifications and not isinstance(verifications, list):
        raise ValueError("resume_state.verifications must be a list")
    iteration = state.get("iteration")
    if not isinstance(iteration, int) or isinstance(iteration, bool) or not (0 <= iteration <= MAX_ITERS):
        raise ValueError(f"resume_state.iteration must be an int in 0..{MAX_ITERS}")
    if iteration != len(verdicts):
        raise ValueError("resume_state.iteration must equal len(verdicts)")
    if verifications and len(verifications) != len(verdicts):
        raise ValueError("resume_state.verifications must equal len(verdicts)")
    if iteration > 0 and not (state.get("delivered") or "").strip():
        raise ValueError("resume_state.delivered must be non-empty once a cycle has run")
    if verdicts and verdicts[-1].get("verdict") not in _RETRY_VERDICTS:
        # Mirror the loop's exit condition (token not retryable AND verification ok):
        # a cycle can end PASS with a FAILED source verification — that mission is
        # still in flight (the failure feeds the next synthesis), so its checkpoint
        # must stay resumable rather than be mis-rejected as complete.
        last = verifications[-1] if verifications else None
        verification_failed = isinstance(last, dict) and not last.get("ok", True)
        if not verification_failed:
            raise ValueError("resume_state is already complete (last verdict is not a retry verdict)")
    state = dict(state)
    state["escalation"] = escalation
    if verifications:
        state["verifications"] = verifications
    return state


def run_mission_cli(
    goal: str,
    engine: str = "claude-code",
    on_event: Optional[Callable[[dict], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
    asset_clause: Optional[str] = None,
    context_clause: Optional[str] = None,
    mcp_config_path: Optional[str] = None,
    mcp_allowed_tools: Optional[list] = None,
    persona_doctrine: Optional[dict] = None,
    on_checkpoint: Optional[Callable[[dict], None]] = None,
    resume_state: Optional[dict] = None,
    escalation: Optional[object] = None,
    verification: Optional[object] = None,
) -> dict:
    """Run a full mission via a local agent CLI tool: route → execute → synthesize → inspect.

    Known but unvalidated engines are refused before binary lookup or subprocess
    work starts; there is no silent substitution for production missions. A
    validated engine must also declare guaranteed headless web search, the hard
    precondition for research-grade mission work under Constitution Art. II.

    The inspector is a real gate (Art. IX): on VETO or PASS-WITH-FIXES the synthesis is
    re-run with the inspector's findings injected as required fixes, up to MAX_ITERS. If
    it still hasn't PASSed at the cap, the best result is delivered with a residual_risk
    note. Departments run once — only the cross-department synthesis is re-tried.

    Returns a dossier dict (goal, route, dept_outputs, delivered, verdicts, iteration).
    Web search is live — the CLI tool fetches real pages at execution time.

    ``should_cancel`` is an optional cancel predicate, polled in two places: at
    phase boundaries (after routing, before each department, before each
    synthesise→inspect iteration) as a no-spend early-exit, AND inside ``_call``
    while a child process is in flight — so a Stop kills the running subprocess
    immediately instead of waiting up to the per-call timeout. Either way the
    mission raises ``MissionCancelled``, which propagates before any persistence,
    so nothing is saved. An aborted mission yields no dossier, so no verdict is
    altered and no un-inspected result is delivered (Art. IX). When None, every
    check is a no-op and behaviour is byte-identical to a non-cancellable run.

    ``asset_clause`` is an optional studio-supplied instruction appended verbatim
    to each department prompt and the synthesis prompt (so a department or the
    synthesis may emit fenced ``asset`` markers for the studio to render
    post-inspection). It is NOT given to the inspector, the router, or the slug —
    those see the unmodified goal. When None the clause is never appended, so the
    prompts — and standalone agency-kit's behaviour — are byte-identical to a run
    without it (the same additive, default-None contract as on_event/should_cancel).

    ``context_clause`` is the studio's Wave-4 RAG hook: a block of sourced excerpts
    retrieved from the user's own uploaded documents, appended verbatim to each
    department prompt and the synthesis prompt as authoritative reference material.
    Same additive, default-None contract as ``asset_clause`` — NOT given to the
    inspector, router, or slug, and when None nothing is appended (byte-identical to
    standalone agency-kit). The veto loop / _short_verdict logic is untouched.

    ``mcp_config_path`` / ``mcp_allowed_tools`` are the studio's Wave-6 MCP tool-calling
    hook (claude-code only): a path to a ``--mcp-config`` file the studio wrote from the
    user's configured MCP servers, and the ``mcp__*`` tool patterns to allow. When set they
    are spliced (via ``_with_mcp``) into the DEPARTMENT and SYNTHESIS commands only — so the
    model can invoke those servers' tools while producing deliverables — and NOT into the
    router or the inspector (which stay on the base command, exactly like ``context_clause``
    is withheld from the inspector, so the Art. IX quality gate is unchanged). Default None ⇒
    the command is byte-identical to standalone agency-kit; a non-claude engine ignores them.

    ``persona_doctrine`` is the studio's Wave-6 persona-doctrine hook: a dict keyed by
    department name (a ``DEPT_NAMES`` key, plus the reserved ``"commander"`` key for the
    synthesis) → a curated persona doctrine string. Unlike ``mcp_config_path`` (a CLI-arg
    splice) this augments the PROMPT TEXT — each dept's persona is woven into that dept's
    DEPARTMENT DOCTRINE block, and the ``"commander"`` persona into the synthesis commander
    doctrine. Like ``context_clause`` it reaches the DEPARTMENT and SYNTHESIS prompts only —
    NOT the router or inspector — so the Art. IX gate's inputs are unchanged. Default None (or
    a dict lacking a given key) ⇒ that prompt is byte-identical to standalone agency-kit.

    ``on_checkpoint`` / ``resume_state`` are the studio's crash-recovery hooks (a mission is
    minutes of paid work with no mid-flight persistence, so a transient API drop mid-synthesis
    loses everything). ``on_checkpoint`` is an observational snapshot callback (``_checkpoint``,
    same swallow-exceptions discipline as ``on_event``) fired at every phase boundary — after
    routing, after each department, and after each COMPLETED synth→inspect cycle — so the studio
    can persist the state. ``resume_state`` is a prior snapshot that re-enters the mission
    mid-flight: routing is skipped (the saved route is reused), departments already in
    ``dept_outputs`` are skipped, and the veto loop is re-entered at the saved ``iteration`` with
    the saved ``delivered``/``fixes``. Both default None ⇒ byte-identical to standalone agency-kit.

    Art. IX is preserved by construction: checkpoints fire ONLY after a verdict is recorded, so a
    snapshot's ``delivered`` was always inspected; a crash mid-cycle rolls back to the last
    completed cycle and resume RE-RUNS both that synthesis AND its inspection — no un-inspected
    result can ever ship. The iteration counter CONTINUES from the snapshot (``while iteration <
    MAX_ITERS`` re-entered with the saved value), so a resumed mission gets exactly the veto budget
    it had left, never a fresh one. Neither hook touches the router or inspector prompts, and the
    veto loop body / ``_short_verdict`` logic is unchanged — resume with identical inputs reproduces
    the exact state as-if the crash never happened.
    """
    spec = ensure_production_engine(engine)  # unknown / unvalidated / no-web-search → refuse
    cmd = list(spec.run_cmd)
    # Departments + synthesis may call the user's MCP tools; the router + inspector never do
    # (they run on the base `cmd`), so the quality gate's inputs are untouched by this hook.
    exec_cmd = _with_mcp(cmd, mcp_config_path, mcp_allowed_tools)
    # The contract is EscalationConfig | None. A plain dict is the shape the studio deals
    # in (the request field), and only runner_bridge._resolve_escalation converts it — so
    # coerce a dict here too rather than let getattr() silently read defaults and disable
    # escalation without a word (a foot-gun for any future caller that skips the resolve).
    if isinstance(escalation, dict):
        from agency_cli.escalation import EscalationConfig
        escalation = EscalationConfig(
            enabled=bool(escalation.get("enabled", True)),
            budget=int(escalation.get("budget", 6)),
        )
    if isinstance(verification, dict):
        from agency_cli.verification import coerce_config
        verification = coerce_config(verification)
    escalation_active = bool(
        escalation is not None
        and getattr(escalation, "enabled", False)
        and getattr(escalation, "budget", 0) > 0
    )
    roster = None
    if escalation_active:
        from agency_cli.escalation import build_roster
        roster = build_roster(Path(__file__).resolve().parents[1] / "payload" / "agents")
    # Fail fast with a clear message if either CLI is absent. Both are checked because an
    # engine may use a different binary for routing than for research work; the run binary
    # is checked first so the message is byte-identical for the built-in engines (which
    # share one binary, so the route binary is a no-op dedupe). A missing route binary would
    # otherwise be swallowed by _route_via_cli's keyword fallback, silently degrading routing.
    checked_binaries: list = []
    for binary in (cmd[0], spec.route_cmd[0]):
        if binary in checked_binaries:
            continue
        checked_binaries.append(binary)
        if shutil.which(binary) is None:
            raise RuntimeError(
                f"engine '{engine}' needs the '{binary}' CLI on PATH — install it and "
                f"authenticate first. Check availability with: agency check"
            )
    # Resume: validate the snapshot up front (fail loud — a bad resume must not silently re-run
    # from scratch and re-spend the work the checkpoint exists to save).
    if resume_state is not None:
        resume_state = _validate_resume_state(resume_state)

    # Route — reuse the saved route on resume (never re-route: routing already spent a call and
    # the departments below key off it), else route live and checkpoint the decision.
    if resume_state is not None:
        route = list(resume_state["route"])
        print(f"[{engine}] resuming... {' → '.join(route)}", flush=True)
        _emit(on_event, {"phase": "route", "status": "done", "route": route, "resumed": True})
    else:
        print(f"[{engine}] routing...", end=" ", flush=True)
        route = _route_via_cli(engine, goal, should_cancel=should_cancel)
        print(f"{' → '.join(route)}", flush=True)
        _emit(on_event, {"phase": "route", "status": "done", "route": route})
        _checkpoint(on_checkpoint, "route", goal, engine, route, {})
    _check_cancel(should_cancel)   # CP1: after routing, before any department spends a call

    # Seed completed departments from the snapshot; a resumed run skips them (no re-spend) and only
    # runs the ones that never finished.
    dept_outputs: dict = dict(resume_state.get("dept_outputs") or {}) if resume_state else {}
    escalation_traces: dict = dict(resume_state.get("escalation") or {}) if resume_state else {}
    for dept in route:
        _check_cancel(should_cancel)   # CP2: skip a department that has not started yet
        if dept in dept_outputs:       # already completed in a prior (crashed) run — don't re-run
            _emit(on_event, {"phase": "dept", "dept": dept, "status": "done", "resumed": True})
            continue
        print(f"[{engine}] {dept}...", end=" ", flush=True)
        _emit(on_event, {"phase": "dept", "dept": dept, "status": "start"})
        if escalation_active and roster is not None and dept in roster.commanders:
            from agency_cli.escalation import run_department
            dept_outputs[dept], escalation_traces[dept] = run_department(
                dept,
                goal,
                dept_outputs,
                config=escalation,
                roster=roster,
                call=_call,
                base_cmd=cmd,
                exec_cmd=exec_cmd,
                run_timeout=spec.run_timeout,
                should_cancel=should_cancel,
                on_event=on_event,
                asset_clause=asset_clause,
                context_clause=context_clause,
                persona_doctrine=persona_doctrine,
                cancelled=MissionCancelled,
            )
        else:
            dept_outputs[dept] = _call(
                exec_cmd,
                _dept_prompt(dept, goal, dept_outputs, asset_clause=asset_clause,
                             context_clause=context_clause,
                             persona_doctrine=persona_doctrine),
                timeout=spec.run_timeout,
                should_cancel=should_cancel,
            )
        print("done", flush=True)
        _emit(on_event, {"phase": "dept", "dept": dept, "status": "done"})
        _checkpoint(on_checkpoint, "dept", goal, engine, route, dept_outputs, escalation=escalation_traces)

    # Seed the veto loop from the snapshot (continue the iteration budget — never a fresh one) or
    # from scratch. Replaying the completed cycles to on_event keeps the GUI timeline coherent
    # (iteration N doesn't appear from nowhere on a resume).
    if resume_state:
        verdicts = [dict(v) for v in resume_state["verdicts"]]
        verifications = [dict(v) for v in resume_state.get("verifications", [])]
        delivered = resume_state["delivered"]
        fixes = resume_state.get("fixes")
        iteration = resume_state["iteration"]
        for v in verdicts:
            _emit(on_event, {"phase": "synth", "iteration": v["iteration"], "status": "done", "resumed": True})
            _emit(on_event, {"phase": "inspect", "iteration": v["iteration"], "verdict": v["verdict"], "resumed": True})
    else:
        verdicts = []
        verifications = []
        delivered = ""
        fixes = None
        iteration = 0
    probe_cache = {}
    while iteration < MAX_ITERS:
        _check_cancel(should_cancel)   # CP3: between complete synth→inspect cycles, never within one
        iteration += 1
        label = "synthesising" if iteration == 1 else f"re-synthesising (iter {iteration})"
        print(f"[{engine}] {label}...", end=" ", flush=True)
        _emit(on_event, {"phase": "synth", "iteration": iteration, "status": "start"})
        delivered = _call(
            exec_cmd,
            _synth_prompt(goal, route, dept_outputs, fixes, asset_clause=asset_clause,
                          context_clause=context_clause,
                          persona_doctrine=persona_doctrine),
            timeout=spec.run_timeout,
            should_cancel=should_cancel,
        )
        print("done", flush=True)
        _emit(on_event, {"phase": "synth", "iteration": iteration, "status": "done"})

        verification_report = None
        if verification is not None:
            from agency_cli.verification import verify_cycle
            _check_cancel(should_cancel)
            _emit(on_event, {"phase": "verify", "iteration": iteration, "status": "start"})
            verification_report = verify_cycle(
                iteration, route, dept_outputs, delivered, verification, cache=probe_cache
            )
            _check_cancel(should_cancel)

        print(f"[{engine}] inspecting...", end=" ", flush=True)
        _emit(on_event, {"phase": "inspect", "iteration": iteration, "status": "start"})
        verdict_text = _call(
            cmd, _inspect_prompt(goal, delivered, verification_report), timeout=spec.run_timeout, should_cancel=should_cancel
        )
        token = _short_verdict(verdict_text)
        print(token, flush=True)
        _emit(on_event, {"phase": "inspect", "iteration": iteration, "verdict": token})

        verdicts.append({"engine": engine, "verdict": token, "detail": verdict_text, "iteration": iteration})
        verification_ok = True
        if verification_report is not None:
            verification_report = dict(verification_report)
            verification_report["missing"] = _parse_unsourced_claims(verdict_text)
            if verification_report["missing"]:
                verification_report["ok"] = False
            verifications.append(verification_report)
            verification_ok = bool(verification_report["ok"])
            _emit(on_event, {
                "phase": "verify",
                "iteration": iteration,
                "status": "done",
                "ok": verification_ok,
                "rate": verification_report.get("rate"),
                "checked": len(verification_report.get("sources") or []),
            })
        # Checkpoint the completed (inspected) cycle before deciding whether to loop — so a crash in
        # the NEXT synthesis rolls back to here, and resume re-runs that synthesis + its inspection.
        next_fixes = None
        if token in _RETRY_VERDICTS:
            next_fixes = verdict_text
        if not verification_ok and verification_report is not None:
            next_fixes = "\n\n".join(p for p in (next_fixes, _verification_fix_block(verification_report)) if p)
        _checkpoint(on_checkpoint, "cycle", goal, engine, route, dept_outputs,
                    escalation=escalation_traces,
                    delivered=delivered, verdicts=verdicts, iteration=iteration,
                    verifications=verifications, fixes=next_fixes)
        if token not in _RETRY_VERDICTS and verification_ok:   # PASS, or no actionable verdict — stop
            break
        fixes = next_fixes                 # feed findings into the next synthesis

    dossier = {
        "goal": goal,
        "route": route,
        "context": None,
        "dept_outputs": dept_outputs,
        "decisions": [],
        "sources": _extract_sources(delivered),
        "open_to_verify": [],
        "direction_check": None,
        "verdicts": verdicts,
        "iteration": iteration,
        "delivered": delivered,
    }
    if escalation_traces:
        dossier["escalation"] = escalation_traces
    if verification is not None:
        dossier["verification"] = {
            "min_sources": getattr(verification, "min_sources", 3),
            "resolve": getattr(verification, "resolve", False),
            "cycles": verifications,
            "final": verifications[-1] if verifications else None,
        }
    verification_failed = bool(verifications and not verifications[-1].get("ok"))
    if verdicts[-1]["verdict"] in _RETRY_VERDICTS or verification_failed:   # cap reached without a clean PASS
        reason = (
            "Source verification failed"
            if verification_failed and verdicts[-1]["verdict"] not in _RETRY_VERDICTS
            else f"Inspector did not PASS after {iteration} iteration(s)"
        )
        dossier["residual_risk"] = (
            f"{reason}; delivered the best "
            f"available result. Last verdict: {verdicts[-1]['verdict']}."
        )
    return dossier
