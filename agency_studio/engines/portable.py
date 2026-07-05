"""Small stdlib helpers for portable binary/loopback backends."""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from . import models


@dataclass(frozen=True)
class PortableUnavailable(RuntimeError):
    reason: str
    enablement: str

    def __str__(self) -> str:
        return self.enablement


def find_binary(name: str) -> str | None:
    return shutil.which(name)


def require_loopback(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("gateway URL must use http(s)")
    host = (parsed.hostname or "").lower()
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("gateway URL must point at loopback (127.0.0.1, ::1, or localhost)")
    return url.rstrip("/")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        require_loopback(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def get_json(url: str, *, timeout: float = 1.0) -> object:
    require_loopback(url)
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(url, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8") or "{}")


def post_json(url: str, payload: object, *, timeout: float = 30.0) -> object:
    require_loopback(url)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(req, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8") or "{}")


def run_subprocess(argv: list[str], *, timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, text=True, capture_output=True, timeout=timeout, check=True)
    except subprocess.TimeoutExpired as exc:
        raise PortableUnavailable("backend_timeout", f"backend timed out after {timeout:g}s: {argv[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise PortableUnavailable("backend_error", detail or f"backend failed: {argv[0]}") from exc


def join_url(base: str, path: str) -> str:
    return urljoin(require_loopback(base) + "/", path.lstrip("/"))


def verify_model_file(spec: models.ModelFile) -> Path:
    dest = models.models_dir() / spec.name
    hint = f"place {spec.name} from {spec.url} in {models.models_dir()} (sha256 {spec.sha256})"
    if not dest.exists():
        raise PortableUnavailable("missing_model_files", hint)
    try:
        models.verify_sha256(dest, spec.sha256)
    except models.IntegrityError as exc:
        raise PortableUnavailable("model_files_mismatch", f"re-download {spec.name} from {spec.url}") from exc
    return dest
