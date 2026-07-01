"""Tests for the Agency Studio stdlib HTTP/SSE server (`agency_studio/server.py`).

Mirrors agency-kit's offline test pattern: the only boundary stubbed is the
subprocess wrapper (`cli_engine._call`) plus the PATH lookup (`shutil.which`), so
the real `run_mission_cli` (with the new `on_event` hook) runs end-to-end without
a CLI installed and without any network. HOME is redirected to a tmp dir so the
~/.agency store is never touched; missions/ is written under tmp_path.
"""

import http.client
import json
import socket
import threading
import time

import pytest

from agency_cli.engines import cli_engine
from agency_studio import server


# ── helpers ───────────────────────────────────────────────────────────────────

def _stub_engine(monkeypatch, inspector="VERDICT: PASS"):
    """Make run_mission_cli run offline: route → JSON array, inspect → verdict,
    everything else → canned text. Keys off stable prompt text, never call order."""
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: "/usr/local/bin/" + b)

    def _call(cmd, prompt, timeout=900, should_cancel=None):
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


def test_path_inside_resolves_inside_root_and_rejects_traversal(tmp_path):
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
    # run → route → dept(s) → synth → inspect → done, in order.
    assert phases[0] == "run"
    assert server._RUN_ID_RE.match(events[0]["run_id"]), "first frame announces the run id"
    route_event = next(e for e in events if e["phase"] == "route")
    assert route_event["route"] == ["solve", "product"]
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


def test_stream_mission_wires_a_live_cancel_predicate(monkeypatch, tmp_path):
    # The server must hand the worker a cooperative-cancel predicate so a client
    # disconnect can stop the run (the GUI's "Stop mission"). Capture it and confirm
    # it is a live, initially-False callable — the cancel_event.is_set bound method.
    # (What happens once it returns True — MissionCancelled + no-persist — is locked
    # deterministically in the engine/bridge tests; the disconnect→set race is not
    # worth a flaky socket test.)
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_cli import runner_bridge

    captured = {}

    def _fake_run(goal, project_root, engine, on_event=None, should_cancel=None,
                  asset_clause=None, render_assets=None, context_clause=None):
        captured["should_cancel"] = should_cancel
        on_event({"phase": "route", "status": "done", "route": []})
        return runner_bridge.MissionResult(
            path=tmp_path, dossier={"verdicts": [], "mission_id": "test-id"}
        )

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request(
            "POST", "/api/mission",
            body=json.dumps({"goal": "x"}),
            headers={"Content-Type": "application/json"},
        )
        _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    sc = captured.get("should_cancel")
    assert callable(sc), "server must pass a should_cancel predicate to the worker"
    assert sc() is False, "predicate must read False while the client stays connected"


def test_write_heartbeat_writes_an_sse_comment_when_connected():
    # The v2 mid-call kill hinges on noticing a disconnect during an event-silent
    # engine call. The drain loop probes by WRITING a heartbeat; a connected client
    # takes the write and the frame is an SSE comment (":" prefix, no data: field) so
    # the GUI parser ignores it — it must never look like a mission event.
    import io

    handler = server.StudioHandler.__new__(server.StudioHandler)
    handler.wfile = io.BytesIO()
    assert handler._write_heartbeat() is True, "a connected client must read as live"
    frame = handler.wfile.getvalue()
    assert frame.startswith(b":"), "heartbeat must be an SSE comment, not a data: frame"
    assert b"data:" not in frame


def test_write_heartbeat_reports_gone_on_broken_pipe():
    # A failed write is the reliable 'client gone' signal (the GUI aborted the fetch).
    class _BrokenWfile:
        def write(self, _data):
            raise BrokenPipeError()

        def flush(self):
            pass

    handler = server.StudioHandler.__new__(server.StudioHandler)
    handler.wfile = _BrokenWfile()
    assert handler._write_heartbeat() is False, "a broken pipe must read as gone"


# ── explicit cancel endpoint (run-id) ───────────────────────────────────────────

def test_cancel_endpoint_sets_event_then_404s_unknown_and_malformed(tmp_path):
    # POST /api/mission/{run_id}/cancel sets that run's cancel_event (202); an
    # unknown or malformed run id is a 404 and never mutates the registry.
    httpd, host, port = _start(tmp_path)
    cancel_event = threading.Event()
    run_id = "a" * 32
    httpd.runs[run_id] = cancel_event  # inject a fake in-flight run
    try:
        resp, body = _post(host, port, f"/api/mission/{run_id}/cancel")
        assert resp.status == 202
        assert json.loads(body) == {"status": "cancelling", "run_id": run_id}
        assert cancel_event.is_set(), "cancel must set the registered run's event"

        unknown, _ = _post(host, port, "/api/mission/" + ("b" * 32) + "/cancel")
        assert unknown.status == 404  # unknown run

        malformed, _ = _post(host, port, "/api/mission/not-a-valid-run/cancel")
        assert malformed.status == 404  # malformed id, never a registry key
    finally:
        httpd.shutdown()


