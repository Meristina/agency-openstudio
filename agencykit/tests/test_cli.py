"""Regression tests for the CLI layer — runner_bridge, integrations, scaffolder.

Each test documents a specific bug that was found and fixed; the test name names
the scenario so a future reader knows why the guard exists.
"""

from pathlib import Path

import pytest


# ---- runner_bridge._dossier_md ----------------------------------------------
# Bug: field list was copied from product-kit and contained "baseline"/"assumptions"
# which do not exist in the agency dossier; "route" was absent entirely.

def test_dossier_md_renders_route_field_not_baseline():
    from agency_cli.runner_bridge import _dossier_md

    dossier = {
        "goal": "launch product",
        "route": ["product", "marketing"],
        "context": None,
        "iteration": 1,
        "direction_check": None,
        "dept_outputs": {"product": "p-out", "marketing": "m-out"},
        "decisions": [],
        "sources": [],
        "open_to_verify": [],
        "verdicts": [],
    }
    md = _dossier_md("001-test", dossier)
    assert "**route**" in md, "route field missing from dossier MD"
    assert "baseline" not in md, "product-kit 'baseline' field leaked into agency dossier MD"
    assert "assumptions" not in md, "product-kit 'assumptions' section leaked into agency dossier MD"


def test_dossier_md_renders_escalation_section_only_when_present():
    from agency_cli.runner_bridge import _dossier_md

    base = {
        "goal": "launch", "route": ["marketing"], "context": None, "iteration": 1,
        "direction_check": None, "dept_outputs": {"marketing": "m-out"},
        "decisions": [], "sources": [], "open_to_verify": [], "verdicts": [],
    }
    # absent key ⇒ no section (byte-identical off, Principle X)
    assert "## Escalation" not in _dossier_md("001-test", base)

    dossier = dict(base)
    dossier["escalation"] = {
        "marketing": {
            "budget": 4, "consumed": 4, "est_tokens": 35900,
            "finalized_by": "escalation",
            "selection": {
                "officers": ["officer-2-strategy"], "soldiers": ["soldier-stp"],
                "rationale": {"soldier-stp": "STP fits"},
            },
            "invocations": [
                {"role": "officer", "name": "officer-2-strategy", "est_tokens": 15000},
                {"role": "soldier", "name": "soldier-positioning",
                 "skipped": "budget-exhausted", "est_tokens": 0},
            ],
        },
    }
    md = _dossier_md("001-test", dossier)
    assert "## Escalation" in md and "### marketing" in md
    assert "budget: 4, consumed: 4" in md
    assert "soldier-stp: STP fits" in md
    assert "SKIPPED (budget-exhausted)" in md


def test_dossier_md_lists_departments_run():
    from agency_cli.runner_bridge import _dossier_md

    dossier = {
        "goal": "build and market",
        "route": ["product", "marketing"],
        "context": None,
        "iteration": 2,
        "direction_check": None,
        "dept_outputs": {"product": "p-out", "marketing": "m-out"},
        "decisions": ["ship Q3"],
        "sources": ["internal doc"],
        "open_to_verify": [],
        "verdicts": [],
    }
    md = _dossier_md("002-test", dossier)
    assert "product" in md and "marketing" in md, "dept_outputs keys not rendered in dossier MD"


def test_serialize_dossier_retries_past_a_colliding_folder(tmp_path, monkeypatch):
    # TOCTOU guard: a real collision only happens when a concurrent mission claims
    # the NNN that _next_id() just computed. Simulate it by pinning _next_id to "001"
    # for the first (colliding) attempt, then "002" — the retry loop must recover.
    from agency_cli import runner_bridge
    from agency_kit.store import slug as _slug

    goal = "diagnose the outage"
    missions = tmp_path / "missions"
    missions.mkdir()
    (missions / f"001-{_slug(goal, max_words=6)}").mkdir()  # already claimed

    ids = iter(["001", "002"])
    monkeypatch.setattr(runner_bridge, "_next_id", lambda _m: next(ids))

    out = runner_bridge.serialize_dossier({"goal": goal, "delivered": "fix"}, tmp_path)

    assert out.name.startswith("002-")  # recovered onto the next free id
    assert (out / "dossier.md").is_file()
    assert (out / "deliverable.md").is_file()


