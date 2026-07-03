"""cli_engine — run missions via a local agent CLI (Claude Code / Codex / Gemini).

Uses subprocess instead of any LLM SDK or API key: each CLI tool uses its own
authenticated session and its own live web search.

Supported engines (all provide live web search, which Art. I of the constitution
requires — facts must come from real searched sources, never invented):
  claude-code   claude --allowedTools WebSearch -p "<prompt>"
  codex         codex --search exec --color never --sandbox read-only -- "<prompt>"
  gemini        gemini -p "<prompt>"        (google_web_search built-in, on by default)

Extension point: other agent CLIs (cursor-agent, opencode, copilot) can be added
to ENGINES below, but only once they can guarantee live web search headlessly —
without it a mission would fabricate data and violate Art. I.
"""

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

# Execution commands — live web search enabled for real research
ENGINES: dict = {
    "claude-code": ["claude", "--allowedTools", "WebSearch", "-p"],
    "codex": ["codex", "--search", "exec", "--color", "never", "--sandbox", "read-only", "--"],
    "gemini": ["gemini", "-p"],
}

# Routing commands — classification only, no web search needed
_ROUTE_CMD: dict = {
    "claude-code": ["claude", "-p"],
    "codex": ["codex", "--color", "never", "--sandbox", "read-only", "--"],
    "gemini": ["gemini", "-p"],
}


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
    route_cmd = _ROUTE_CMD.get(engine, _ROUTE_CMD["claude-code"])
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
        response = _call(route_cmd, prompt, timeout=60, should_cancel=should_cancel)
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


# A cited source URL. Bounded so it stops at whitespace and the markdown delimiters
# that wrap a link — ( ) [ ] < > " ' | — so the URL is captured cleanly whether the
# synthesis emits it in a Sources table cell, a list, or an inline [text](url) link.
_SOURCE_URL_RE = re.compile(r"https?://[^\s<>()\[\]\"'|]+")


def _extract_sources(text: str) -> list:
    """Surface the source URLs cited in a deliverable, de-duplicated in first-seen
    order, for the dossier's structured ``sources`` field.

    The synthesis prompt asks for "all sources cited with URLs and dates", so the
    URLs live in the delivered markdown (typically a "Sources cited" table). Pulling
    them by URL shape is format-agnostic — it works for tables, lists, or inline
    links — and additive: text with no URL yields ``[]``, exactly the prior
    behaviour. ``decisions`` / ``open_to_verify`` are deliberately NOT auto-extracted:
    their layout (prose vs table vs list) is model-dependent, so a heuristic parser
    would risk injecting markdown noise rather than reliable items.
    """
    seen: dict = {}
    for raw in _SOURCE_URL_RE.findall(text or ""):
        url = raw.rstrip(".,;:!?")  # drop trailing sentence punctuation
        if url:
            seen.setdefault(url, None)
    return list(seen)


def _fmt_dept_outputs(dept_outputs: dict) -> str:
    if not dept_outputs:
        return "(no prior department output)"
    parts = []
    for dept, output in dept_outputs.items():
        truncated = output[:_MAX_DEPT_CHARS]
        suffix = f"\n... [truncated — {len(output) - _MAX_DEPT_CHARS} chars omitted]" if len(output) > _MAX_DEPT_CHARS else ""
        parts.append(f"### {dept.upper()}\n{truncated}{suffix}")
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
        f"DEPARTMENT OUTPUTS:\n{_fmt_dept_outputs(dept_outputs)}\n\n"
        + fixes_block
        + "Synthesise all department outputs into a final cross-department mission dossier. "
        "List decisions taken, open items to verify, and all sources cited with URLs and dates."
        + (f"\n\n{context_clause}" if context_clause else "")
        + (f"\n\n{asset_clause}" if asset_clause else "")
    )


