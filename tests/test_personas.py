"""Offline tests for the Wave-6 persona-doctrine store (agency_studio/personas.py).

The store, validation, the drift guard, and the doctrine builder are pure filesystem — driven
directly. The only stubbed boundary is the importer's ``PersonaSource`` (the network fetch),
exactly as the knowledge-graph suite stubs the ``Extractor``. No model, no network, no extra.
"""

import builtins

import pytest

from agency_kit.departments import VALID_DEPTS
from agency_studio import personas


def _write(root, dept, name, body):
    d = root / "personas" / dept
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.md").write_text(body, encoding="utf-8")


# ── load + validation ─────────────────────────────────────────────────────────
def test_store_load_empty_is_empty(tmp_path):
    assert personas.load_personas(tmp_path) == []
    assert personas.stats(tmp_path) == {"total": 0, "enabled": 0, "by_dept": {}}


def test_store_save_then_load_roundtrips(tmp_path):
    _write(tmp_path, "marketing", "growth", "You are a razor-focused growth marketer.")
    loaded = personas.load_personas(tmp_path)
    assert len(loaded) == 1
    p = loaded[0]
    assert (p.dept, p.name, p.enabled) == ("marketing", "growth", True)
    assert p.doctrine == "You are a razor-focused growth marketer."


def test_leading_underscore_file_is_disabled(tmp_path):
    _write(tmp_path, "product", "_draft", "A work-in-progress persona.")
    loaded = personas.load_personas(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].enabled is False
    assert loaded[0].name == "draft"          # the underscore is stripped from the name
    # A disabled persona is excluded from the doctrine map…
    assert personas.build_persona_doctrine(root=tmp_path) == {}
    # …but still counted in stats (so the GUI can show it exists).
    assert personas.stats(tmp_path)["total"] == 1
    assert personas.stats(tmp_path)["enabled"] == 0


def test_load_rejects_unknown_dept_key(tmp_path):
    _write(tmp_path, "marketing", "ok", "valid persona")
    _write(tmp_path, "legal", "nope", "a department that does not exist")   # not in DEPT_NAMES
    # Non-strict (runtime default): the unknown-department subdir is skipped, valid survives.
    loaded = personas.load_personas(tmp_path)
    assert [p.dept for p in loaded] == ["marketing"]
    # Strict (import path): the drift is refused loudly, naming the offender.
    with pytest.raises(ValueError, match="legal"):
        personas.load_personas(tmp_path, strict=True)


@pytest.mark.parametrize("dept", sorted(VALID_DEPTS) + ["commander"])
def test_load_accepts_all_valid_keys(tmp_path, dept):
    _write(tmp_path, dept, "p", f"persona for {dept}")
    loaded = personas.load_personas(tmp_path)
    assert [p.dept for p in loaded] == [dept]


def test_load_skips_corrupt_entry(tmp_path):
    _write(tmp_path, "solve", "blank", "   \n  ")          # empty after strip → skipped
    _write(tmp_path, "solve", "real", "a real persona")
    loaded = personas.load_personas(tmp_path)
    assert [p.name for p in loaded] == ["real"]


# ── build_persona_doctrine (the None/empty contract + drift guard) ─────────────
def test_build_persona_doctrine_empty_store_is_empty(tmp_path):
    # Empty dict ⇒ the mission is byte-identical (the build_kg_context_clause → None parallel).
    assert personas.build_persona_doctrine(root=tmp_path) == {}


def test_build_persona_doctrine_maps_known_keys_only(tmp_path):
    _write(tmp_path, "marketing", "a", "MKT")
    _write(tmp_path, "commander", "c", "CMD")
    _write(tmp_path, "legal", "x", "DRIFT")   # unknown dept — never enters the map
    doctrine = personas.build_persona_doctrine(root=tmp_path)
    assert set(doctrine) <= (set(VALID_DEPTS) | {"commander"})
    assert doctrine["marketing"] == "MKT"
    assert doctrine["commander"] == "CMD"
    assert "legal" not in doctrine


def test_build_persona_doctrine_concatenates_per_key(tmp_path):
    _write(tmp_path, "marketing", "a", "FIRST")
    _write(tmp_path, "marketing", "b", "SECOND")
    doctrine = personas.build_persona_doctrine(root=tmp_path)
    assert doctrine["marketing"] == "FIRST\n\nSECOND"


