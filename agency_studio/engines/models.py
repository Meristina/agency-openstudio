"""models — model-file registry + integrity-checked resolution for the [media] extra.

Most Wave-2 weights need no manifest here: ``mflux`` (FLUX.1) and ``mlx-whisper``
pull their tensors from the Hugging Face hub by repo id and rely on HF's own
content-addressed (hashed-blob) cache for integrity. Only **Kokoro-onnx** ships two
plain release files — the ONNX graph and the packed voices — and those we resolve
ourselves, so this module applies the two supply-chain rules from docs/SECURITY.md
to them:

  * #4 — **validate the download URL** (https only, host on an allowlist). A model
    file is never fetched from an arbitrary URL.
  * #5 — **verify the SHA-256** of the downloaded bytes before the file is ever
    handed to a back-end that will load (and execute graph ops over) it.

Weights are cached under the OS cache dir (``~/.cache/agency-studio/models``), never
inside the repo, so nothing here is committable (see .gitignore).

Zero runtime dependencies: the download path is stdlib ``urllib`` + ``hashlib``.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

# Hosts a model file may be downloaded from (SECURITY.md #4). Kokoro-onnx publishes
# its release artifacts on GitHub, which 302-redirects the actual bytes to
# release-assets.githubusercontent.com — so BOTH must be allowlisted (a redirect to
# any other host is refused mid-download, see _AllowlistRedirectHandler). Hugging
# Face is allowed for any direct-URL weight we add later. Anything else is refused.
_ALLOWED_HOSTS = frozenset({
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "huggingface.co",
    "cdn-lfs.huggingface.co",
})

# Hard ceiling on a single model download. Kokoro's files are well under this; the
# bound stops a redirect-to-something-enormous from filling the disk unbounded.
_MAX_DOWNLOAD_BYTES = 1 << 30  # 1 GiB

# How many bytes to pull per read while streaming a download.
_CHUNK = 1 << 20  # 1 MiB

# Per-operation socket timeout. Without it a stalled/half-open connection would hang
# the read forever — and because a model download can run while the ModelManager
# lock is held, an unbounded hang would deadlock the whole multimodal layer.
_DOWNLOAD_TIMEOUT = 60.0  # seconds


@dataclass(frozen=True)
class ModelFile:
    """A single direct-URL model file pinned by URL + SHA-256 (both required).

    The digest is mandatory: a direct-URL weight is never downloaded-then-loaded
    without an integrity check (SECURITY.md #5). Hub-managed weights (mflux,
    mlx-whisper) are NOT ModelFiles — they ride Hugging Face's content-addressed
    cache and need no manifest here.
    """
    name: str
    url: str
    sha256: str


# Kokoro-82M ONNX assets (MIT). SHA-256 digests pinned from a verified download on
# the target Mac (the GitHub release 302-redirects to release-assets.github-
# usercontent.com — both hosts allowlisted; every redirect hop is re-validated).
KOKORO_MODEL = ModelFile(
    name="kokoro-v1.0.onnx",
    url="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    sha256="7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5",
)
KOKORO_VOICES = ModelFile(
    name="voices-v1.0.bin",
    url="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
    sha256="bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
)

# Hugging Face repo ids for the hub-managed back-ends (no manifest needed — HF's
# cache is content-addressed). Centralised here so the model choice lives in one place.
STT_HF_REPO = "mlx-community/whisper-large-v3-turbo"  # MLX-converted Whisper turbo

# Image: a non-gated, pre-quantized (8-bit) mflux build of FLUX.1-schnell. The
# official black-forest-labs/FLUX.1-schnell repo is GATED (license + login), so we
# load the ready-to-use mflux-format weights mflux's own docs point to (the
# `dhairyashil/…-mflux-…` repos for mflux >= 0.6.0). 8-bit keeps quality visibly on
# par with full precision (4-bit deviates); Apache-2.0; verified loading + generating
# on the target Mac in Wave 2.4.
IMAGE_MODEL_REPO = "dhairyashil/FLUX.1-schnell-mflux-8bit"


# ── selectable image-model registry ──────────────────────────────────────────
# The user picks one image model per generation. Each entry is a *backend-agnostic*
# descriptor: the GUI-facing metadata (id/label/note/default) plus a ``backend``
# discriminator and the parameters that backend needs to load the model. Today every
# entry is ``backend="mflux"`` (the mflux module + class + ModelConfig factory +
# optional model_path override + default step count), but the discriminator keeps the
# registry pluggable: a future non-mflux entry (e.g. a "boogu" backend) just sets a
# different ``backend`` and carries its own loader params — ModelManager dispatches on
# the discriminator and never has to be rewritten. All three models below are
# mflux-native, non-gated, Apache-2.0, and 16 GB-friendly; verified live on the Mac.

@dataclass(frozen=True)
class ImageModel:
    """One selectable image model. ``backend`` discriminates the loader family; the
    mflux fields (``module``/``class_name``/``config_factory``/``model_path``) are read
    only by the mflux loader. A non-mflux backend would leave those empty and carry its
    own fields."""
    id: str
    label: str            # GUI display name
    note: str             # short one-line descriptor for the GUI
    backend: str          # loader discriminator: "mflux" today (future: "boogu", …)
    default: bool = False
    # -- mflux backend params --
    module: str = ""               # import module for the mflux class
    class_name: str = ""           # mflux class name in that module
    config_factory: str = ""       # ModelConfig factory method, e.g. "schnell"
    model_path: "str | None" = None  # repo override, or None → mflux's default repo
    steps_default: int = 4         # default num_inference_steps for this model
    steps_max: int = 8             # upper bound the API accepts for this model (compute guard)
    # -- boogu backend params (None for mflux entries) --
    base_repo: "str | None" = None  # the Boogu image weights repo (HF)
    qwen_repo: "str | None" = None  # the Qwen3-VL conditioner repo (HF)


DEFAULT_IMAGE_MODEL = "flux-schnell"

# Insertion order IS the registry order the API exposes (Py 3.7+ dicts preserve it).
IMAGE_MODELS: "dict[str, ImageModel]" = {
    "flux-schnell": ImageModel(
        id="flux-schnell", label="FLUX.1-schnell", note="Photoreal · 2–4 step",
        backend="mflux", default=True,
        module="mflux.models.flux.variants.txt2img.flux", class_name="Flux1",
        config_factory="schnell",
        model_path=IMAGE_MODEL_REPO,  # schnell's official repo is GATED → use the mirror
        steps_default=4, steps_max=8,  # schnell is distilled for 1-4 steps
    ),
    "z-image-turbo": ImageModel(
        id="z-image-turbo", label="Z-Image-Turbo", note="Fast · great text · 8-step",
        backend="mflux",
        module="mflux.models.z_image.variants.z_image", class_name="ZImage",
        config_factory="z_image_turbo",
        model_path=None,  # default Tongyi-MAI/Z-Image-Turbo is non-gated
        steps_default=8, steps_max=16,  # distilled to 8; allow headroom for tuning
    ),
    "flux2-klein-4b": ImageModel(
        id="flux2-klein-4b", label="FLUX.2 Klein 4B", note="Modern · Apache-2.0",
        backend="mflux",
        module="mflux.models.flux2.variants.txt2img.flux2_klein", class_name="Flux2Klein",
        config_factory="flux2_klein_4b",
        model_path=None,  # default black-forest-labs/FLUX.2-klein-4B is non-gated
        steps_default=4, steps_max=50,  # non-distilled "modern" model — allow quality steps
    ),
    # Experimental: Boogu-Image-0.1 (Apache-2.0, #1 on Qwen-Image-Bench) via the
    # community MLX port (the `[boogu]` extra). Heaviest option — the 10B image model
    # rides a Qwen3-VL-8B conditioner — and SLOW (~30 steps; minutes/image on a 16 GB
    # Mac). Validated end-to-end on the target Mac in Wave 2.4. Loaded mutually
    # exclusive like every other model. Both weight repos are non-gated.
    "boogu-base": ImageModel(
        id="boogu-base", label="Boogu-Image 0.1 (experimental)",
        note="Highest quality · slow · experimental",
        backend="boogu",
        base_repo="mlx-community/Boogu-Image-0.1-Base-4bit",
        qwen_repo="mlx-community/Qwen3-VL-8B-Instruct-4bit",
        steps_default=16, steps_max=50,
    ),
}


def image_model(model_id: str) -> ImageModel:
    """Resolve an image-model id to its registry entry. Raises ``ValueError`` on an
    unknown id (the server validates before the manager runs; the manager re-validates
    so a direct call can't load an unregistered model)."""
    try:
        return IMAGE_MODELS[model_id]
    except KeyError:
        raise ValueError(
            f"unknown image model {model_id!r} (known: {sorted(IMAGE_MODELS)})"
        ) from None


def image_models_payload() -> "list[dict]":
    """The ordered ``image_models`` list for GET /api/models (registry order)."""
    return [
        {"id": m.id, "label": m.label, "note": m.note, "default": m.default}
        for m in IMAGE_MODELS.values()
    ]


class IntegrityError(RuntimeError):
    """A downloaded model file failed its pinned SHA-256 check (SECURITY.md #5)."""


def models_dir() -> Path:
    """The local cache directory for direct-URL model files. Overridable via
    ``AGENCY_STUDIO_MODELS_DIR`` (used by tests to point at a tmp path)."""
    override = os.environ.get("AGENCY_STUDIO_MODELS_DIR")
    base = Path(override) if override else Path.home() / ".cache" / "agency-studio" / "models"
    base.mkdir(parents=True, exist_ok=True)
    return base


def validate_url(url: str) -> None:
    """Enforce SECURITY.md #4: https only, host on the allowlist. Raises ``ValueError``
    on anything else, BEFORE any network access."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"refusing non-https model URL: {url!r}")
    if parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError(
            f"refusing model URL from disallowed host {parsed.hostname!r} "
            f"(allowed: {sorted(_ALLOWED_HOSTS)})"
        )


def verify_sha256(path: Path, expected: str) -> None:
    """Enforce SECURITY.md #5: the file's SHA-256 must equal ``expected`` (hex).
    Raises ``IntegrityError`` on mismatch."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    actual = h.hexdigest()
    if actual.lower() != expected.lower():
        raise IntegrityError(
            f"checksum mismatch for {path.name}: expected {expected}, got {actual}"
        )


class _AllowlistRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Re-validate EVERY redirect hop against the host allowlist (SECURITY.md #4).

    The default opener follows 30x redirects to any host, so validating only the
    initial URL is not enough: an allowlisted host (GitHub release URLs 302 by
    design) could bounce the bytes to an arbitrary host. This rejects a redirect to
    a disallowed host before urllib fetches it — the allowlist now governs the bytes
    actually downloaded, not just the URL first asked for.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        validate_url(newurl)  # raises ValueError on a non-allowlisted/non-https hop
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download(url: str, dest: Path) -> None:
    """Stream ``url`` to ``dest`` (https + allowlisted host only, every redirect hop
    re-validated, size-bounded, timeout-bounded).

    Writes to a temp file in the same directory and atomically renames on success,
    so a partial/aborted download never leaves a corrupt file at ``dest``.
    """
    validate_url(url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(_AllowlistRedirectHandler())
    fd, tmp_name = tempfile.mkstemp(dir=str(dest.parent), suffix=".part")
    tmp = Path(tmp_name)
    try:
        # Adopt the fd into a file object FIRST, so it is always closed by this
        # `with` — even if open() below raises before a byte is read. (Opening the
        # response in the same `with` would leak the fd on that failure path.)
        with os.fdopen(fd, "wb") as out:
            total = 0
            # validate_url constrained the initial scheme+host; the redirect handler
            # re-checks every hop, and the timeout stops a stalled read from hanging
            # (and, since downloads can run under the ModelManager lock, deadlocking).
            with opener.open(url, timeout=_DOWNLOAD_TIMEOUT) as resp:  # noqa: S310
                while True:
                    chunk = resp.read(_CHUNK)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > _MAX_DOWNLOAD_BYTES:
                        raise ValueError(f"download exceeded {_MAX_DOWNLOAD_BYTES} bytes: {url}")
                    out.write(chunk)
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink()


def ensure_file(spec: ModelFile) -> Path:
    """Resolve a pinned model file to a local path, integrity-checked EVERY time.

    Cache miss → validate URL, stream the download (redirects re-validated), verify
    SHA-256, expose. Cache hit → still verify the cached file's SHA-256 before
    returning it, so on-disk corruption or post-download tampering is caught on every
    load, not only the first (SECURITY.md #5). A failed check removes the bad file
    and raises ``IntegrityError`` — an unverified file is never handed to a back-end.
    """
    dest = models_dir() / spec.name
    if not dest.exists():
        _download(spec.url, dest)
    try:
        verify_sha256(dest, spec.sha256)
    except IntegrityError:
        dest.unlink(missing_ok=True)  # never leave/return an unverified file
        raise
    return dest


def ensure_kokoro_files() -> "tuple[Path, Path]":
    """Resolve the two Kokoro-onnx files (model graph, voices) to local paths."""
    return ensure_file(KOKORO_MODEL), ensure_file(KOKORO_VOICES)