def test_endpoint_cancel_stops_an_in_flight_mission_and_emits_cancelled(monkeypatch, tmp_path):
    # End-to-end: a streaming mission, cancelled via the explicit endpoint from a
    # second connection, must end with a `cancelled` terminal frame (not `done`).
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_cli import runner_bridge
    from agency_cli.engines.cli_engine import MissionCancelled

    def _fake_run(goal, project_root, engine, on_event=None, should_cancel=None,
                  asset_clause=None, render_assets=None, context_clause=None):
        on_event({"phase": "route", "status": "done", "route": ["solve"]})
        for _ in range(500):  # ~5s ceiling: a stuck cancel fails the test, never hangs CI
            if should_cancel():
                raise MissionCancelled()
            time.sleep(0.01)
        return runner_bridge.MissionResult(path=tmp_path, dossier={"verdicts": [], "mission_id": "x"})

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    httpd, host, port = _start(tmp_path)

    def _cancel_when_registered():
        for _ in range(500):
            with httpd.runs_lock:
                ids = list(httpd.runs)
            if ids:
                c = http.client.HTTPConnection(host, port)
                c.request("POST", f"/api/mission/{ids[0]}/cancel")
                c.getresponse().read()
                return
            time.sleep(0.01)

    try:
        threading.Thread(target=_cancel_when_registered, daemon=True).start()
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=json.dumps({"goal": "g"}),
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    phases = [e["phase"] for e in events]
    assert phases[0] == "run", "the run id is announced first"
    assert phases[-1] == "cancelled", "an endpoint cancel ends the stream with a cancelled frame"
    assert "done" not in phases, "a cancelled mission must not also report done"


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


def test_post_mission_malformed_json_is_400(tmp_path):
    # The sole POST endpoint must reject a non-JSON body before running anything.
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=b"{not json",
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        assert resp.status == 400
        assert json.loads(resp.read())["error"] == "body must be JSON"
    finally:
        httpd.shutdown()


def test_veto_then_pass_streams_two_inspect_events(monkeypatch, tmp_path):
    # Art. IX: a VETO loops, never skips — the SSE must show both iterations.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: "/usr/local/bin/" + b)
    seq = iter(["VETO: invented stat", "VERDICT: PASS"])

    def _call(cmd, prompt, timeout=900, should_cancel=None):
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


def test_history_is_scoped_to_the_server_project(monkeypatch, tmp_path):
    # The GUI must list only THIS project's missions, not every mission in the
    # global ~/.agency store (the server is launched with --path).
    monkeypatch.setenv("HOME", str(tmp_path))
    proj_a = tmp_path / "projA"
    proj_b = tmp_path / "projB"
    _save_dossier("001-in-a", proj_a, goal="mission in A")
    _save_dossier("002-in-b", proj_b, goal="mission in B")

    httpd, host, port = _start(proj_a)
    try:
        _resp, body = _get(host, port, "/api/missions")
        goals = [m["goal"] for m in json.loads(body)["missions"]]
        assert "mission in A" in goals
        assert "mission in B" not in goals  # other project's mission is not listed
    finally:
        httpd.shutdown()


def test_get_mission_from_another_project_is_404(monkeypatch, tmp_path):
    # A confined server (--path projA) must not disclose projB's dossier by id.
    monkeypatch.setenv("HOME", str(tmp_path))
    _save_dossier("20260101-000000-foreign", tmp_path / "projB",
                  goal="confidential", delivered="secret deliverable")
    httpd, host, port = _start(tmp_path / "projA")
    try:
        resp, body = _get(host, port, "/api/mission/20260101-000000-foreign")
        assert resp.status == 404
        assert b"confidential" not in body and b"secret" not in body
    finally:
        httpd.shutdown()


def test_get_legacy_unstamped_mission_is_served(monkeypatch, tmp_path):
    # A mission with no project_root stamp (pre-feature) stays openable by id.
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_kit import store
    store.save({"mission_id": "20260101-000000-legacy", "goal": "old mission",
                "verdicts": [], "delivered": "x"})  # no project_root
    httpd, host, port = _start(tmp_path / "projA")
    try:
        resp, body = _get(host, port, "/api/mission/20260101-000000-legacy")
        assert resp.status == 200
        assert json.loads(body)["goal"] == "old mission"
    finally:
        httpd.shutdown()


def test_get_corrupt_dossier_is_404_not_crash(monkeypatch, tmp_path):
    # A truncated/invalid dossier.json must yield a clean 404, not an uncaught
    # JSONDecodeError that drops the connection (do_GET has no top-level handler).
    monkeypatch.setenv("HOME", str(tmp_path))
    mdir = tmp_path / ".agency" / "missions" / "20260101-000000-corrupt"
    mdir.mkdir(parents=True)
    (mdir / "dossier.json").write_text("{ not valid json", encoding="utf-8")
    httpd, host, port = _start(tmp_path)
    try:
        resp, _ = _get(host, port, "/api/mission/20260101-000000-corrupt")
        assert resp.status == 404
    finally:
        httpd.shutdown()


def test_get_mission_rejects_path_traversal(monkeypatch, tmp_path):
    # A traversal id must be rejected before it can reach store.load(), which
    # builds a filesystem path from the id (docs/SECURITY.md).
    monkeypatch.setenv("HOME", str(tmp_path))

    def _must_not_load(_mission_id):
        raise AssertionError("store.load must not be called for a traversal id")

    monkeypatch.setattr("agency_kit.store.load", _must_not_load)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("GET", "/api/mission/../../../../etc/passwd")
        resp = conn.getresponse()
        body = resp.read()
        assert resp.status == 404
        assert b"passwd" not in body and b"root:" not in body
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


def test_options_preflight_grants_loopback_cors(tmp_path):
    # The browser issues OPTIONS before the POST mission stream; it must get the
    # 204 preflight with the loopback origin echoed and the methods/headers grant.
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("OPTIONS", "/api/mission", headers={"Origin": "http://127.0.0.1:5173"})
        resp = conn.getresponse()
        resp.read()
        assert resp.status == 204
        assert resp.getheader("Access-Control-Allow-Origin") == "http://127.0.0.1:5173"
        assert resp.getheader("Access-Control-Allow-Methods") == "GET, POST, DELETE, OPTIONS"
        assert resp.getheader("Access-Control-Allow-Headers") == "Content-Type"
    finally:
        httpd.shutdown()


# ── DNS-rebinding: Host-header allowlist ────────────────────────────────────────

