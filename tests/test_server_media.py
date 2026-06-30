"""Tests for the Wave-2 multimodal HTTP endpoints (`/api/image`, `/api/tts`,
`/api/stt`, `/api/models`, and `/media/...` asset serving).

Fully offline: the server runs for real (loopback, ephemeral port) but the heavy
back-ends are stubbed at the ``local_media`` adapter boundary, so the full
request → ModelManager → (stub) → asset-on-disk → /media serve path is exercised
without MLX, real weights, or the network.
"""

import http.client
import json
import threading

import pytest

from agency_studio import server
from agency_studio.engines import local_media


# ── helpers ───────────────────────────────────────────────────────────────────

def _start(project_root):
    httpd = server.make_server(host="127.0.0.1", port=0, project_root=str(project_root))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    host, port = httpd.server_address
    return httpd, host, port


def _request(host, port, method, path, body=None, headers=None):
    """One request per connection (avoids HTTP/1.1 keep-alive reuse races)."""
    conn = http.client.HTTPConnection(host, port)
    try:
        conn.request(method, path, body=body, headers=headers or {})
        resp = conn.getresponse()
        return resp.status, resp.read()
    finally:
        conn.close()


def _stub_media(monkeypatch):
    """Stub the multimodal back-ends so the real ModelManager runs without MLX."""
    monkeypatch.setattr(local_media, "_probe_image", lambda entry: None)
    monkeypatch.setattr(local_media, "_probe_stt", lambda: None)
    monkeypatch.setattr(local_media, "_probe_tts", lambda: None)
    monkeypatch.setattr(local_media, "_load_image_backend", lambda entry: object())
    monkeypatch.setattr(local_media, "_load_stt_backend", lambda: object())
    monkeypatch.setattr(local_media, "_load_tts_backend", lambda: object())

    def _run_image(entry, model, *, prompt, steps, seed, width, height, out_path):
        out_path.write_bytes(b"\x89PNG\r\n\x1a\nstub")

    def _run_tts(model, *, text, voice, out_path):
        out_path.write_bytes(b"RIFFstub")

    monkeypatch.setattr(local_media, "_run_image_backend", _run_image)
    monkeypatch.setattr(local_media, "_run_stt_backend", lambda model, *, audio_path: "transcribed text")
    monkeypatch.setattr(local_media, "_run_tts_backend", _run_tts)


# ── /api/image ──────────────────────────────────────────────────────────────