def test_cancelled_mission_persists_nothing(tmp_path, monkeypatch):
    # No-persist invariant: when the engine raises MissionCancelled, _run_and_persist
    # must propagate it WITHOUT calling store.save or writing a missions/<id>/ folder.
    from agency_cli import runner_bridge
    from agency_cli.engines.cli_engine import MissionCancelled

    def _raise(*a, **k):
        raise MissionCancelled()

    saved = {"n": 0}
    monkeypatch.setattr("agency_cli.engines.cli_engine.run_mission_cli", _raise)
    monkeypatch.setattr("agency_kit.store.save", lambda *a, **k: saved.__setitem__("n", saved["n"] + 1))

    with pytest.raises(MissionCancelled):
        runner_bridge.run("diagnose the outage", project_root=str(tmp_path))

    assert saved["n"] == 0, "store.save must never run for a cancelled mission"
    assert not (tmp_path / "missions").exists(), "no mission folder may be written on cancel"


# ---- runner_bridge multimodal hook (Wave 3 D2 — render_assets / asset_clause) ----
# The Studio threads `asset_clause` into the engine and a best-effort `render_assets`
# callback that runs AFTER the engine returns but BEFORE persistence, gated strictly
# on a clean Inspector PASS, and never destructive. Default None ⇒ unchanged.

def _stub_mission(monkeypatch, *, verdict="PASS", delivered="HERO ASSET", residual=False):
    """Stub run_mission_cli to return a fixed dossier and store.save to a no-op.
    new_mission_id / canonical_project_root run real (pure). Returns a `captured`
    dict recording the asset_clause the bridge forwarded to the engine. The dossier
    is a fresh SHALLOW copy per call — safe because these tests only mutate top-level
    keys (a test that mutated a nested list would need a deepcopy)."""
    base = {
        "goal": "launch a brand",
        "route": ["marketing"],
        "context": None,
        "dept_outputs": {"marketing": "m-out"},
        "decisions": [], "sources": [], "open_to_verify": [],
        "direction_check": None,
        "verdicts": [{"engine": "claude-code", "verdict": verdict, "iteration": 1}],
        "iteration": 1,
        "delivered": delivered,
    }
    if residual:
        base["residual_risk"] = "did not PASS"

    captured = {"asset_clause": "<unset>", "context_clause": "<unset>",
                "mcp_config_path": "<unset>", "mcp_allowed_tools": "<unset>",
                "persona_doctrine": "<unset>",
                "on_checkpoint": "<unset>", "resume_state": "<unset>",
                "escalation": "<unset>"}

    def _fake_run(goal, engine="claude-code", on_event=None, should_cancel=None,
                  asset_clause=None, context_clause=None,
                  mcp_config_path=None, mcp_allowed_tools=None,
                  persona_doctrine=None, on_checkpoint=None, resume_state=None,
                  escalation=None):
        captured["asset_clause"] = asset_clause
        captured["context_clause"] = context_clause
        captured["mcp_config_path"] = mcp_config_path
        captured["mcp_allowed_tools"] = mcp_allowed_tools
        captured["persona_doctrine"] = persona_doctrine
        captured["on_checkpoint"] = on_checkpoint
        captured["resume_state"] = resume_state
        captured["escalation"] = escalation
        return dict(base)  # a fresh copy per call

    monkeypatch.setattr("agency_cli.engines.cli_engine.run_mission_cli", _fake_run)
    monkeypatch.setattr("agency_kit.store.save", lambda *a, **k: None)
    return captured


