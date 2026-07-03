import json
from pathlib import Path

import pytest

from agency_cli import escalation


PAYLOAD = Path(__file__).resolve().parents[1] / "agency_cli" / "payload" / "agents"


def _recorder(outputs):
    calls = []
    queue = list(outputs)

    def call(cmd, prompt, timeout=900, should_cancel=None):
        calls.append((cmd, prompt))
        if should_cancel and should_cancel():
            from agency_cli.engines.cli_engine import MissionCancelled
            raise MissionCancelled()
        item = queue.pop(0)
        if isinstance(item, BaseException):
            raise item  # a queued exception simulates a failing CLI call
        return item

    return call, calls


def test_frontmatter_parser_and_roster_builds_real_and_virtual_officers():
    roster = escalation.build_roster(PAYLOAD)

    assert roster.commanders["marketing"].name == "commander-marketing"
    assert [r.name for r in roster.officers["marketing"]][:2] == [
        "officer-1-research",
        "officer-2-strategy",
    ]
    assert any(r.name == "comms/o6-events" and r.virtual for r in roster.virtual_officers["comms"])
    assert len(roster.soldiers) >= 100
    assert all(len(r.summary) <= 200 for r in roster.soldiers[:5])


def test_dept_officers_resolve_to_payload_files():
    names = {p.stem for p in PAYLOAD.glob("*.md")}
    for commander in escalation.DEPT_COMMANDERS.values():
        assert commander in names
    for officers in escalation.DEPT_OFFICERS.values():
        for officer in officers:
            assert officer in names


def test_run_department_happy_path_trace_and_assembly():
    roster = escalation.build_roster(PAYLOAD)
    call, calls = _recorder([
        json.dumps({"officers": ["officer-2-strategy"], "soldiers": ["soldier-stp"], "rationale": {"soldier-stp": "STP fits"}}),
        "COMMANDER OUT",
        "OFFICER OUT",
        "SOLDIER OUT",
    ])
    events = []

    output, trace = escalation.run_department(
        "marketing",
        "position a B2B analytics product",
        {},
        config=escalation.EscalationConfig(budget=6),
        roster=roster,
        call=call,
        base_cmd=["base"],
        exec_cmd=["exec"],
        run_timeout=9,
        on_event=events.append,
    )

    assert [i["role"] for i in trace["invocations"]] == ["selection", "commander", "officer", "soldier"]
    assert [i["name"] for i in trace["invocations"]][2:] == ["officer-2-strategy", "soldier-stp"]
    assert trace["selection"]["rationale"]["officer-2-strategy"] == "(no rationale returned)"
    assert trace["consumed"] == 4
    assert trace["est_tokens"] == sum(i["est_tokens"] for i in trace["invocations"])
    assert "COMMANDER OUT" in output and "Officer: officer-2-strategy" in output and "SOLDIER OUT" in output
    # the commander brief must appear exactly once — a second copy means the
    # commander invocation record leaked into the assembly or the prompts
    assert output.count("COMMANDER OUT") == 1
    officer_prompt, soldier_prompt = calls[2][1], calls[3][1]
    assert officer_prompt.count("COMMANDER OUT") == 1
    assert soldier_prompt.count("COMMANDER OUT") == 1
    assert len(calls) == 4
    assert [(e["step"], e["name"], e["status"]) for e in events] == [
        ("selection", "commander-marketing-selection", "start"),
        ("selection", "commander-marketing-selection", "done"),
        ("commander", "commander-marketing", "start"),
        ("commander", "commander-marketing", "done"),
        ("officer", "officer-2-strategy", "start"),
        ("officer", "officer-2-strategy", "done"),
        ("soldier", "soldier-stp", "start"),
        ("soldier", "soldier-stp", "done"),
    ]


def test_empty_selection_records_doctrine_fallback():
    roster = escalation.build_roster(PAYLOAD)
    call, calls = _recorder([
        json.dumps({"officers": [], "soldiers": [], "rationale": {}}),
        "FALLBACK OUT",
    ])

    output, trace = escalation.run_department(
        "marketing", "quick sanity", {}, config=escalation.EscalationConfig(),
        roster=roster, call=call, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
    )

    assert output == "FALLBACK OUT"
    assert trace["finalized_by"] == "doctrine-fallback"
    assert trace["fallback_reason"] == "router-selected-none"
    assert [c[0] for c in calls] == [["base"], ["exec"]]