def _inspect_prompt(goal: str, delivered: str) -> str:
    inspector_doc = _load("inspector-agency")
    return (
        (f"{inspector_doc}\n\n" if inspector_doc else "")
        + f"MISSION GOAL:\n{goal}\n\n"
        f"DELIVERABLE:\n{delivered}\n\n"
        "Use WebSearch to spot-check at least 3 sources cited. "
        "Issue a verdict: PASS, PASS-WITH-FIXES, or VETO. "
        "Flag any invented data, outdated figures, or unverifiable claims."
    )


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
    delivered: str = "",
    verdicts: tuple = (),
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
        on_checkpoint({
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
        })
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
    verdicts = state.get("verdicts") or []
    if not isinstance(verdicts, list):
        raise ValueError("resume_state.verdicts must be a list")
    iteration = state.get("iteration")
    if not isinstance(iteration, int) or isinstance(iteration, bool) or not (0 <= iteration <= MAX_ITERS):
        raise ValueError(f"resume_state.iteration must be an int in 0..{MAX_ITERS}")
    if iteration != len(verdicts):
        raise ValueError("resume_state.iteration must equal len(verdicts)")
    if iteration > 0 and not (state.get("delivered") or "").strip():
        raise ValueError("resume_state.delivered must be non-empty once a cycle has run")
    if verdicts and verdicts[-1].get("verdict") not in _RETRY_VERDICTS:
        raise ValueError("resume_state is already complete (last verdict is not a retry verdict)")
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
) -> dict:
    """Run a full mission via a local agent CLI tool: route → execute → synthesize → inspect.

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
    cmd = ENGINES.get(engine)
    if cmd is None:
        raise ValueError(f"Unknown engine '{engine}'. Available: {', '.join(ENGINES)}")
    # Departments + synthesis may call the user's MCP tools; the router + inspector never do
    # (they run on the base `cmd`), so the quality gate's inputs are untouched by this hook.
    exec_cmd = _with_mcp(cmd, mcp_config_path, mcp_allowed_tools)
    if shutil.which(cmd[0]) is None:  # fail fast with a clear message if the CLI is absent
        raise RuntimeError(
            f"engine '{engine}' needs the '{cmd[0]}' CLI on PATH — install it and "
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
    for dept in route:
        _check_cancel(should_cancel)   # CP2: skip a department that has not started yet
        if dept in dept_outputs:       # already completed in a prior (crashed) run — don't re-run
            _emit(on_event, {"phase": "dept", "dept": dept, "status": "done", "resumed": True})
            continue
        print(f"[{engine}] {dept}...", end=" ", flush=True)
        _emit(on_event, {"phase": "dept", "dept": dept, "status": "start"})
        dept_outputs[dept] = _call(
            exec_cmd,
            _dept_prompt(dept, goal, dept_outputs, asset_clause=asset_clause,
                         context_clause=context_clause,
                         persona_doctrine=persona_doctrine),
            should_cancel=should_cancel,
        )
        print("done", flush=True)
        _emit(on_event, {"phase": "dept", "dept": dept, "status": "done"})
        _checkpoint(on_checkpoint, "dept", goal, engine, route, dept_outputs)

    # Seed the veto loop from the snapshot (continue the iteration budget — never a fresh one) or
    # from scratch. Replaying the completed cycles to on_event keeps the GUI timeline coherent
    # (iteration N doesn't appear from nowhere on a resume).
    if resume_state:
        verdicts = [dict(v) for v in resume_state["verdicts"]]
        delivered = resume_state["delivered"]
        fixes = resume_state.get("fixes")
        iteration = resume_state["iteration"]
        for v in verdicts:
            _emit(on_event, {"phase": "synth", "iteration": v["iteration"], "status": "done", "resumed": True})
            _emit(on_event, {"phase": "inspect", "iteration": v["iteration"], "verdict": v["verdict"], "resumed": True})
    else:
        verdicts = []
        delivered = ""
        fixes = None
        iteration = 0
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
            should_cancel=should_cancel,
        )
        print("done", flush=True)
        _emit(on_event, {"phase": "synth", "iteration": iteration, "status": "done"})

        print(f"[{engine}] inspecting...", end=" ", flush=True)
        _emit(on_event, {"phase": "inspect", "iteration": iteration, "status": "start"})
        verdict_text = _call(
            cmd, _inspect_prompt(goal, delivered), should_cancel=should_cancel
        )
        token = _short_verdict(verdict_text)
        print(token, flush=True)
        _emit(on_event, {"phase": "inspect", "iteration": iteration, "verdict": token})

        verdicts.append({"engine": engine, "verdict": token, "detail": verdict_text, "iteration": iteration})
        # Checkpoint the completed (inspected) cycle before deciding whether to loop — so a crash in
        # the NEXT synthesis rolls back to here, and resume re-runs that synthesis + its inspection.
        _checkpoint(on_checkpoint, "cycle", goal, engine, route, dept_outputs,
                    delivered=delivered, verdicts=verdicts, iteration=iteration,
                    fixes=verdict_text if token in _RETRY_VERDICTS else None)
        if token not in _RETRY_VERDICTS:   # PASS, or no actionable verdict — stop
            break
        fixes = verdict_text               # feed the inspector's findings into the next synthesis

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
    if verdicts[-1]["verdict"] in _RETRY_VERDICTS:   # cap reached without a clean PASS
        dossier["residual_risk"] = (
            f"Inspector did not PASS after {iteration} iteration(s); delivered the best "
            f"available result. Last verdict: {verdicts[-1]['verdict']}."
        )
    return dossier