def test_render_assets_runs_on_pass_and_manifest_is_persisted(tmp_path, monkeypatch):
    from agency_cli import runner_bridge
    _stub_mission(monkeypatch, verdict="PASS", delivered="HERO ASSET here")

    seen = {}

    def _render(dossier):
        # mission_id must already be set so the renderer can scope its output dir.
        seen["mission_id"] = dossier.get("mission_id")
        dossier["assets"] = [{
            "type": "image", "status": "ok",
            "url": "/media/missions/x/images/a.png", "model": "flux-schnell", "seconds": 3,
        }]
        dossier["delivered"] = dossier["delivered"].replace("ASSET", "![a](/media/missions/x/images/a.png)")

    res = runner_bridge.run("launch a brand", project_root=str(tmp_path), render_assets=_render)

    assert seen.get("mission_id"), "render_assets must see a mission_id already stamped"
    assert res.dossier.get("assets"), "manifest must be attached to the returned dossier"
    md = (res.path / "dossier.md").read_text(encoding="utf-8")
    assert "## Assets" in md and "/media/missions/x/images/a.png" in md
    # The cosmetic rewrite happened before serialization → the persisted deliverable carries it.
    deliv = (res.path / "deliverable.md").read_text(encoding="utf-8")
    assert "![a](/media/missions/x/images/a.png)" in deliv


def test_render_assets_skipped_when_not_pass(tmp_path, monkeypatch):
    # A VETO at the cap still returns a populated `delivered` (+ residual_risk), but the
    # strict == 'PASS' gate must NOT render — and the deliverable is still persisted.
    from agency_cli import runner_bridge
    _stub_mission(monkeypatch, verdict="VETO", residual=True)

    calls = []
    res = runner_bridge.run(
        "launch a brand", project_root=str(tmp_path),
        render_assets=lambda d: calls.append(1),
    )
    assert calls == [], "render_assets must not run on a non-PASS verdict"
    assert "assets" not in res.dossier
    assert (res.path / "deliverable.md").is_file(), "deliverable persists even when assets are skipped"


def test_render_assets_pass_with_fixes_is_not_a_pass(tmp_path, monkeypatch):
    # Exact-token gate: PASS-WITH-FIXES is not a clean PASS → no render.
    from agency_cli import runner_bridge
    _stub_mission(monkeypatch, verdict="PASS-WITH-FIXES")
    calls = []
    runner_bridge.run(
        "launch a brand", project_root=str(tmp_path),
        render_assets=lambda d: calls.append(1),
    )
    assert calls == [], "PASS-WITH-FIXES must not trigger asset rendering"


@pytest.mark.parametrize("exc", [
    ImportError("media extra not installed"),    # MediaUnavailable ⊂ ImportError ([media] absent)
    RuntimeError("metal command buffer crashed"),  # a backend/Metal crash mid-render
])
def test_render_assets_failure_never_discards_the_deliverable(tmp_path, monkeypatch, exc):
    # Best-effort: ANY render exception is swallowed by the broad `except Exception`, so
    # the already-inspected PASS deliverable is still persisted, UNMODIFIED and without a
    # manifest. Covering both ImportError and RuntimeError pins the broad catch — a future
    # narrowing to `except ImportError` would make the RuntimeError case fail loudly.
    from agency_cli import runner_bridge
    _stub_mission(monkeypatch, verdict="PASS", delivered="HERO ASSET here")

    def _boom(dossier):
        raise exc

    res = runner_bridge.run("launch a brand", project_root=str(tmp_path), render_assets=_boom)

    assert "assets" not in res.dossier
    assert (res.path / "dossier.md").is_file()
    deliv = (res.path / "deliverable.md").read_text(encoding="utf-8")
    assert "HERO ASSET here" in deliv, "the deliverable must survive a render failure unmutated"


def test_asset_clause_is_threaded_to_the_engine(tmp_path, monkeypatch):
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path), asset_clause="ASSET CLAUSE")
    assert captured["asset_clause"] == "ASSET CLAUSE"


def test_default_run_forwards_no_clause_and_renders_nothing(tmp_path, monkeypatch):
    # Standalone path: no hook supplied ⇒ asset_clause stays None, no asset section.
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    res = runner_bridge.run("launch a brand", project_root=str(tmp_path))
    assert captured["asset_clause"] is None
    assert "assets" not in res.dossier
    assert "## Assets" not in (res.path / "dossier.md").read_text(encoding="utf-8")


