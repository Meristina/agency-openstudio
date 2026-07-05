"""seedance — cloud video as a department deliverable (Wave 6, the seedance brick).

The Wave-3 asset pipeline lets a department render a *local* multimodal deliverable — a
marketing image (FLUX), a comms narration (Kokoro) — from a fenced ```asset marker in the
mission's ``delivered`` text. Seedance adds one more asset type, ``video``, but it is the
studio's FIRST *cloud* asset modality: text-to-video is far beyond a 16 GB Mac, so the render
is an off-machine API call (seedance-2.0). Everything else is reused: the video rides the same
``assets.parse_markers`` → ``assets.render`` → ``assets.rewrite_delivered`` pipeline and the
same shipped ``asset_clause`` / ``render_assets`` engine hooks — **zero new agency-kit surface**,
exactly like visual RAG rode ``context_clause``.

Why the security model is stricter than every other brick
----------------------------------------------------------
Brick 4's cloud VLM only ever runs at INGEST time, on an image the user picked and explicitly
consented to upload — a mission never touches the network. A *video* marker is different: it is
emitted by a department (MODEL OUTPUT — untrusted) and rendered DURING a mission. Left ungated,
an untrusted marker alone could trigger an off-machine call mid-mission — breaking the studio's
"a mission never touches the network by default" invariant. So video is **triple-gated**:

  1. a per-mission ``video`` opt-in flag (default off) — without it ``assets.parse_markers``
     drops every video marker before it is ever built, so the mission is byte-identical to today;
  2. an env-only API key (``AGENCY_STUDIO_VIDEO_API_KEY``) — read at call time, never a request
     field, never persisted, never logged, never returned by an endpoint;
  3. an https-only endpoint (SECURITY.md #4).

All three must hold for a single byte to leave the machine. The marker itself never chooses the
model tier, duration, or resolution — those are the parser's fixed safe caps (assets.py), so an
untrusted marker can't weaponise an expensive/long render as a cost-DoS.

Cloud by default, local since the OpenMontage fusion
----------------------------------------------------
Text-to-*footage* generation does not fit the target Mac, so ``seedance-2.0`` (cloud) stays
the default. But the OpenMontage fusion added a genuinely LOCAL alternative — *composition*
video (animated text/stat scenes) rendered by ``openmontage/remotion-composer`` across a
subprocess boundary (``openmontage_backend.py``, the ``local`` triple, resolved lazily in
``_backend``). Select it per-install with ``AGENCY_STUDIO_VIDEO_BACKEND=openmontage-remotion``
— zero server/GUI change, the ``make_extractor`` pattern. The cloud POST + poll + download is
still validated live on the network (deferred like Wave 2/5); until then ``_run_cloud``
degrades to a clean ``SeedanceUnavailable`` rather than a silent no-op.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from .engines.local_media import MediaUnavailable

# The env var the cloud backend reads its API key from — never a request field, never persisted.
# Absent ⇒ the cloud backend is unavailable (a clean 501, never a silent network attempt).
CLOUD_API_KEY_ENV = "AGENCY_STUDIO_VIDEO_API_KEY"
# Optional override for the remote model id — Volcengine Ark model/endpoint ids are account- and
# region-specific (e.g. a ``doubao-seedance-…`` id or an ``ep-…`` endpoint id), so the registry's
# generic ``api_model`` can be pointed at the user's real model WITHOUT a code change. Still not a
# request field — env-only, like the key.
CLOUD_MODEL_ENV = "AGENCY_STUDIO_VIDEO_MODEL"

# Fixed, safe render parameters. Untrusted marker output never chooses compute size / length —
# a long, high-res clip is the expensive tier, so a marker could otherwise weaponise it as a
# cost-DoS. These are the studio's single source of truth for a marker-driven video.
VIDEO_DURATION_SECONDS = 5      # a short clip — the cheap tier
VIDEO_RESOLUTION = "720p"       # not 1080p/4k — untrusted output never picks the pricey size

# Network bounds for the async render (create task → poll → download). A 5 s 720p clip renders
# fast; the poll ceiling is a safety net so a stuck/rejected task can't hang a mission forever.
_HTTP_TIMEOUT = 60             # seconds per HTTP request
_POLL_INTERVAL = 5            # seconds between task-status polls
_POLL_MAX_ATTEMPTS = 120     # ~10 min ceiling (120 × 5 s) before giving up

# Hard ceiling on the downloaded clip. A 5 s 720p mp4 is a few MB; this stops a hostile/broken
# video_url from streaming an unbounded body into memory + disk on the 16 GB Mac.
_MAX_VIDEO_BYTES = 200 * 1024 * 1024  # 200 MiB
_DOWNLOAD_CHUNK = 1 << 20             # 1 MiB per read while streaming


class SeedanceUnavailable(MediaUnavailable):
    """Raised when the cloud-video render path is unavailable — the API key is absent, or the
    live network call is not yet wired. An ``ImportError`` subclass (via ``MediaUnavailable``) so
    the server's optional-extra handler maps it to a 501 + hint, exactly like ``VisualUnavailable``
    / ``KnowledgeUnavailable``. Only a render can raise it; a mission that doesn't opt into video
    never touches this module."""


# ── the video model registry (self-contained; mirrors visual.VISUAL_MODELS) ───────
@dataclass(frozen=True)
class VideoModel:
    id: str
    label: str
    backend: str                # "cloud" (API, off-machine) — the only backend for now
    endpoint: str = ""          # cloud: the https API endpoint
    api_model: str = ""         # cloud: the remote model id
    default: bool = False


DEFAULT_VIDEO_MODEL = "seedance-2.0"

# Per-install backend selector (the knowledge.make_extractor pattern): name a registry id in
# the env to change which video model a marker-driven render uses — the marker itself still
# never chooses. Unset ⇒ DEFAULT_VIDEO_MODEL; an unknown name fails loud at render time.
VIDEO_BACKEND_ENV = "AGENCY_STUDIO_VIDEO_BACKEND"

# The concrete endpoint + request surface are validated live on the network (deferred like
# Wave 2/5). Until then the cloud backend degrades to SeedanceUnavailable. The endpoint is
# https (enforced by _probe_cloud); a marker never names a model, so this registry is the only
# place a video model id is chosen.
VIDEO_MODELS: "dict[str, VideoModel]" = {
    "seedance-2.0": VideoModel(
        id="seedance-2.0", label="Seedance 2.0 (cloud API, off-machine)", backend="cloud",
        endpoint="https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks",
        api_model="seedance-2-0", default=True,
    ),
    # The OpenMontage fusion's local backend — composition video (Remotion) rendered fully
    # on-machine by openmontage/remotion-composer across a subprocess boundary. No endpoint,
    # no key: its probe gates on node/npx + the vendored subtree (openmontage_backend.py).
    "openmontage-remotion": VideoModel(
        id="openmontage-remotion", label="OpenMontage Remotion (local, on-machine)",
        backend="local",
    ),
}


def default_video_model() -> str:
    """The registry id a model-less render resolves to: ``$AGENCY_STUDIO_VIDEO_BACKEND`` when
    set (fail-loud on an unknown name — a typo must not silently fall back to a cloud call),
    else ``DEFAULT_VIDEO_MODEL``. The env is read at call time, like the API key."""
    name = (os.environ.get(VIDEO_BACKEND_ENV) or "").strip()
    if not name:
        from . import capabilities
        return capabilities.resolve("video")
    if name not in VIDEO_MODELS:
        raise ValueError(
            f"unknown {VIDEO_BACKEND_ENV}={name!r} — available: {', '.join(VIDEO_MODELS)}"
        )
    return name


def video_model(model_id: str) -> VideoModel:
    """Resolve a registry entry by id, ``ValueError`` on unknown (the known set is listed) — the
    same validate-before-load contract as ``visual.visual_model`` / ``models.image_model``."""
    try:
        return VIDEO_MODELS[model_id]
    except KeyError:
        raise ValueError(
            f"unknown video model '{model_id}' — available: {', '.join(VIDEO_MODELS)}"
        ) from None


# ── the cloud backend seam (probe / load / run; the network call is stubbed offline) ──
# Module-level so the offline suite can stub the boundary (like visual._run_cloud) — the live
# network POST is the deferred surface.
def _probe_cloud(entry: VideoModel) -> None:
    """Availability + safety gate for the cloud backend. Enforces https on the endpoint
    (SECURITY.md #4) and that the API key is present in the environment (never a request field).
    Absent key ⇒ ``SeedanceUnavailable`` — a clean error, NEVER a silent network attempt. Run
    before any eviction, so a missing key can't destroy a warm model."""
    if urlparse(entry.endpoint).scheme != "https":
        raise ValueError(f"video cloud endpoint must be https — got {entry.endpoint!r}")
    if not os.environ.get(CLOUD_API_KEY_ENV):
        raise SeedanceUnavailable(
            f"cloud video needs an API key in ${CLOUD_API_KEY_ENV} (off-machine, opt-in)"
        )


def _load_cloud(entry: VideoModel):
    """A lightweight https client descriptor bound to the endpoint. No weights, no residency cost
    — but it still flows through the manager's residency seam so eviction/warm-chip logic needs no
    special case (mirrors ``visual._load_cloud``). The concrete client/SDK is validated live."""
    return {"endpoint": entry.endpoint, "api_model": entry.api_model, "key_env": CLOUD_API_KEY_ENV}


# ── the raw network primitives (isolated so the offline suite monkeypatches them) ──
class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse HTTP redirects on the AUTHENTICATED API calls.

    The bearer key rides the ``Authorization`` header; urllib's default redirect handler
    replays every request header on a 30x — so a redirect could bounce the key to another
    host, or to plain ``http:`` (a downgrade), leaking it in cleartext. The Ark task API
    answers directly, so a redirect is unexpected: treat it as an error rather than follow
    it and forward the credential."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        raise urllib.error.HTTPError(
            req.full_url, code,
            f"seedance: refusing redirect to {newurl!r} (would forward the API key)",
            headers, fp,
        )


