import hashlib
import http.client
import json
import threading
from pathlib import Path

from agency_studio import server


def _isolate_home(monkeypatch, tmp_path):
    """Point the ~/.agency store at tmp_path on every platform.

    ``Path.home()`` reads HOME on POSIX but USERPROFILE on Windows (ntpath
    ignores HOME since Python 3.8), so both must be set for the store and the
    taxonomy registry to land in the isolated tmp dir.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))


def _start(project_root):
    httpd = server.make_server(host="127.0.0.1", port=0, project_root=str(project_root))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    return httpd, host, port


def _request(host, port, method, path, body=None):
    conn = http.client.HTTPConnection(host, port)
    headers = {"Content-Type": "application/json"} if body is not None else {}
    conn.request(method, path, body=json.dumps(body).encode("utf-8") if body is not None else None, headers=headers)
    resp = conn.getresponse()
    raw = resp.read()
    return resp.status, json.loads(raw or b"{}")


def _read_sse(resp):
    events = []
    for raw in resp:
        line = raw.decode("utf-8").strip()
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:"):].strip()))
    return events


def _save(mid, root, **extra):
    from agency_kit import store

    dossier = {
        "mission_id": mid,
        "goal": extra.pop("goal", "demo"),
        "project_root": store.canonical_project_root(root),
        "route": [],
        "iteration": 1,
        "verdicts": [{"verdict": "PASS"}],
        "delivered": "x",
    }
    dossier.update(extra)
    store.save(dossier)
    return store.missions_path() / mid / "dossier.json"


def test_post_mission_validates_and_persists_tags(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    from agency_cli import runner_bridge

    calls = {"n": 0}

    def _fake_run(**kwargs):
        calls["n"] += 1
        return runner_bridge.MissionResult(
            path=tmp_path,
            dossier={"mission_id": "m1", "goal": kwargs["goal"], "project_root": str(tmp_path), "verdicts": [{"verdict": "PASS"}]},
        )

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    httpd, host, port = _start(tmp_path)
    try:
        status, _body = _request(host, port, "POST", "/api/mission", {"goal": "x", "client": "bad\nname"})
        assert status == 400
        assert calls["n"] == 0

        conn = http.client.HTTPConnection(host, port)
        conn.request(
            "POST",
            "/api/mission",
            body=json.dumps({"goal": "x", "client": "Acme", "project": "Rebrand", "campaign": "Spring"}),
            headers={"Content-Type": "application/json"},
        )
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    done = events[-1]
    assert done["phase"] == "done"
    assert done["attribution"] == {"client": "Acme", "project": "Rebrand", "campaign": "Spring"}
    saved = json.loads((tmp_path / ".agency" / "missions" / "m1" / "dossier.json").read_text(encoding="utf-8"))
    assert {k: saved[k] for k in ("client", "project", "campaign")} == {
        "client": "Acme",
        "project": "Rebrand",
        "campaign": "Spring",
    }


def test_taxonomy_tree_and_filtered_missions_are_workspace_scoped(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    workspace = tmp_path / "workspace"
    other = tmp_path / "other"
    workspace.mkdir()
    other.mkdir()
    _save("m1", workspace, client="Acme", project="Rebrand", campaign="Spring")
    _save("m2", workspace)
    _save("m3", other, client="Other", project="Hidden")
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (tmp_path / ".agency").rglob("*") if p.is_file()}

    httpd, host, port = _start(workspace)
    try:
        status, tree = _request(host, port, "GET", "/api/taxonomy")
        assert status == 200
        assert tree["clients"][0]["name"] == "Acme"
        assert {c["name"] for c in tree["clients"]} == {"Acme", "Studio"}

        status, filtered = _request(host, port, "GET", "/api/missions?client=acme")
        assert status == 200
        assert [m["mission_id"] for m in filtered["missions"]] == ["m1"]
        assert filtered["missions"][0]["project"] == "Rebrand"

        status, none = _request(host, port, "GET", "/api/missions?client=Nobody")
        assert status == 200
        assert none == {"missions": []}

        status, bad = _request(host, port, "GET", "/api/missions?client=bad%0Aname")
        assert status == 400
        assert "error" in bad
    finally:
        httpd.shutdown()

    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (tmp_path / ".agency").rglob("*") if p.is_file()}
    assert after == before


def test_assign_writes_only_registry_and_clear_round_trips(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    dossier_path = _save("m1", workspace)
    before = hashlib.sha256(dossier_path.read_bytes()).hexdigest()

    httpd, host, port = _start(workspace)
    try:
        status, body = _request(host, port, "POST", "/api/mission/m1/assign", {"client": "Acme", "project": "Rebrand"})
        assert status == 200
        assert body["attribution"] == {"client": "Acme", "project": "Rebrand", "campaign": None}
        assert (tmp_path / ".agency" / "taxonomy.json").exists()
        assert hashlib.sha256(dossier_path.read_bytes()).hexdigest() == before

        status, filtered = _request(host, port, "GET", "/api/missions?client=Acme")
        assert status == 200
        assert [m["mission_id"] for m in filtered["missions"]] == ["m1"]

        status, body = _request(host, port, "POST", "/api/mission/m1/assign", {"clear": True})
        assert status == 200
        assert body["attribution"]["client"] == "Studio"
        assert hashlib.sha256(dossier_path.read_bytes()).hexdigest() == before

        status, _ = _request(host, port, "POST", "/api/mission/nope/assign", {"client": "Acme"})
        assert status == 404
        status, _ = _request(host, port, "POST", "/api/mission/m1/assign", {"client": "bad\nname"})
        assert status == 400
    finally:
        httpd.shutdown()