def test_context_clause_is_threaded_to_the_engine(tmp_path, monkeypatch):
    # Wave 4 D2: the RAG context_clause reaches run_mission_cli through the bridge.
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path), context_clause="CTX")
    assert captured["context_clause"] == "CTX"


def test_default_run_forwards_no_context_clause(tmp_path, monkeypatch):
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path))
    assert captured["context_clause"] is None


def test_escalation_defaults_on_and_opt_outs_are_resolved(tmp_path, monkeypatch):
    from agency_cli import runner_bridge
    from agency_cli.escalation import EscalationConfig

    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path))
    assert captured["escalation"] == EscalationConfig()

    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path), escalation=False)
    assert captured["escalation"] is None

    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path), escalation={"budget": 0})
    assert captured["escalation"] is None


def test_escalation_dict_is_type_checked(tmp_path, monkeypatch):
    from agency_cli import runner_bridge

    _stub_mission(monkeypatch, verdict="PASS")
    with pytest.raises(ValueError):
        runner_bridge.run("launch", project_root=str(tmp_path), escalation={"enabled": "yes"})


def test_mcp_tool_hook_is_threaded_to_the_engine(tmp_path, monkeypatch):
    # Wave 6: the MCP tool-calling hook reaches run_mission_cli through the bridge.
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path),
                      mcp_config_path="/tmp/mcp.json", mcp_allowed_tools=["mcp__wiki"])
    assert captured["mcp_config_path"] == "/tmp/mcp.json"
    assert captured["mcp_allowed_tools"] == ["mcp__wiki"]


def test_default_run_forwards_no_mcp_tool_hook(tmp_path, monkeypatch):
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path))
    assert captured["mcp_config_path"] is None
    assert captured["mcp_allowed_tools"] is None


def test_persona_hook_is_threaded_to_the_engine(tmp_path, monkeypatch):
    # Wave 6: the persona-doctrine hook reaches run_mission_cli through the bridge.
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path),
                      persona_doctrine={"marketing": "You are a razor-focused growth marketer."})
    assert captured["persona_doctrine"] == {"marketing": "You are a razor-focused growth marketer."}


def test_default_run_forwards_no_persona_hook(tmp_path, monkeypatch):
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path))
    assert captured["persona_doctrine"] is None


def test_resume_forwards_the_multimodal_hook(tmp_path, monkeypatch):
    # resume() regenerates assets under its fresh mission id exactly like a first run.
    from agency_cli import runner_bridge
    _stub_mission(monkeypatch, verdict="PASS")
    monkeypatch.setattr("agency_kit.store.load", lambda mid: {"goal": "launch a brand"})

    calls = []

    def _render(dossier):
        calls.append(1)
        dossier["assets"] = [{"type": "tts", "status": "ok"}]

    res = runner_bridge.resume("001-old", project_root=str(tmp_path), render_assets=_render)
    assert calls == [1], "resume must forward render_assets to _run_and_persist"
    assert res.dossier.get("assets")


def test_resume_forwards_the_persona_hook(tmp_path, monkeypatch):
    # resume() threads persona_doctrine through _run_and_persist → run_mission_cli, like run().
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    monkeypatch.setattr("agency_kit.store.load", lambda mid: {"goal": "launch a brand"})
    runner_bridge.resume("001-old", project_root=str(tmp_path),
                         persona_doctrine={"commander": "You are a decisive agency chief."})
    assert captured["persona_doctrine"] == {"commander": "You are a decisive agency chief."}


def test_checkpoint_and_resume_state_threaded_through_run(tmp_path, monkeypatch):
    # The crash-recovery hooks reach run_mission_cli through run().
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    cb = lambda snap: None
    state = {"route": ["marketing"], "dept_outputs": {}, "verdicts": [], "iteration": 0, "delivered": ""}
    runner_bridge.run("launch a brand", project_root=str(tmp_path),
                      on_checkpoint=cb, resume_state=state)
    assert captured["on_checkpoint"] is cb
    assert captured["resume_state"] == state