class _HttpsOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Allow redirects on the UNauthenticated download (a CDN may 302 the media URL), but
    re-validate https on EVERY hop so the initial-URL check can't be bypassed by a
    downgrade to http mid-chain."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        if urlparse(newurl).scheme != "https":
            raise urllib.error.HTTPError(
                req.full_url, code, f"seedance: refusing non-https redirect to {newurl!r}",
                headers, fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


# Openers built once. The authenticated calls never follow a redirect; the download follows
# only https→https hops.
_API_OPENER = urllib.request.build_opener(_NoRedirectHandler())
_DOWNLOAD_OPENER = urllib.request.build_opener(_HttpsOnlyRedirectHandler())


def _http_post_json(url: str, payload: dict, key: str) -> dict:
    """POST ``payload`` as JSON with a bearer key, return the parsed JSON response. The key rides
    the Authorization header only — never the body, never logged (urllib errors carry the URL/status
    but not request headers). Redirects are refused so the key can't be forwarded off the endpoint."""
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with _API_OPENER.open(req, timeout=_HTTP_TIMEOUT) as resp:  # nosec - https enforced by _probe_cloud, no redirects
        return json.loads(resp.read().decode("utf-8"))


def _http_get_json(url: str, key: str) -> dict:
    """GET a JSON resource with a bearer key → parsed JSON. Redirects are refused (see
    ``_NoRedirectHandler``) so the key never leaves the endpoint host/scheme."""
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with _API_OPENER.open(req, timeout=_HTTP_TIMEOUT) as resp:  # nosec - https enforced upstream, no redirects
        return json.loads(resp.read().decode("utf-8"))


def _http_download(url: str, out_path: Path,
                   should_cancel: "Callable[[], bool] | None" = None) -> None:
    """Download ``url`` (an https media URL from the API response) to ``out_path``, streaming in
    chunks with a hard byte ceiling (``_MAX_VIDEO_BYTES``) so an oversized/broken URL can't fill
    RAM+disk. https is enforced on the initial URL AND every redirect hop (no auth header rides
    this request, so following a CDN 302 is safe as long as it stays https).

    Writes to a ``.part`` temp file in the same directory and atomically renames on success, so a
    truncated/aborted download (a mid-stream error, the size cap, or a ``should_cancel`` abort)
    NEVER leaves a partial .mp4 at ``out_path`` — it is always complete or absent. ``should_cancel``
    (optional) is polled per chunk so a "Stop mission" aborts a slow download promptly."""
    if urlparse(url).scheme != "https":
        raise RuntimeError("seedance: refusing a non-https video_url")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(out_path.parent), suffix=".part")
    tmp = Path(tmp_name)
    try:
        # Adopt the fd FIRST so it is always closed by this `with` — even if .open() below raises.
        with os.fdopen(fd, "wb") as out:
            with _DOWNLOAD_OPENER.open(url, timeout=_HTTP_TIMEOUT) as resp:  # nosec - https checked here + each hop
                total = 0
                while True:
                    if should_cancel is not None and should_cancel():
                        raise RuntimeError("seedance: download cancelled")
                    chunk = resp.read(_DOWNLOAD_CHUNK)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > _MAX_VIDEO_BYTES:
                        raise RuntimeError(f"seedance: video exceeded {_MAX_VIDEO_BYTES} bytes")
                    out.write(chunk)
        tmp.replace(out_path)  # atomic: out_path is complete or absent, never truncated
    finally:
        if tmp.exists():
            tmp.unlink()  # a failed/aborted download leaves no partial behind


