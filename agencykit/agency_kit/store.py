"""Mission store — persist dossiers to disk; list and resume missions.

Saves each dossier to ~/.agency/missions/<YYYYMMDD-HHMMSS-ffffff>-<slug>/dossier.json
so missions survive across CLI runs and can be resumed or audited offline.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def slug(text: str, max_words: int = 5) -> str:
    """URL-safe slug from text. Public so callers can pass their preferred max_words."""
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return "-".join(s.split("-")[:max_words]) or "mission"


def missions_path() -> Path:
    """Return the missions directory path without creating it."""
    return Path.home() / ".agency" / "missions"


def missions_dir() -> Path:
    d = missions_path()
    d.mkdir(parents=True, exist_ok=True)
    return d


def agency_dir() -> Path:
    """Return ~/.agency, creating it if absent. Public so batch_runner and other
    callers don't need to duplicate this one-liner."""
    d = Path.home() / ".agency"
    d.mkdir(parents=True, exist_ok=True)
    return d


def split_frontmatter(content: str) -> tuple:
    """Canonical YAML front-matter splitter. Returns ``(frontmatter, body)``.

    The closing delimiter is matched as a line of its own (``\\n---``), so a
    ``---`` that appears inside the body is not mistaken for the end of the
    front-matter. If no well-formed front-matter is present, returns
    ``("", content)`` (the whole input is the body). This is the single
    implementation used by ``strip_frontmatter`` (here), ``cli_engine``, and
    ``integrations`` so the three never diverge.
    """
    if not content.startswith("---"):
        return "", content
    end = content.find("\n---", 3)
    if end == -1:
        return "", content
    return content[3:end], content[end + 4:]


def strip_frontmatter(content: str) -> str:
    """Strip YAML front-matter (---...---) written by store.save().

    Returns the body text with leading/trailing whitespace removed.
    If no front-matter is present, returns the original string unchanged.
    """
    fm, body = split_frontmatter(content)
    return body.strip() if fm else content


def new_mission_id(goal: str) -> str:
    """Generate a mission ID of the form ``<YYYYMMDD-HHMMSS-ffffff>-<slug>``.

    The microsecond field (``%f``) is the uniqueness guarantee: two workers that
    start in the same second still get distinct IDs. No filesystem lock is used —
    a lock would only serialise the call, not inject entropy, so two same-second
    same-goal workers would have collided whether it was held or not.
    """
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return f"{ts}-{slug(goal)}"