def test_foreign_host_header_is_rejected_403(tmp_path):
    # Even reaching the loopback-bound socket, a request whose Host names a non-loopback
    # name (a rebound evil.com) is refused with 403 before any route runs — the defense
    # the Origin allowlist alone can't provide against DNS rebinding.
    httpd, host, port = _start(tmp_path)
    try:
        raw = _raw_request(
            host, port,
            b"GET /api/missions HTTP/1.1\r\nHost: evil.example.com\r\n"
            b"Connection: close\r\n\r\n",
        )
        assert raw.startswith(b"HTTP/1.1 403")
    finally:
        httpd.shutdown()


def test_loopback_host_header_is_allowed(tmp_path):
    # The legitimate local client (Host: 127.0.0.1:<port>) passes the guard.
    httpd, host, port = _start(tmp_path)
    try:
        raw = _raw_request(
            host, port,
            f"GET /api/missions HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n"
            f"Connection: close\r\n\r\n".encode(),
        )
        assert not raw.startswith(b"HTTP/1.1 403"), "a loopback Host must not be rejected"
    finally:
        httpd.shutdown()


# ── SSE streaming: a stalled (non-draining) client is detected as gone ──────────

def test_sse_writes_treat_socket_timeout_as_a_gone_client():
    # With a send deadline on the streaming socket, a write that times out (a client that
    # opened the stream but stopped reading) is reported as gone — the same as a broken
    # pipe — so the drain loop sets cancel_event instead of blocking the handler forever.
    handler = server.StudioHandler.__new__(server.StudioHandler)

    class _StalledWfile:
        def write(self, _b):
            raise socket.timeout("send timed out")

        def flush(self):
            pass

    handler.wfile = _StalledWfile()
    assert handler._write_sse({"phase": "x"}) is False
    assert handler._write_heartbeat() is False


# ── PDF export: GET /api/mission/{id}/pdf ───────────────────────────────────────

def _get(host, port, path):
    conn = http.client.HTTPConnection(host, port)
    conn.request("GET", path)
    resp = conn.getresponse()
    return resp, resp.read()


def _post(host, port, path, body=None):
    conn = http.client.HTTPConnection(host, port)
    conn.request("POST", path, body=body)
    resp = conn.getresponse()
    return resp, resp.read()


def _save_dossier(mission_id, project_root, *, goal="demo", delivered="x"):
    """Save a dossier into the (HOME-isolated) global store, stamped with the
    canonical project_root, so the server's project-scope gate admits it."""
    from agency_kit import store
    store.save({
        "mission_id": mission_id, "goal": goal,
        "project_root": store.canonical_project_root(project_root),
        "verdicts": [], "delivered": delivered,
    })