def test_post_image_generates_and_serves(monkeypatch, tmp_path):
    _stub_media(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(
            host, port, "POST", "/api/image",
            body=json.dumps({"prompt": "a luxury food photograph", "seed": 7}),
            headers={"Content-Type": "application/json"},
        )
        assert status == 200
        payload = json.loads(body)
        assert payload["seed"] == 7
        assert payload["model"] == "flux-schnell"  # default model echoed back
        assert payload["url"].startswith("/media/images/")
        assert payload["url"].endswith(".png")
        # The generated asset is actually served back through /media (path_inside).
        asset_status, asset_body = _request(host, port, "GET", payload["url"])
        assert asset_status == 200
        assert asset_body.startswith(b"\x89PNG")
    finally:
        httpd.shutdown()


def test_post_image_missing_prompt_400(monkeypatch, tmp_path):
    _stub_media(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        status, _ = _request(
            host, port, "POST", "/api/image",
            body=json.dumps({"prompt": "   "}),
            headers={"Content-Type": "application/json"},
        )
        assert status == 400
    finally:
        httpd.shutdown()


def test_post_image_explicit_model_echoed(monkeypatch, tmp_path):
    """An explicit valid model id is accepted and echoed back in the 200 JSON."""
    _stub_media(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(
            host, port, "POST", "/api/image",
            body=json.dumps({"prompt": "great text", "model": "z-image-turbo"}),
            headers={"Content-Type": "application/json"},
        )
        assert status == 200
        assert json.loads(body)["model"] == "z-image-turbo"
    finally:
        httpd.shutdown()


def test_post_image_unknown_model_400(monkeypatch, tmp_path):
    """An unknown model id is a clean 400 (validated against the registry before the
    manager runs), never a 500."""
    _stub_media(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        status, _ = _request(
            host, port, "POST", "/api/image",
            body=json.dumps({"prompt": "x", "model": "totally-made-up"}),
            headers={"Content-Type": "application/json"},
        )
        assert status == 400
    finally:
        httpd.shutdown()


def test_post_image_rejects_oversized_dimensions(monkeypatch, tmp_path):
    """Bound the COMPUTE, not just the bytes: an out-of-range width/height/steps is a
    400 before the manager runs, so it can't OOM the Mac or wedge the media lock."""
    _stub_media(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        for bad in ({"prompt": "x", "width": 100000}, {"prompt": "x", "steps": 9999}):
            status, _ = _request(
                host, port, "POST", "/api/image",
                body=json.dumps(bad), headers={"Content-Type": "application/json"},
            )
            assert status == 400
    finally:
        httpd.shutdown()


def test_post_image_backend_failure_returns_500(monkeypatch, tmp_path):
    """A genuine inference failure is a clean 500 — never a 400 (which would imply a
    client error and could leak an internal model URL/size cap)."""
    _stub_media(monkeypatch)

    def _explode(entry, model, **kwargs):
        raise RuntimeError("model download exceeded cap: https://internal/url")

    monkeypatch.setattr(local_media, "_run_image_backend", _explode)
    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(
            host, port, "POST", "/api/image",
            body=json.dumps({"prompt": "x"}), headers={"Content-Type": "application/json"},
        )
        assert status == 500
        assert "https://internal/url" not in body.decode()  # internal detail not leaked
    finally:
        httpd.shutdown()


def test_post_image_missing_extra_returns_501(monkeypatch, tmp_path):
    """The [media] extra absent → the probe raises MediaUnavailable (an ImportError)
    → the route answers 501 with the install hint, never a 500 traceback."""
    _stub_media(monkeypatch)

    def _no_mflux(entry):
        raise local_media.MediaUnavailable("image generation needs mflux — pip install ...")

    monkeypatch.setattr(local_media, "_probe_image", _no_mflux)
    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(
            host, port, "POST", "/api/image",
            body=json.dumps({"prompt": "anything"}),
            headers={"Content-Type": "application/json"},
        )
        assert status == 501
        assert "mflux" in json.loads(body)["error"]
    finally:
        httpd.shutdown()


# ── /api/tts ──────────────────────────────────────────────────────────────────

def test_post_tts_generates_and_serves(monkeypatch, tmp_path):
    _stub_media(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(
            host, port, "POST", "/api/tts",
            body=json.dumps({"text": "hello there", "voice": "af_heart"}),
            headers={"Content-Type": "application/json"},
        )
        assert status == 200
        payload = json.loads(body)
        assert payload["voice"] == "af_heart"
        assert payload["url"].startswith("/media/audio/")
        asset_status, asset_body = _request(host, port, "GET", payload["url"])
        assert asset_status == 200
        assert asset_body.startswith(b"RIFF")
    finally:
        httpd.shutdown()


# ── /api/stt ──────────────────────────────────────────────────────────────────

def test_post_stt_transcribes(monkeypatch, tmp_path):
    _stub_media(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(
            host, port, "POST", "/api/stt",
            body=b"RIFF....fake-wav-bytes",
            headers={"Content-Type": "audio/wav"},
        )
        assert status == 200
        assert json.loads(body)["text"] == "transcribed text"
    finally:
        httpd.shutdown()


def test_post_stt_empty_body_400(monkeypatch, tmp_path):
    _stub_media(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        status, _ = _request(
            host, port, "POST", "/api/stt", body=b"",
            headers={"Content-Type": "audio/wav"},
        )
        assert status == 400
    finally:
        httpd.shutdown()


# ── /api/models + asset traversal ─────────────────────────────────────────────

def test_models_status_reports_resident(monkeypatch, tmp_path):
    _stub_media(monkeypatch)
    httpd, host, port = _start(tmp_path)
    try:
        # Nothing loaded yet → resident is null; the image_models list is reported.
        status, body = _request(host, port, "GET", "/api/models")
        assert status == 200
        payload = json.loads(body)
        assert payload["resident"] is None
        # New shape: ordered image_models with id/label/note/default; flux-schnell first + default.
        ids = [m["id"] for m in payload["image_models"]]
        assert ids == ["flux-schnell", "z-image-turbo", "flux2-klein-4b", "boogu-base"]
        assert payload["image_models"][0]["default"] is True
        assert payload["image_models"][0]["label"] == "FLUX.1-schnell"
        assert sum(m["default"] for m in payload["image_models"]) == 1  # exactly one default
        assert payload["models"]["tts"] == "kokoro-v1.0"

        # After a generation the image model is warm; resident is the model id.
        _request(host, port, "POST", "/api/image",
                 body=json.dumps({"prompt": "warm it"}),
                 headers={"Content-Type": "application/json"})
        _, body2 = _request(host, port, "GET", "/api/models")
        assert json.loads(body2)["resident"] == "flux-schnell"
    finally:
        httpd.shutdown()


def test_post_mission_json_array_body_is_400_not_500(tmp_path):
    """A non-object JSON body (e.g. an array) must be a clean 400 on every route — the
    shared _read_json_body guard prevents the old payload.get-on-a-list 500."""
    httpd, host, port = _start(tmp_path)
    try:
        status, _ = _request(
            host, port, "POST", "/api/mission",
            body=json.dumps([1, 2, 3]), headers={"Content-Type": "application/json"},
        )
        assert status == 400
    finally:
        httpd.shutdown()


def test_media_asset_traversal_blocked(monkeypatch, tmp_path):
    _stub_media(monkeypatch)
    # A secret outside the assets root must never be reachable via /media.
    (tmp_path / "secret.txt").write_text("TOP SECRET", encoding="utf-8")
    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(host, port, "GET", "/media/../../secret.txt")
        assert status == 404
        assert b"TOP SECRET" not in body
    finally:
        httpd.shutdown()
