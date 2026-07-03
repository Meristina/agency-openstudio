"""Offline contract tests for the CLI engine registry and subprocess boundary.

The subprocess/kill-tree tests spawn real fake-binary processes (no network, no real
engine CLI, no Node), so they encode POSIX process-group semantics and are skipped on
Windows; the registry/refusal logic tests are platform-agnostic and always run."""

import os
import sys
import textwrap
import time

import pytest

from agency_cli.engines import cli_engine

# Applied to tests that spawn real subprocesses / rely on POSIX process groups.
requires_posix = pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX process-group / exec semantics"
)


def _write_executable(path, body):
    text = textwrap.dedent(body).lstrip()
    # Run the fakes under the SAME interpreter as the test process, not whatever
    # `python3` happens to resolve to on PATH (it may be absent on a container/CI image).
    if text.startswith("#!/usr/bin/env python3"):
        text = f"#!{sys.executable}" + text[len("#!/usr/bin/env python3"):]
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture
def fake_binary(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))

    def _make(name, body):
        return _write_executable(bin_dir / name, body)

    return _make


def _wait_until_gone(pid, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        except PermissionError:
            return  # pid recycled to a process we don't own → our target is gone
        time.sleep(0.02)
    pytest.fail(f"process {pid} is still alive")


def _read_pids(path):
    for _ in range(100):
        if path.exists():
            values = [int(x) for x in path.read_text(encoding="utf-8").split()]
            if len(values) == 2:
                return values
        time.sleep(0.02)
    pytest.fail(f"pid file {path} was not written")


# A fake engine that spawns a child, records both pids, then blocks — for kill-tree tests.
_TREE_ENGINE_BODY = """
    #!/usr/bin/env python3
    import os
    import subprocess
    import sys
    import time
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    with open(os.environ["FAKE_PID_FILE"], "w", encoding="utf-8") as f:
        f.write(f"{os.getpid()} {child.pid}")
        f.flush()
    time.sleep(30)
    """


@pytest.fixture
def tree_engine(fake_binary, tmp_path, monkeypatch):
    """Install the kill-tree fake binary + fast cancel/terminate timing, and return a
    factory ``(name) -> (name, pid_file)``. The caller triggers the kill (cancel or
    timeout); pass the resulting pid_file to ``_assert_tree_dead``."""
    monkeypatch.setattr(cli_engine, "_CANCEL_POLL_SECONDS", 0.02)
    monkeypatch.setattr(cli_engine, "_TERMINATE_GRACE", 0.5)
    pid_file = tmp_path / "tree-pids.txt"
    monkeypatch.setenv("FAKE_PID_FILE", str(pid_file))

    def _make(name):
        fake_binary(name, _TREE_ENGINE_BODY)
        return name, pid_file

    return _make


def _assert_tree_dead(pid_file):
    parent_pid, child_pid = _read_pids(pid_file)
    _wait_until_gone(parent_pid)
    _wait_until_gone(child_pid)


def test_engine_views_match_specs_and_register_engine_refreshes_views(monkeypatch):
    assert set(cli_engine.ENGINES) == set(cli_engine.ENGINE_SPECS)
    assert set(cli_engine._ROUTE_CMD) == set(cli_engine.ENGINE_SPECS)
    for name, spec in cli_engine.ENGINE_SPECS.items():
        assert cli_engine.ENGINES[name] == list(spec.run_cmd)
        assert cli_engine._ROUTE_CMD[name] == list(spec.route_cmd)

    original_specs = dict(cli_engine.ENGINE_SPECS)
    monkeypatch.setattr(cli_engine, "ENGINE_SPECS", dict(original_specs))
    cli_engine._refresh_engine_views()

    try:
        spec = cli_engine.EngineSpec(
            name="test-engine",
            run_cmd=("test-runner", "--run"),
            route_cmd=("test-router", "--route"),
            web_search_headless=True,
            validated=True,
        )
        cli_engine.register_engine(spec)

        assert cli_engine.ENGINE_SPECS["test-engine"] == spec
        assert cli_engine.ENGINES["test-engine"] == ["test-runner", "--run"]
        assert cli_engine._ROUTE_CMD["test-engine"] == ["test-router", "--route"]
    finally:
        cli_engine.ENGINE_SPECS.clear()
        cli_engine.ENGINE_SPECS.update(original_specs)
        cli_engine._refresh_engine_views()


@requires_posix
def test_fake_binary_fixture_executes_from_temp_path(fake_binary):
    fake_binary(
        "echo-engine",
        """
        #!/usr/bin/env python3
        import sys
        print("ARGS:" + "|".join(sys.argv[1:]))
        """,
    )

    assert cli_engine._call(["echo-engine", "--mode"], "hello") == "ARGS:--mode|hello"


@requires_posix
def test_call_run_and_route_commands_return_stdout_for_each_spec(fake_binary):
    # Write a fake for BOTH the run and route binaries of each spec (they coincide for the
    # built-ins, but a future engine may split them — don't rely on the coincidence).
    for spec in cli_engine.ENGINE_SPECS.values():
        for binary in {spec.run_cmd[0], spec.route_cmd[0]}:
            fake_binary(
                binary,
                """
                #!/usr/bin/env python3
                import sys
                print(sys.argv[-1])
                """,
            )

    for spec in cli_engine.ENGINE_SPECS.values():
        assert cli_engine._call(list(spec.run_cmd), f"run:{spec.name}") == f"run:{spec.name}"
        assert cli_engine._call(list(spec.route_cmd), f"route:{spec.name}") == f"route:{spec.name}"


@requires_posix
def test_call_missing_binary_and_timeout_paths(fake_binary, monkeypatch):
    with pytest.raises(RuntimeError, match="not found on PATH"):
        cli_engine._call(["definitely-absent-engine"], "hello")

    monkeypatch.setattr(cli_engine, "_CANCEL_POLL_SECONDS", 0.02)
    monkeypatch.setattr(cli_engine, "_TERMINATE_GRACE", 0.5)
    fake_binary(
        "sleep-engine",
        """
        #!/usr/bin/env python3
        import time
        time.sleep(5)
        print("late")
        """,
    )

    with pytest.raises(RuntimeError, match=r"timed out after 0\.3s"):
        cli_engine._call(["sleep-engine"], "hello", timeout=0.3)


@requires_posix
def test_call_cancel_kills_parent_and_child(tree_engine):
    name, pid_file = tree_engine("cancel-tree-engine")

    def should_cancel():
        return pid_file.exists() and len(pid_file.read_text(encoding="utf-8").split()) == 2

    with pytest.raises(cli_engine.MissionCancelled):
        cli_engine._call([name], "hello", should_cancel=should_cancel)

    _assert_tree_dead(pid_file)


@requires_posix
def test_call_timeout_kills_parent_and_child(tree_engine):
    name, pid_file = tree_engine("timeout-tree-engine")

    with pytest.raises(RuntimeError, match=r"timed out after 0\.3s"):
        cli_engine._call([name], "hello", timeout=0.3)

    _assert_tree_dead(pid_file)


@pytest.mark.parametrize("engine", ["codex", "gemini"])
def test_run_mission_refuses_unvalidated_engines_before_subprocess(monkeypatch, engine):
    monkeypatch.setattr(cli_engine, "_call", lambda *a, **k: pytest.fail("must not invoke CLI"))

    with pytest.raises(cli_engine.EngineNotValidated) as exc:
        cli_engine.run_mission_cli("goal", engine=engine)

    message = str(exc.value)
    assert engine in message
    assert "NOT validated" in message
    assert "claude-code" in message


def test_run_mission_validated_engine_proceeds_past_guards(monkeypatch):
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: f"/fake/{b}")
    calls = {"n": 0}

    def fake_call(cmd, prompt, timeout=900, should_cancel=None):
        calls["n"] += 1
        if "json array" in prompt.lower():
            return '["product"]'
        if "issue a verdict" in prompt.lower():
            return "VERDICT: PASS"
        return "OUTPUT"

    monkeypatch.setattr(cli_engine, "_call", fake_call)

    dossier = cli_engine.run_mission_cli("goal", engine="claude-code")

    assert calls["n"] >= 3
    assert dossier["verdicts"][-1]["verdict"] == "PASS"