def test_mission_pdf_streams_the_exported_file(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    _save_dossier("20260630-101010-demo", tmp_path)
    pdf = tmp_path / "deliverable.pdf"
    pdf.write_bytes(b"%PDF-1.7\nfake pdf bytes\n%%EOF")
    # Capture the kwargs so we assert the server threads the studio_assets root through
    # to the exporter (Wave 3 — so /media asset refs resolve to on-disk files).
    captured = {}

    def _export(_mid, **kw):
        captured.update(kw)
        return pdf

    monkeypatch.setattr("agency_cli.exporter.export_pdf", _export)
    httpd, host, port = _start(tmp_path)
    try:
        resp, body = _get(host, port, "/api/mission/20260630-101010-demo/pdf")
        assert resp.status == 200
        assert resp.getheader("Content-Type") == "application/pdf"
        assert "attachment" in (resp.getheader("Content-Disposition") or "")
        assert body.startswith(b"%PDF")
        assert str(captured["assets_root"]).endswith("studio_assets")
    finally:
        httpd.shutdown()


def test_mission_pdf_missing_extra_is_501(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    _save_dossier("20260630-101010-demo", tmp_path)

    def _no_extra(_mid, **kw):
        raise ImportError('WeasyPrint not installed. Run:  pip install -e ".[pdf]"')

    monkeypatch.setattr("agency_cli.exporter.export_pdf", _no_extra)
    httpd, host, port = _start(tmp_path)
    try:
        resp, body = _get(host, port, "/api/mission/20260630-101010-demo/pdf")
        assert resp.status == 501
        assert "pip install" in json.loads(body)["error"]
    finally:
        httpd.shutdown()


def test_mission_pdf_unknown_mission_is_404(monkeypatch, tmp_path):
    # No saved dossier → the scope gate returns 404 before any export attempt.
    monkeypatch.setenv("HOME", str(tmp_path))
    httpd, host, port = _start(tmp_path)
    try:
        resp, _ = _get(host, port, "/api/mission/20260630-101010-demo/pdf")
        assert resp.status == 404
    finally:
        httpd.shutdown()


def test_mission_pdf_no_deliverable_is_404(monkeypatch, tmp_path):
    # Dossier exists (passes the scope gate) but has no deliverable.md, so
    # export_pdf raises and the OSError→404 branch must answer cleanly.
    monkeypatch.setenv("HOME", str(tmp_path))
    _save_dossier("20260630-101010-demo", tmp_path)
    monkeypatch.setattr(
        "agency_cli.exporter.export_pdf",
        lambda _mid, **kw: (_ for _ in ()).throw(FileNotFoundError("no deliverable")),
    )
    httpd, host, port = _start(tmp_path)
    try:
        resp, _ = _get(host, port, "/api/mission/20260630-101010-demo/pdf")
        assert resp.status == 404
    finally:
        httpd.shutdown()


def test_mission_pdf_rejects_path_traversal(monkeypatch, tmp_path):
    # The id is validated before export_pdf runs — a traversal id never exports.
    def _must_not_export(_mid, **kw):
        raise AssertionError("export_pdf must not run for a traversal id")

    monkeypatch.setattr("agency_cli.exporter.export_pdf", _must_not_export)
    httpd, host, port = _start(tmp_path)
    try:
        resp, body = _get(host, port, "/api/mission/../../../../etc/passwd/pdf")
        assert resp.status == 404
        assert b"root:" not in body
    finally:
        httpd.shutdown()


def test_mission_pdf_render_error_is_500(monkeypatch, tmp_path):
    # A render failure AFTER the [pdf] extra is present (not ImportError/OSError)
    # must surface as a clean 500, not a dropped connection.
    monkeypatch.setenv("HOME", str(tmp_path))
    _save_dossier("20260630-101010-demo", tmp_path)

    def _boom(_mid, **kw):
        raise RuntimeError("WeasyPrint failed to render")

    monkeypatch.setattr("agency_cli.exporter.export_pdf", _boom)
    httpd, host, port = _start(tmp_path)
    try:
        resp, body = _get(host, port, "/api/mission/20260630-101010-demo/pdf")
        assert resp.status == 500
        assert "PDF export failed" in json.loads(body)["error"]
    finally:
        httpd.shutdown()


def test_mission_pdf_from_another_project_is_404(monkeypatch, tmp_path):
    # Scoping the LIST isn't enough: the PDF export of a foreign mission must also
    # be refused (it produces a shareable artifact), and export must not even run.
    monkeypatch.setenv("HOME", str(tmp_path))
    _save_dossier("20260101-000000-foreign", tmp_path / "projB")

    def _must_not_export(_mid, **kw):
        raise AssertionError("export_pdf must not run for a foreign mission")

    monkeypatch.setattr("agency_cli.exporter.export_pdf", _must_not_export)
    httpd, host, port = _start(tmp_path / "projA")  # server confined to projA
    try:
        resp, _ = _get(host, port, "/api/mission/20260101-000000-foreign/pdf")
        assert resp.status == 404
    finally:
        httpd.shutdown()


# ── request-body hardening ──────────────────────────────────────────────────────

def _raw_request(host, port, request_bytes):
    """Send a hand-crafted HTTP request (bypassing http.client's own framing) and
    return the raw response bytes — for malformed Content-Length cases."""
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(request_bytes)
        sock.settimeout(5)
        chunks = []
        try:
            while True:
                buf = sock.recv(4096)
                if not buf:
                    break
                chunks.append(buf)
        except socket.timeout:
            pass
    return b"".join(chunks)


def test_negative_content_length_is_400(tmp_path):
    httpd, host, port = _start(tmp_path)
    try:
        raw = _raw_request(
            host, port,
            b"POST /api/mission HTTP/1.1\r\nHost: localhost\r\n"
            b"Content-Length: -1\r\nConnection: close\r\n\r\n",
        )
        assert raw.startswith(b"HTTP/1.1 400")
    finally:
        httpd.shutdown()


def test_oversized_content_length_is_413(tmp_path):
    # A Content-Length above the cap is rejected WITHOUT reading the body, so the
    # handler thread never blocks waiting on bytes the client won't send. The reject
    # also tells keep-alive clients the socket is closing (Connection: close).
    httpd, host, port = _start(tmp_path)
    try:
        raw = _raw_request(
            host, port,
            b"POST /api/mission HTTP/1.1\r\nHost: localhost\r\n"
            b"Content-Length: 2000000\r\n\r\n",
        )
        assert raw.startswith(b"HTTP/1.1 413")
        assert b"Connection: close" in raw
    finally:
        httpd.shutdown()


def test_chunked_body_is_rejected_as_411(tmp_path):
    # http.server can't decode a chunked body; an unread chunk-framed body would
    # desync the socket, so Transfer-Encoding is refused before any read.
    httpd, host, port = _start(tmp_path)
    try:
        raw = _raw_request(
            host, port,
            b"POST /api/mission HTTP/1.1\r\nHost: localhost\r\n"
            b"Transfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n",
        )
        assert raw.startswith(b"HTTP/1.1 411")
        assert b"Connection: close" in raw
    finally:
        httpd.shutdown()


def test_withheld_body_times_out_as_408(monkeypatch, tmp_path):
    # A declared-but-withheld body (slowloris) must not pin the handler thread; the
    # bounded read returns 408 instead of blocking forever.
    monkeypatch.setattr(server, "_BODY_READ_TIMEOUT", 0.3)
    httpd, host, port = _start(tmp_path)
    try:
        raw = _raw_request(
            host, port,
            b"POST /api/mission HTTP/1.1\r\nHost: localhost\r\n"
            b"Content-Length: 50\r\n\r\n",  # promises 50 bytes, sends none
        )
        assert raw.startswith(b"HTTP/1.1 408")
    finally:
        httpd.shutdown()


def test_unknown_post_path_is_404(tmp_path):
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/nope", body=json.dumps({"x": 1}),
                     headers={"Content-Type": "application/json"})
        assert conn.getresponse().status == 404
    finally:
        httpd.shutdown()


# ── static serving: SPA fallback + content types ────────────────────────────────

def test_missing_asset_with_extension_is_404_not_index(tmp_path):
    # A stale/renamed hashed bundle must 404 — never the SPA index as text/html,
    # which the browser would reject as a module script (blank-screen failure).
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>spa</title>", encoding="utf-8")
    httpd, host, port = _start(tmp_path, static_root=dist)
    try:
        resp, body = _get(host, port, "/assets/index-abc123.js")
        assert resp.status == 404
        assert b"<!doctype html>" not in body
    finally:
        httpd.shutdown()


def test_extensionless_route_falls_back_to_index(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>spa</title>", encoding="utf-8")
    httpd, host, port = _start(tmp_path, static_root=dist)
    try:
        resp, body = _get(host, port, "/missions/some-id")  # client-side route
        assert resp.status == 200
        assert b"spa" in body
    finally:
        httpd.shutdown()


def test_dotted_route_segment_still_falls_back_to_index(tmp_path):
    # A route whose last segment has a dot (e.g. a version) is NOT a known asset
    # type, so it must fall back to index.html, not 404.
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>spa</title>", encoding="utf-8")
    httpd, host, port = _start(tmp_path, static_root=dist)
    try:
        resp, body = _get(host, port, "/missions/v1.2")
        assert resp.status == 200
        assert b"spa" in body
    finally:
        httpd.shutdown()


def test_static_serves_known_content_type(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("x", encoding="utf-8")
    (dist / "logo.webp").write_bytes(b"RIFFfakewebp")
    httpd, host, port = _start(tmp_path, static_root=dist)
    try:
        resp, _ = _get(host, port, "/logo.webp")
        assert resp.status == 200
        assert resp.getheader("Content-Type") == "image/webp"
    finally:
        httpd.shutdown()


# ── Wave 3: asset render hook wiring (_build_render_assets + ASSET_CLAUSE) ─────

def test_build_render_assets_renders_rewrites_and_emits(tmp_path):
    # The closure the worker hands the bridge: parse markers from `delivered`, render via
    # the one warm manager into studio_assets/missions/<id>/, attach the manifest, rewrite
    # `delivered`, and queue an SSE asset frame.
    import queue
    from types import SimpleNamespace
    from pathlib import Path

    class _FakeMgr:
        def generate_image(self, prompt, *, model, width, height, out_dir):
            p = Path(out_dir) / "images" / "a.png"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"\x89PNG")
            return SimpleNamespace(path=p, model=model, seconds=1.0)

    fake_server = SimpleNamespace(
        media_lock=threading.Lock(), media=_FakeMgr(), assets_root=tmp_path,
        retention_lock=threading.Lock(), media_budget_bytes=10**12,  # huge → prune is a no-op
    )
    events: "queue.Queue" = queue.Queue()
    cancel = threading.Event()
    render_assets = server._build_render_assets(fake_server, events, cancel)

    dossier = {
        "mission_id": "001-x",
        "route": ["marketing"],
        "delivered": "Hi\n```asset\n" + json.dumps({"type": "image", "prompt": "hero"}) + "\n```\nBye",
    }
    render_assets(dossier)

    assert dossier["assets"][0]["status"] == "ok"
    assert "![hero](/media/missions/001-x/images/a.png)" in dossier["delivered"]
    assert (tmp_path / "missions" / "001-x" / "images" / "a.png").is_file()
    frames = []
    while not events.empty():
        frames.append(events.get())
    assert any(f.get("phase") == "asset" for f in frames), "an SSE asset frame must be queued"


def test_build_render_assets_stop_skips_render_without_gpu(tmp_path):
    # The closure must thread should_cancel=cancel_event.is_set into render, so a Stop
    # landing in the post-inspection window aborts the render with no GPU spend. A
    # regression dropping the predicate (should_cancel=None) would pass every other test.
    import queue
    from types import SimpleNamespace

    class _FakeMgr:
        def __init__(self):
            self.calls = 0

        def generate_image(self, *a, **k):
            self.calls += 1
            raise AssertionError("render must not run once the mission is cancelled")

    mgr = _FakeMgr()
    fake_server = SimpleNamespace(
        media_lock=threading.Lock(), media=mgr, assets_root=tmp_path,
        retention_lock=threading.Lock(), media_budget_bytes=10**12,
    )
    cancel = threading.Event()
    cancel.set()  # Stop already requested before render
    render_assets = server._build_render_assets(fake_server, queue.Queue(), cancel)

    dossier = {
        "mission_id": "001-x", "route": ["marketing"],
        "delivered": "```asset\n" + json.dumps({"type": "image", "prompt": "hero"}) + "\n```",
    }
    render_assets(dossier)
    assert mgr.calls == 0
    assert dossier["assets"][0]["status"] == "skipped"


def test_build_render_assets_no_markers_is_a_noop(tmp_path):
    from types import SimpleNamespace
    import queue
    fake_server = SimpleNamespace(media_lock=threading.Lock(), media=object(), assets_root=tmp_path)
    render_assets = server._build_render_assets(fake_server, queue.Queue(), threading.Event())
    dossier = {"mission_id": "001-x", "route": ["marketing"], "delivered": "no markers here"}
    render_assets(dossier)
    assert "assets" not in dossier  # nothing parsed → nothing attached, delivered untouched


def test_build_render_assets_strips_off_route_fence_without_touching_gpu(tmp_path):
    # Repro from #19: a marketing-only mission whose model emits a `tts` marker → dropped
    # off-route → zero valid requests. No manager is touched (media would raise if used), but
    # the raw fence must still be stripped from `delivered` so it never reaches the PDF.
    from types import SimpleNamespace
    import queue

    class _BoomMgr:  # any attribute access is a test failure — render must not run
        def __getattr__(self, name):
            raise AssertionError("the warm manager must not be touched with no valid requests")

    fake_server = SimpleNamespace(media_lock=threading.Lock(), media=_BoomMgr(), assets_root=tmp_path)
    render_assets = server._build_render_assets(fake_server, queue.Queue(), threading.Event())
    dossier = {
        "mission_id": "001-x", "route": ["marketing"],  # comms did NOT run → tts is off-route
        "delivered": "Intro\n```asset\n" + json.dumps({"type": "tts", "text": "hi"}) + "\n```\nOutro",
    }
    render_assets(dossier)
    assert "```asset" not in dossier["delivered"], "the off-route fence is stripped"
    assert dossier["delivered"] == "Intro\nOutro"
    assert "assets" not in dossier  # nothing rendered/attempted → no manifest attached


def test_build_render_assets_prunes_old_missions_after_render(tmp_path):
    # Post-render retention: an old mission's assets are evicted once the budget is exceeded,
    # while the just-rendered mission (keep={id}) is protected even though it is newest.
    import os
    import queue
    from types import SimpleNamespace
    from pathlib import Path

    old = tmp_path / "missions" / "000-old" / "images" / "big.png"
    old.parent.mkdir(parents=True, exist_ok=True)
    old.write_bytes(b"\0" * 5000)
    os.utime(old, (1000, 1000))  # ancient → first to evict
    os.utime(tmp_path / "missions" / "000-old", (1000, 1000))  # backdate the dir past the grace

    class _FakeMgr:
        def generate_image(self, prompt, *, model, width, height, out_dir):
            p = Path(out_dir) / "images" / "a.png"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"\x89PNG")
            return SimpleNamespace(path=p, model=model, seconds=1.0)

    fake_server = SimpleNamespace(
        media_lock=threading.Lock(), media=_FakeMgr(), assets_root=tmp_path,
        retention_lock=threading.Lock(), media_budget_bytes=1000,  # tiny → must evict the old one
    )
    render_assets = server._build_render_assets(fake_server, queue.Queue(), threading.Event())
    dossier = {
        "mission_id": "001-new", "route": ["marketing"],
        "delivered": "```asset\n" + json.dumps({"type": "image", "prompt": "hero"}) + "\n```",
    }
    render_assets(dossier)
    assert not (tmp_path / "missions" / "000-old").exists(), "old mission evicted by the cap"
    assert (tmp_path / "missions" / "001-new").is_dir(), "the just-rendered mission is kept"


def test_make_server_prunes_over_budget_assets_at_startup(tmp_path):
    # Boot-time prune bounds growth even if a prior run was killed before it could prune.
    import os
    assets = tmp_path / "studio_assets"
    stale = assets / "missions" / "000" / "images" / "big.png"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_bytes(b"\0" * 5000)
    os.utime(stale, (1000, 1000))
    os.utime(assets / "missions" / "000", (1000, 1000))  # backdate the dir past the grace window
    httpd = server.make_server(
        host="127.0.0.1", port=0, project_root=str(tmp_path), media_budget_bytes=1000,
    )
    try:
        assert not (assets / "missions" / "000").exists(), "startup prune evicts over-budget assets"
    finally:
        httpd.server_close()


def test_post_mission_passes_asset_hook_to_runner(monkeypatch, tmp_path):
    # The worker must forward ASSET_CLAUSE + a render_assets callable into runner_bridge.run.
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_cli import runner_bridge
    captured = {}

    def _fake_run(goal, project_root, engine, on_event=None, should_cancel=None,
                  asset_clause=None, render_assets=None, context_clause=None):
        captured["asset_clause"] = asset_clause
        captured["render_assets"] = render_assets
        return runner_bridge.MissionResult(
            path=tmp_path, dossier={"verdicts": [{"verdict": "PASS"}], "mission_id": "x"}
        )

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=json.dumps({"goal": "g"}),
                     headers={"Content-Type": "application/json"})
        _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    assert captured["asset_clause"] == server.ASSET_CLAUSE
    assert callable(captured["render_assets"])