def test_default_run_forwards_no_checkpoint_or_resume_state(tmp_path, monkeypatch):
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    runner_bridge.run("launch a brand", project_root=str(tmp_path))
    assert captured["on_checkpoint"] is None
    assert captured["resume_state"] is None


def test_resume_forwards_on_checkpoint_but_never_resume_state(tmp_path, monkeypatch):
    # resume(mission_id) re-runs from scratch — it forwards on_checkpoint but never a resume_state
    # (a mission-id re-run and a checkpoint-continue are mutually exclusive operations).
    from agency_cli import runner_bridge
    captured = _stub_mission(monkeypatch, verdict="PASS")
    monkeypatch.setattr("agency_kit.store.load", lambda mid: {"goal": "launch a brand"})
    cb = lambda snap: None
    runner_bridge.resume("001-old", project_root=str(tmp_path), on_checkpoint=cb)
    assert captured["on_checkpoint"] is cb
    assert captured["resume_state"] is None


def test_cli_verification_flags_forward_to_runner_bridge(monkeypatch, tmp_path):
    from agency_cli import cli

    captured = []
    result = type("R", (), {"path": tmp_path, "dossier": {"verdicts": [], "mission_id": "m"}})()

    def _run(goal, **kwargs):
        captured.append(("run", kwargs.get("verification")))
        return result

    def _resume(mid, **kwargs):
        captured.append(("resume", kwargs.get("verification")))
        return result

    monkeypatch.setattr("agency_cli.runner_bridge.run", _run)
    monkeypatch.setattr("agency_cli.runner_bridge.resume", _resume)

    assert cli.main(["run", "goal"]) == 0
    assert cli.main(["run", "goal", "--min-sources", "0"]) == 0
    assert cli.main(["run", "goal", "--min-sources", "0", "--resolve-sources"]) == 0
    assert cli.main(["resume", "m1", "--min-sources", "5", "--resolve-sources"]) == 0

    # The opt-out is forwarded EXPLICITLY as min_sources=0 — never as None, which
    # runner_bridge._resolve_verification would resolve back to the default config
    # and silently re-enable the gate the operator just disabled.
    assert captured == [
        ("run", {"min_sources": 3, "resolve": False}),
        ("run", {"min_sources": 0, "resolve": False}),
        ("run", {"min_sources": 0, "resolve": True}),
        ("resume", {"min_sources": 5, "resolve": True}),
    ]


def test_cli_min_sources_negative_is_argparse_error():
    from agency_cli import cli
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["run", "goal", "--min-sources", "-1"])


def test_dossier_md_assets_section_only_when_present():
    from agency_cli.runner_bridge import _dossier_md
    base = {
        "goal": "g", "route": ["marketing"], "context": None, "iteration": 1,
        "direction_check": None, "dept_outputs": {"marketing": "m"},
        "decisions": [], "sources": [], "open_to_verify": [], "verdicts": [],
    }
    md_absent = _dossier_md("001", base)
    assert "## Assets" not in md_absent
    # None / [] render nothing → byte-identical to the absent case (non-studio runs).
    assert _dossier_md("001", {**base, "assets": None}) == md_absent
    assert _dossier_md("001", {**base, "assets": []}) == md_absent
    # Present → a readable line per manifest entry.
    md = _dossier_md("001", {**base, "assets": [
        {"type": "tts", "status": "ok", "url": "/media/a.wav", "seconds": 2},
        {"type": "image", "status": "failed", "reason": "metal crash"},
    ]})
    assert "## Assets" in md
    assert "tts [ok] /media/a.wav (2s)" in md
    assert "image [failed] metal crash" in md


# ---- integrations._install_claude -------------------------------------------
# Bug: sources["skills"].iterdir() called unconditionally; agency-kit has no
# skills/ directory, so `agency init --agent claude` raised FileNotFoundError.

def test_install_claude_without_skills_dir_does_not_crash(tmp_path):
    from agency_cli.integrations import _install_claude

    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    (commands_dir / "mission.md").write_text(
        "---\ndescription: run a mission\n---\n\n$ARGUMENTS\n", encoding="utf-8"
    )
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    sources = {
        "commands": commands_dir,
        "agents": agents_dir,
        "skills": tmp_path / "skills",  # intentionally absent
    }
    target = tmp_path / "target"
    target.mkdir()

    result = _install_claude(sources, target)
    assert result["skills"] == 0, "skills count should be 0 when skills/ dir is absent"
    assert result["commands"] == 1


