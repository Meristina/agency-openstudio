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

# Hugging Face repo ids for the hub-managed back-ends, each PINNED to an immutable commit SHA
# (the `*_REVISION` / `*_revision` fields below). HF content-addressing only guarantees the bytes
# match the repo's CURRENT blob — not that the repo still points at the known-good weights reviewed
# on the target Mac. Pinning a 40-hex commit SHA (itself content-addressed) gives those hub weights
# the same supply-chain guarantee the Kokoro SHA-256 manifest gives the direct-URL files
# (docs/SECURITY.md #4/#5), so a force-push or a compromised mirror can't silently swap in different
# weights on the next download.
STT_HF_REPO = "mlx-community/whisper-large-v3-turbo"  # MLX-converted Whisper turbo
STT_HF_REVISION = "a4aaeec0636e6fef84abdcbe3544cb2bf7e9f6fb"

# Image: a non-gated, pre-quantized (8-bit) mflux build of FLUX.1-schnell. The
# official black-forest-labs/FLUX.1-schnell repo is GATED (license + login), so we
# load the ready-to-use mflux-format weights mflux's own docs point to (the
# `dhairyashil/…-mflux-…` repos for mflux >= 0.6.0). 8-bit keeps quality visibly on
# par with full precision (4-bit deviates); Apache-2.0; verified loading + generating
# on the target Mac in Wave 2.4.
IMAGE_MODEL_REPO = "dhairyashil/FLUX.1-schnell-mflux-8bit"

# Portable image checkpoint: SD 1.5 Q4_0 GGUF (single file, CPU-tractable,
# CreativeML-OpenRAIL-M — recorded in docs/LICENSES.md). SDXL-Turbo was rejected:
# its weights are SAI non-commercial, unusable for agency deliverables (FR-011).
# URL pinned to an immutable revision; sha256 is HF's published LFS digest.
SDCPP_MODEL = ModelFile(
    name="stable-diffusion-v1-5-pruned-emaonly-Q4_0.gguf",
    url="https://huggingface.co/second-state/stable-diffusion-v1-5-GGUF/resolve/031b5f5df991f511b3f5fa8fed6d99048ababb69/stable-diffusion-v1-5-pruned-emaonly-Q4_0.gguf",
    sha256="b8944e9fe0b69b36ae1b5bb0185b3a7b8ef14347fe0fa9af6c64c4829022261f",
)
# Whisper large-v3-turbo ggml (same weights family as the MLX default). URL pinned
# to an immutable revision; sha256 is HF's published LFS digest.
WHISPERCPP_MODEL = ModelFile(
    name="ggml-large-v3-turbo.bin",
    url="https://huggingface.co/ggerganov/whisper.cpp/resolve/5359861c739e955e79d9a303bcbc70fb988958b1/ggml-large-v3-turbo.bin",
    sha256="1fc70f774d38eb169993ac391eea357ef47c88757ef72ee5943879b7e8e2bc69",
)


# ── selectable image-model registry ──────────────────────────────────────────
# The user picks one image model per generation. Each entry is a *backend-agnostic*
# descriptor: the GUI-facing metadata (id/label/note/default) plus a ``backend``
# discriminator and the parameters that backend needs to load the model. Most entries
# are ``backend="mflux"`` (the mflux module + class + ModelConfig factory + optional
# model_path override + quantize + default step count); the discriminator keeps the
# registry pluggable, and the live ``backend="boogu"`` entry below proves it — it carries
# its own (base_repo/qwen_repo) params and ModelManager dispatches on the discriminator
# without changing. The three mflux models are non-gated, Apache-2.0, 16 GB-friendly
# (8-bit: schnell via a pre-quantized mirror, klein via ``quantize=8`` on load);
# Boogu is experimental (its own [boogu] extra). All verified live on the target Mac.

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
    revision: "str | None" = None  # immutable commit SHA pinning model_path (None = unpinned)
    quantize: "int | None" = None  # bits to quantize on load (None = repo's native/pre-quantized)
    steps_default: int = 4         # default num_inference_steps for this model
    steps_max: int = 8             # upper bound the API accepts for this model (compute guard)
    # -- boogu backend params (None for mflux entries) --
    base_repo: "str | None" = None  # the Boogu image weights repo (HF)
    qwen_repo: "str | None" = None  # the Qwen3-VL conditioner repo (HF)
    base_revision: "str | None" = None  # immutable commit SHA pinning base_repo
    qwen_revision: "str | None" = None  # immutable commit SHA pinning qwen_repo
    binary: str = ""
    model_file: "ModelFile | None" = None


