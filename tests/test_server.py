"""Tests for the Agency Studio stdlib HTTP/SSE server (`agency_studio/server.py`).

Mirrors agency-kit's offline test pattern: the only boundary stubbed is the
subprocess wrapper (`cli_engine._call`) plus the PATH lookup (`shutil.which`), so
the real `run_mission_cli` (with the new `on_event` hook) runs end-to-end without
a CLI installed and without any network. HOME is redirected to a tmp dir so the
~/.agency store is never touched; missions/ is written under tmp_path.
"""

import http.client
import json
import threading

import pytest

from agency_cli.engines import cli_engine
from agency_studio import server


# ── helpers ───────────────────────────────────────────────────────────────────

def _stub_engine(monkeypatch, inspector="VERDICT: PASS"):
    """Make run_mission_cli run offline: route → JSON array, inspect → verdict,
    everything else → canned text. Keys off stable prompt text, never call order."""
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: "/usr/local/bin/" + b)

    def _call(cmd, prompt, timeout=900):
        low = prompt.lower()
        if "json array" in low:
            return '["solve", "product"]'
        if "issue a verdict" in low:
            return inspector
        return "DEPARTMENT / SYNTHESIS OUTPUT"

    monkeypatch.setattr(cli_engine, "_call", _call)


def _start(project_root, static_root=None):
    """Start the studio server on an ephemeral loopback port in a daemon thread."""
    httpd = server.make_server(
        host="127.0.0.1", port=0,
        project_root=str(project_root), static_root=static_root,
    )
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    return httpd, host, port


def _read_sse(resp):
    """Drain an SSE response into a list of decoded event dicts."""
    events = []
    for raw in resp:
        line = raw.decode("utf-8").strip()
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:"):].strip()))
    return events


# ── security: bind + traversal ─────────────────────────────────────────────────

def test_server_binds_loopback_only(tmp_path):
    httpd, host, _ = _start(tmp_path)
    try:
        assert host == "127.0.0.1"  # never 0.0.0.0 (docs/SECURITY.md)
    finally:
        httpd.shutdown()


def test_serve_refuses_non_loopback_host():
    with pytest.raises(ValueError):
        server.serve(host="0.0.0.0", port=8765)


def test_path_traversal_returns_404(tmp_path):
    # Build a tiny GUI root with one real file; the secret sits OUTSIDE it.
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>ok</title>", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("TOP SECRET", encoding="utf-8")

    httpd, host, port = _start(tmp_path, static_root=dist)
    try:
        conn = http.client.HTTPConnection(host, port)
        # --path-as-is style: the raw traversal must not escape the GUI root.
        conn.request("GET", "/../secret.txt")
        resp = conn.getresponse()
        body = resp.read()
        assert resp.status == 404
        assert b"TOP SECRET" not in body

        # Sanity: a legitimate file inside the root is served.
        conn.request("GET", "/index.html")
        ok = conn.getresponse()
        assert ok.status == 200
        assert b"ok" in ok.read()
    finally:
        httpd.shutdown()


def test_path_inside_unit(tmp_path):
    root = tmp_path / "dist"
    root.mkdir()
    (root / "app.js").write_text("//", encoding="utf-8")
    assert server.path_inside(root, "/app.js") == (root / "app.js").resolve()
    assert server.path_inside(root, "/../secret.txt") is None
    assert server.path_inside(root, "/../../etc/passwd") is None


# ── API: mission SSE stream ─────────────────────────────────────────────────────

