"""scaffolder — `agency init`: copy the command pack into a target project and write the
chosen harness's command files (via integrations).

Resolves the payload from the **repo root** when running from a source checkout (dev). A bundled
mode (shipping the pack inside the wheel) is the optional next step; for now `agency init`
requires a source checkout / editable install.
"""

import importlib.util
import shutil
import sys
from pathlib import Path

from . import integrations


def _spec_present(name: str) -> bool:
    """True if `name` is importable. Handles stub modules whose __spec__ is None."""
    try:
        return importlib.util.find_spec(name) is not None
    except ValueError:
        return name in sys.modules


def sources() -> dict:
    """Locate the payload source. Keys: agency, commands, agents, skills, mode.

    In a source checkout .agency/ is served live from root (so edits take effect without
    re-running sync), but agents/ and skills/ always come from the bundled payload so the
    full 100+ agent bundle is installed regardless of which sibling repos are present.
    """
    here = Path(__file__).resolve()
    root = here.parents[1]
    payload = here.parent / "payload"
    if (root / ".agency").is_dir() and (payload / "agents").is_dir():
        return {"agency": root / ".agency", "commands": root / ".agency" / "commands",
                "agents": payload / "agents", "skills": payload / "skills", "mode": "source"}
    if (payload / "agency").is_dir():
        return {"agency": payload / "agency", "commands": payload / "agency" / "commands",
                "agents": payload / "agents", "skills": payload / "skills", "mode": "bundled"}
    raise RuntimeError("Agency-Kit payload not found — run `agency sync` first, or re-install.")


def init(target: str, agent: str = "claude") -> dict:
    """Scaffold .agency/ + missions/ into `target` and install the harness command pack."""
    src = sources()
    target = Path(target).resolve()
    target.mkdir(parents=True, exist_ok=True)

    # 1) the .agency/ payload (the command pack) — plans/ is internal dev work, not user content
    agency_src = Path(src["agency"]).resolve()
    agency_dst = (target / ".agency").resolve()
    if agency_src != agency_dst:
        shutil.copytree(agency_src, agency_dst, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("plans"))

    # 2) memory/constitution.md
    constitution = target / ".agency" / "memory" / "constitution.md"
    constitution.parent.mkdir(parents=True, exist_ok=True)
    if not constitution.is_file():
        constitution.write_text(
            "# Agency Constitution\n\n"
            "The agency is the unified orchestrator for nine optional department kits "
            "(product-kit, marketing-kit, solve-kit, finance-kit, comms-kit, data-kit, "
            "ops-kit, people-kit, tech-kit).\n",
            encoding="utf-8",
        )

    # 3) missions/ output dir
    (target / "missions").mkdir(exist_ok=True)

    # 4) harness integration (commands + engine for claude)
    summary = integrations.install(agent, src, target)
    summary["target"] = str(target)
    summary["payload_mode"] = src["mode"]
    return summary


def _engine_binaries() -> dict:
    """Map each engine name to ``(binary, validated)``, derived from
    cli_engine.ENGINE_SPECS (the single source of truth) so names and validation
    status never drift."""
    from .engines.cli_engine import ENGINE_SPECS
    return {name: (spec.run_cmd[0], spec.validated) for name, spec in ENGINE_SPECS.items()}


def check(target: str = ".") -> list:
    """Lightweight prerequisite/health check. Returns (label, ok, detail) tuples."""
    checks = []

    # .agency/memory/constitution.md exists (prefer target, fall back to payload source)
    constitution = Path(target).resolve() / ".agency" / "memory" / "constitution.md"
    if not constitution.is_file():
        try:
            constitution = sources()["agency"] / "memory" / "constitution.md"
        except RuntimeError:
            pass
    checks.append(("constitution present", constitution.is_file(), str(constitution)))

    # agency_kit core importable (router + departments)
    checks.append((
        "agency_kit importable",
        _spec_present("agency_kit"),
        "pip install -e . (editable) or pip install agency-kit",
    ))

    # At least one VALIDATED engine's CLI on PATH. Only validated engines may run a
    # production mission, so an unvalidated engine on PATH (antigravity/opencode) does NOT
    # make the studio runnable — reporting it as healthy would be misleading.
    engines = _engine_binaries()
    validated_found = [n for n, (binary, ok) in engines.items() if ok and shutil.which(binary)]
    unvalidated_found = [n for n, (binary, ok) in engines.items() if not ok and shutil.which(binary)]
    if validated_found:
        detail = f"available: {', '.join(validated_found)}"
    elif unvalidated_found:
        detail = (f"only unvalidated engines on PATH ({', '.join(unvalidated_found)}) — "
                  "they are refused for missions; install a validated engine (Claude Code)")
    else:
        detail = "none on PATH — install a validated engine (Claude Code)"
    checks.append((
        "at least one validated engine CLI available",
        bool(validated_found),
        detail,
    ))
    return checks