def test_budget_exhaustion_records_skips_and_keeps_output():
    roster = escalation.build_roster(PAYLOAD)
    call, _ = _recorder([
        json.dumps({"officers": ["officer-2-strategy", "officer-3-brand"], "soldiers": ["soldier-stp", "soldier-positioning"], "rationale": {}}),
        "COMMANDER OUT",
        "OFFICER OUT",
    ])

    output, trace = escalation.run_department(
        "marketing", "launch", {}, config=escalation.EscalationConfig(budget=3),
        roster=roster, call=call, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
    )

    assert trace["consumed"] == 3
    assert trace["consumed"] <= trace["budget"]
    assert [i.get("skipped") for i in trace["invocations"] if i.get("skipped")] == [
        "budget-exhausted",
        "budget-exhausted",
        "budget-exhausted",
    ]
    assert "COMMANDER OUT" in output and "OFFICER OUT" in output


def test_fallback_call_failure_degrades_instead_of_aborting():
    # T043: the doctrine-fallback call must degrade like every specialist call — a
    # failing CLI there (e.g. a session limit) must not abort the whole mission (FR-007)
    from agency_cli.engines.cli_engine import MissionCancelled
    roster = escalation.build_roster(PAYLOAD)
    call, calls = _recorder([
        json.dumps({"officers": [], "soldiers": [], "rationale": {}}),  # router selects nothing
        RuntimeError("CLI engine 'claude' exited 1: session limit"),     # fallback call fails
    ])

    output, trace = escalation.run_department(
        "marketing", "quick sanity", {}, config=escalation.EscalationConfig(),
        roster=roster, call=call, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
        cancelled=MissionCancelled,
    )

    assert output == ""  # degraded to the (empty) prior, no exception raised
    assert trace["finalized_by"] == "doctrine-fallback"
    assert trace["fallback_reason"] == "router-selected-none+fallback-call-failed"
    assert len(calls) == 2


def test_all_specialists_failed_marks_doctrine_fallback_not_escalation():
    # T043: when the commander runs but every selected specialist fails, the dept is
    # NOT a real escalation — it must fall back to a full-doctrine deliverable and be
    # labelled doctrine-fallback, not silently reported as finalized_by=escalation
    from agency_cli.engines.cli_engine import MissionCancelled
    roster = escalation.build_roster(PAYLOAD)
    call, _ = _recorder([
        json.dumps({"officers": ["officer-2-strategy"], "soldiers": ["soldier-stp"], "rationale": {}}),
        "COMMANDER OUT",
        RuntimeError("CLI exited 1"),   # officer-2-strategy fails
        RuntimeError("CLI exited 1"),   # soldier-stp fails
        "DOCTRINE FALLBACK OUT",        # the doctrine fallback succeeds
    ])

    output, trace = escalation.run_department(
        "marketing", "launch", {}, config=escalation.EscalationConfig(),
        roster=roster, call=call, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
        cancelled=MissionCancelled,
    )

    assert output == "DOCTRINE FALLBACK OUT"
    assert trace["finalized_by"] == "doctrine-fallback"
    assert trace["fallback_reason"] == "all-specialists-failed"
    call_failed = [i for i in trace["invocations"] if i.get("skipped") == "call-failed"]
    assert {i["name"] for i in call_failed} == {"officer-2-strategy", "soldier-stp"}


def test_null_officers_in_selection_does_not_crash():
    # LLMs sometimes emit null instead of [] for an array field; a present-but-null
    # key defeats dict.get(key, []) and must not abort the mission (FR-007)
    roster = escalation.build_roster(PAYLOAD)
    call, _ = _recorder([
        json.dumps({"officers": None, "soldiers": ["soldier-stp"], "rationale": None}),
        "COMMANDER OUT",
        "SOLDIER OUT",
    ])

    output, trace = escalation.run_department(
        "marketing", "launch", {}, config=escalation.EscalationConfig(),
        roster=roster, call=call, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
    )

    assert trace["selection"]["officers"] == []
    assert trace["selection"]["soldiers"] == ["soldier-stp"]
    assert "SOLDIER OUT" in output