def test_done_frame_carries_asset_summary(monkeypatch, tmp_path):
    # The terminal `done` frame surfaces the manifest + rendered/total counts for the GUI.
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_cli import runner_bridge

    def _fake_run(goal, project_root, engine, on_event=None, should_cancel=None,
                  asset_clause=None, render_assets=None, context_clause=None):
        return runner_bridge.MissionResult(path=tmp_path, dossier={
            "verdicts": [{"verdict": "PASS"}], "mission_id": "x",
            "assets": [
                {"type": "image", "status": "ok", "url": "/media/a.png"},
                {"type": "tts", "status": "failed", "reason": "x"},
            ],
        })

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=json.dumps({"goal": "g"}),
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    done = next(e for e in events if e["phase"] == "done")
    assert done["assets_total"] == 2 and done["assets_rendered"] == 1
    assert len(done["assets"]) == 2


# ── Wave 4 — RAG: /api/docs endpoints + retrieval injection ─────────────────────

def _delete(host, port, path):
    conn = http.client.HTTPConnection(host, port)
    conn.request("DELETE", path)
    resp = conn.getresponse()
    return resp, resp.read()


class _FakeRetriever:
    """In-memory stand-in for LocalRetriever — no markitdown, no MLX, no sqlite. Lets the
    endpoint + injection wiring be tested without the [studio] extra."""

    def __init__(self, *, hits=None):
        self._docs = {}
        self._hits = hits or []

    def ingest(self, doc_bytes, filename):
        from agency_studio.rag import DocMeta
        import uuid as _uuid
        meta = DocMeta(id=_uuid.uuid4().hex, filename=filename,
                       title=f"Title of {filename}", n_chunks=3, created=123.0)
        self._docs[meta.id] = meta
        self.last_bytes = doc_bytes
        return meta

    def list_docs(self):
        return list(self._docs.values())

    def delete(self, doc_id):
        return self._docs.pop(doc_id, None) is not None

    def retrieve(self, query, *, k=5):
        return self._hits


