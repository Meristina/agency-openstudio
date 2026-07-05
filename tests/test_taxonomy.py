import json
import os
from pathlib import Path

import pytest

from agency_studio import taxonomy


def test_normalize_and_validate_names():
    assert taxonomy.clean_name("  Acme  ") == "Acme"
    assert taxonomy.name_key("  İSTANBUL  ") == "i̇stanbul"
    assert taxonomy.clean_name("  ") is None
    assert taxonomy.project_key("Acme", "Launch") != taxonomy.project_key("Other", "Launch")

    with pytest.raises(ValueError):
        taxonomy.clean_name("x" * 121)
    with pytest.raises(ValueError):
        taxonomy.clean_name("bad\nname")


def test_registry_preserves_first_typed_names_and_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    reg = taxonomy.Registry()
    reg.remember("Acme", "Rebrand", "Spring")
    reg.remember("acme", "rebrand", "spring")
    reg.set_override("m1", {"client": "ACME", "project": "Rebrand", "campaign": None})
    taxonomy.save_registry(reg)

    path = tmp_path / ".agency" / "taxonomy.json"
    assert path.exists()
    assert not list(path.parent.glob("taxonomy.json.*"))

    loaded = taxonomy.load_registry()
    assert loaded.names["client:acme"] == "Acme"
    assert loaded.names["project:acme/rebrand"] == "Rebrand"
    assert loaded.overrides["m1"] == {"client": "ACME", "project": "Rebrand", "campaign": None}

    loaded.clear_override("m1")
    assert "m1" not in loaded.overrides

    path.write_text("{", encoding="utf-8")
    assert taxonomy.load_registry() == taxonomy.Registry()


def test_resolve_attribution_order_and_defaults(tmp_path):
    reg = taxonomy.Registry(overrides={"m1": {"client": "Override", "project": "P", "campaign": None}})
    dossier = {
        "mission_id": "m1",
        "client": "Field",
        "project": "Field Project",
        "campaign": "Launch",
        "project_root": str(tmp_path / "workspace"),
    }
    assert taxonomy.resolve(dossier, reg) == {"client": "Override", "project": "P", "campaign": None}

    assert taxonomy.resolve({**dossier, "mission_id": "m2"}, taxonomy.Registry()) == {
        "client": "Field",
        "project": "Field Project",
        "campaign": "Launch",
    }
    assert taxonomy.resolve({"mission_id": "m3", "campaign": "Kept", "project_root": str(tmp_path / "workspace")}, taxonomy.Registry()) == {
        "client": "Studio",
        "project": "workspace",
        "campaign": "Kept",
    }
    assert taxonomy.resolve({"mission_id": "m4"}, taxonomy.Registry()) == {
        "client": "Studio",
        "project": "Unassigned",
        "campaign": None,
    }


def _write_dossier(root: Path, mid: str, dossier: dict):
    d = root / mid
    d.mkdir(parents=True)
    (d / "dossier.json").write_text(json.dumps({"mission_id": mid, **dossier}), encoding="utf-8")


def test_scan_skips_corrupt_scopes_workspace_and_is_read_only(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    missions = tmp_path / ".agency" / "missions"
    workspace = tmp_path / "workspace"
    other = tmp_path / "other"
    workspace.mkdir()
    other.mkdir()
    _write_dossier(missions, "m1", {"goal": "a", "project_root": str(workspace)})
    _write_dossier(missions, "m2", {"goal": "b", "project_root": str(other)})
    bad = missions / "bad"
    bad.mkdir()
    (bad / "dossier.json").write_text("{", encoding="utf-8")
    before = {p: (p.read_bytes(), os.stat(p).st_mtime_ns) for p in missions.rglob("*") if p.is_file()}

    rows = list(taxonomy.scan_dossiers(workspace))

    assert [r.mission_id for r in rows] == ["m1"]
    after = {p: (p.read_bytes(), os.stat(p).st_mtime_ns) for p in missions.rglob("*") if p.is_file()}
    assert after == before


def test_tree_and_filters(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    missions = tmp_path / ".agency" / "missions"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_dossier(missions, "m1", {"client": "Acme", "project": "Rebrand", "campaign": "Spring", "project_root": str(workspace)})
    _write_dossier(missions, "m2", {"client": "Acme", "project": "Rebrand", "project_root": str(workspace)})
    _write_dossier(missions, "m3", {"project_root": str(workspace)})

    tree = taxonomy.build_tree(taxonomy.scan_dossiers(workspace), taxonomy.Registry())
    assert tree == {
        "clients": [
            {"name": "Acme", "missions": 2, "projects": [
                {"name": "Rebrand", "missions": 2, "campaigns": [{"name": "Spring", "missions": 1}]}
            ]},
            {"name": "Studio", "missions": 1, "projects": [
                {"name": "workspace", "missions": 1, "campaigns": []}
            ]},
        ]
    }

    rows = list(taxonomy.filter_rows(taxonomy.scan_dossiers(workspace), taxonomy.Registry(), client="acme", campaign="spring"))
    assert [r["mission_id"] for r in rows] == ["m1"]
