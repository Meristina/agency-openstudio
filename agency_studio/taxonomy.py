"""Client/project/campaign taxonomy layered over the existing mission store."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

MAX_NAME = 120
DEFAULT_CLIENT = "Studio"
DEFAULT_PROJECT = "Unassigned"


def clean_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    name = value.strip()
    if not name:
        return None
    if len(name) > MAX_NAME:
        raise ValueError("taxonomy names must be 120 characters or fewer")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise ValueError("taxonomy names cannot contain control characters")
    return name


def name_key(value: object) -> str | None:
    name = clean_name(value)
    return name.casefold() if name is not None else None


def client_key(client: object) -> str:
    return f"client:{name_key(client)}"


def project_key(client: object, project: object) -> str:
    return f"project:{name_key(client)}/{name_key(project)}"


def campaign_key(client: object, project: object, campaign: object) -> str:
    return f"campaign:{name_key(client)}/{name_key(project)}/{name_key(campaign)}"


def validate_fields(data: dict) -> dict[str, str | None]:
    return {k: clean_name(data.get(k)) for k in ("client", "project", "campaign")}


@dataclass
class Registry:
    overrides: dict[str, dict[str, str | None]] = field(default_factory=dict)
    names: dict[str, str] = field(default_factory=dict)

    def remember(self, client: object, project: object, campaign: object = None) -> None:
        c = clean_name(client)
        p = clean_name(project)
        k = clean_name(campaign)
        if c:
            self.names.setdefault(client_key(c), c)
        if c and p:
            self.names.setdefault(project_key(c, p), p)
        if c and p and k:
            self.names.setdefault(campaign_key(c, p, k), k)

    def display_client(self, client: str) -> str:
        return self.names.get(client_key(client), client)

    def display_project(self, client: str, project: str) -> str:
        return self.names.get(project_key(client, project), project)

    def display_campaign(self, client: str, project: str, campaign: str) -> str:
        return self.names.get(campaign_key(client, project, campaign), campaign)

    def set_override(self, mission_id: str, attribution: dict[str, str | None]) -> None:
        clean = validate_fields(attribution)
        self.overrides[mission_id] = clean
        self.remember(clean["client"], clean["project"], clean["campaign"])

    def clear_override(self, mission_id: str) -> None:
        self.overrides.pop(mission_id, None)


def _registry_path() -> Path:
    from agency_kit import store

    return store.agency_dir() / "taxonomy.json"


def load_registry() -> Registry:
    try:
        data = json.loads(_registry_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Registry()
    if not isinstance(data, dict):
        return Registry()
    overrides = data.get("overrides") if isinstance(data.get("overrides"), dict) else {}
    names = data.get("names") if isinstance(data.get("names"), dict) else {}
    clean_overrides = {
        str(mid): {k: clean_name((attr or {}).get(k)) for k in ("client", "project", "campaign")}
        for mid, attr in overrides.items()
        if isinstance(attr, dict)
    }
    clean_names = {str(k): str(v) for k, v in names.items() if isinstance(v, str)}
    return Registry(clean_overrides, clean_names)


def save_registry(registry: Registry) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(
        json.dumps({"version": 1, "overrides": registry.overrides, "names": registry.names}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _default_project(dossier: dict) -> str:
    stamped = dossier.get("project_root")
    if not isinstance(stamped, str) or not stamped.strip():
        return DEFAULT_PROJECT
    return Path(stamped.strip()).name or DEFAULT_PROJECT


def resolve(dossier: dict, registry: Registry) -> dict[str, str | None]:
    mid = str(dossier.get("mission_id") or "")
    if mid in registry.overrides:
        override = registry.overrides[mid]
        return {
            "client": clean_name(override.get("client")) or DEFAULT_CLIENT,
            "project": clean_name(override.get("project")) or _default_project(dossier),
            "campaign": clean_name(override.get("campaign")),
        }
    fields = validate_fields(dossier)
    return {
        "client": fields["client"] or DEFAULT_CLIENT,
        "project": fields["project"] or _default_project(dossier),
        "campaign": fields["campaign"],
    }


@dataclass
class ScannedDossier:
    mission_id: str
    dossier: dict
    attribution: dict[str, str | None]


def scan_dossiers(project_root: str | Path | None = None, registry: Registry | None = None) -> Iterator[ScannedDossier]:
    from agency_kit import store

    reg = registry or load_registry()
    try:
        dirs = sorted(store.missions_path().iterdir(), reverse=True)
    except OSError:
        return
    for d in dirs:
        p = d / "dossier.json"
        if not d.is_dir() or not p.exists():
            continue
        try:
            dossier = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(dossier, dict) or not store.mission_in_project(dossier, project_root):
            continue
        yield ScannedDossier(str(dossier.get("mission_id") or d.name), dossier, resolve(dossier, reg))


def summary_row(row: ScannedDossier, registry: Registry) -> dict:
    from agency_kit import store

    a = row.attribution
    registry.remember(a["client"], a["project"], a["campaign"])
    return {
        "mission_id": row.mission_id,
        "goal": str(row.dossier.get("goal") or "")[:80],
        "route": row.dossier.get("route", []),
        "iteration": row.dossier.get("iteration", 0),
        "verdict": store.last_verdict_token(row.dossier),
        "delivered": bool(row.dossier.get("delivered")),
        "client": registry.display_client(a["client"]),
        "project": registry.display_project(a["client"], a["project"]),
        "campaign": registry.display_campaign(a["client"], a["project"], a["campaign"]) if a["campaign"] else None,
    }


def matches(attribution: dict[str, str | None], **filters: str | None) -> bool:
    for level, wanted in filters.items():
        key = name_key(wanted)
        if key is not None and name_key(attribution.get(level)) != key:
            return False
    return True


def filter_rows(rows: Iterator[ScannedDossier], registry: Registry, **filters: str | None) -> Iterator[dict]:
    for row in rows:
        if matches(row.attribution, **filters):
            yield summary_row(row, registry)


def build_tree(rows: Iterator[ScannedDossier], registry: Registry) -> dict:
    clients: dict[str, dict] = {}
    for row in rows:
        a = row.attribution
        registry.remember(a["client"], a["project"], a["campaign"])
        ck = name_key(a["client"])
        pk = name_key(a["project"])
        client = clients.setdefault(ck, {"name": a["client"], "missions": 0, "projects": {}})
        client["missions"] += 1
        project = client["projects"].setdefault(pk, {"name": a["project"], "missions": 0, "campaigns": {}})
        project["missions"] += 1
        if a["campaign"]:
            kk = name_key(a["campaign"])
            campaign = project["campaigns"].setdefault(kk, {"name": a["campaign"], "missions": 0})
            campaign["missions"] += 1

    out = []
    for client in clients.values():
        projects = []
        for project in client["projects"].values():
            campaigns = [
                {"name": registry.display_campaign(client["name"], project["name"], c["name"]), "missions": c["missions"]}
                for c in project["campaigns"].values()
            ]
            campaigns.sort(key=lambda x: x["name"].casefold())
            projects.append({
                "name": registry.display_project(client["name"], project["name"]),
                "missions": project["missions"],
                "campaigns": campaigns,
            })
        projects.sort(key=lambda x: x["name"].casefold())
        out.append({
            "name": registry.display_client(client["name"]),
            "missions": client["missions"],
            "projects": projects,
        })
    out.sort(key=lambda x: x["name"].casefold())
    return {"clients": out}
