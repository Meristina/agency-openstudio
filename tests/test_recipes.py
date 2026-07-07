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


def test_recipe_resume_from_failed_compose(monkeypatch, tmp_path):
    # Per-stage resume (T043/T039): a run that fails at a POST-mission stage (compose) offers a
    # checkpoint; resuming replays the completed mission (the veto-gated mission does NOT re-run) and
    # restarts at the failed stage. The expensive stage's minutes/tokens are never re-spent.
    from agency_kit import store
    from agency_studio import openmontage_backend as omb

    store_dir = tmp_path / ".store"
    store_dir.mkdir()
    monkeypatch.setattr(store, "missions_dir", lambda: store_dir)

    mission_calls = []

    def fake_run(**kwargs):
        mission_calls.append(1)
        mid = store.new_mission_id("launch coffee")
        dossier = {
            "mission_id": mid, "goal": "launch coffee",
            "project_root": store.canonical_project_root(str(tmp_path)),
            "route": ["marketing"], "delivered": "# Strategy\n\nLaunch it.",
            "assets": [], "verdicts": [{"verdict": "PASS"}],
        }
        store.save(dossier)
        return runner_bridge.MissionResult(path=store_dir / mid / "dossier.json", dossier=dossier)

    compose_calls = []

    def flaky_render(prompt, out_path, should_cancel=None):
        compose_calls.append(1)
        if len(compose_calls) == 1:
            raise RuntimeError("compose boom")  # fatal on the first attempt
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"\x00\x00\x00\x18ftypmp42")

    monkeypatch.setattr(runner_bridge, "run", fake_run)
    monkeypatch.setattr(omb, "render_composition", flaky_render)

    httpd, host, port = _start(tmp_path)
    try:
        # First run: mission succeeds, compose fails → an error frame naming a resumable checkpoint.
        events = _read_sse(_post_recipe(host, port, recipe_id="full-campaign", subject="launch coffee"))
        err = events[-1]
        assert err["phase"] == "error" and err["resumable"]
        cid = err["checkpoint"]
        assert cid and len(mission_calls) == 1

        # Resume: mission is replayed (not re-run), compose is retried → the run completes.
        events2 = _read_sse(_post_recipe(host, port, recipe_id="full-campaign",
                                         subject="launch coffee", resume_from=cid))
        assert events2[-1]["phase"] == "done"
        assert len(mission_calls) == 1   # the veto-gated mission did NOT re-run
        assert len(compose_calls) == 2   # compose was retried
        # The replayed mission stage is marked as such on the resume stream.
        assert any(e.get("stage") == "mission" and e.get("replayed") for e in events2)
    finally:
        httpd.shutdown()


def test_recipe_checkpoint_not_leaked_into_mission_paths(tmp_path):
    # CodeRabbit (Major): recipe checkpoints share the checkpoints dir + id namespace with missions,
    # so the mission listing/resume MUST skip them (they carry no mission goal/flags). A recipe
    # checkpoint never surfaces as a mission checkpoint nor drives a mission run.
    from agency_studio.recipes import checkpoint

    docs_root = tmp_path / ".agency-studio"
    cid = "reciperun1"
    checkpoint.write(docs_root, checkpoint.envelope(
        run_id=cid, recipe_id="full-campaign", subject="x", cloud_optins=[],
        completed_stages=["mission"], outputs={"mission": {"mission_id": "m1"}}))
    assert checkpoint.load(docs_root, cid) is not None  # it IS a valid recipe checkpoint

    httpd, host, port = _start(tmp_path)
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("GET", "/api/checkpoints")
        listed = json.loads(conn.getresponse().read())["checkpoints"]
        assert all(c.get("id") != cid for c in listed)  # not listed as a mission checkpoint
        # Never resumed as a mission (would rebuild a mission with no goal/flags): any non-200.
        conn = http.client.HTTPConnection(host, port)
        conn.request("POST", "/api/mission", body=json.dumps({"resume_from": cid, "goal": ""}),
                     headers={"Content-Type": "application/json"})
        assert conn.getresponse().status != 200
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


def _post_recipe(host, port, **body):
    conn = http.client.HTTPConnection(host, port)
    conn.request("POST", "/api/recipe", body=json.dumps(body),
                 headers={"Content-Type": "application/json"})
    return conn.getresponse()


def test_production_recipe_501_when_runtime_absent(monkeypatch, tmp_path):
    # An absent OpenMontage runtime (no Node) degrades to an honest error frame + install hint —
    # never a fabricated dossier (Principle III). The probe fires the moment the pipeline stage runs.
    from agency_studio.recipes import om_bridge

    monkeypatch.setattr(om_bridge.shutil, "which", lambda b: None)  # nothing on PATH
    httpd, host, port = _start(tmp_path)
    try:
        resp = _post_recipe(host, port, recipe_id="cinematic", subject="a teaser",
                            cloud_optins=["pipeline"])
        events = _read_sse(resp)
        assert resp.status == 200
        assert events[-1]["phase"] == "error"
        assert "Node.js" in events[-1]["message"]
    finally:
        httpd.shutdown()


