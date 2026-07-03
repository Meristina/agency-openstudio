"""Tests for the mission store — focused on project-scoped listing/matching.

list_missions() lists the global ~/.agency store; passing project_root scopes the
listing to one project (the Studio GUI launched with --path), so it doesn't surface
every mission on the machine. mission_in_project() is the per-dossier predicate the
server reuses to scope GET-by-id / PDF.
"""

import json

from agency_kit import store


def _save(monkeypatch, missions_root, mission_id, goal, project_root=None):
    """Write a minimal dossier.json into a fake missions dir for one mission.
    Omits project_root when None (a pre-feature 'legacy' mission)."""
    monkeypatch.setattr(store, "missions_dir", lambda: missions_root)
    d = missions_root / mission_id
    d.mkdir(parents=True)
    dossier = {"mission_id": mission_id, "goal": goal, "verdicts": [], "delivered": "x"}
    if project_root is not None:
        dossier["project_root"] = project_root
    (d / "dossier.json").write_text(json.dumps(dossier), encoding="utf-8")


def test_list_missions_unscoped_returns_all(monkeypatch, tmp_path):
    missions = tmp_path / "missions"
    _save(monkeypatch, missions, "001-a", "in A", str((tmp_path / "projA").resolve()))
    _save(monkeypatch, missions, "002-b", "in B", str((tmp_path / "projB").resolve()))
    assert {m["goal"] for m in store.list_missions()} == {"in A", "in B"}


def test_list_missions_empty_project_root_lists_all(monkeypatch, tmp_path):
    # A falsy project_root ("" / None) means 'no scoping', not 'scope to CWD'.
    missions = tmp_path / "missions"
    _save(monkeypatch, missions, "001-a", "in A", str((tmp_path / "projA").resolve()))
    _save(monkeypatch, missions, "002-b", "in B", str((tmp_path / "projB").resolve()))
    assert {m["goal"] for m in store.list_missions(project_root="")} == {"in A", "in B"}


def test_list_missions_scoped_filters_by_project_root(monkeypatch, tmp_path):
    missions = tmp_path / "missions"
    _save(monkeypatch, missions, "001-a", "in A", str((tmp_path / "projA").resolve()))
    _save(monkeypatch, missions, "002-b", "in B", str((tmp_path / "projB").resolve()))
    scoped = store.list_missions(project_root=str(tmp_path / "projA"))
    assert [m["goal"] for m in scoped] == ["in A"]  # only this project's mission


def test_list_missions_scoped_includes_unstamped_legacy(monkeypatch, tmp_path):
    # A mission saved before the project_root stamp existed has no such field and
    # must still appear — upgrading must not hide a user's existing history.
    missions = tmp_path / "missions"
    _save(monkeypatch, missions, "001-a", "in A", str((tmp_path / "projA").resolve()))
    _save(monkeypatch, missions, "000-legacy", "legacy", None)
    goals = {m["goal"] for m in store.list_missions(project_root=str(tmp_path / "projA"))}
    assert goals == {"in A", "legacy"}


def test_mission_in_project_matches_stamp_and_allows_legacy(tmp_path):
    root = str((tmp_path / "projA").resolve())
    assert store.mission_in_project({"project_root": root}, str(tmp_path / "projA"))
    assert not store.mission_in_project({"project_root": root}, str(tmp_path / "projB"))
    assert store.mission_in_project({}, str(tmp_path / "projA"))   # legacy → allowed
    assert store.mission_in_project({"project_root": root}, "")    # no scope → allowed
    assert not store.mission_in_project(["not", "a", "dict"], str(tmp_path / "projA"))


def test_list_missions_skips_malformed_dossiers(monkeypatch, tmp_path):
    # A non-object dossier.json is skipped (not crash); a wrong-typed goal is coerced
    # rather than raising; a valid sibling still lists. "Programming errors propagate"
    # stays intact — only explicit data-shape guards do the skipping/coercion.
    import json
    missions = tmp_path / "missions"
    _save(monkeypatch, missions, "001-ok", "good", None)
    array_dir = missions / "002-array"
    array_dir.mkdir()
    (array_dir / "dossier.json").write_text("[1, 2, 3]", encoding="utf-8")
    typed_dir = missions / "003-typed"
    typed_dir.mkdir()
    (typed_dir / "dossier.json").write_text(
        json.dumps({"mission_id": "003-typed", "goal": 123, "verdicts": [["bad"]]}),
        encoding="utf-8",
    )

    rows = {m["mission_id"]: m for m in store.list_missions()}
    assert "001-ok" in rows                       # valid mission listed
    assert "002-array" not in rows                # non-object dossier skipped
    assert rows["003-typed"]["goal"] == "123"     # non-str goal coerced, not crashed
    assert rows["003-typed"]["verdict"] == "—"    # non-dict verdict entry tolerated


def test_last_verdict_token_handles_missing_and_malformed(tmp_path):
    assert store.last_verdict_token({"verdicts": []}) == "in-progress"
    assert store.last_verdict_token({}) == "in-progress"
    assert store.last_verdict_token({"verdicts": [{"verdict": "PASS"}]}) == "PASS"
    assert store.last_verdict_token({"verdicts": [{}]}) == "—"
    assert store.last_verdict_token({"verdicts": ["oops"]}) == "—"