def test_build_persona_doctrine_route_narrows_departments(tmp_path):
    _write(tmp_path, "marketing", "a", "MKT")
    _write(tmp_path, "solve", "b", "SOLVE")
    _write(tmp_path, "commander", "c", "CMD")
    doctrine = personas.build_persona_doctrine(route=["marketing"], root=tmp_path)
    assert set(doctrine) == {"marketing", "commander"}   # routed dept + reserved commander key
    assert "solve" not in doctrine


def test_build_persona_doctrine_respects_per_key_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(personas, "MAX_PERSONAS_PER_KEY", 2)
    for i in range(4):
        _write(tmp_path, "product", f"p{i}", f"body{i}")
    body = personas.build_persona_doctrine(root=tmp_path)["product"]
    assert body.count("body") == 2   # only the first MAX_PERSONAS_PER_KEY are concatenated


# ── importer seam ([personas] absent degrades cleanly; stub writes) ───────────
def test_personas_unavailable_is_an_importerror():
    assert issubclass(personas.PersonasUnavailable, ImportError)


def test_importer_absent_dep_raises_personas_unavailable(monkeypatch):
    real_import = builtins.__import__

    def _no_requests(name, *a, **k):
        if name == "requests":
            raise ImportError("no requests")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _no_requests)
    with pytest.raises(personas.PersonasUnavailable):
        personas.AgencyAgentsSource().fetch()


def test_querying_a_built_store_needs_no_importer(tmp_path, monkeypatch):
    # Reading/injecting an already-curated store must never touch the importer/network.
    def _boom(*a, **k):
        raise AssertionError("the importer must not be reached on the query path")

    monkeypatch.setattr(personas.AgencyAgentsSource, "fetch", _boom)
    _write(tmp_path, "marketing", "a", "MKT")
    assert personas.build_persona_doctrine(root=tmp_path) == {"marketing": "MKT"}
    assert personas.stats(tmp_path)["enabled"] == 1


class _StubSource:
    """A deterministic PersonaSource (the offline import boundary), mirroring KG's _StubExtractor."""

    def __init__(self, items):
        self._items = items

    def fetch(self):
        return self._items


def test_importer_stubbed_writes_curated_personas(tmp_path):
    written = personas.import_personas(
        _StubSource([
            personas.Persona("marketing", "growth", "MKT persona"),
            personas.Persona("commander", "chief", "CMD persona"),
            personas.Persona("legal", "bad", "DRIFT — unknown department"),   # filtered on import
        ]),
        root=tmp_path,
    )
    assert written == 2   # the unknown-department persona is refused (drift guard)
    reloaded = {p.dept: p.doctrine for p in personas.load_personas(tmp_path)}
    assert reloaded == {"marketing": "MKT persona", "commander": "CMD persona"}


def test_import_sanitizes_traversal_in_persona_name(tmp_path):
    # A hostile persona name from an external source must not escape the store dir (_safe_name).
    written = personas.import_personas(
        _StubSource([personas.Persona("marketing", "../../evil", "pwn")]), root=tmp_path,
    )
    assert written == 1
    store = tmp_path / "personas"
    # The file lands INSIDE personas/marketing/, never outside the store.
    all_md = list(store.rglob("*.md"))
    assert all_md and all(store / "marketing" in md.parents for md in all_md)
    assert not (tmp_path.parent / "evil.md").exists()   # no traversal above the store


def test_load_truncates_an_oversized_body(tmp_path, monkeypatch):
    monkeypatch.setattr(personas, "MAX_PERSONA_CHARS", 10)
    _write(tmp_path, "product", "big", "x" * 100)
    assert personas.load_personas(tmp_path)[0].doctrine == "x" * 10


def test_build_persona_doctrine_caps_the_per_key_block(tmp_path, monkeypatch):
    monkeypatch.setattr(personas, "MAX_DOCTRINE_CHARS", 12)
    _write(tmp_path, "product", "a", "aaaaaa")   # 6 + "\n\n" (2) + 6 = 14 > 12 → truncated
    _write(tmp_path, "product", "b", "bbbbbb")
    assert len(personas.build_persona_doctrine(root=tmp_path)["product"]) == 12


def test_import_skips_existing_unless_overwrite(tmp_path):
    _write(tmp_path, "marketing", "growth", "ORIGINAL")
    src = _StubSource([personas.Persona("marketing", "growth", "REPLACED")])
    assert personas.import_personas(src, root=tmp_path) == 0            # exists → skipped
    assert personas.load_personas(tmp_path)[0].doctrine == "ORIGINAL"
    assert personas.import_personas(src, root=tmp_path, overwrite=True) == 1
    assert personas.load_personas(tmp_path)[0].doctrine == "REPLACED"