def _use_fake_retriever(monkeypatch, fake):
    monkeypatch.setattr(server.StudioHandler, "_retriever", lambda self: fake)


def test_ingest_document_then_list(monkeypatch, tmp_path):
    _use_fake_retriever(monkeypatch, _FakeRetriever())
    httpd, host, port = _start(tmp_path)
    try:
        resp, body = _post(host, port, "/api/docs?filename=report.pdf", body=b"raw pdf bytes")
        assert resp.status == 201
        meta = json.loads(body)
        assert meta["filename"] == "report.pdf" and meta["n_chunks"] == 3
        resp, body = _get(host, port, "/api/docs")
        docs = json.loads(body)["docs"]
        assert len(docs) == 1 and docs[0]["id"] == meta["id"]
    finally:
        httpd.shutdown()


def test_ingest_dot_filename_does_not_crash(monkeypatch, tmp_path):
    # filename '.' reduces to an empty basename; without the 'upload' fallback the upload
    # path would be the temp DIR and open() would raise IsADirectoryError out of the handler
    # (dropped connection + leaked temp dir). The fallback makes it a normal ingest.
    _use_fake_retriever(monkeypatch, _FakeRetriever())
    httpd, host, port = _start(tmp_path)
    try:
        resp, body = _post(host, port, "/api/docs?filename=.", body=b"some content")
        assert resp.status == 201
        assert json.loads(body)["filename"] == "upload"
    finally:
        httpd.shutdown()