def save(dossier: dict) -> "Path | None":
    """Persist the dossier as JSON. Creates/overwrites <missions_dir>/<mission_id>/dossier.json.

    Returns the dossier.json path on success, or ``None`` when there is nothing to
    persist — i.e. the dossier carries no ``mission_id`` (call ``new_mission_id``
    first), or a disk write failed. Never raises: a disk failure must not abort a
    live mission. Callers must handle the ``None`` case before using the result.
    """
    try:
        mid = dossier.get("mission_id")
        if not mid:
            return None
        d = missions_dir() / mid
        d.mkdir(exist_ok=True)
        path = d / "dossier.json"
        path.write_text(json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")
        if dossier.get("delivered"):
            last_verdict = last_verdict_token(dossier)
            meta = "\n".join([
                "---",
                f"mission_id: {dossier.get('mission_id', '')}",
                f"route: {json.dumps(dossier.get('route', []))}",
                f"departments: {', '.join(dossier.get('route', []))}",
                f"iteration: {dossier.get('iteration', 0)}",
                f"verdict: {last_verdict}",
                "delivered: true",
                "---",
            ])
            (d / "deliverable.md").write_text(meta + "\n\n" + dossier["delivered"], encoding="utf-8")
        return path
    except Exception as e:
        print(f"  [store] warning: could not save dossier — {e}", file=sys.stderr)
        return None


def load(mission_id: str) -> dict:
    """Load a dossier from disk. Raises FileNotFoundError if not found."""
    path = missions_dir() / mission_id / "dossier.json"
    return json.loads(path.read_text(encoding="utf-8"))


def last_verdict_token(dossier: dict) -> str:
    """The Inspector's last verdict token, for display/metadata: ``in-progress`` when
    no verdict was recorded, ``—`` when the last entry has no verdict. Tolerant of a
    malformed (non-dict) verdict entry so one bad dossier can't crash save/list."""
    verdicts = dossier.get("verdicts") or []
    if not verdicts:
        return "in-progress"
    last = verdicts[-1]
    return last.get("verdict", "—") if isinstance(last, dict) else "—"


def canonical_project_root(path) -> str:
    """Canonical string form of a project root — resolves symlinks and relativity so
    the same directory always compares equal however it was typed. Used to stamp a
    mission (write side) and to match it (read side); both must use this one form."""
    return str(Path(path).resolve())


def _same_project(a: str, b: str) -> bool:
    """Whether two canonical project roots denote the same directory.

    Exact match first (covers the common case and Windows case-folding via
    ``normcase``), then a stat-based ``samefile`` fallback that resolves
    case-insensitive matches on macOS APFS — but only while both directories still
    exist. Known limitation: a case-variant path to a directory that has since been
    moved/deleted won't match (no portable case-fold without a live dir)."""
    if os.path.normcase(a) == os.path.normcase(b):
        return True
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def _matches_project(dossier, wanted: "str | None") -> bool:
    """Core scope test against an already-canonical ``wanted`` root (or None = no
    scope). A non-dict dossier never matches; a dossier with no (or empty)
    ``project_root`` stamp is treated as belonging, so pre-feature missions stay
    visible and openable."""
    if wanted is None:
        return True
    if not isinstance(dossier, dict):
        return False
    stamped = dossier.get("project_root")
    if not stamped:
        return True  # legacy / unstamped mission
    return _same_project(stamped, wanted)


def mission_in_project(dossier: dict, project_root) -> bool:
    """Whether a loaded dossier belongs to ``project_root``. A falsy ``project_root``
    (None / "") means no scoping (always True). Used by the Studio server to scope
    GET-by-id and PDF the same way ``list_missions`` scopes the listing."""
    wanted = canonical_project_root(project_root) if project_root else None
    return _matches_project(dossier, wanted)


def list_missions(project_root: "str | None" = None) -> list:
    """Return a summary list of saved missions, newest first.

    When ``project_root`` is given, only missions belonging to that project are
    returned (``mission_in_project``) — so a project-scoped caller (the Studio GUI
    launched with ``--path``) sees its own missions, not every mission on the
    machine. Missions saved before the ``project_root`` stamp existed are still
    listed (treated as belonging) so upgrading never hides a user's history. A
    falsy ``project_root`` (None / "") lists every mission — unchanged for the
    ``agency missions`` CLI.

    Note: this scans every dossier in the global store and filters in memory; fine
    for a local tool's mission counts. A per-project index would be the move if the
    store ever grows large.
    """
    wanted = canonical_project_root(project_root) if project_root else None  # resolve once
    result = []
    for d in sorted(missions_dir().iterdir(), reverse=True):
        if not d.is_dir():
            continue
        p = d / "dossier.json"
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not _matches_project(data, wanted):
                continue  # malformed (non-object) dossier, or out of project scope
            result.append({
                "mission_id": data.get("mission_id", d.name),
                "goal": str(data.get("goal") or "")[:80],  # str(): tolerate a non-str goal
                "route": data.get("route", []),
                "iteration": data.get("iteration", 0),
                "verdict": last_verdict_token(data),
                "delivered": bool(data.get("delivered")),
            })
        except (OSError, json.JSONDecodeError, KeyError):
            # Recoverable: a corrupt/unreadable JSON file or a missing key — skip
            # that one mission. Programming errors (other exceptions) propagate.
            continue
    return result
