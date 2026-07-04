import http.client
import json
import threading

from agency_studio import server


def _start(project_root):
    httpd = server.make_server(host="127.0.0.1", port=0, project_root=str(project_root))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    return httpd, host, port


def _read_sse(resp):
    events = []
    for raw in resp:
        line = raw.decode("utf-8").strip()
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:"):].strip()))
    return events


def test_verify_frames_pass_through_sse(monkeypatch, tmp_path):
    from agency_cli import runner_bridge

    def _fake_run(goal, project_root, engine, on_event=None, **kwargs):
        on_event({"phase": "verify", "iteration": 1, "status": "start"})
        on_event({"phase": "verify", "iteration": 1, "status": "done", "ok": True, "rate": None, "checked": 2})
        return runner_bridge.MissionResult(path=tmp_path, dossier={"verdicts": [], "mission_id": "m"})

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request(
            "POST",
            "/api/mission",
            body=json.dumps({"goal": "g"}),
            headers={"Content-Type": "application/json"},
        )
        events = _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    assert {"phase": "verify", "iteration": 1, "status": "start"} in events
    assert {"phase": "verify", "iteration": 1, "status": "done", "ok": True, "rate": None, "checked": 2} in events


def test_mission_request_forwards_verification_default_valid_and_junk(monkeypatch, tmp_path):
    from agency_cli import runner_bridge

    captured = []

    def _fake_run(goal, project_root, engine, on_event=None, resume_state=None, verification=None, **kwargs):
        captured.append(verification)
        return runner_bridge.MissionResult(path=tmp_path, dossier={"verdicts": [], "mission_id": "m"})

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    httpd, host, port = _start(tmp_path)
    try:
        for body in (
            {"goal": "absent"},
            {"goal": "valid", "verification": {"min_sources": 5, "resolve": True}},
            {"goal": "junk", "verification": "not an object"},
            {"goal": "field junk", "verification": {"min_sources": "bad", "resolve": "yes"}},
            # bool is an int subclass: true must not silently lower the threshold to 1
            {"goal": "bool junk", "verification": {"min_sources": True, "resolve": False}},
            # min_sources=0 is the documented opt-out — preserved, not "corrected"
            {"goal": "opt-out", "verification": {"min_sources": 0, "resolve": False}},
            # negative is corrected back to the default threshold
            {"goal": "negative", "verification": {"min_sources": -2, "resolve": True}},
            # json.loads parses Infinity → float('inf'); int() would raise OverflowError
            {"goal": "infinity", "verification": {"min_sources": float("inf"), "resolve": False}},
        ):
            conn = http.client.HTTPConnection(host, port)
            conn.request("POST", "/api/mission", body=json.dumps(body), headers={"Content-Type": "application/json"})
            _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    assert captured == [
        {"min_sources": 3, "resolve": False},
        {"min_sources": 5, "resolve": True},
        {"min_sources": 3, "resolve": False},
        {"min_sources": 3, "resolve": False},
        {"min_sources": 3, "resolve": False},
        {"min_sources": 0, "resolve": False},
        {"min_sources": 3, "resolve": True},
        {"min_sources": 3, "resolve": False},
    ]


def test_resume_checkpoint_verification_wins_over_body(monkeypatch, tmp_path):
    from agency_cli import runner_bridge

    cid = "a" * 32
    server._write_checkpoint(tmp_path / ".agency-studio", {
        "id": cid,
        "created": "now",
        "goal": "g",
        "engine": "claude-code",
        "flags": {"verification": {"min_sources": 7, "resolve": True}},
        "state": {"route": ["marketing"], "dept_outputs": {}, "verdicts": [], "iteration": 0, "delivered": ""},
    })
    captured = []

    def _fake_run(goal, project_root, engine, on_event=None, resume_state=None, verification=None, **kwargs):
        captured.append(verification)
        return runner_bridge.MissionResult(path=tmp_path, dossier={"verdicts": [], "mission_id": "m"})

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request(
            "POST",
            "/api/mission",
            body=json.dumps({"resume_from": cid, "verification": {"min_sources": 1, "resolve": False}}),
            headers={"Content-Type": "application/json"},
        )
        _read_sse(conn.getresponse())
    finally:
        httpd.shutdown()

    assert captured == [{"min_sources": 7, "resolve": True}]
