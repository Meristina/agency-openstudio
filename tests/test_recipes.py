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
