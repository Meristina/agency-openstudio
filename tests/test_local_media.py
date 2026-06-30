"""Tests for the Wave-2 local multimodal layer (`agency_studio/engines/`).

Fully offline, mirroring agency-kit's pattern: the only boundary stubbed is the
heavy back-end (the ``_load_*`` / ``_run_*`` adapters and the download path), so the
real ``ModelManager`` mutual-exclusion + warm-reuse logic and the real ``models``
URL/checksum guards run end-to-end without MLX, without weights, and without network.
"""

import hashlib

import pytest

from agency_studio.engines import local_media, models


# ── models: URL validation (SECURITY.md #4) ──────────────────────────────────

def test_validate_url_accepts_https_allowlisted_host():
    # GitHub release host (where Kokoro files live) — must pass.
    models.validate_url(
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/x/kokoro-v1.0.onnx"
    )


@pytest.mark.parametrize("bad_url", [
    "http://github.com/x/model.onnx",                 # not https
    "https://evil.example.com/model.onnx",            # host not on allowlist
    "ftp://huggingface.co/model.bin",                 # not https
])
def test_validate_url_rejects_bad_urls(bad_url):
    with pytest.raises(ValueError):
        models.validate_url(bad_url)


# ── models: checksum verification (SECURITY.md #5) ────────────────────────────

def test_verify_sha256_matches(tmp_path):
    f = tmp_path / "weights.bin"
    f.write_bytes(b"hello world")
    digest = hashlib.sha256(b"hello world").hexdigest()
    models.verify_sha256(f, digest)  # no raise


def test_verify_sha256_mismatch_raises(tmp_path):
    f = tmp_path / "weights.bin"
    f.write_bytes(b"tampered")
    with pytest.raises(models.IntegrityError):
        models.verify_sha256(f, hashlib.sha256(b"original").hexdigest())