def test_list_docs_empty(monkeypatch, tmp_path):
    _use_fake_retriever(monkeypatch, _FakeRetriever())
    httpd, host, port = _start(tmp_path)
    try:
        resp, body = _get(host, port, "/api/docs")
        assert resp.status == 200 and json.loads(body) == {"docs": []}
    finally:
        httpd.shutdown()


def test_ingest_empty_body_is_400(monkeypatch, tmp_path):
    _use_fake_retriever(monkeypatch, _FakeRetriever())
    httpd, host, port = _start(tmp_path)
    try:
        resp, _ = _post(host, port, "/api/docs?filename=x.txt", body=b"")
        assert resp.status == 400
    finally:
        httpd.shutdown()


def test_delete_document_is_idempotent(monkeypatch, tmp_path):
    _use_fake_retriever(monkeypatch, _FakeRetriever())
    httpd, host, port = _start(tmp_path)
    try:
        _, body = _post(host, port, "/api/docs?filename=a.md", body=b"# H\ntext")
        doc_id = json.loads(body)["id"]
        resp, body = _delete(host, port, f"/api/docs/{doc_id}")
        assert resp.status == 200 and json.loads(body)["deleted"] == doc_id
        assert json.loads(_get(host, port, "/api/docs")[1])["docs"] == []
        resp, _ = _delete(host, port, f"/api/docs/{doc_id}")  # already gone
        assert resp.status == 404
    finally:
        httpd.shutdown()


def test_ingest_without_studio_extra_returns_501(tmp_path):
    # No stub: the REAL retriever runs, markitdown is absent offline → MediaUnavailable → 501.
    httpd, host, port = _start(tmp_path)
    try:
        resp, body = _post(host, port, "/api/docs?filename=r.pdf", body=b"%PDF-1.7 bytes")
        assert resp.status == 501
        assert "studio" in body.decode().lower()
    finally:
        httpd.shutdown()


def test_models_status_includes_embed_models(tmp_path):
    httpd, host, port = _start(tmp_path)
    try:
        resp, body = _get(host, port, "/api/models")
        payload = json.loads(body)
        ids = [m["id"] for m in payload["embed_models"]]
        assert "nomic-text-v1.5" in ids
        default = next(m for m in payload["embed_models"] if m["default"])
        assert default["id"] == "nomic-text-v1.5"
    finally:
        httpd.shutdown()


