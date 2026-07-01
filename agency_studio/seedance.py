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

Cloud-only by design
--------------------
Unlike ``visual.py`` (a local MLX default + an optional cloud backend) there is no local video
model — text-to-video does not fit the target Mac, so ``seedance-2.0`` is intrinsically remote.
The backend seam therefore carries a single ``cloud`` triple. The concrete POST + poll +
download is validated live on the network (deferred like Wave 2/5); until then ``_run_cloud``
degrades to a clean ``SeedanceUnavailable`` rather than a silent no-op.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .engines.local_media import MediaUnavailable

# The env var the cloud backend reads its API key from — never a request field, never persisted.
# Absent ⇒ the cloud backend is unavailable (a clean 501, never a silent network attempt).
CLOUD_API_KEY_ENV = "AGENCY_STUDIO_VIDEO_API_KEY"

# Fixed, safe render parameters. Untrusted marker output never chooses compute size / length —
# a long, high-res clip is the expensive tier, so a marker could otherwise weaponise it as a
# cost-DoS. These are the studio's single source of truth for a marker-driven video.
VIDEO_DURATION_SECONDS = 5      # a short clip — the cheap tier
VIDEO_RESOLUTION = "720p"       # not 1080p/4k — untrusted output never picks the pricey size


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
}


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


def _run_cloud(backend, entry: VideoModel, *, prompt: str, out_path: Path) -> None:
    """Render one video from ``prompt`` via the cloud API over https and write the mp4 to
    ``out_path``. The API key is read from the environment at call time (never from ``backend`` /
    disk), never logged. The concrete POST + task-poll + download is network-deferred (validated
    live); until then it raises ``SeedanceUnavailable`` rather than silently produce nothing."""
    key = os.environ.get(CLOUD_API_KEY_ENV)
    if not key:  # defence in depth — _probe_cloud already gated this
        raise SeedanceUnavailable(f"cloud video needs an API key in ${CLOUD_API_KEY_ENV}")
    raise SeedanceUnavailable(
        "live cloud video rendering is validated on the network path (deferred); "
        "the marker + render pipeline is fully wired and offline-tested"
    )


_VIDEO_BACKENDS = {
    "cloud": (_probe_cloud, _load_cloud, _run_cloud),
}


def _backend(entry: VideoModel):
    """The ``(probe, load, run)`` triple for a model's backend — mirrors ``visual._backend``.
    ``ValueError`` on an unknown backend name."""
    try:
        return _VIDEO_BACKENDS[entry.backend]
    except KeyError:
        raise ValueError(f"unknown video backend '{entry.backend}'") from None
