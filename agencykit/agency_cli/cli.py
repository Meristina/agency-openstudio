"""agency — Agency-Kit CLI.

Subcommands: init, run, missions, resume, check, sync, tui, export, batch.
"""

import argparse
import inspect
import sys

from .verification import DEFAULT_MIN_SOURCES

# Flush stdout immediately so `agency run` output is visible in real time when
# stdout is redirected (e.g. piped to a file or captured by a test runner).
sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]

from . import __version__, scaffolder


def _cmd_init(args) -> int:
    summary = scaffolder.init(args.path, agent=args.agent)
    print(f"Initialized Agency-Kit in {summary['target']} (harness: {summary['agent']})")
    print(f"  payload source : {summary['payload_mode']}")
    if "commands" in summary:
        print(f"  commands       : {summary['commands']} → /agency.<name>")
    for k in ("agents", "skills", "note"):
        if k in summary:
            print(f"  {k:<14} : {summary[k]}")
    print('Next:  agency run "<your mission goal>"   (or use /agency.mission in your harness)')
    return 0


def _cmd_dry_run(args) -> int:
    from agency_kit.router import keyword_classify
    route = keyword_classify(args.goal)
    print(f"\n[dry-run] Goal: {args.goal}")
    print(f"[dry-run] Planned route ({len(route)} dept(s), keyword classifier — no model call):")
    for i, dept in enumerate(route, 1):
        print(f"  {i}. {dept}")
    print("\n[dry-run] No engine call made. Remove --dry-run to execute.")
    return 0


def _args_escalation(args):
    if getattr(args, "no_escalation", False):
        return False
    budget = getattr(args, "escalation_budget", None)
    if budget is None:
        return None
    return {"budget": budget}


def _nonnegative_int(value: str) -> int:
    n = int(value)
    if n < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return n


def _args_verification(args):
    # Always forward the explicit payload — returning None for the opt-out would make
    # runner_bridge._resolve_verification recreate the DEFAULT config and silently
    # re-enable the gate the operator just disabled. The min_sources=0 → disabled
    # mapping is the bridge's job, not this parser's.
    return {
        "min_sources": getattr(args, "min_sources", DEFAULT_MIN_SOURCES),
        "resolve": bool(getattr(args, "resolve_sources", False)),
    }


def _call_supported(fn, *args, **kwargs):
    sig = inspect.signature(fn)
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        return fn(*args, **kwargs)
    return fn(*args, **{k: v for k, v in kwargs.items() if k in sig.parameters})


