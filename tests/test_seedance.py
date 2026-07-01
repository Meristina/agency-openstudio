"""Offline tests for the Wave-6 seedance brick (`agency_studio/seedance.py`).

Fully offline: the cloud video render is never actually POSTed — the boundary (`_run_cloud`) is a
network-deferred stub, so these tests assert the *gates* around it (https-only, env-key, the
cloud-only backend registry) and the `ModelManager.generate_video` dispatch, without touching the
network. The marker-side gating (the per-mission `allow_video` opt-in) is covered in
`test_assets.py`; the two together are the "an untrusted marker alone can never network" invariant.
"""

import pytest

from agency_studio import seedance
from agency_studio.engines.local_media import ModelManager, VideoResult


# ── the registry + resolution contract ────────────────────────────────────────
def test_default_video_model_is_registered_and_cloud():
    entry = seedance.video_model(seedance.DEFAULT_VIDEO_MODEL)
    assert entry.backend == "cloud" and entry.default is True


def test_every_registered_endpoint_is_https():
    # SECURITY.md #4 — an off-machine flow may only target https. The parser never lets a marker
    # name a model, so the registry is the ONLY place a video endpoint is chosen: assert them all.
    for entry in seedance.VIDEO_MODELS.values():
        assert entry.endpoint.startswith("https://"), entry.id


def test_video_model_unknown_id_raises():
    with pytest.raises(ValueError, match="unknown video model"):
        seedance.video_model("nope")


def test_seedance_is_cloud_only():
    # Unlike visual RAG (local default + optional cloud), video has no local backend — text-to-video
    # doesn't fit the 16 GB Mac, so the seam carries a single cloud triple.
    assert set(seedance._VIDEO_BACKENDS) == {"cloud"}


def test_backend_unknown_name_raises():
    bad = seedance.VideoModel(id="x", label="x", backend="local")
    with pytest.raises(ValueError, match="unknown video backend"):
        seedance._backend(bad)


# ── the cloud backend's safety gates (network-free) ───────────────────────────
def test_seedance_unavailable_is_an_importerror():
    # So the server's optional-extra handler maps it to a 501 + hint (like VisualUnavailable).
    assert issubclass(seedance.SeedanceUnavailable, ImportError)


def test_cloud_backend_requires_https_endpoint():
    bad = seedance.VideoModel(id="x", label="x", backend="cloud",
                              endpoint="http://insecure.example/v1", api_model="m")
    with pytest.raises(ValueError, match="https"):
        seedance._probe_cloud(bad)


def test_cloud_backend_requires_env_key(monkeypatch):
    monkeypatch.delenv(seedance.CLOUD_API_KEY_ENV, raising=False)
    with pytest.raises(seedance.SeedanceUnavailable, match=seedance.CLOUD_API_KEY_ENV):
        seedance._probe_cloud(seedance.VIDEO_MODELS[seedance.DEFAULT_VIDEO_MODEL])


def test_cloud_probe_passes_with_https_and_key(monkeypatch):
    monkeypatch.setenv(seedance.CLOUD_API_KEY_ENV, "k")
    # https endpoint + key present → no raise, no network.
    seedance._probe_cloud(seedance.VIDEO_MODELS[seedance.DEFAULT_VIDEO_MODEL])


def test_cloud_run_is_deferred_and_never_leaks_the_key(monkeypatch, tmp_path):
    # PLACEHOLDER coverage: _run_cloud is a deferred stub that raises before building any request,
    # so this only catches a hardcoded secret in that one message — it does NOT exercise a real
    # request/logging path (there is none yet). The genuine no-leak guarantee MUST be re-audited
    # with a redaction test when the live cloud POST lands (see docs/WAVE6-PLAN.md Brick 5).
    monkeypatch.setenv(seedance.CLOUD_API_KEY_ENV, "super-secret-key-value")
    entry = seedance.VIDEO_MODELS[seedance.DEFAULT_VIDEO_MODEL]
    with pytest.raises(seedance.SeedanceUnavailable) as exc:
        seedance._run_cloud(seedance._load_cloud(entry), entry, prompt="a clip", out_path=tmp_path / "x.mp4")
    assert "super-secret-key-value" not in str(exc.value)


def test_cloud_run_without_key_raises_before_any_request(monkeypatch, tmp_path):
    # Defence in depth: even reaching _run_cloud with no key raises (never a silent network attempt).
    monkeypatch.delenv(seedance.CLOUD_API_KEY_ENV, raising=False)
    entry = seedance.VIDEO_MODELS[seedance.DEFAULT_VIDEO_MODEL]
    with pytest.raises(seedance.SeedanceUnavailable):
        seedance._run_cloud({"endpoint": entry.endpoint}, entry, prompt="a clip", out_path=tmp_path / "x.mp4")


# ── ModelManager.generate_video dispatch (no network, no residency cost) ──────
def test_generate_video_rejects_empty_prompt(tmp_path):
    mgr = ModelManager(tmp_path)
    with pytest.raises(ValueError, match="prompt must not be empty"):
        mgr.generate_video("   ")


def test_generate_video_unknown_model_raises(tmp_path):
    mgr = ModelManager(tmp_path)
    with pytest.raises(ValueError, match="unknown video model"):
        mgr.generate_video("a clip", model="nope")


def test_generate_video_without_key_raises_seedance_unavailable(monkeypatch, tmp_path):
    # A real ModelManager, default (cloud) model, no API key → SeedanceUnavailable from the probe,
    # BEFORE any eviction or network. This is the render-time half of the triple gate.
    monkeypatch.delenv(seedance.CLOUD_API_KEY_ENV, raising=False)
    mgr = ModelManager(tmp_path)
    with pytest.raises(seedance.SeedanceUnavailable, match=seedance.CLOUD_API_KEY_ENV):
        mgr.generate_video("a drone shot of a city")


def test_generate_video_returns_videoresult_when_backend_stubbed(monkeypatch, tmp_path):
    # Stub the whole (probe, load, run) triple so the manager's happy path is exercised end-to-end
    # offline: it must write under videos/ and return a VideoResult with the resolved model id +
    # prompt. Patch `_backend` (not the module fns) because `_VIDEO_BACKENDS` binds direct refs.
    def _fake_run(backend, entry, *, prompt, out_path):
        out_path.write_bytes(b"\x00fakemp4")   # simulate the downloaded clip

    monkeypatch.setattr(seedance, "_backend",
                        lambda entry: (lambda e: None, lambda e: {"stub": True}, _fake_run))
    mgr = ModelManager(tmp_path)
    result = mgr.generate_video("a timelapse of clouds", out_dir=tmp_path / "missions" / "m1")
    assert isinstance(result, VideoResult)
    assert result.model == seedance.DEFAULT_VIDEO_MODEL
    assert result.prompt == "a timelapse of clouds"
    assert result.path.suffix == ".mp4" and result.path.is_file()
    assert result.path.parent.name == "videos"