def test_install_claude_with_skills_dir_copies_them(tmp_path):
    from agency_cli.integrations import _install_claude

    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    skills_dir = tmp_path / "skills"
    (skills_dir / "my-skill").mkdir(parents=True)
    (skills_dir / "my-skill" / "SKILL.md").write_text("# My Skill\n", encoding="utf-8")

    sources = {"commands": commands_dir, "agents": agents_dir, "skills": skills_dir}
    target = tmp_path / "target"
    target.mkdir()

    result = _install_claude(sources, target)
    assert result["skills"] == 1
    assert (target / ".claude" / "skills" / "my-skill" / "SKILL.md").exists()


# ---- scaffolder.check() -----------------------------------------------------
# Engine-only health check: agency_kit importable + at least one engine on PATH.

def test_check_reports_agency_kit_importable(tmp_path):
    from agency_cli.scaffolder import check

    results = check(str(tmp_path))
    by_label = {label: ok for label, ok, _ in results}

    assert "agency_kit importable" in by_label, "health check missing 'agency_kit importable' entry"
    assert by_label["agency_kit importable"], "agency_kit core not importable"
    # The engine-availability check is always present (value depends on PATH).
    assert any("engine CLI available" in label for label in by_label), (
        "health check missing the engine-on-PATH entry"
    )


# ---- agency missions ---------------------------------------------------------
# Bug surface: _cmd_missions printed nothing when the missions dir was empty;
# no test existed to guard this code path.

def test_cmd_missions_empty(monkeypatch, capsys):
    from agency_cli.cli import _cmd_missions
    from argparse import Namespace

    monkeypatch.setattr("agency_kit.store.list_missions", lambda: [])
    rc = _cmd_missions(Namespace())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No missions" in out


def test_cmd_missions_lists_rows(monkeypatch, capsys):
    from agency_cli.cli import _cmd_missions
    from argparse import Namespace

    fake = [
        {"mission_id": "20260101-000000-test-goal", "goal": "test goal", "route": ["product"],
         "iteration": 1, "verdict": "PASS", "delivered": True},
    ]
    monkeypatch.setattr("agency_kit.store.list_missions", lambda: fake)
    rc = _cmd_missions(Namespace())
    assert rc == 0
    out = capsys.readouterr().out
    assert "test-goal" in out
    assert "PASS" in out


# ---- agency resume ----------------------------------------------------------
# Bug surface: _cmd_resume called runner_bridge.resume but the error path for a
# missing mission_id was never tested.

def test_cmd_resume_missing_mission(monkeypatch, capsys):
    from agency_cli.cli import _cmd_resume
    from argparse import Namespace

    def _raise(*a, **kw):
        raise FileNotFoundError("not found")

    monkeypatch.setattr("agency_cli.runner_bridge.resume", _raise)
    # Stub missions_path (no mkdir) so the error message is pure display with no disk side-effect.
    monkeypatch.setattr("agency_kit.store.missions_path", lambda: Path("/stub/missions"))
    rc = _cmd_resume(Namespace(mission_id="nonexistent-id", path=".", engine="claude-code"))
    assert rc == 2
    err = capsys.readouterr().err
    assert "nonexistent-id" in err


# ---- agency export ----------------------------------------------------------
# Bug surface: _cmd_export must catch BOTH error paths and yield rc==2 with an
# 'error' message — FileNotFoundError (mission/deliverable absent) and ImportError
# (WeasyPrint not installed). One parametrize over the raised exception covers both.

@pytest.mark.parametrize("exc", [
    FileNotFoundError("deliverable.md not found for mission: x"),
    ImportError('WeasyPrint not installed. Run:  pip install -e ".[pdf]"'),
])
def test_cmd_export_error_paths_return_rc2(monkeypatch, capsys, exc):
    from agency_cli import exporter
    from agency_cli.cli import _cmd_export
    from argparse import Namespace

    def _raise(mid):
        raise exc

    monkeypatch.setattr(exporter, "export_pdf", _raise)
    rc = _cmd_export(Namespace(mission_id="any-mission"))
    assert rc == 2
    assert "error" in capsys.readouterr().err.lower()


