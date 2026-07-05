import json

import pytest

from agency_studio import capabilities
from agency_studio.engines import models


def _available(entries):
    return [
        capabilities.CapabilityEntry(
            id=e.id,
            label=e.label,
            family="image",
            cost="free",
            availability="available",
            default=e.default,
        )
        for e in entries
    ]


def test_stt_tts_registries_wrap_existing_constants():
    stt = models.stt_model(models.DEFAULT_STT_MODEL)
    assert stt.repo == models.STT_HF_REPO
    assert stt.revision == models.STT_HF_REVISION
    assert stt.probe_module == "mlx_whisper"
    assert stt.default

    tts = models.tts_model(models.DEFAULT_TTS_MODEL)
    assert tts.probe_module == "kokoro_onnx"
    assert tts.default


def test_selection_store_tolerates_missing_bad_and_wrong_shape(tmp_path):
    store = capabilities.SelectionStore(tmp_path / "selections.json")
    assert store.load() == {}

    store.path.write_text("{bad", encoding="utf-8")
    assert store.load() == {}

    store.path.write_text(json.dumps({"version": 2, "selections": {"image": "x"}}), encoding="utf-8")
    assert store.load() == {}


def test_selection_store_round_trips_without_key_values(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_STUDIO_VIDEO_API_KEY", "secret-value")
    store = capabilities.SelectionStore(tmp_path / "selections.json")
    store.set("image", "flux-schnell")
    assert store.load() == {"image": "flux-schnell"}
    assert "secret-value" not in store.path.read_text(encoding="utf-8")


def test_resolve_env_selection_default_precedence(monkeypatch, tmp_path):
    store = capabilities.SelectionStore(tmp_path / "selections.json")
    monkeypatch.setattr(capabilities, "image_entries", lambda: _available(models.IMAGE_MODELS.values()))
    monkeypatch.setitem(capabilities.BUILDERS, "image", capabilities.image_entries)

    assert capabilities.resolve("image", store=store) == models.DEFAULT_IMAGE_MODEL
    store.set("image", "flux2-klein-4b")
    assert capabilities.resolve("image", store=store) == "flux2-klein-4b"
    monkeypatch.setenv("AGENCY_STUDIO_IMAGE_MODEL", "flux-schnell")
    assert capabilities.resolve("image", store=store) == "flux-schnell"
    monkeypatch.setenv("AGENCY_STUDIO_IMAGE_MODEL", "nope")
    with pytest.raises(ValueError):
        capabilities.resolve("image", store=store)


def test_extra_hints_name_the_extra_that_provides_the_module(monkeypatch):
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    assert capabilities._extra_available("mlx_embedding_models")[2] == "pip install 'agency-studio[studio]'"
    assert capabilities._extra_available("mlx_vlm")[2] == "pip install 'agency-studio[visual]'"
    assert capabilities._extra_available("mcp")[2] == "pip install 'agency-studio[mcp]'"
    assert capabilities._extra_available("gliner2")[2] == "pip install 'agency-studio[kg]'"
    # Unmapped module: still a concrete step, never a wrong extra.
    assert "unknown_module" in capabilities._extra_available("unknown_module")[2]


def test_tts_unavailable_when_soundfile_missing(monkeypatch):
    # /api/tts needs BOTH kokoro_onnx and soundfile (_probe_tts gates on both);
    # the inventory must not report AVAILABLE when only the engine is installed.
    monkeypatch.setattr(
        "importlib.util.find_spec",
        lambda name: object() if name == "kokoro_onnx" else None,
    )
    entry = capabilities.tts_entries()[0]
    assert entry.availability == "unavailable"
    assert entry.reason == "missing_extra"
    assert entry.enablement == "pip install 'agency-studio[media]'"


def test_inventory_survives_bad_env_override(monkeypatch, tmp_path):
    store = capabilities.SelectionStore(tmp_path / "selections.json")
    monkeypatch.setattr(capabilities, "image_entries", lambda: _available(models.IMAGE_MODELS.values()))
    monkeypatch.setitem(capabilities.BUILDERS, "image", capabilities.image_entries)
    monkeypatch.setattr(capabilities, "production_tool_entries", lambda refresh=False: [])
    monkeypatch.setitem(capabilities.BUILDERS, "production-tools", capabilities.production_tool_entries)
    monkeypatch.setattr(capabilities, "mcp_entries", lambda: [])
    monkeypatch.setitem(capabilities.BUILDERS, "mcp", capabilities.mcp_entries)
    monkeypatch.setenv("AGENCY_STUDIO_IMAGE_MODEL", "nope")

    inv = capabilities.inventory(store=store)  # must not raise (SC-005)
    fam = next(f for f in inv["families"] if f["family"] == "image")
    assert fam["env_override"] == "AGENCY_STUDIO_IMAGE_MODEL"
    assert fam["active"] == models.DEFAULT_IMAGE_MODEL
    # Consumers still fail loud on the same bad env value.
    with pytest.raises(ValueError):
        capabilities.resolve("image", store=store)


def test_stale_selection_flagged_and_skipped(monkeypatch, tmp_path):
    store = capabilities.SelectionStore(tmp_path / "selections.json")
    monkeypatch.setattr(capabilities, "image_entries", lambda: _available(models.IMAGE_MODELS.values()))
    monkeypatch.setitem(capabilities.BUILDERS, "image", capabilities.image_entries)
    monkeypatch.setattr(capabilities, "production_tool_entries", lambda refresh=False: [])
    monkeypatch.setitem(capabilities.BUILDERS, "production-tools", capabilities.production_tool_entries)
    monkeypatch.setattr(capabilities, "mcp_entries", lambda: [])
    monkeypatch.setitem(capabilities.BUILDERS, "mcp", capabilities.mcp_entries)
    store.set("image", "gone-model")

    inv = capabilities.inventory(store=store)
    fam = next(f for f in inv["families"] if f["family"] == "image")
    assert fam["selected"] == "gone-model"
    assert fam["selected_stale"] is True
    assert capabilities.resolve("image", store=store) == models.DEFAULT_IMAGE_MODEL


def test_catalog_probe_failure_then_refresh(monkeypatch):
    monkeypatch.setattr(capabilities, "_CATALOG_CACHE", None)

    def boom():
        raise RuntimeError("no python deps in subtree")

    monkeypatch.setattr(capabilities, "_spawn_catalog", boom)
    entries = capabilities.production_tool_entries(refresh=True)
    assert entries[0].reason == "catalog_error"

    good = json.dumps({"tools": [
        {"name": "image_selector", "tier": "hybrid", "description": "pick images"},
        {"name": "upscaler", "tier": "local_gpu"},
        {"name": "stock_fetch", "tier": "api"},
    ]})
    monkeypatch.setattr(capabilities, "_spawn_catalog", lambda: good)
    # Without refresh the failed probe is cached; refresh re-probes.
    assert capabilities.production_tool_entries()[0].reason == "catalog_error"
    fresh = capabilities.production_tool_entries(refresh=True)
    costs = {e.id: (e.cost, e.tier) for e in fresh}
    assert costs == {
        "image_selector": ("free_paid", "hybrid"),
        "upscaler": ("free", "local_gpu"),
        "stock_fetch": ("paid", "api"),
    }


def test_mcp_entries_tolerate_broken_config(monkeypatch):
    def broken():
        raise OSError("mcp.json unreadable")

    monkeypatch.setattr(capabilities.mcp_client, "list_servers", broken)
    entries = capabilities.mcp_entries()
    assert entries[0].reason == "catalog_error"

    monkeypatch.setattr(capabilities.mcp_client, "list_servers", lambda: [
        {"name": "wiki", "transport": "stdio", "command": "definitely-not-a-real-cmd"},
    ])
    monkeypatch.setattr("importlib.util.find_spec", lambda name: object())
    entries = capabilities.mcp_entries()
    assert entries[0].id == "wiki"
    assert entries[0].cost == "free"
    assert entries[0].availability == "unavailable"  # command not on PATH


def test_select_refuses_unavailable_entry(monkeypatch, tmp_path):
    store = capabilities.SelectionStore(tmp_path / "selections.json")
    monkeypatch.setattr(capabilities, "image_entries", lambda: [
        capabilities.CapabilityEntry(
            id="x",
            label="X",
            family="image",
            cost="free",
            availability="unavailable",
            reason="missing_extra",
            enablement="install it",
        )
    ])
    monkeypatch.setitem(capabilities.BUILDERS, "image", capabilities.image_entries)

    status, body = capabilities.select("image", "x", store=store)
    assert status == 409
    assert body["reason"] == "missing_extra"
    assert store.load() == {}


def test_default_uses_first_available_when_builtin_unavailable():
    entries = [
        capabilities.CapabilityEntry("a", "A", "image", "free", "unavailable", default=True),
        capabilities.CapabilityEntry("b", "B", "image", "free", "available"),
    ]
    assert capabilities._default(entries) == "b"


def test_preflight_returns_all_blockers(monkeypatch):
    monkeypatch.setattr(capabilities, "image_entries", lambda: [
        capabilities.CapabilityEntry("img", "Image", "image", "free", "unavailable", reason="missing_binary", enablement="install sd", default=True)
    ])
    monkeypatch.setitem(capabilities.BUILDERS, "image", capabilities.image_entries)
    monkeypatch.setattr(capabilities, "tts_entries", lambda: [
        capabilities.CapabilityEntry("tts", "TTS", "tts", "free", "unavailable", reason="missing_extra", enablement="install media", default=True)
    ])
    monkeypatch.setitem(capabilities.BUILDERS, "tts", capabilities.tts_entries)
    blockers = capabilities.preflight(["image", "tts"])
    assert [(b.family, b.entry, b.reason) for b in blockers] == [
        ("image", "img", "missing_binary"),
        ("tts", "tts", "missing_extra"),
    ]
