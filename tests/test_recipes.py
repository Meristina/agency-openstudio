import http.client
import json
import threading
from pathlib import Path

from agency_cli import runner_bridge
from agency_studio import server
from agency_studio.recipes.registry import RECIPES, serialize_recipe


def _start(project_root):
    httpd = server.make_server(host="127.0.0.1", port=0, project_root=str(project_root), static_root=project_root)
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


def test_registry_has_composed_and_production_recipes():
    assert {"full-campaign", "client-pitch", "turnkey-event", "social-content-pack"} <= set(RECIPES)
    assert len([r for r in RECIPES.values() if r.kind == "production"]) == 13
    assert serialize_recipe(RECIPES["full-campaign"])["stages"][0]["kind"] == "mission"


def test_full_campaign_produces_video_and_attaches_it(monkeypatch, tmp_path):
    # The real done-when: one run yields a dossier AND a locally-composed video attached to it.
    # Boundaries monkeypatched (runner_bridge.run, the Remotion render) — no CLI, no Node, no GPU.
    from agency_kit import store
    from agency_studio import openmontage_backend as omb

    def fake_run(**kwargs):
        mid = store.new_mission_id("launch coffee")
        dossier = {
            "mission_id": mid, "goal": "launch coffee",
            "project_root": store.canonical_project_root(str(tmp_path)),
            "route": ["marketing"], "delivered": "# Strategy\n\nLaunch it.",
            "assets": [], "verdicts": [{"verdict": "PASS"}],
        }
        path = store.save(dossier)
        kwargs["on_event"]({"phase": "route", "status": "done", "route": ["marketing"]})
        return runner_bridge.MissionResult(path=path, dossier=dossier)

    def fake_render(prompt, out_path, should_cancel=None):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"\x00\x00\x00\x18ftypmp42")  # a stand-in mp4

    monkeypatch.setattr(runner_bridge, "run", fake_run)
    monkeypatch.setattr(omb, "render_composition", fake_render)

    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        body = json.dumps({"recipe_id": "full-campaign", "subject": "launch coffee"})
        conn.request("POST", "/api/recipe", body=body, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        events = _read_sse(resp)
        assert resp.status == 200
        # A real compose asset frame (status ok, a video), not a fabricated one.
        compose = [e for e in events if e.get("stage") == "compose" and e.get("phase") == "asset"]
        assert compose and compose[0]["status"] == "ok"
        # The done frame carries the dossier with the video attached.
        done = events[-1]
        assert done["phase"] == "done"
        assert any(a.get("type") == "video" and a.get("status") == "ok" for a in done["assets"])
    finally:
        httpd.shutdown()


def test_recipe_run_rejects_nested_secret(tmp_path):
    # Keys are env-only: a secret smuggled inside the nested `inputs` container must be rejected
    # too, not just top-level fields (CodeRabbit finding).
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        body = json.dumps({"recipe_id": "full-campaign", "inputs": {"subject": "x", "api_key": "sk-leak"}})
        conn.request("POST", "/api/recipe", body=body, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        assert resp.status == 400
        assert b"environment variables" in resp.read()
    finally:
        httpd.shutdown()


def test_production_recipe_tier_derived_from_manifest():
    # C1: a pipeline whose manifest declares a paid budget is a cloud (opt-in) stage; a
    # zero/absent-budget pipeline stays local. Regression guard for the indented-field bug.
    assert RECIPES["cinematic"].stages[0].tier == "cloud"
    assert RECIPES["talking-head"].stages[0].tier == "cloud"
    assert RECIPES["framework-smoke"].stages[0].tier == "local"


def test_production_recipe_requires_cloud_optin(tmp_path):
    # A cloud-tier production recipe launched without opting in is refused up front — never a
    # silent paid run (FR-008).
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        body = json.dumps({"recipe_id": "cinematic", "subject": "a teaser"})
        conn.request("POST", "/api/recipe", body=body, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        assert resp.status == 501
        assert b"cloud opt-in" in resp.read()
    finally:
        httpd.shutdown()


def test_production_recipe_does_not_fabricate(monkeypatch, tmp_path):
    # Principle III: with the OpenMontage runner unwired, a production run must fail honestly
    # (error frame) rather than fabricate a PASS verdict / "completed" dossier.
    from agency_studio.recipes import om_bridge

    monkeypatch.setattr(om_bridge.shutil, "which", lambda b: "/usr/local/bin/" + b)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        body = json.dumps({"recipe_id": "cinematic", "subject": "a teaser", "cloud_optins": ["pipeline"]})
        conn.request("POST", "/api/recipe", body=body, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        events = _read_sse(resp)
        assert resp.status == 200
        assert events[-1]["phase"] == "error"
        assert "not available" in events[-1]["message"]
    finally:
        httpd.shutdown()


def test_second_run_blocked_while_active(tmp_path):
    # Single active run (FR-020): a launch while a run is registered is refused with 409.
    httpd, host, port = _start(tmp_path)
    try:
        httpd.runs["active-1"] = {"cancel": threading.Event(), "explicit": threading.Event()}
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/recipe", body=json.dumps({"recipe_id": "full-campaign", "subject": "x"}),
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        assert resp.status == 409
        assert json.loads(resp.read())["run_id"] == "active-1"
    finally:
        httpd.shutdown()


def test_cancel_recipe_run(tmp_path):
    # Cancel reuses the mission run registry: unknown → 404, active → 202 with the events set
    # (the orchestrator/mission poll them and kill the whole tree).
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/recipe/nope/cancel", body="", headers={"Content-Length": "0"})
        assert conn.getresponse().status == 404

        cancel, explicit = threading.Event(), threading.Event()
        httpd.runs["run-9"] = {"cancel": cancel, "explicit": explicit}
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/recipe/run-9/cancel", body="", headers={"Content-Length": "0"})
        assert conn.getresponse().status == 202
        assert cancel.is_set() and explicit.is_set()
    finally:
        httpd.shutdown()


def test_recipe_catalog_endpoint_returns_keys(tmp_path):
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("GET", "/api/recipes")
        resp = conn.getresponse()
        data = json.loads(resp.read())
        assert resp.status == 200
        assert len(data["recipes"]) == 17
        assert data["recipes"][0]["name_key"].startswith("recipes.")
    finally:
        httpd.shutdown()


def test_recipe_run_rejects_missing_subject(tmp_path):
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/recipe", body=json.dumps({"recipe_id": "full-campaign"}), headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        assert resp.status == 400
        assert b"subject" in resp.read()
    finally:
        httpd.shutdown()


def test_full_campaign_streams_done(monkeypatch, tmp_path):
    def fake_run(**kwargs):
        kwargs["on_event"]({"phase": "route", "status": "done", "route": ["marketing"]})
        return runner_bridge.MissionResult(
            path=Path(tmp_path),
            dossier={"mission_id": "m1", "verdicts": [{"verdict": "PASS"}], "assets": [{"status": "ok", "type": "image"}]},
        )

    monkeypatch.setattr(runner_bridge, "run", fake_run)
    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        body = json.dumps({"recipe_id": "full-campaign", "subject": "launch coffee"})
        conn.request("POST", "/api/recipe", body=body, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        events = _read_sse(resp)
        assert resp.status == 200
        assert events[0]["phase"] == "run"
        assert any(e.get("stage") == "compose" for e in events)
        assert events[-1]["phase"] == "done"
        assert events[-1]["mission_id"] == "m1"
    finally:
        httpd.shutdown()