# ---- agency tui -------------------------------------------------------------
# Bug surface: _cmd_tui must catch ImportError from tui.launch() (textual absent)
# and return exit code 2. The tui module itself is importable without textual
# because all textual imports are deferred inside launch().

def test_cmd_tui_missing_textual(monkeypatch, capsys):
    from agency_cli import tui
    from agency_cli.cli import _cmd_tui
    from argparse import Namespace

    def _raise():
        raise ImportError('Textual not installed. Run:  pip install -e ".[tui]"')

    monkeypatch.setattr(tui, "launch", _raise)
    rc = _cmd_tui(Namespace())
    assert rc == 2
    assert "error" in capsys.readouterr().err.lower()


def test_cmd_tui_success(monkeypatch):
    from agency_cli import tui
    from agency_cli.cli import _cmd_tui
    from argparse import Namespace

    launched = []

    def _noop():
        launched.append(True)

    monkeypatch.setattr(tui, "launch", _noop)
    rc = _cmd_tui(Namespace())
    assert rc == 0
    assert launched


# ---- agency run forwards the engine -----------------------------------------
# Bug surface: the --engine flag must reach runner_bridge.run; a typo in the
# kwarg name would silently default the engine.

def test_cmd_run_forwards_engine(monkeypatch, tmp_path):
    from agency_cli.cli import _cmd_run
    from argparse import Namespace

    from agency_cli.runner_bridge import MissionResult

    calls = {}

    def _fake_run(goal, project_root, engine="claude-code", escalation=None):
        calls["engine"] = engine
        calls["goal"] = goal
        calls["escalation"] = escalation
        return MissionResult(path=tmp_path / "001-result", dossier={})

    monkeypatch.setattr("agency_cli.runner_bridge.run", _fake_run)
    rc = _cmd_run(Namespace(goal="ship it", path=str(tmp_path), engine="gemini", dry_run=False,
                            no_escalation=False, escalation_budget=8))
    assert rc == 0
    assert calls.get("engine") == "gemini", "--engine not forwarded to runner_bridge.run"
    assert calls["escalation"] == {"budget": 8}


# ---- agency run --dry-run ---------------------------------------------------
# Bug surface: _cmd_dry_run prints the planned keyword route without any engine call.

def test_cmd_dry_run_shows_route(capsys, monkeypatch):
    from agency_cli.cli import _cmd_run
    from argparse import Namespace

    monkeypatch.setattr("agency_kit.router.keyword_classify", lambda goal: ["product", "marketing"])

    rc = _cmd_run(Namespace(goal="launch our product", path=".", engine="claude-code", dry_run=True,
                            no_escalation=False, escalation_budget=None))
    assert rc == 0
    out = capsys.readouterr().out
    assert "product" in out
    assert "marketing" in out
    assert "dry-run" in out.lower()
    assert "no engine call" in out.lower()


# ---- agency batch -----------------------------------------------------------
# Bug surface: _cmd_batch dispatches to batch_runner functions via the batch_cmd
# attribute — verify each subcommand hits the right function and returns its code.

def test_cmd_batch_add(monkeypatch):
    from agency_cli.cli import _cmd_batch
    from argparse import Namespace
    from agency_cli import batch_runner

    calls = {}

    def _fake_add(goal, priority, notes):
        calls["goal"] = goal
        calls["priority"] = priority
        calls["notes"] = notes
        return 0

    monkeypatch.setattr(batch_runner, "add", _fake_add)
    rc = _cmd_batch(Namespace(batch_cmd="add", goal="launch widget", priority=3, notes="urgent"))
    assert rc == 0
    assert calls["goal"] == "launch widget"
    assert calls["priority"] == 3


