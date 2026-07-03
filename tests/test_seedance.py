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
    # A LOCAL entry (the OpenMontage fusion) is the inverse invariant: no endpoint at all — it
    # must never look like it has an off-machine surface.
    for entry in seedance.VIDEO_MODELS.values():
        if entry.backend == "cloud":
            assert entry.endpoint.startswith("https://"), entry.id
        else:
            assert entry.endpoint == "" and entry.api_model == "", entry.id


def test_video_model_unknown_id_raises():
    with pytest.raises(ValueError, match="unknown video model"):
        seedance.video_model("nope")


def test_static_registry_is_cloud_only_local_resolves_lazily():
    # The static triple registry stays cloud-only; the OpenMontage `local` triple resolves
    # lazily inside _backend (a subprocess-boundary module, imported only when selected).
    assert set(seedance._VIDEO_BACKENDS) == {"cloud"}
    from agency_studio import openmontage_backend
    probe, load, run = seedance._backend(seedance.VIDEO_MODELS["openmontage-remotion"])
    assert (probe, load, run) == (openmontage_backend._probe_local,
                                  openmontage_backend._load_local,
                                  openmontage_backend._run_local)


def test_backend_unknown_name_raises():
    bad = seedance.VideoModel(id="x", label="x", backend="nope")
    with pytest.raises(ValueError, match="unknown video backend"):
        seedance._backend(bad)


# ── the env backend selector (default_video_model) ────────────────────────────
def test_default_video_model_unset_env_is_cloud_default(monkeypatch):
    monkeypatch.delenv(seedance.VIDEO_BACKEND_ENV, raising=False)
    assert seedance.default_video_model() == seedance.DEFAULT_VIDEO_MODEL


def test_default_video_model_env_selects_local(monkeypatch):
    monkeypatch.setenv(seedance.VIDEO_BACKEND_ENV, "openmontage-remotion")
    assert seedance.default_video_model() == "openmontage-remotion"


def test_default_video_model_env_typo_fails_loud(monkeypatch):
    # A typo must never silently fall back to the CLOUD default (an off-machine call the
    # user thought they had redirected locally).
    monkeypatch.setenv(seedance.VIDEO_BACKEND_ENV, "openmontage-typo")
    with pytest.raises(ValueError, match=seedance.VIDEO_BACKEND_ENV):
        seedance.default_video_model()


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


def _stub_ark(monkeypatch, *, post=None, polls, download=None):
    """Stub the three network primitives so _run_cloud runs offline: create-task returns ``post``,
    successive polls return ``polls`` items, download writes ``download`` bytes to out_path."""
    calls = {"post": [], "get": [], "dl": []}
    monkeypatch.setattr(seedance, "_http_post_json",
                        lambda url, payload, key: (calls["post"].append((url, payload, key)),
                                                   post or {"id": "task-123"})[1])
    seq = iter(polls)
    monkeypatch.setattr(seedance, "_http_get_json",
                        lambda url, key: (calls["get"].append(url), next(seq))[1])
    monkeypatch.setattr(seedance, "_http_download",
                        lambda url, out, should_cancel=None: (calls["dl"].append(url),
                                                              out.write_bytes(download or b"MP4")))
    monkeypatch.setattr(seedance.time, "sleep", lambda s: None)  # no real wait between polls
    return calls


def test_cloud_run_creates_polls_downloads(monkeypatch, tmp_path):
    # The real 3-step flow (create → poll → download) with the network primitives stubbed.
    monkeypatch.setenv(seedance.CLOUD_API_KEY_ENV, "super-secret-key-value")
    calls = _stub_ark(monkeypatch, polls=[
        {"status": "running"},
        {"status": "succeeded", "content": {"video_url": "https://cdn.example/x.mp4"}},
    ], download=b"MP4DATA")
    entry = seedance.VIDEO_MODELS[seedance.DEFAULT_VIDEO_MODEL]
    out = tmp_path / "clip.mp4"
    seedance._run_cloud(seedance._load_cloud(entry), entry, prompt="a lake at sunrise", out_path=out)
    assert out.read_bytes() == b"MP4DATA"
    url, payload, key = calls["post"][0]
    assert payload["duration"] == seedance.VIDEO_DURATION_SECONDS       # fixed safe caps, not the marker's
    assert payload["resolution"] == seedance.VIDEO_RESOLUTION
    assert payload["content"][0]["text"] == "a lake at sunrise"          # marker text is only the prompt
    assert key == "super-secret-key-value"                               # key on the header path
    assert calls["get"][0].endswith("/task-123")                         # polled the created task
    assert calls["dl"] == ["https://cdn.example/x.mp4"]


def test_cloud_run_model_env_override(monkeypatch, tmp_path):
    # AGENCY_STUDIO_VIDEO_MODEL overrides the registry api_model (Ark ids are account-specific).
    monkeypatch.setenv(seedance.CLOUD_API_KEY_ENV, "k")
    monkeypatch.setenv(seedance.CLOUD_MODEL_ENV, "ep-my-real-endpoint")
    calls = _stub_ark(monkeypatch, polls=[
        {"status": "succeeded", "content": {"video_url": "https://cdn/x.mp4"}}])
    entry = seedance.VIDEO_MODELS[seedance.DEFAULT_VIDEO_MODEL]
    seedance._run_cloud(seedance._load_cloud(entry), entry, prompt="x", out_path=tmp_path / "x.mp4")
    assert calls["post"][0][1]["model"] == "ep-my-real-endpoint"