def test_mission_injects_retrieved_context_and_emits_phase(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_studio.rag import Chunk
    from agency_cli import runner_bridge
    fake = _FakeRetriever(hits=[Chunk("d1", 0, "Solar", "panels convert sunlight", score=0.9)])
    fake.ingest(b"seed", "solar.md")   # one doc present → retrieval runs
    _use_fake_retriever(monkeypatch, fake)

    captured = {}

    def _fake_run(goal, project_root, engine, on_event=None, should_cancel=None,
                  asset_clause=None, render_assets=None, context_clause=None):
        captured["context_clause"] = context_clause
        on_event({"phase": "route", "status": "done", "route": []})
        return runner_bridge.MissionResult(path=tmp_path, dossier={"verdicts": [], "mission_id": "id"})

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=json.dumps({"goal": "solar plan"}),
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    retrieval = [e for e in events if e.get("phase") == "retrieval"]
    assert any(e["status"] == "done" and e["hits"] == 1 for e in retrieval)
    assert captured["context_clause"] is not None
    assert "REFERENCE DOCUMENTS" in captured["context_clause"]


def test_mission_without_docs_injects_no_context(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_cli import runner_bridge
    _use_fake_retriever(monkeypatch, _FakeRetriever())  # no docs ingested

    captured = {}

    def _fake_run(goal, project_root, engine, on_event=None, should_cancel=None,
                  asset_clause=None, render_assets=None, context_clause=None):
        captured["context_clause"] = context_clause
        on_event({"phase": "route", "status": "done", "route": []})
        return runner_bridge.MissionResult(path=tmp_path, dossier={"verdicts": [], "mission_id": "id"})

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=json.dumps({"goal": "x"}),
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    assert captured["context_clause"] is None
    assert not [e for e in events if e.get("phase") == "retrieval"]


# ── Wave 5 — web search: opt-in web context injection ───────────────────────────

def _capture_run(monkeypatch, captured):
    """Stub runner_bridge.run to record the context_clause and emit a minimal timeline."""
    from agency_cli import runner_bridge

    def _fake_run(goal, project_root, engine, on_event=None, should_cancel=None,
                  asset_clause=None, render_assets=None, context_clause=None):
        captured["context_clause"] = context_clause
        on_event({"phase": "route", "status": "done", "route": []})
        return runner_bridge.MissionResult(path=None, dossier={"verdicts": [], "mission_id": "id"})

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)


def _stub_web_search(monkeypatch, results):
    from agency_studio import websearch
    monkeypatch.setattr(websearch, "web_search", lambda goal, k=5: results)


def test_mission_with_web_flag_injects_web_context_and_emits_phase(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_studio.websearch import WebResult
    _use_fake_retriever(monkeypatch, _FakeRetriever())  # no docs → RAG contributes nothing
    _stub_web_search(monkeypatch, [WebResult("Solar 101", "https://a.example", "sun to power")])
    captured = {}
    _capture_run(monkeypatch, captured)

    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission",
                     body=json.dumps({"goal": "solar plan", "web_search": True}),
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    web = [e for e in events if e.get("phase") == "websearch"]
    assert any(e["status"] == "done" and e["hits"] == 1 for e in web)
    assert captured["context_clause"] is not None
    assert "WEB SEARCH RESULTS" in captured["context_clause"]


def test_mission_without_web_flag_does_no_web_search(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    _use_fake_retriever(monkeypatch, _FakeRetriever())

    called = {"n": 0}

    def _boom(goal, k=5):
        called["n"] += 1
        raise AssertionError("web_search must not run when the flag is absent")

    from agency_studio import websearch
    monkeypatch.setattr(websearch, "web_search", _boom)
    captured = {}
    _capture_run(monkeypatch, captured)

    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=json.dumps({"goal": "x"}),  # no web_search
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    assert called["n"] == 0
    assert captured["context_clause"] is None
    assert not [e for e in events if e.get("phase") == "websearch"]


def test_mission_composes_rag_then_web_context(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_studio.rag import Chunk
    from agency_studio.websearch import WebResult
    fake = _FakeRetriever(hits=[Chunk("d1", 0, "Solar", "panels convert sunlight", score=0.9)])
    fake.ingest(b"seed", "solar.md")   # one doc → RAG contributes a block
    _use_fake_retriever(monkeypatch, fake)
    _stub_web_search(monkeypatch, [WebResult("Fresh", "https://n.example", "latest figures")])
    captured = {}
    _capture_run(monkeypatch, captured)

    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission",
                     body=json.dumps({"goal": "solar plan", "web_search": True}),
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    clause = captured["context_clause"]
    assert "REFERENCE DOCUMENTS" in clause and "WEB SEARCH RESULTS" in clause
    # User docs (RAG) first, fresh web after — the compose order.
    assert clause.index("REFERENCE DOCUMENTS") < clause.index("WEB SEARCH RESULTS")


# ── Wave 5 — MCP: opt-in resource context injection + GET /api/mcp ──────────────

def _stub_mcp_resources(monkeypatch, items):
    from agency_studio import mcp_client
    monkeypatch.setattr(mcp_client, "read_resources", lambda goal, k=5: items)


def test_mission_with_mcp_flag_injects_mcp_context_and_emits_phase(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_studio.mcp_client import McpResource
    _use_fake_retriever(monkeypatch, _FakeRetriever())  # no docs
    _stub_mcp_resources(monkeypatch, [McpResource("wiki", "u://1", "Onboarding", "hire steps")])
    captured = {}
    _capture_run(monkeypatch, captured)

    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission",
                     body=json.dumps({"goal": "hiring plan", "mcp": True}),
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    mcp = [e for e in events if e.get("phase") == "mcp"]
    assert any(e["status"] == "done" and e["hits"] == 1 for e in mcp)
    assert "MCP RESOURCES" in captured["context_clause"]


def test_mission_without_mcp_flag_does_no_mcp(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    _use_fake_retriever(monkeypatch, _FakeRetriever())

    called = {"n": 0}

    def _boom(goal, k=5):
        called["n"] += 1
        raise AssertionError("MCP must not run when the flag is absent")

    from agency_studio import mcp_client
    monkeypatch.setattr(mcp_client, "read_resources", _boom)
    captured = {}
    _capture_run(monkeypatch, captured)

    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=json.dumps({"goal": "x"}),
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    assert called["n"] == 0
    assert not [e for e in events if e.get("phase") == "mcp"]


def test_mission_composes_rag_web_then_mcp(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_studio.rag import Chunk
    from agency_studio.websearch import WebResult
    from agency_studio.mcp_client import McpResource
    fake = _FakeRetriever(hits=[Chunk("d1", 0, "Solar", "panels", score=0.9)])
    fake.ingest(b"seed", "solar.md")
    _use_fake_retriever(monkeypatch, fake)
    _stub_web_search(monkeypatch, [WebResult("Fresh", "https://n.example", "latest")])
    _stub_mcp_resources(monkeypatch, [McpResource("wiki", "u://1", "Wiki", "note")])
    captured = {}
    _capture_run(monkeypatch, captured)

    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission",
                     body=json.dumps({"goal": "plan", "web_search": True, "mcp": True}),
                     headers={"Content-Type": "application/json"})
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    clause = captured["context_clause"]
    # RAG → web → MCP, in that order.
    assert clause.index("REFERENCE DOCUMENTS") < clause.index("WEB SEARCH RESULTS") < clause.index("MCP RESOURCES")


def test_get_mcp_lists_configured_servers(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_studio import mcp_client
    monkeypatch.setattr(mcp_client, "list_servers", lambda: [
        {"name": "wiki", "transport": "stdio", "enabled": True,
         "command": "run", "args": [], "url": None},
    ])
    httpd, host, port = _start(tmp_path)
    try:
        resp, body = _get(host, port, "/api/mcp")
        assert resp.status == 200
        payload = json.loads(body)
        assert payload["servers"][0]["name"] == "wiki"
    finally:
        httpd.shutdown()


def test_get_mcp_malformed_config_is_400(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_studio import mcp_client

    def _boom():
        raise ValueError("unreadable mcp.json")

    monkeypatch.setattr(mcp_client, "list_servers", _boom)
    httpd, host, port = _start(tmp_path)
    try:
        resp, _body = _get(host, port, "/api/mcp")
        assert resp.status == 400
    finally:
        httpd.shutdown()