def test_cmd_batch_status(monkeypatch):
    from agency_cli.cli import _cmd_batch
    from argparse import Namespace
    from agency_cli import batch_runner

    called = []
    monkeypatch.setattr(batch_runner, "status", lambda: called.append(True) or 0)
    rc = _cmd_batch(Namespace(batch_cmd="status"))
    assert rc == 0
    assert called


def test_cmd_batch_clear(monkeypatch):
    from agency_cli.cli import _cmd_batch
    from argparse import Namespace
    from agency_cli import batch_runner

    calls = {}
    monkeypatch.setattr(batch_runner, "clear", lambda status_filter: calls.update({"sf": status_filter}) or 0)
    rc = _cmd_batch(Namespace(batch_cmd="clear", status_filter="failed"))
    assert rc == 0
    assert calls["sf"] == "failed"


def test_cmd_batch_run_flags(monkeypatch):
    from agency_cli.cli import _cmd_batch
    from argparse import Namespace
    from agency_cli import batch_runner

    calls = {}

    def _fake_run(retry_failed, limit, engine, escalation=None):
        calls.update({"rf": retry_failed, "lim": limit, "engine": engine, "escalation": escalation})
        return 0

    monkeypatch.setattr(batch_runner, "run", _fake_run)
    rc = _cmd_batch(Namespace(batch_cmd="run", retry_failed=True, limit=5, engine="codex",
                              no_escalation=True, escalation_budget=8))
    assert rc == 0
    assert calls["rf"] is True
    assert calls["lim"] == 5
    assert calls["engine"] == "codex"
    assert calls["escalation"] is False


# ---- batch_runner file I/O --------------------------------------------------
# Unit tests for the TSV queue helpers — verify add/status/clear mutate
# the queue file correctly without touching the real ~/.agency directory.

def test_batch_runner_add_creates_queue(tmp_path, monkeypatch):
    from agency_cli import batch_runner

    monkeypatch.setattr(batch_runner, "_agency_dir", lambda: tmp_path)

    rc = batch_runner.add("first goal", priority=3, notes="note1")
    assert rc == 0
    rows = batch_runner._read_tsv(tmp_path / "batch-queue.tsv")
    assert len(rows) == 1
    assert rows[0]["goal"] == "first goal"
    assert rows[0]["priority"] == "3"
    assert rows[0]["status"] == "pending"


def test_batch_runner_add_increments_ids(tmp_path, monkeypatch):
    from agency_cli import batch_runner

    monkeypatch.setattr(batch_runner, "_agency_dir", lambda: tmp_path)

    batch_runner.add("goal A")
    batch_runner.add("goal B")
    rows = batch_runner._read_tsv(tmp_path / "batch-queue.tsv")
    ids = [int(r["id"]) for r in rows]
    assert ids == sorted(set(ids))
    assert len(set(ids)) == 2


def test_batch_runner_status_empty(tmp_path, monkeypatch, capsys):
    from agency_cli import batch_runner

    monkeypatch.setattr(batch_runner, "_agency_dir", lambda: tmp_path)

    rc = batch_runner.status()
    assert rc == 0
    assert "empty" in capsys.readouterr().out.lower()


def test_batch_runner_clear_removes_done(tmp_path, monkeypatch):
    from agency_cli import batch_runner

    monkeypatch.setattr(batch_runner, "_agency_dir", lambda: tmp_path)

    batch_runner.add("keep this")
    batch_runner.add("remove this")
    # Manually write state marking second entry as done
    rows = batch_runner._read_tsv(tmp_path / "batch-queue.tsv")
    done_id = rows[1]["id"]
    batch_runner._write_tsv(
        tmp_path / "batch-state.tsv",
        batch_runner._STATE_COLS,
        [{"id": done_id, "status": "done", "started_at": "", "finished_at": "",
          "last_verdict": "PASS", "retries": "1", "mission_id": ""}],
    )
    rc = batch_runner.clear(status_filter="done")
    assert rc == 0
    remaining = batch_runner._read_tsv(tmp_path / "batch-queue.tsv")
    goals = [r["goal"] for r in remaining]
    assert "keep this" in goals
    assert "remove this" not in goals
