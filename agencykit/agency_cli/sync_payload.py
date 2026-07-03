"""sync_payload — regenerate the bundled payload from all source repos.

Pulls from agency-kit (the meta-orchestrator) AND, when present, the nine department
kit repos (product-kit … tech-kit) so the bundled payload is complete.

Engine-only model: agency-kit no longer installs department kits — departments are
played by the CLI engine. The sibling kit repos are therefore usually ABSENT, and
their contribution to the payload (the `commander-<dept>.md` / `inspector-<dept>.md`
doctrine) is a committed FROZEN SNAPSHOT. So `agency sync` defaults to PRESERVE mode:
it regenerates the agency-level files (`.agency/`, agency `agents/` + `skills/`) and
keeps the kit-derived snapshot untouched. `agency sync --strict` requires every kit
repo and does a clean full rebuild (for kit maintainers cloning all siblings).

Source layout (all repos are expected as siblings of agency-kit):
  agency-kit/     → .agency/, agents/, skills/
  product-kit/    → agents/, skills/
  marketing-kit/  → agents/, skills/
  solve-kit/      → agents/, skills/
  finance-kit/    → agents/, skills/
  comms-kit/      → agents/, skills/
  data-kit/       → agents/, skills/
  ops-kit/        → agents/, skills/
  people-kit/     → agents/, skills/
  tech-kit/       → agents/, skills/

Bundle layout (agency_cli/payload/):
  payload/agency/    ← .agency/ (constitution, commands, templates, scripts)
  payload/agents/    ← merged agents from agency-kit + all dept kits
  payload/skills/    ← merged skills from agency-kit + all dept kits

Naming conflict: every dept kit has its own inspector.md — renamed on copy:
  product-kit/agents/inspector.md   → payload/agents/inspector-product.md
  marketing-kit/agents/inspector.md → payload/agents/inspector-marketing.md
  solve-kit/agents/inspector.md     → payload/agents/inspector-solve.md
  finance-kit/agents/inspector.md   → payload/agents/inspector-finance.md
  comms-kit/agents/inspector.md     → payload/agents/inspector-comms.md
  data-kit/agents/inspector.md      → payload/agents/inspector-data.md
  ops-kit/agents/inspector.md       → payload/agents/inspector-ops.md
  people-kit/agents/inspector.md    → payload/agents/inspector-people.md
  tech-kit/agents/inspector.md      → payload/agents/inspector-tech.md

Run:  agency sync   (or: python -m agency_cli.sync_payload)
"""

import shutil
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def payload_dir() -> Path:
    return Path(__file__).resolve().parent / "payload"


def _dept_root(name: str) -> Path:
    """Sibling repo directory for a department kit (e.g. 'product-kit')."""
    return repo_root().parent / name


# Department kits to pull from — (repo-dir-name, dept-label)
DEPT_KITS = [
    ("product-kit",   "product"),
    ("marketing-kit", "marketing"),
    ("solve-kit",     "solve"),
    ("finance-kit",   "finance"),
    ("comms-kit",     "comms"),
    ("data-kit",      "data"),
    ("ops-kit",       "ops"),
    ("people-kit",    "people"),
    ("tech-kit",      "tech"),
]


def _copy_agents(src: Path, dst: Path, dept: str) -> int:
    """Copy all .md files from src into dst, renaming inspector.md → inspector-<dept>.md.

    Warns on filename collisions (other than the handled inspector.md rename) so silent
    overwrites don't hide agency-level vs dept-level agent conflicts.
    """
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in src.glob("*.md"):
        target_name = f"inspector-{dept}.md" if f.name == "inspector.md" else f.name
        target = dst / target_name
        if target.exists() and target_name != f"inspector-{dept}.md":
            print(f"  [warn] collision: {target_name} already exists — overwriting with {dept} version")
        shutil.copy2(f, target)
        count += 1
    return count


def _copy_skills(src: Path, dst: Path) -> int:
    """Merge skill directories from src into dst (copytree each skill folder)."""
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for skill_dir in src.iterdir():
        if skill_dir.is_dir():
            shutil.copytree(skill_dir, dst / skill_dir.name, dirs_exist_ok=True)
            count += sum(1 for _ in skill_dir.rglob("*") if _.is_file())
    return count


def sync(allow_missing: bool = False) -> dict:
    root, dest = repo_root(), payload_dir()
    summary = {}

    # Pre-flight: verify .agency/ exists (always required)
    agency_src = root / ".agency"
    if not agency_src.exists():
        raise RuntimeError(f"Required source dir not found: {agency_src}")

    # Pre-flight: check all dept-kit repos before wiping anything.
    # Wiping then skipping missing repos would permanently destroy committed agent files.
    missing_kits = [
        repo_name for repo_name, _ in DEPT_KITS
        if not (_dept_root(repo_name) / "agents").exists()
    ]
    if missing_kits and not allow_missing:
        raise RuntimeError(
            f"--strict requires all sibling kit repos, but these are absent: {', '.join(missing_kits)}\n"
            "In the engine-only model the kits are normally absent — just run `agency sync`\n"
            "(preserve mode: regenerates agency-level files, keeps the kit-derived snapshot).\n"
            "Only use --strict if you have cloned all nine kit repos alongside agency-kit."
        )

    # 1) .agency/ → payload/agency/  (plans/ is internal dev work — excluded from the bundle)
    agency_dst = dest / "agency"
    if agency_dst.exists():
        shutil.rmtree(agency_dst)
    shutil.copytree(agency_src, agency_dst, ignore=shutil.ignore_patterns("plans"))
    summary["agency"] = sum(1 for _ in agency_dst.rglob("*") if _.is_file())

    # 2) agents/ — agency-kit first, then all dept kits (with inspector renaming)
    # With allow_missing we update in-place so committed files for absent kits survive.
    agents_dst = dest / "agents"
    if agents_dst.exists() and not allow_missing:
        shutil.rmtree(agents_dst)
    agents_dst.mkdir(parents=True, exist_ok=True)

    n_agents = _copy_agents(root / "agents", agents_dst, "agency")

    for repo_name, dept in DEPT_KITS:
        dept_agents = _dept_root(repo_name) / "agents"
        if not dept_agents.exists():
            print(f"  [skip] {repo_name}/agents not found — keeping committed files")
            continue
        n_agents += _copy_agents(dept_agents, agents_dst, dept)

    summary["agents"] = n_agents

    # 3) skills/ — agency-kit first, then all dept kits (merged, no conflicts)
    # Same allow_missing guard: preserve committed skills for absent kits.
    skills_dst = dest / "skills"
    if skills_dst.exists() and not allow_missing:
        shutil.rmtree(skills_dst)
    skills_dst.mkdir(parents=True, exist_ok=True)

    n_skills = 0
    agency_skills = root / "skills"
    if agency_skills.exists():
        n_skills += _copy_skills(agency_skills, skills_dst)

    for repo_name, _ in DEPT_KITS:
        dept_skills = _dept_root(repo_name) / "skills"
        if not dept_skills.exists():
            print(f"  [skip] {repo_name}/skills not found")
            continue
        n_skills += _copy_skills(dept_skills, skills_dst)

    summary["skills"] = n_skills

    return summary


def main(allow_missing: bool = False) -> int:
    s = sync(allow_missing=allow_missing)
    print(f"Synced payload → {payload_dir()}")
    for k, n in s.items():
        print(f"  {k:<8} {n} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