def test_unparseable_selection_falls_back_explicitly():
    roster = escalation.build_roster(PAYLOAD)
    call, _ = _recorder(["not json", "FALLBACK OUT"])

    output, trace = escalation.run_department(
        "marketing", "launch", {}, config=escalation.EscalationConfig(),
        roster=roster, call=call, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
    )

    assert output == "FALLBACK OUT"
    assert trace["selection"] == {"fallback": "selection-unparseable"}
    assert trace["fallback_reason"] == "selection-unparseable"


def test_selection_can_differ_by_goal_and_records_rationale():
    roster = escalation.build_roster(PAYLOAD)

    call_a, _ = _recorder([
        json.dumps({"officers": ["officer-2-strategy"], "soldiers": ["soldier-stp"], "rationale": {"officer-2-strategy": "positioning goal"}}),
        "COMMANDER A",
        "OFFICER A",
        "SOLDIER A",
    ])
    _, trace_a = escalation.run_department(
        "marketing", "position the product", {}, config=escalation.EscalationConfig(),
        roster=roster, call=call_a, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
    )

    call_b, _ = _recorder([
        json.dumps({"officers": ["officer-4-demand"], "soldiers": ["soldier-content-seo"], "rationale": {"officer-4-demand": "demand goal"}}),
        "COMMANDER B",
        "OFFICER B",
        "SOLDIER B",
    ])
    _, trace_b = escalation.run_department(
        "marketing", "build demand", {}, config=escalation.EscalationConfig(),
        roster=roster, call=call_b, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
    )

    assert trace_a["selection"]["officers"] != trace_b["selection"]["officers"]
    assert trace_a["selection"]["rationale"]["officer-2-strategy"] == "positioning goal"
    assert trace_b["selection"]["rationale"]["officer-4-demand"] == "demand goal"


def test_missing_specialist_file_is_recorded(tmp_path):
    agent_dir = tmp_path / "agents"
    agent_dir.mkdir()
    for name in ("commander-marketing.md", "officer-2-strategy.md", "soldier-stp.md"):
        (agent_dir / name).write_text((PAYLOAD / name).read_text(encoding="utf-8"), encoding="utf-8")
    roster = escalation.build_roster(agent_dir)
    (agent_dir / "soldier-stp.md").unlink()
    call, _ = _recorder([
        json.dumps({"officers": ["officer-2-strategy"], "soldiers": ["soldier-stp"], "rationale": {}}),
        "COMMANDER OUT",
        "OFFICER OUT",
    ])

    _, trace = escalation.run_department(
        "marketing", "launch", {}, config=escalation.EscalationConfig(),
        roster=roster, call=call, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
    )

    assert any(i["role"] == "soldier" and i["name"] == "soldier-stp" and i.get("skipped") == "missing-file" for i in trace["invocations"])


def test_comms_virtual_officer_invoked_and_traced():
    roster = escalation.build_roster(PAYLOAD)
    call, _ = _recorder([
        json.dumps({"officers": ["comms/o6-events"], "soldiers": [], "rationale": {"comms/o6-events": "event goal"}}),
        "COMMANDER OUT",
        "VIRTUAL OUT",
    ])

    _, trace = escalation.run_department(
        "comms", "plan a product launch event", {}, config=escalation.EscalationConfig(),
        roster=roster, call=call, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
    )

    officer = [i for i in trace["invocations"] if i["role"] == "officer"][0]
    assert officer["name"] == "comms/o6-events"
    assert officer["virtual"] is True
    assert "O6 Events" in officer["task"]


def test_cancel_between_specialists_propagates():
    from agency_cli.engines.cli_engine import MissionCancelled

    roster = escalation.build_roster(PAYLOAD)
    call, _ = _recorder([
        json.dumps({"officers": ["officer-2-strategy"], "soldiers": ["soldier-stp"], "rationale": {}}),
        "COMMANDER OUT",
    ])
    checks = {"n": 0}

    def should_cancel():
        checks["n"] += 1
        return checks["n"] > 2

    with pytest.raises(MissionCancelled):
        escalation.run_department(
            "marketing", "launch", {}, config=escalation.EscalationConfig(),
            roster=roster, call=call, base_cmd=["base"], exec_cmd=["exec"], run_timeout=9,
            should_cancel=should_cancel, cancelled=MissionCancelled,
        )