def test_ensure_file_cache_hit_skips_download(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_STUDIO_MODELS_DIR", str(tmp_path))
    payload = b"already here"
    spec = models.ModelFile(
        name="cached.bin", url="https://github.com/x/cached.bin",
        sha256=hashlib.sha256(payload).hexdigest(),
    )
    (tmp_path / "cached.bin").write_bytes(payload)

    def _boom(*a, **k):
        raise AssertionError("download must not run on a cache hit")

    monkeypatch.setattr(models, "_download", _boom)
    assert models.ensure_file(spec) == tmp_path / "cached.bin"  # cache hit, verified, no download


def test_ensure_file_verifies_after_download(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_STUDIO_MODELS_DIR", str(tmp_path))
    payload = b"genuine weights"
    spec = models.ModelFile(
        name="dl.bin", url="https://huggingface.co/x/dl.bin",
        sha256=hashlib.sha256(payload).hexdigest(),
    )

    def _fake_download(url, dest):
        dest.write_bytes(payload)

    monkeypatch.setattr(models, "_download", _fake_download)
    assert models.ensure_file(spec).read_bytes() == payload


def test_ensure_file_bad_checksum_removes_file(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_STUDIO_MODELS_DIR", str(tmp_path))
    spec = models.ModelFile(
        name="bad.bin", url="https://huggingface.co/x/bad.bin",
        sha256=hashlib.sha256(b"expected").hexdigest(),
    )

    monkeypatch.setattr(models, "_download", lambda url, dest: dest.write_bytes(b"corrupt"))
    with pytest.raises(models.IntegrityError):
        models.ensure_file(spec)
    assert not (tmp_path / "bad.bin").exists()  # never leave an unverified file behind


def test_ensure_file_reverifies_cached_file(tmp_path, monkeypatch):
    """A cache hit must still verify SHA-256 — on-disk corruption/tampering after the
    first download is caught on every load, not skipped (SECURITY.md #5)."""
    monkeypatch.setenv("AGENCY_STUDIO_MODELS_DIR", str(tmp_path))
    spec = models.ModelFile(
        name="weights.bin", url="https://huggingface.co/x/weights.bin",
        sha256=hashlib.sha256(b"genuine").hexdigest(),
    )
    # A pre-existing (cached) file whose contents no longer match the pinned digest.
    (tmp_path / "weights.bin").write_bytes(b"tampered-on-disk")

    def _boom(*a, **k):
        raise AssertionError("must not re-download a cache hit")

    monkeypatch.setattr(models, "_download", _boom)
    with pytest.raises(models.IntegrityError):
        models.ensure_file(spec)
    assert not (tmp_path / "weights.bin").exists()  # bad cached file removed


def test_redirect_to_disallowed_host_is_rejected():
    """The host allowlist must govern the bytes actually fetched: a 30x redirect to a
    non-allowlisted host is refused (defends the GitHub-release redirect path)."""
    handler = models._AllowlistRedirectHandler()
    with pytest.raises(ValueError):
        handler.redirect_request(
            req=None, fp=None, code=302, msg="Found", headers={},
            newurl="https://attacker.example/payload",
        )


def test_redirect_to_allowlisted_host_is_permitted(monkeypatch):
    """A redirect to an allowlisted host (real GitHub-release behaviour) is allowed —
    validate_url passes, so the parent handler builds the redirected request."""
    handler = models._AllowlistRedirectHandler()
    captured = {}

    def _fake_super(self, req, fp, code, msg, headers, newurl):
        captured["url"] = newurl
        return "redirected-request"

    # Bypass urllib's real super() (which needs a live Request) — we only assert that
    # an allowlisted hop is NOT rejected and is forwarded to the base handler.
    monkeypatch.setattr(models.urllib.request.HTTPRedirectHandler, "redirect_request", _fake_super)
    out = handler.redirect_request(
        req=None, fp=None, code=302, msg="Found", headers={},
        newurl="https://release-assets.githubusercontent.com/asset/123",
    )
    assert out == "redirected-request"
    assert captured["url"].startswith("https://release-assets.githubusercontent.com/")


# ── ModelManager: stubbing the heavy back-ends ────────────────────────────────

class _FakeModel:
    """Stand-in for a loaded model; records which kind it is."""
    def __init__(self, kind):
        self.kind = kind


def _stub_backends(monkeypatch):
    """Replace every heavy adapter with a counting stub. Returns a dict of counters
    so a test can assert how many times each model was loaded (warm reuse = no reload).

    The image probe/loader now receive the selected registry entry, so the stubs are
    parametrized by model id: ANY of the three image models loads through the same
    stub, and ``counters['loaded_models']`` records the ids loaded in order (so an
    image↔image switch — eviction + reload — is observable)."""
    counters = {"image_load": 0, "stt_load": 0, "tts_load": 0,
                "image_run": 0, "stt_run": 0, "tts_run": 0, "freed": 0,
                "loaded_models": []}

    def _load_image(entry):
        counters["image_load"] += 1
        counters["loaded_models"].append(entry.id)
        return _FakeModel(entry.id)

    def _run_image(entry, model, *, prompt, steps, seed, width, height, out_path):
        counters["image_run"] += 1
        out_path.write_bytes(b"\x89PNG\r\n")  # token bytes so a real file lands

    def _load_stt():
        counters["stt_load"] += 1
        return _FakeModel("stt")

    def _run_stt(model, *, audio_path):
        counters["stt_run"] += 1
        return "transcribed text"

    def _load_tts():
        counters["tts_load"] += 1
        return _FakeModel("tts")

    def _run_tts(model, *, text, voice, out_path):
        counters["tts_run"] += 1
        out_path.write_bytes(b"RIFF")

    monkeypatch.setattr(local_media, "_load_image_backend", _load_image)
    monkeypatch.setattr(local_media, "_run_image_backend", _run_image)
    monkeypatch.setattr(local_media, "_load_stt_backend", _load_stt)
    monkeypatch.setattr(local_media, "_run_stt_backend", _run_stt)
    monkeypatch.setattr(local_media, "_load_tts_backend", _load_tts)
    monkeypatch.setattr(local_media, "_run_tts_backend", _run_tts)
    # Probes are cheap availability checks — stub them to succeed so the suite never
    # tries a real import (a test for the failing-probe path stubs one to raise). The
    # image probe takes the selected entry (and accepts any of the three models).
    monkeypatch.setattr(local_media, "_probe_image", lambda entry: None)
    monkeypatch.setattr(local_media, "_probe_stt", lambda: None)
    monkeypatch.setattr(local_media, "_probe_tts", lambda: None)
    monkeypatch.setattr(local_media, "_free_metal_cache", lambda: counters.__setitem__("freed", counters["freed"] + 1))
    return counters


def test_generate_image_writes_asset_and_result(tmp_path, monkeypatch):
    _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    result = mgr.generate_image("a luxury food photograph", seed=7)
    assert result.path.is_file()
    assert result.path.parent == tmp_path / "images"
    assert result.seed == 7
    assert result.prompt == "a luxury food photograph"
    # Default model is flux-schnell, and the warm key is the model id (not "image").
    assert result.model == "flux-schnell"
    assert mgr.resident == "flux-schnell"
    assert mgr.resident_kind == "flux-schnell"  # back-compat alias


def test_generate_image_defaults_to_flux_schnell(tmp_path, monkeypatch):
    counters = _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    result = mgr.generate_image("no model arg")
    assert result.model == models.DEFAULT_IMAGE_MODEL == "flux-schnell"
    assert counters["loaded_models"] == ["flux-schnell"]


def test_generate_image_explicit_model_selection(tmp_path, monkeypatch):
    counters = _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    result = mgr.generate_image("modern look", model="flux2-klein-4b")
    assert result.model == "flux2-klein-4b"
    assert mgr.resident == "flux2-klein-4b"
    assert counters["loaded_models"] == ["flux2-klein-4b"]


def test_generate_image_unknown_model_raises_valueerror(tmp_path, monkeypatch):
    counters = _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    with pytest.raises(ValueError):
        mgr.generate_image("x", model="not-a-real-model")
    assert counters["image_load"] == 0  # rejected before any load


def test_switching_image_model_evicts_and_reloads(tmp_path, monkeypatch):
    """image↔image is mutually exclusive too: a different model id evicts the warm one
    and loads the new one; repeating the SAME id is a warm hit (no reload, no evict)."""
    counters = _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    mgr.generate_image("one", model="flux-schnell")
    mgr.generate_image("two", model="flux-schnell")     # same id → warm reuse
    assert counters["image_load"] == 1
    assert counters["freed"] == 0
    mgr.generate_image("three", model="flux2-klein-4b")  # switch → evict + reload
    assert counters["freed"] == 1
    assert counters["image_load"] == 2
    assert counters["loaded_models"] == ["flux-schnell", "flux2-klein-4b"]
    assert mgr.resident == "flux2-klein-4b"


def test_steps_default_per_model(tmp_path, monkeypatch):
    """When steps is omitted the model's own steps_default is used (16 for Boogu vs 4
    for the distilled FLUX models)."""
    seen = {}

    def _run_image(entry, model, *, prompt, steps, seed, width, height, out_path):
        seen["steps"] = steps
        out_path.write_bytes(b"\x89PNG\r\n")

    _stub_backends(monkeypatch)
    monkeypatch.setattr(local_media, "_run_image_backend", _run_image)
    mgr = local_media.ModelManager(tmp_path)
    mgr.generate_image("x", model="boogu-base")
    assert seen["steps"] == 16  # boogu-base's steps_default


def test_boogu_backend_registered():
    """Boogu is wired as a distinct, pluggable backend (not mflux)."""
    entry = models.image_model("boogu-base")
    assert entry.backend == "boogu"
    assert entry.base_repo and entry.qwen_repo  # boogu needs both weight repos
    assert "boogu" in local_media._IMAGE_BACKENDS
    assert len(local_media._IMAGE_BACKENDS["boogu"]) == 3  # (probe, load, run) triple


def test_generate_image_routes_boogu_through_backend(tmp_path, monkeypatch):
    """Exercise the REAL dispatch: stub the registry's ``_IMAGE_BACKENDS['boogu']``
    triple (via setitem) — NOT the dispatch functions — so the actual
    ``_image_backend('boogu')`` lookup + ``_probe_image``/``_load_image_backend``/
    ``_run_image_backend`` run and call the boogu triple. A mis-wired triple (wrong
    position, wrong key) would now fail this test."""
    calls = []

    def _probe(entry):
        calls.append(("probe", entry.id))

    def _load(entry):
        calls.append(("load", entry.id))
        return _FakeModel("boogu")

    def _run(model, entry, *, prompt, steps, seed, width, height, out_path):
        calls.append(("run", entry.id, steps))
        out_path.write_bytes(b"\x89PNG\r\n")

    monkeypatch.setitem(local_media._IMAGE_BACKENDS, "boogu", (_probe, _load, _run))
    monkeypatch.setattr(local_media, "_free_metal_cache", lambda: None)

    mgr = local_media.ModelManager(tmp_path)
    result = mgr.generate_image("a red panda surfing", model="boogu-base", steps=7)
    assert result.model == "boogu-base"
    assert result.path.is_file()
    assert mgr.resident == "boogu-base"
    # The real dispatch invoked the boogu triple in order, with the entry threaded through.
    assert ("probe", "boogu-base") in calls
    assert ("load", "boogu-base") in calls
    assert ("run", "boogu-base", 7) in calls


def test_boogu_probe_without_extra_raises_media_unavailable():
    """With the [boogu] extra absent (the test interpreter), the boogu probe raises
    MediaUnavailable — which the server maps to a clean 501, like the [media] path."""
    entry = models.image_model("boogu-base")
    try:
        import boogu_image_mlx  # noqa: F401
        import mlx_vlm  # noqa: F401
    except ImportError:
        with pytest.raises(local_media.MediaUnavailable):
            local_media._boogu_probe(entry)
    else:
        pytest.skip("[boogu] extra is installed in this interpreter")


def test_empty_prompt_rejected(tmp_path, monkeypatch):
    _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    with pytest.raises(ValueError):
        mgr.generate_image("   ")


def test_warm_reuse_does_not_reload_same_kind(tmp_path, monkeypatch):
    counters = _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    mgr.generate_image("one")
    mgr.generate_image("two")
    assert counters["image_load"] == 1   # loaded once, reused warm
    assert counters["image_run"] == 2
    assert counters["freed"] == 0        # no eviction between same-kind calls


def test_switching_modality_evicts_previous_model(tmp_path, monkeypatch):
    counters = _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    mgr.generate_image("draw this")
    assert mgr.resident == "flux-schnell"
    mgr.synthesize("say this")
    assert mgr.resident == "tts"
    assert counters["freed"] == 1        # the image model was evicted on switch
    assert counters["tts_load"] == 1


def test_transcribe_requires_existing_file(tmp_path, monkeypatch):
    _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    with pytest.raises(FileNotFoundError):
        mgr.transcribe(tmp_path / "nope.wav")


def test_transcribe_returns_text(tmp_path, monkeypatch):
    _stub_backends(monkeypatch)
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"RIFF....")
    mgr = local_media.ModelManager(tmp_path)
    result = mgr.transcribe(audio)
    assert result.text == "transcribed text"
    assert mgr.resident_kind == "stt"


def test_synthesize_writes_audio_asset(tmp_path, monkeypatch):
    _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    result = mgr.synthesize("hello there", voice="af_heart")
    assert result.path.is_file()
    assert result.path.parent == tmp_path / "audio"
    assert result.voice == "af_heart"


# ── MediaUnavailable: the [media] extra absent → clean error (server maps to 501) ──

def test_missing_extra_raises_media_unavailable(tmp_path, monkeypatch):
    """When the probe can't import its lib it raises MediaUnavailable; the manager
    surfaces it unchanged (the server turns it into a 501)."""
    _stub_backends(monkeypatch)

    def _no_lib(entry):
        raise local_media.MediaUnavailable("image generation needs mflux — install ...")

    monkeypatch.setattr(local_media, "_probe_image", _no_lib)
    mgr = local_media.ModelManager(tmp_path)
    with pytest.raises(local_media.MediaUnavailable):
        mgr.generate_image("anything")


def test_media_unavailable_is_an_importerror():
    """The server maps optional-extra-missing to 501 via `except ImportError` (the
    [pdf] path). MediaUnavailable MUST be catchable that way, or the route 500s."""
    assert issubclass(local_media.MediaUnavailable, ImportError)


def test_failed_probe_does_not_evict_warm_model(tmp_path, monkeypatch):
    """A request for an UNINSTALLED modality must not destroy the model that is
    already warm: the probe fails before eviction, so the warm model survives."""
    counters = _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    mgr.generate_image("warm it up")          # image now warm
    assert mgr.resident == "flux-schnell"

    monkeypatch.setattr(local_media, "_probe_tts",
                        lambda: (_ for _ in ()).throw(local_media.MediaUnavailable("no kokoro")))
    with pytest.raises(local_media.MediaUnavailable):
        mgr.synthesize("won't load")

    assert mgr.resident == "flux-schnell"      # warm image model preserved
    assert counters["freed"] == 0              # nothing was evicted
    mgr.generate_image("still warm")
    assert counters["image_load"] == 1         # reused, never reloaded


def test_synthesize_rejects_unlisted_voice(tmp_path, monkeypatch):
    """An unlisted voice is rejected at the manager (chokepoint to the TTS backend) and
    never reaches the backend — /api/tts maps the same allowlist to a 400."""
    _stub_backends(monkeypatch)
    mgr = local_media.ModelManager(tmp_path)
    with pytest.raises(ValueError):
        mgr.synthesize("hello", voice="zz_not_a_voice")
    assert "af_heart" in models.ALLOWED_VOICES   # the default is a member, so it always passes