def test_validated_specs_declare_headless_web_search():
    assert all(
        spec.web_search_headless
        for spec in cli_engine.ENGINE_SPECS.values()
        if spec.validated
    )


def test_engine_spec_rejects_validated_without_headless_web_search():
    # The invariant is enforced at construction (fail fast at registration), so an
    # inconsistent spec cannot even be built through the public API — the primary defence.
    with pytest.raises(ValueError, match="headless web search"):
        cli_engine.EngineSpec(
            name="broken",
            run_cmd=("broken",),
            route_cmd=("broken",),
            web_search_headless=False,
            validated=True,
        )


def test_run_mission_web_search_guard_is_defense_in_depth(monkeypatch):
    # Guard 3 (validated but no headless web search → refuse) is defence in depth: the
    # EngineSpec invariant makes this state unconstructible through the public API, so we
    # corrupt a valid frozen spec via object.__setattr__ to prove the runtime guard STILL
    # fires if a bad spec ever reaches the registry (a future bug, a hand-built object).
    # run_mission_cli reads ENGINE_SPECS directly, so setitem alone is enough.
    spec = cli_engine.EngineSpec(
        name="broken",
        run_cmd=("broken",),
        route_cmd=("broken",),
        web_search_headless=True,
        validated=True,
    )
    object.__setattr__(spec, "web_search_headless", False)  # bypass frozen + __post_init__
    monkeypatch.setitem(cli_engine.ENGINE_SPECS, "broken", spec)
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: pytest.fail("must not check binary"))
    monkeypatch.setattr(cli_engine, "_call", lambda *a, **k: pytest.fail("must not invoke CLI"))

    with pytest.raises(cli_engine.EngineNotValidated) as exc:
        cli_engine.run_mission_cli("goal", engine="broken")

    message = str(exc.value)
    assert "broken" in message
    assert "web_search_headless" in message
    assert "headless web search" in message


