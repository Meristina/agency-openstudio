import subprocess

import pytest

from agency_studio.engines import models, portable


def test_require_loopback_accepts_local_http_urls():
    assert portable.require_loopback("http://127.0.0.1:8080") == "http://127.0.0.1:8080"
    assert portable.require_loopback("http://localhost:8080/x") == "http://localhost:8080/x"
    assert portable.require_loopback("http://[::1]:8080") == "http://[::1]:8080"


@pytest.mark.parametrize("url", ["ftp://127.0.0.1/x", "http://example.com", "https://192.168.1.10"])
def test_require_loopback_rejects_non_loopback_or_non_http(url):
    with pytest.raises(ValueError):
        portable.require_loopback(url)


def test_run_subprocess_timeout_is_reason_coded(monkeypatch):
    def boom(*a, **k):
        raise subprocess.TimeoutExpired(["x"], 1)

    monkeypatch.setattr(portable.subprocess, "run", boom)
    with pytest.raises(portable.PortableUnavailable) as exc:
        portable.run_subprocess(["x"], timeout=1)
    assert exc.value.reason == "backend_timeout"


def test_verify_model_file_reason_codes(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENCY_STUDIO_MODELS_DIR", str(tmp_path))
    spec = models.ModelFile("m.bin", "https://huggingface.co/x/y", "00")
    with pytest.raises(portable.PortableUnavailable) as missing:
        portable.verify_model_file(spec)
    assert missing.value.reason == "missing_model_files"

    (tmp_path / "m.bin").write_bytes(b"x")
    with pytest.raises(portable.PortableUnavailable) as mismatch:
        portable.verify_model_file(spec)
    assert mismatch.value.reason == "model_files_mismatch"


def test_find_binary_is_single_stub_point(monkeypatch):
    monkeypatch.setattr(portable.shutil, "which", lambda name: f"/bin/{name}")
    assert portable.find_binary("sd") == "/bin/sd"