DEFAULT_IMAGE_MODEL = "flux-schnell"

# Insertion order IS the registry order the API exposes (Py 3.7+ dicts preserve it).
IMAGE_MODELS: "dict[str, ImageModel]" = {
    "flux-schnell": ImageModel(
        id="flux-schnell", label="FLUX.1-schnell", note="Photoreal · 2–4 step",
        backend="mflux", default=True,
        module="mflux.models.flux.variants.txt2img.flux", class_name="Flux1",
        config_factory="schnell",
        model_path=IMAGE_MODEL_REPO,  # schnell's official repo is GATED → use the mirror
        revision="84ce28edf39a0c68b96d95c255620fbb7b8507be",  # pin the third-party mirror
        quantize=None,  # the mirror is already 8-bit — no re-quantization
        steps_default=4, steps_max=8,  # schnell is distilled for 1-4 steps
    ),
    # NOTE: Z-Image-Turbo was evaluated and DROPPED — on the 16 GB M4 it crashes with a
    # Metal GPU timeout (kIOGPUCommandBufferCallbackErrorTimeout) at the first denoise
    # step, even at 256²/4 steps and quantize=8 (mflux's z-image codepath; FLUX-family
    # models run fine). Not 16 GB-viable here, so it is not offered. (Wave 2.4 live test.)
    "flux2-klein-4b": ImageModel(
        id="flux2-klein-4b", label="FLUX.2 Klein 4B", note="Modern · Apache-2.0",
        backend="mflux",
        module="mflux.models.flux2.variants.txt2img.flux2_klein", class_name="Flux2Klein",
        config_factory="flux2_klein_4b",
        # mflux's default repo for this config, named EXPLICITLY (not None) so `revision` pins it —
        # _pinned_repo only applies a pin when both repo and revision are set. Same pattern as
        # flux-schnell: the pinned snapshot resolves to a local path passed as model_path.
        model_path="black-forest-labs/FLUX.2-klein-4B",  # non-gated
        revision="e7b7dc27f91deacad38e78976d1f2b499d76a294",  # pin the reviewed weights (SECURITY.md #4/#5)
        quantize=8,  # quantize the 4B model on load to stay comfortable on 16 GB
        steps_default=4, steps_max=16,  # DISTILLED — high quality in ~4 steps; modest headroom
    ),
    # Experimental: Boogu-Image-0.1 (Apache-2.0, #1 on Qwen-Image-Bench) via the
    # community MLX port (the `[boogu]` extra). Heaviest option — the 10B image model
    # rides a Qwen3-VL-8B conditioner — and SLOW: non-distilled, so it needs many steps
    # (default 16 here; the model recommends ~30 for best quality). Unlike every other
    # model it loads TWO heavyweight models CO-RESIDENT (base + the Qwen3-VL conditioner
    # in one pipeline), so it does NOT fit the 16 GB reference Mac: a live run (#39) swap-
    # thrashed (~19.7 GB swap, no diffusion step after ~9 min) and had to be killed. Treat
    # as **>16 GB only** (needs ~32 GB+, not yet re-validated there). This is why boogu is
    # excluded from the untrusted marker allowlist (assets.MARKER_IMAGE_MODELS). Both weight
    # repos are non-gated.
    "boogu-base": ImageModel(
        id="boogu-base", label="Boogu-Image 0.1 (experimental)",
        note="Highest quality · experimental · needs >16 GB RAM (swap-thrashes on 16 GB)",
        backend="boogu",
        base_repo="mlx-community/Boogu-Image-0.1-Base-4bit",
        qwen_repo="mlx-community/Qwen3-VL-8B-Instruct-4bit",
        base_revision="ce80bab5737cf123a4a60a427a1944559b094d5c",
        qwen_revision="defcdea7cc7a4b0858fea563cbbce171d328e457",
        steps_default=16, steps_max=50,
    ),
    "stable-diffusion-cpp": ImageModel(
        id="stable-diffusion-cpp",
        label="Stable Diffusion (CPU, stable-diffusion.cpp)",
        note="Portable CPU backend · stable-diffusion.cpp",
        backend="sdcpp",
        binary="sd",
        model_file=SDCPP_MODEL,
        steps_default=20,   # SD 1.5 needs ~20 steps (the 4-step default was SDXL-Turbo's)
        steps_max=50,
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


# ── selectable text-embedding registry (Wave 4 — RAG / LocalDocs) ─────────────
# The retriever (agency_studio/rag.py) embeds document chunks and the mission goal
# with ONE of these, loaded via ``mlx_embedding_models`` (MLX-native, MIT) inside the
# ``[studio]`` extra. Each entry is a backend-agnostic descriptor carrying exactly the
# fields ``mlx_embedding_models.EmbeddingModel.__init__`` needs (repo, pooling, normalize,
# max_length, nomic_bert, apply_ln) PLUS the immutable commit SHA that pins the weights
# (same supply-chain guarantee as STT_HF_REVISION / the image mirror pins, SECURITY.md
# #4/#5 — HF host already allowlisted) and the retrieval instruction prefixes some models
# require. Passing the pinned local snapshot dir as EmbeddingModel(model_path=...) gives
# BOTH the revision pin AND the correct per-model pooling (from_registry would re-resolve
# the repo at HEAD, unpinned). All entries are 16 GB-friendly and MIT/Apache; both are in
# mlx_embedding_models' own registry, so the config below matches its known-good values.

@dataclass(frozen=True)
class EmbedModel:
    """One selectable embedding model. The mlx_embedding_models fields load the model;
    ``query_prefix``/``doc_prefix`` are the retrieval instructions a model expects on each
    text (nomic requires ``search_query:`` / ``search_document:``; bge-m3 uses none)."""
    id: str
    label: str            # GUI display name
    note: str             # short one-line descriptor
    repo: str             # HF repo id for the weights
    revision: "str | None"  # immutable commit SHA pinning ``repo`` (None = unpinned)
    ndim: int             # embedding dimensionality (drives the sqlite-vec column width)
    pooling_strategy: str  # "mean" | "first" | "max" — mlx_embedding_models pooling
    max_length: int       # tokenizer truncation length
    normalize: bool = True    # L2-normalize (cosine similarity needs unit vectors)
    nomic_bert: bool = False  # load NomicBert instead of Bert
    apply_ln: bool = False    # nomic-v1.5 applies a final LayerNorm
    query_prefix: str = ""    # prepended to a query before embedding (retrieval instruction)
    doc_prefix: str = ""      # prepended to a document chunk before embedding
    default: bool = False
    backend: str = "mlx"
    gateway_env: str = ""
    gateway_default: str = ""


DEFAULT_EMBED_MODEL = "nomic-text-v1.5"

# Insertion order IS the registry order the API exposes.
EMBED_MODELS: "dict[str, EmbedModel]" = {
    # nomic-embed-text-v1.5 — Apache-2.0, 137M, ~0.4 GB, 768-dim, 8k ctx. Fastest and the
    # lowest-footprint competent retriever on a 16 GB Mac; the ROADMAP's named pick. Needs
    # the search_query:/search_document: task prefixes; applies a final LayerNorm.
    "nomic-text-v1.5": EmbedModel(
        id="nomic-text-v1.5", label="nomic-embed-text v1.5",
        note="Fast · 768-dim · 16 GB-ideal", repo="nomic-ai/nomic-embed-text-v1.5",
        revision="e9b6763023c676ca8431644204f50c2b100d9aab",
        ndim=768, pooling_strategy="mean", max_length=2048,
        nomic_bert=True, apply_ln=True,
        query_prefix="search_query: ", doc_prefix="search_document: ",
        default=True,
    ),
    # bge-m3 — MIT, 568M, ~0.7 GB, 1024-dim, 8k ctx, multilingual. Higher retrieval quality
    # (MTEB 64.5) at ~3× the cost; no instruction prefixes for retrieval.
    "bge-m3": EmbedModel(
        id="bge-m3", label="BGE-M3",
        note="Higher quality · 1024-dim · multilingual", repo="BAAI/bge-m3",
        revision="5617a9f61b028005a4858fdac845db406aefb181",
        ndim=1024, pooling_strategy="first", max_length=8192,
    ),
    "nomic-embed-gguf": EmbedModel(
        id="nomic-embed-gguf",
        label="nomic-embed GGUF (llama.cpp)",
        note="Portable loopback embedding gateway",
        repo="nomic-ai/nomic-embed-text-v1.5-GGUF",
        revision=None,
        ndim=768,
        pooling_strategy="mean",
        max_length=2048,
        backend="llamacpp-gateway",
        gateway_env="AGENCY_STUDIO_EMBED_GATEWAY_URL",
        gateway_default="http://127.0.0.1:8080",
    ),
}


def embed_model(model_id: str) -> EmbedModel:
    """Resolve an embedding-model id to its registry entry. Raises ``ValueError`` on an
    unknown id (the retriever validates before the manager loads; the manager re-validates
    so a direct call can't load an unregistered model)."""
    try:
        return EMBED_MODELS[model_id]
    except KeyError:
        raise ValueError(
            f"unknown embedding model {model_id!r} (known: {sorted(EMBED_MODELS)})"
        ) from None


def embed_models_payload() -> "list[dict]":
    """The ordered ``embed_models`` list for GET /api/models (registry order)."""
    return [
        {"id": m.id, "label": m.label, "note": m.note, "ndim": m.ndim, "default": m.default}
        for m in EMBED_MODELS.values()
    ]


# ── selectable speech registries ─────────────────────────────────────────────
@dataclass(frozen=True)
class SttModel:
    id: str
    label: str
    note: str
    repo: str
    revision: str
    probe_module: str
    default: bool = False
    backend: str = "mlx"
    binary: str = ""
    model_file: "ModelFile | None" = None


@dataclass(frozen=True)
class TtsModel:
    id: str
    label: str
    note: str
    repo: str
    revision: str
    probe_module: str
    default: bool = False


DEFAULT_STT_MODEL = "whisper-large-v3-turbo"
DEFAULT_TTS_MODEL = "kokoro-v1.0"

STT_MODELS: "dict[str, SttModel]" = {
    DEFAULT_STT_MODEL: SttModel(
        id=DEFAULT_STT_MODEL,
        label="Whisper large-v3 turbo",
        note="Local speech-to-text · MLX",
        repo=STT_HF_REPO,
        revision=STT_HF_REVISION,
        probe_module="mlx_whisper",
        default=True,
    ),
    "whisper-cpp": SttModel(
        id="whisper-cpp",
        label="Whisper.cpp (CPU)",
        note="Portable speech-to-text · whisper.cpp",
        repo="ggerganov/whisper.cpp",
        revision="",
        probe_module="",
        backend="whispercpp",
        binary="whisper-cli",
        model_file=WHISPERCPP_MODEL,
    ),
}

TTS_MODELS: "dict[str, TtsModel]" = {
    DEFAULT_TTS_MODEL: TtsModel(
        id=DEFAULT_TTS_MODEL,
        label="Kokoro v1.0",
        note="Local text-to-speech · ONNX",
        repo="kokoro-v1.0",
        revision="",
        probe_module="kokoro_onnx",
        default=True,
    ),
}


def stt_model(model_id: str) -> SttModel:
    try:
        return STT_MODELS[model_id]
    except KeyError:
        raise ValueError(f"unknown STT model {model_id!r} (known: {sorted(STT_MODELS)})") from None


def tts_model(model_id: str) -> TtsModel:
    try:
        return TTS_MODELS[model_id]
    except KeyError:
        raise ValueError(f"unknown TTS model {model_id!r} (known: {sorted(TTS_MODELS)})") from None


def stt_models_payload() -> "list[dict]":
    return [
        {"id": m.id, "label": m.label, "note": m.note, "default": m.default}
        for m in STT_MODELS.values()
    ]


def tts_models_payload() -> "list[dict]":
    return [
        {"id": m.id, "label": m.label, "note": m.note, "default": m.default}
        for m in TTS_MODELS.values()
    ]


# Kokoro-82M v1.0 en-us voices. ``local_media._run_tts_backend`` forces lang="en-us",
# so only the American/British English voices are offered; the default is af_heart.
# /api/tts validates a client-supplied voice against this set (an unknown voice is a
# 400, not forwarded to the backend), and ``ModelManager.synthesize`` re-validates so a
# direct caller can't reach the backend with an unlisted voice. Mirrors the hexgrad/
# Kokoro-82M v1.0 voice list (en only).
ALLOWED_VOICES = frozenset({
    # American English — female
    "af_alloy", "af_aoede", "af_bella", "af_heart", "af_jessica", "af_kore",
    "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
    # American English — male
    "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael",
    "am_onyx", "am_puck", "am_santa",
    # British English — female
    "bf_alice", "bf_emma", "bf_isabella", "bf_lily",
    # British English — male
    "bm_daniel", "bm_fable", "bm_george", "bm_lewis",
})


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