@requires_posix
def test_registered_validated_fake_engine_runs_full_mission(fake_binary, monkeypatch):
    original_specs = dict(cli_engine.ENGINE_SPECS)
    monkeypatch.setattr(cli_engine, "ENGINE_SPECS", dict(original_specs))
    cli_engine._refresh_engine_views()

    fake_binary(
        "fake-engine-cli",
        """
        #!/usr/bin/env python3
        import sys
        prompt = sys.argv[-1]
        low = prompt.lower()
        if "json array" in low:
            print('["product"]')
        elif "issue a verdict" in low:
            print("VERDICT: PASS\\nChecked https://example.com/source")
        else:
            print("Deliverable for fake engine. Source: https://example.com/source")
        """,
    )
    spec = cli_engine.EngineSpec(
        name="fake-engine",
        run_cmd=("fake-engine-cli", "--run"),
        route_cmd=("fake-engine-cli", "--route"),
        web_search_headless=True,
        validated=True,
    )
    try:
        cli_engine.register_engine(spec)

        dossier = cli_engine.run_mission_cli("prove the extension contract", engine="fake-engine")

        assert "fake-engine" in cli_engine.ENGINES
        assert dossier["route"] == ["product"]
        assert set(dossier["dept_outputs"]) == {"product"}
        assert dossier["delivered"]
        assert dossier["verdicts"][-1]["engine"] == "fake-engine"
        assert dossier["verdicts"][-1]["verdict"] == "PASS"
        assert dossier["sources"] == ["https://example.com/source"]
    finally:
        cli_engine.ENGINE_SPECS.clear()
        cli_engine.ENGINE_SPECS.update(original_specs)
        cli_engine._refresh_engine_views()