def _run_cloud(backend, entry: VideoModel, *, prompt: str, out_path: Path,
               should_cancel: "Callable[[], bool] | None" = None) -> None:
    """Render one video from ``prompt`` via the seedance cloud API (Volcengine Ark) over https and
    write the mp4 to ``out_path``. Three network steps: POST create-task → poll the task until it
    succeeds → download the resulting video_url. The API key is read from the environment at call
    time (never from ``backend`` / disk), never logged. Duration/resolution are the fixed safe caps
    — the (untrusted) marker text is ONLY the prompt, never the compute size. A runtime API/network
    failure propagates as a ``RuntimeError`` (→ the render bridge writes a ``_[video unavailable]_``
    placeholder), an absent key as ``SeedanceUnavailable`` (→ 501). ``should_cancel`` (optional) is
    polled each iteration so a "Stop mission" aborts the up-to-~10-min poll promptly instead of
    waiting out the budget."""
    key = os.environ.get(CLOUD_API_KEY_ENV)
    if not key:  # defence in depth — _probe_cloud already gated this
        raise SeedanceUnavailable(f"cloud video needs an API key in ${CLOUD_API_KEY_ENV}")
    endpoint = backend["endpoint"]
    api_model = os.environ.get(CLOUD_MODEL_ENV) or backend["api_model"]
    # 1. create the async render task (fixed safe caps — the marker never chooses tier/size/length)
    created = _http_post_json(endpoint, {
        "model": api_model,
        "content": [{"type": "text", "text": prompt}],
        "resolution": VIDEO_RESOLUTION,
        "duration": VIDEO_DURATION_SECONDS,
    }, key)
    task_id = created.get("id")
    if not task_id:
        raise RuntimeError(f"seedance: create-task response carried no task id ({sorted(created)})")
    # 2. poll until the task reaches a terminal state
    poll_url = f"{endpoint}/{task_id}"
    for _ in range(_POLL_MAX_ATTEMPTS):
        if should_cancel is not None and should_cancel():
            raise RuntimeError("seedance: render cancelled")
        time.sleep(_POLL_INTERVAL)
        status_body = _http_get_json(poll_url, key)
        status = (status_body.get("status") or "").lower()
        if status == "succeeded":
            video_url = (status_body.get("content") or {}).get("video_url")
            if not video_url:
                raise RuntimeError("seedance: task succeeded but carried no video_url")
            _http_download(video_url, out_path, should_cancel)  # 3. download the mp4 (https-checked)
            return
        if status in ("failed", "rejected", "canceled", "cancelled"):
            raise RuntimeError(f"seedance render {status}: {status_body.get('error') or 'no detail'}")
    raise RuntimeError(f"seedance: task {task_id} did not finish within the poll budget")


_VIDEO_BACKENDS = {
    "cloud": (_probe_cloud, _load_cloud, _run_cloud),
}


def _backend(entry: VideoModel):
    """The ``(probe, load, run)`` triple for a model's backend — mirrors ``visual._backend``.
    ``local`` (the OpenMontage fusion) resolves lazily so this module stays import-light and
    self-contained when only the cloud path is exercised. ``ValueError`` on an unknown name."""
    if entry.backend == "local":
        from . import openmontage_backend  # lazy — subprocess-boundary module, stdlib-only
        return (
            openmontage_backend._probe_local,
            openmontage_backend._load_local,
            openmontage_backend._run_local,
        )
    try:
        return _VIDEO_BACKENDS[entry.backend]
    except KeyError:
        raise ValueError(f"unknown video backend '{entry.backend}'") from None
