"""Structural invariants for agency-kit — the engine-path spine.

After the openai-agents SDK path was removed, `agency_kit` is pure-stdlib (the
keyword router + the departments source-of-truth + the mission store) and missions
run through a local agent CLI engine. These tests confirm the remaining spine
imports cleanly, the department dependency graph holds, and the payload doctrine
mirrors have not drifted.
"""

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "agency_kit"


# ---- the Constitution doctrine is present and wired -------------------------
# Bug surface: constitution.md could be deleted/emptied, or the commander doctrine
# file could lose its article references. Check both the source file and the
# agents/ doctrine that the engine loads at runtime.

def test_constitution_present_and_articles_wired():
    constitution = ROOT / ".agency" / "memory" / "constitution.md"
    assert constitution.is_file(), "constitution.md missing at canonical path"
    text = constitution.read_text(encoding="utf-8")
    for art in ("Article IV", "Article VI", "Article IX"):
        assert art in text, f"constitution missing {art}"

    commander_doc = (ROOT / "agents" / "commander-agency.md").read_text(encoding="utf-8")
    assert "Art. IV" in commander_doc, "commander doctrine must reference Art. IV (sovereignty)"
    assert "Art. VI" in commander_doc, "commander doctrine must reference Art. VI (don't over-route)"


# ---- the spine imports cleanly (no SDK) -------------------------------------

def test_router_is_keyword_only_no_sdk():
    # Bug surface: a stray `from agents import ...` would re-introduce the SDK dep.
    from agency_kit.router import keyword_classify
    assert callable(keyword_classify)
    import agency_kit.router as r
    assert not hasattr(r, "classify"), "LLM classify() should be gone"
    assert not hasattr(r, "router_agent"), "SDK router_agent should be gone"


def test_cli_entrypoint_importable_without_sdk():
    from agency_cli.cli import main
    assert callable(main)


def test_store_exposes_persistence_api_without_sdk():
    from agency_kit.store import save, load, list_missions, new_mission_id
    assert callable(save) and callable(load)
    assert callable(list_missions) and callable(new_mission_id)


def test_engine_entrypoint_importable_without_sdk():
    # Pure import smoke test — the ENGINES/_ROUTE_CMD registry contract is owned by
    # test_engine.py::test_engines_registry_has_three_web_search_engines.
    from agency_cli.engines.cli_engine import run_mission_cli
    assert callable(run_mission_cli)


# ---- dependency graph + topological scheduler -------------------------------
# departments.py stays the canonical ordering model even though the engine runs
# departments sequentially — these pin the invariants and the wave layering.

def test_dependency_graph_covers_every_department():
    from agency_kit.departments import DEPT_NAMES, DEPT_DEPENDENCIES, VALID_DEPTS
    assert set(DEPT_DEPENDENCIES) == set(DEPT_NAMES), (
        "every department must declare its dependencies (even if empty)"
    )
    for dept, deps in DEPT_DEPENDENCIES.items():
        assert dept not in deps, f"{dept} cannot depend on itself"
        for dep in deps:
            assert dep in VALID_DEPTS, f"{dept} depends on unknown department {dep!r}"


def test_every_non_solve_department_depends_on_solve():
    from agency_kit.departments import DEPT_NAMES, DEPT_DEPENDENCIES
    assert DEPT_DEPENDENCIES["solve"] == (), "solve is the root — it has no upstream"
    for dept in DEPT_NAMES:
        if dept == "solve":
            continue
        assert "solve" in DEPT_DEPENDENCIES[dept], (
            f"{dept} must depend on solve (the foundational diagnosis)"
        )


def test_canonical_order_is_a_valid_topological_sort():
    from agency_kit.departments import DEPT_NAMES, DEPT_DEPENDENCIES
    pos = {d: i for i, d in enumerate(DEPT_NAMES)}
    assert pos["solve"] == 0, "solve must lead the canonical order"
    for dept, deps in DEPT_DEPENDENCIES.items():
        for dep in deps:
            assert pos[dep] < pos[dept], (
                f"{dept} depends on {dep}, which is not strictly upstream of it"
            )