def test_production_pipeline_produces_and_records_deliverable(monkeypatch, tmp_path):
    # The real done-when for a production recipe: one run drives the pipeline's executive-producer
    # skill over the subprocess boundary, produces a video, and lands a lightweight deliverable
    # record retrievable via the library/export path (FR-018). The one impure surface — the CLI-agent
    # spawn — is monkeypatched (no CLI, no Node), everything else is real.
    from agency_kit import store
    from agency_studio.recipes import om_bridge

    store_dir = tmp_path / ".store"
    store_dir.mkdir()
    monkeypatch.setattr(store, "missions_dir", lambda: store_dir)  # isolate from ~/.agency
    monkeypatch.setattr(om_bridge.shutil, "which", lambda b: "/usr/local/bin/" + b)

    def fake_spawn(cmd, cwd, timeout, should_cancel=None):
        work = Path(cmd[cmd.index("--add-dir") + 1])  # the renderer-fixed writable dir
        work.mkdir(parents=True, exist_ok=True)
        art = work / "final.mp4"
        art.write_bytes(b"\x00\x00\x00\x18ftypmp42")  # a stand-in mp4
        return f"OM_ARTIFACT={art}\n"

    monkeypatch.setattr(om_bridge, "_spawn_agent", fake_spawn)

    httpd, host, port = _start(tmp_path)
    try:
        resp = _post_recipe(host, port, recipe_id="cinematic", subject="a teaser",
                            cloud_optins=["pipeline"])
        events = _read_sse(resp)
        assert resp.status == 200
        # A real pipeline asset frame (a produced video, not a fabricated one).
        assets = [e for e in events if e.get("stage") == "pipeline" and e.get("phase") == "asset"]
        assert assets and assets[0]["status"] == "ok"
        done = events[-1]
        assert done["phase"] == "done"
        assert any(a.get("type") == "video" and a.get("status") == "ok" for a in done["assets"])
        # The lightweight deliverable record is persisted and retrievable (FR-018).
        recorded = store.load(done["mission_id"])
        assert recorded["pipeline"] == "cinematic"
        assert recorded["kind"] == "production"
        assert recorded["assets"][0]["type"] == "video"
    finally:
        httpd.shutdown()


def test_production_pipeline_honest_failure_no_record(monkeypatch, tmp_path):
    # Principle III: when the agent cannot produce a video it prints OM_ERROR — the run reports an
    # honest error frame and writes NO deliverable record (nothing fabricated).
    from agency_kit import store
    from agency_studio.recipes import om_bridge

    store_dir = tmp_path / ".store"
    monkeypatch.setattr(store, "missions_dir", lambda: store_dir)
    monkeypatch.setattr(om_bridge.shutil, "which", lambda b: "/usr/local/bin/" + b)
    monkeypatch.setattr(om_bridge, "_spawn_agent",
                        lambda cmd, cwd, timeout, should_cancel=None: "OM_ERROR=no local footage\n")

    httpd, host, port = _start(tmp_path)
    try:
        resp = _post_recipe(host, port, recipe_id="cinematic", subject="a teaser",
                            cloud_optins=["pipeline"])
        events = _read_sse(resp)
        assert resp.status == 200
        assert events[-1]["phase"] == "error"
        assert "no local footage" in events[-1]["message"]
        assert not store_dir.exists() or not list(store_dir.glob("*/dossier.json"))
    finally:
        httpd.shutdown()


def test_om_bridge_rejects_artifact_outside_work_dir(monkeypatch, tmp_path):
    # Security: the agent's OM_ARTIFACT must live inside the renderer-fixed work dir. A path that
    # escapes it (an attempt to pull an arbitrary local file into the deliverable) is rejected.
    from agency_studio.recipes import om_bridge

    monkeypatch.setattr(om_bridge.shutil, "which", lambda b: "/usr/local/bin/" + b)
    outside = tmp_path / "secret.mp4"
    outside.write_bytes(b"x")
    monkeypatch.setattr(om_bridge, "_spawn_agent",
                        lambda cmd, cwd, timeout, should_cancel=None: f"OM_ARTIFACT={outside}\n")
    work = tmp_path / "work"
    out = tmp_path / "out.mp4"
    import pytest
    with pytest.raises(RuntimeError, match="outside its work dir"):
        om_bridge.run_pipeline("cinematic", "a teaser", work_dir=work, out_path=out,
                               should_cancel=lambda: False)


def test_om_bridge_fallback_ignores_symlink_escape(tmp_path):
    # Security (CodeRabbit): the no-sentinel fallback must not follow a `*.mp4` symlink out of the
    # work dir — `.is_file()` follows links, so a link to an outside file could otherwise be moved
    # into the deliverable. Such a work dir yields an honest "no video" failure, not the escape.
    from agency_studio.recipes import om_bridge
    import pytest

    work = tmp_path / "work"
    work.mkdir()
    outside = tmp_path / "real.mp4"
    outside.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    try:
        (work / "link.mp4").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not creatable on this platform/privilege level")
    with pytest.raises(RuntimeError, match="without producing a video"):
        om_bridge._resolve_artifact("", work)


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