def test_cloud_run_failed_status_raises_runtimeerror(monkeypatch, tmp_path):
    monkeypatch.setenv(seedance.CLOUD_API_KEY_ENV, "k")
    _stub_ark(monkeypatch, polls=[{"status": "failed", "error": "content rejected"}])
    entry = seedance.VIDEO_MODELS[seedance.DEFAULT_VIDEO_MODEL]
    with pytest.raises(RuntimeError):
        seedance._run_cloud(seedance._load_cloud(entry), entry, prompt="x", out_path=tmp_path / "x.mp4")


def test_cloud_run_no_task_id_raises(monkeypatch, tmp_path):
    monkeypatch.setenv(seedance.CLOUD_API_KEY_ENV, "k")
    _stub_ark(monkeypatch, post={"unexpected": 1}, polls=[])
    entry = seedance.VIDEO_MODELS[seedance.DEFAULT_VIDEO_MODEL]
    with pytest.raises(RuntimeError):
        seedance._run_cloud(seedance._load_cloud(entry), entry, prompt="x", out_path=tmp_path / "x.mp4")


def test_cloud_run_poll_budget_exhaustion_raises(monkeypatch, tmp_path):
    # A task that never reaches a terminal state must give up after _POLL_MAX_ATTEMPTS instead of
    # hanging the mission worker forever. Guards the anti-hang bound (a `while True` regression would
    # otherwise poll indefinitely with no test catching it).
    import itertools
    monkeypatch.setenv(seedance.CLOUD_API_KEY_ENV, "k")
    monkeypatch.setattr(seedance, "_POLL_MAX_ATTEMPTS", 4)
    calls = _stub_ark(monkeypatch, polls=itertools.repeat({"status": "running"}))
    entry = seedance.VIDEO_MODELS[seedance.DEFAULT_VIDEO_MODEL]
    with pytest.raises(RuntimeError, match="did not finish within the poll budget"):
        seedance._run_cloud(seedance._load_cloud(entry), entry, prompt="x", out_path=tmp_path / "x.mp4")
    assert len(calls["get"]) == 4   # polled exactly the budget, then gave up


def test_cloud_run_honours_should_cancel(monkeypatch, tmp_path):
    # A "Stop mission" (should_cancel → True) must abort the poll promptly rather than run out the
    # ~10-min budget. First poll checks cancel BEFORE the status GET, so no GET happens.
    import itertools
    monkeypatch.setenv(seedance.CLOUD_API_KEY_ENV, "k")
    calls = _stub_ark(monkeypatch, polls=itertools.repeat({"status": "running"}))
    entry = seedance.VIDEO_MODELS[seedance.DEFAULT_VIDEO_MODEL]
    with pytest.raises(RuntimeError, match="cancelled"):
        seedance._run_cloud(seedance._load_cloud(entry), entry, prompt="x",
                            out_path=tmp_path / "x.mp4", should_cancel=lambda: True)
    assert calls["get"] == []   # aborted before the first status poll, no wasted network


def test_cloud_download_streams_with_size_cap(monkeypatch, tmp_path):
    # The real _http_download (not stubbed) must stream to disk and refuse an oversized body.
    import io

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            self.close()

    monkeypatch.setattr(seedance, "_MAX_VIDEO_BYTES", 8)
    monkeypatch.setattr(seedance._DOWNLOAD_OPENER, "open",
                        lambda url, timeout=None: _Resp(b"way too many bytes"))
    out = tmp_path / "big.mp4"
    with pytest.raises(RuntimeError, match="exceeded"):
        seedance._http_download("https://cdn.example/big.mp4", out)
    # No orphaned/truncated file left behind (temp-file + atomic rename), and no leftover .part.
    assert not out.exists()
    assert list(tmp_path.glob("*.part")) == []


def test_cloud_download_cancel_leaves_no_partial(monkeypatch, tmp_path):
    # A Stop during the download aborts promptly and leaves no partial .mp4 at out_path.
    import io

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            self.close()

    monkeypatch.setattr(seedance._DOWNLOAD_OPENER, "open",
                        lambda url, timeout=None: _Resp(b"x" * 4096))
    out = tmp_path / "clip.mp4"
    with pytest.raises(RuntimeError, match="cancelled"):
        seedance._http_download("https://cdn.example/x.mp4", out, should_cancel=lambda: True)
    assert not out.exists()
    assert list(tmp_path.glob("*.part")) == []


def test_cloud_download_rejects_non_https(tmp_path):
    # Defence in depth: a video_url that isn't https is refused before any fetch (SECURITY.md #4).
    with pytest.raises(RuntimeError):
        seedance._http_download("http://cdn.example/x.mp4", tmp_path / "x.mp4")


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
    def _fake_run(backend, entry, *, prompt, out_path, should_cancel=None):
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