def test_dependency_layers_solve_precedes_product():
    from agency_kit.departments import dependency_layers
    assert dependency_layers(["product", "solve"]) == [["solve"], ["product"]]


def test_dependency_layers_full_route_collapses_to_four_waves():
    from agency_kit.departments import dependency_layers, DEPT_NAMES
    waves = dependency_layers(list(DEPT_NAMES))
    assert waves[0] == ["solve"]
    assert waves[1] == ["product"]
    assert set(waves[2]) == {"marketing", "data", "ops", "people", "tech"}
    assert set(waves[3]) == {"finance", "comms"}
    flat = [d for wave in waves for d in wave]
    assert sorted(flat) == sorted(DEPT_NAMES), "every routed dept appears exactly once"


def test_dependency_layers_drops_dependency_absent_from_route():
    from agency_kit.departments import dependency_layers
    assert dependency_layers(["comms", "product"]) == [["product"], ["comms"]]


def test_dependency_layers_dedupes_and_keeps_canonical_order():
    from agency_kit.departments import dependency_layers
    assert dependency_layers(["ops", "data", "data"]) == [["data", "ops"]]


def test_dependency_layers_rejects_unknown_department():
    from agency_kit.departments import dependency_layers
    with pytest.raises(ValueError):
        dependency_layers(["product", "nonsense"])


# ---- departments.py — single source of truth --------------------------------

def test_departments_module_importable():
    from agency_kit.departments import DEPT_NAMES, VALID_DEPTS, dept_list_text
    assert len(DEPT_NAMES) == 9
    assert VALID_DEPTS == frozenset(DEPT_NAMES)
    text = dept_list_text()
    for name in DEPT_NAMES:
        assert name in text, f"dept_list_text() missing '{name}'"


# ---- sync_payload pre-flight guard ------------------------------------------

def test_sync_preflight_raises_when_kits_missing(tmp_path):
    from agency_cli import sync_payload

    fake_root = tmp_path / "agency-kit"
    (fake_root / ".agency" / "memory").mkdir(parents=True)
    (fake_root / ".agency" / "memory" / "constitution.md").write_text("# Constitution\n")
    (fake_root / "agents").mkdir()
    payload = fake_root / "agency_cli" / "payload"
    payload.mkdir(parents=True)

    orig_root = sync_payload.repo_root
    orig_payload = sync_payload.payload_dir
    sync_payload.repo_root = lambda: fake_root
    sync_payload.payload_dir = lambda: payload
    try:
        # --strict path (allow_missing=False) still refuses to wipe when kits are absent.
        with pytest.raises(RuntimeError, match="strict requires all sibling kit repos"):
            sync_payload.sync(allow_missing=False)
        # Preserve mode (the default) must NOT raise — keeps the kit snapshot.
        sync_payload.sync(allow_missing=True)
    finally:
        sync_payload.repo_root = orig_root
        sync_payload.payload_dir = orig_payload


# ---- payload sync drift guard -----------------------------------------------

_SYNCED_AGENTS = [
    "router-agency.md",
    "commander-agency.md",
    "inspector-agency.md",
    "_shared-agency.md",
    "_shared-product.md",
    "_shared-marketing.md",
    "_shared-solve.md",
    "_shared-finance.md",
    "_shared-comms.md",
    "_shared-data.md",
    "_shared-ops.md",
    "_shared-people.md",
    "_shared-tech.md",
    "_shared-eu.md",
    "_shared-us.md",
    "_shared-fr.md",
]


@pytest.mark.parametrize("fname", _SYNCED_AGENTS)
def test_payload_agent_matches_source(fname):
    source = ROOT / "agents" / fname
    mirror = ROOT / "agency_cli" / "payload" / "agents" / fname
    assert source.read_text(encoding="utf-8") == mirror.read_text(encoding="utf-8"), (
        f"agency_cli/payload/agents/{fname} has drifted — run `agency sync`."
    )