def test_post_mission_streams_full_sse_timeline(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))  # isolate ~/.agency store
    _stub_engine(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request(
            "POST", "/api/mission",
            body=json.dumps({"goal": "diagnose and rebuild onboarding"}),
            headers={"Content-Type": "application/json"},
        )
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    phases = [e["phase"] for e in events]
    # route → dept(s) → synth → inspect → done, in order.
    assert phases[0] == "route"
    assert events[0]["route"] == ["solve", "product"]
    assert {"phase": "dept", "dept": "solve", "status": "start"} in events
    assert {"phase": "dept", "dept": "product", "status": "done"} in events
    assert any(e["phase"] == "synth" for e in events)
    assert any(e["phase"] == "inspect" and e.get("verdict") == "PASS" for e in events)
    done = events[-1]
    assert done["phase"] == "done"
    assert done["verdict"] == "PASS"
    assert done["mission_id"]


def test_post_mission_writes_mission_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    _stub_engine(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request(
            "POST", "/api/mission",
            body=json.dumps({"goal": "launch a new product"}),
            headers={"Content-Type": "application/json"},
        )
        _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    mission_dirs = list((tmp_path / "missions").iterdir())
    assert len(mission_dirs) == 1
    folder = mission_dirs[0]
    assert (folder / "dossier.md").is_file()
    assert (folder / "deliverable.md").is_file()
    assert "DEPARTMENT / SYNTHESIS OUTPUT" in (folder / "deliverable.md").read_text()


def test_post_mission_missing_goal_is_400(tmp_path):
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=json.dumps({}),
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        assert resp.status == 400
        assert "goal" in json.loads(resp.read())["error"]
    finally:
        httpd.shutdown()


def test_veto_then_pass_streams_two_inspect_events(monkeypatch, tmp_path):
    # Art. IX: a VETO loops, never skips — the SSE must show both iterations.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: "/usr/local/bin/" + b)
    seq = iter(["VETO: invented stat", "VERDICT: PASS"])

    def _call(cmd, prompt, timeout=900):
        low = prompt.lower()
        if "json array" in low:
            return '["product"]'
        if "issue a verdict" in low:
            return next(seq)
        return "OUTPUT"

    monkeypatch.setattr(cli_engine, "_call", _call)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=json.dumps({"goal": "fix churn"}),
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    verdicts = [e["verdict"] for e in events if e["phase"] == "inspect" and "verdict" in e]
    assert verdicts == ["VETO", "PASS"]
    assert events[-1]["phase"] == "done" and events[-1]["verdict"] == "PASS"


# ── API: list / get saved missions ──────────────────────────────────────────────

def test_missions_list_and_get_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    _stub_engine(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        # Run one mission so the store has something.
        conn.request("POST", "/api/mission", body=json.dumps({"goal": "build a landing page"}),
                     headers={"Content-Type": "application/json"})
        done = _read_sse(conn.getresponse())[-1]
        mission_id = done["mission_id"]

        # List.
        conn.request("GET", "/api/missions")
        listing = json.loads(conn.getresponse().read())["missions"]
        assert any(m["mission_id"] == mission_id for m in listing)

        # Get one.
        conn.request("GET", f"/api/mission/{mission_id}")
        dossier = json.loads(conn.getresponse().read())
        assert dossier["goal"] == "build a landing page"
        assert dossier["route"] == ["solve", "product"]

        # Missing one → 404.
        conn.request("GET", "/api/mission/does-not-exist")
        assert conn.getresponse().status == 404
    finally:
        httpd.shutdown()


# ── CORS: loopback only, never wildcard ─────────────────────────────────────────

def test_cors_echoes_loopback_origin_never_wildcard(tmp_path):
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("GET", "/api/missions", headers={"Origin": "http://127.0.0.1:5173"})
        resp = conn.getresponse()
        resp.read()
        acao = resp.getheader("Access-Control-Allow-Origin")
        assert acao == "http://127.0.0.1:5173"
        assert acao != "*"

        # A non-loopback origin gets NO CORS grant.
        conn.request("GET", "/api/missions", headers={"Origin": "http://evil.example.com"})
        resp2 = conn.getresponse()
        resp2.read()
        assert resp2.getheader("Access-Control-Allow-Origin") is None
    finally:
        httpd.shutdown()