def _cmd_run(args) -> int:
    if getattr(args, "dry_run", False):
        return _cmd_dry_run(args)
    from . import checkpoints, runner_bridge

    goal = args.goal
    engine = getattr(args, "engine", "claude-code")
    project_root = args.path

    # Crash recovery: if this exact goal was interrupted mid-flight, resume from its last
    # checkpoint (skip routing + completed departments) instead of re-paying that work.
    # Pre-validate so a stale/incompatible envelope degrades to a fresh run, and so a bad
    # checkpoint is never confused with a genuine run error below.
    resume_state = None
    if not getattr(args, "fresh", False):
        saved = checkpoints.read(goal, engine, project_root)
        if saved is not None:
            from .engines.cli_engine import _validate_resume_state
            try:
                resume_state = _validate_resume_state(saved)
                print(f"Resuming interrupted mission ({checkpoints.describe(saved)}); "
                      "pass --fresh to start over.")
            except ValueError:
                print("warning: saved checkpoint is unusable; starting a fresh run.", file=sys.stderr)
                checkpoints.clear(goal, engine, project_root)

    try:
        result = _call_supported(
            runner_bridge.run,
            goal, project_root=project_root,
            engine=engine,
            escalation=_args_escalation(args),
            verification=_args_verification(args),
            on_checkpoint=lambda snap: checkpoints.write(goal, engine, project_root, snap),
            resume_state=resume_state,
        )
    except (RuntimeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    # The durable dossier now supersedes the transient checkpoint.
    checkpoints.clear(goal, engine, project_root)
    _print_mission_result(result)
    return 0


def _print_mission_result(result) -> None:
    """Show the project path AND the store mission_id (the id `resume`/`export` need)."""
    verdicts = result.dossier.get("verdicts") or []
    verdict = verdicts[-1].get("verdict", "—") if verdicts else "—"
    print(f"Mission written to: {result.path}")
    print(f"  mission id : {result.dossier.get('mission_id', '?')}   (use with `agency resume` / `agency export`)")
    print(f"  verdict    : {verdict}")
    if result.dossier.get("residual_risk"):
        print(f"  residual   : {result.dossier['residual_risk']}")


def _cmd_missions(args) -> int:
    from agency_kit import store
    missions = store.list_missions()
    if not missions:
        print("No missions saved yet. Run:  agency run \"<your goal>\"")
        return 0
    print(f"{'MISSION ID':<38}  {'VERDICT':<15}  GOAL")
    print("-" * 90)
    for m in missions:
        tick = "✓" if m["delivered"] else "○"
        goal_preview = m["goal"][:42] + "…" if len(m["goal"]) > 42 else m["goal"]
        print(f"{m['mission_id']:<38}  {m['verdict']:<15}  {tick} {goal_preview}")
    return 0


def _cmd_resume(args) -> int:
    from agency_kit import store
    from . import runner_bridge
    try:
        result = _call_supported(
            runner_bridge.resume,
            args.mission_id, project_root=args.path,
            engine=getattr(args, "engine", "claude-code"),
            escalation=_args_escalation(args),
            verification=_args_verification(args),
        )
    except FileNotFoundError:
        print(f"error: mission '{args.mission_id}' not found in {store.missions_path()}",
              file=sys.stderr)
        return 2
    except (RuntimeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    _print_mission_result(result)
    return 0


def _cmd_sync(args) -> int:
    from . import sync_payload
    # Default: preserve mode (engine-only — sibling kits are usually absent; their
    # payload snapshot is kept). --strict requires all kit repos for a clean full regen.
    allow_missing = not getattr(args, "strict", False)
    try:
        return sync_payload.main(allow_missing=allow_missing)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def _cmd_export(args) -> int:
    try:
        from . import exporter
        path = exporter.export_pdf(args.mission_id)
    except (FileNotFoundError, ImportError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"error: PDF export failed — {e}", file=sys.stderr)
        return 2
    print(f"PDF exported to: {path}")
    return 0


def _cmd_tui(args) -> int:
    try:
        from . import tui
        tui.launch()
    except ImportError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


def _cmd_batch(args) -> int:
    from . import batch_runner
    cmd = getattr(args, "batch_cmd", None)
    if cmd == "add":
        return batch_runner.add(args.goal, priority=args.priority, notes=args.notes)
    if cmd == "run":
        return _call_supported(
            batch_runner.run,
            retry_failed=getattr(args, "retry_failed", False),
            limit=getattr(args, "limit", 0),
            engine=getattr(args, "engine", "claude-code"),
            escalation=_args_escalation(args),
            verification=_args_verification(args),
        )
    if cmd == "status":
        return batch_runner.status()
    if cmd == "clear":
        return batch_runner.clear(status_filter=getattr(args, "status_filter", "done"))
    return 1


def _cmd_check(args) -> int:
    ok_all = True
    for label, ok, detail in scaffolder.check(args.path):
        mark = "✓" if ok else "✗"
        ok_all = ok_all and ok
        print(f"  {mark} {label}" + (f"  ({detail})" if detail and not ok else ""))
    return 0 if ok_all else 1


def _harness_choices():
    from .integrations import SUPPORTED
    return list(SUPPORTED)


def _engine_choices():
    """Engine names from the single source of truth (cli_engine.ENGINES)."""
    from .engines.cli_engine import ENGINES
    return list(ENGINES)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agency",
        description="AI Agency — unified orchestrator for nine optional department kits (product, marketing, solve, finance, comms, data, ops, people, tech)",
    )
    p.add_argument("--version", action="version", version=f"agency-kit {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init", help="scaffold .agency/ + harness commands into a project")
    pi.add_argument("path", nargs="?", default=".", help="target project dir (default: .)")
    pi.add_argument("--agent", default="claude", choices=_harness_choices(),
                    help="agent harness: claude | codex | cursor | copilot | gemini | opencode")
    pi.set_defaults(func=_cmd_init)

    pr = sub.add_parser("run", help="headless mission via a local agent CLI engine")
    pr.add_argument("goal", help="the mission goal, one line")
    pr.add_argument("path", nargs="?", default=".", help="project dir for missions/ output")
    pr.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="classify goal with keyword heuristic and show planned route — no engine call")
    pr.add_argument("--engine", default="claude-code",
                    choices=_engine_choices(),
                    help="local agent CLI engine (default: claude-code). Each uses its own auth + web search.")
    pr.add_argument("--no-escalation", action="store_true",
                    help="run each department through the legacy doctrine-only path")
    pr.add_argument("--escalation-budget", type=int, metavar="N",
                    help="max escalation calls per department (0 disables escalation)")
    pr.add_argument("--min-sources", type=_nonnegative_int, default=DEFAULT_MIN_SOURCES, metavar="N",
                    help="minimum counted sources per department (0 disables the blocking gate; report-only when combined with --resolve-sources)")
    pr.add_argument("--resolve-sources", action="store_true",
                    help="probe cited URLs online with HTTPS HEAD requests")
    pr.add_argument("--fresh", action="store_true",
                    help="ignore any saved checkpoint for this goal and start from scratch "
                         "(otherwise an interrupted run of the same goal resumes automatically)")
    pr.set_defaults(func=_cmd_run)

    pm = sub.add_parser("missions", help="list saved missions from ~/.agency/missions/")
    pm.set_defaults(func=_cmd_missions)

    pre = sub.add_parser("resume", help="re-run a saved mission's goal through the engine")
    pre.add_argument("mission_id", help="mission ID shown by `agency missions`")
    pre.add_argument("path", nargs="?", default=".", help="project dir for missions/ output")
    pre.add_argument("--engine", default="claude-code",
                     choices=_engine_choices(),
                     help="local agent CLI engine (default: claude-code)")
    pre.add_argument("--no-escalation", action="store_true",
                     help="run each department through the legacy doctrine-only path")
    pre.add_argument("--escalation-budget", type=int, metavar="N",
                     help="max escalation calls per department (0 disables escalation)")
    pre.add_argument("--min-sources", type=_nonnegative_int, default=DEFAULT_MIN_SOURCES, metavar="N",
                     help="minimum counted sources per department (0 disables the blocking gate; report-only when combined with --resolve-sources)")
    pre.add_argument("--resolve-sources", action="store_true",
                     help="probe cited URLs online with HTTPS HEAD requests")
    pre.set_defaults(func=_cmd_resume)

    pc = sub.add_parser("check", help="prerequisite / health check")
    pc.add_argument("path", nargs="?", default=".")
    pc.set_defaults(func=_cmd_check)

    ps = sub.add_parser("sync", help="regenerate the bundled payload from the repo source")
    ps.add_argument("--strict", action="store_true",
                    help="require ALL sibling dept-kit repos and do a clean full rebuild "
                         "(default: preserve mode — regenerate agency-level files, keep the "
                         "committed kit-derived payload snapshot for absent kits)")
    ps.set_defaults(func=_cmd_sync)

    pt = sub.add_parser("tui", help="launch terminal UI — Pipeline / Viewer / Analytics (needs pip install -e \".[tui]\")")
    pt.set_defaults(func=_cmd_tui)

    pe = sub.add_parser("export", help="export a mission deliverable to PDF (needs pip install -e \".[pdf]\")")
    pe.add_argument("mission_id", help="mission ID (from `agency missions`)")
    pe.set_defaults(func=_cmd_export)

    pb = sub.add_parser("batch", help="batch mission queue: add / run / status / clear")
    bsub = pb.add_subparsers(dest="batch_cmd", required=True)

    pba = bsub.add_parser("add", help="add a goal to the queue")
    pba.add_argument("goal", help="mission goal")
    pba.add_argument("--priority", type=int, default=5, metavar="N",
                     help="execution priority — lower = higher priority (default: 5)")
    pba.add_argument("--notes", default="", help="optional notes attached to the queue entry")
    pba.set_defaults(func=_cmd_batch)

    pbr = bsub.add_parser("run", help="execute pending goals sequentially")
    pbr.add_argument("--limit", type=int, default=0, metavar="N",
                     help="max goals to run this session (default: 0 = all pending)")
    pbr.add_argument("--retry-failed", dest="retry_failed", action="store_true",
                     help="also retry goals that errored")
    pbr.add_argument("--engine", default="claude-code",
                     choices=_engine_choices(),
                     help="local agent CLI engine (default: claude-code)")
    pbr.add_argument("--no-escalation", action="store_true",
                     help="run each department through the legacy doctrine-only path")
    pbr.add_argument("--escalation-budget", type=int, metavar="N",
                     help="max escalation calls per department (0 disables escalation)")
    pbr.add_argument("--min-sources", type=_nonnegative_int, default=DEFAULT_MIN_SOURCES, metavar="N",
                     help="minimum counted sources per department (0 disables the blocking gate; report-only when combined with --resolve-sources)")
    pbr.add_argument("--resolve-sources", action="store_true",
                     help="probe cited URLs online with HTTPS HEAD requests")
    pbr.set_defaults(func=_cmd_batch)

    pbs = bsub.add_parser("status", help="show queue and run state")
    pbs.set_defaults(func=_cmd_batch)

    pbc = bsub.add_parser("clear", help="remove entries from the queue by status")
    pbc.add_argument("--status", dest="status_filter", default="done",
                     help="status to remove (default: done)")
    pbc.set_defaults(func=_cmd_batch)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
