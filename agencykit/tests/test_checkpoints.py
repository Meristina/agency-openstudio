"""Crash-recovery checkpoint store (agency_cli.checkpoints) — fully offline."""

import pytest

from agency_cli import checkpoints
from agency_kit import store


@pytest.fixture
def home(tmp_path, monkeypatch):
    # Redirect ~/.agency to a temp dir so checkpoints write under the sandbox.
    monkeypatch.setattr(store, "agency_dir", lambda: tmp_path)
    return tmp_path


def _snapshot():
    # A valid "dept" checkpoint: all routed departments done, no inspection cycle yet —
    # the shape a mission killed mid-synthesis leaves behind.
    return {
        "version": 1, "phase": "dept", "goal": "g", "engine": "claude-code",
        "route": ["solve", "product"], "dept_outputs": {"solve": "s", "product": "p"},
        "delivered": "", "verdicts": [], "iteration": 0, "fixes": None,
    }


def test_round_trip_write_read_clear(home):
    g, e, p = "diagnose churn", "claude-code", str(home)
    assert checkpoints.read(g, e, p) is None
    checkpoints.write(g, e, p, _snapshot())
    assert checkpoints.read(g, e, p) == _snapshot()
    checkpoints.clear(g, e, p)
    assert checkpoints.read(g, e, p) is None


def test_clear_is_idempotent_when_absent(home):
    checkpoints.clear("never-written", "claude-code", str(home))  # must not raise


def test_write_leaves_no_temp_file(home):
    checkpoints.write("g", "claude-code", str(home), _snapshot())
    assert list((home / "checkpoints").glob("*.tmp")) == []


def test_read_tolerates_a_corrupt_file(home):
    # A kill mid-write (or a hand-edited file) must degrade to a fresh run, never raise.
    g, e, p = "g", "claude-code", str(home)
    checkpoints.path_for(g, e, p).write_text("{ not valid json", encoding="utf-8")
    assert checkpoints.read(g, e, p) is None


def test_key_separates_goal_engine_and_project(home, tmp_path):
    base = checkpoints.path_for("goal one", "claude-code", str(home))
    assert base != checkpoints.path_for("goal two", "claude-code", str(home))
    assert base != checkpoints.path_for("goal one", "codex", str(home))
    other = tmp_path / "other"
    other.mkdir()
    assert base != checkpoints.path_for("goal one", "claude-code", str(other))


def test_describe_summarizes_progress():
    assert "2/2 departments done" in checkpoints.describe(_snapshot())
    cyc = {**_snapshot(), "iteration": 2, "verdicts": [{}, {}]}
    assert "2 inspection cycles" in checkpoints.describe(cyc)
