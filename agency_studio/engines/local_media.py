"""local_media — local multimodal inference on Apple Silicon (Metal).

Wave 2 gives the studio creative *hands*, all running locally on the Mac, nothing
leaving the machine:

  * **image** — FLUX.1-schnell via ``mflux`` (MLX-native, 2-4 step, fast + high quality)
  * **speech-to-text** — Whisper large-v3-turbo via ``mlx-whisper``
  * **text-to-speech** — Kokoro-82M via ``kokoro-onnx``

None of these are core dependencies. They live in the optional ``[media]`` extra and
are imported **lazily**, inside the back-end functions — so the stdlib server boots
and missions run with the extra absent. A multimodal request with the extra missing
raises ``MediaUnavailable``, which the server maps to HTTP 501 + install guidance
(mirroring the ``[pdf]`` export path).

Memory model — why this is simple, not fearful
------------------------------------------------
The heavy reasoning ("brain") runs REMOTELY via the Claude CLI subscription, so it
never occupies local RAM. On this machine only the multimodal models compete for
memory, and they are small relative to a 16 GB Mac. So the design optimises for
SPEED: a model is loaded once and kept **warm** for fast repeat calls. The single
``ModelManager`` keeps at most one model resident and evicts the previous one only
when you switch model (e.g. image → voice). A lock serialises GPU/Metal use across
the threaded HTTP server so two requests never stomp on the same device.
"""

from __future__ import annotations

import gc
import importlib
import random
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from . import models


class MediaUnavailable(ImportError):
    """A multimodal back-end could not be imported — the ``[media]`` extra is not
    installed. Subclasses ``ImportError`` ON PURPOSE: the server's 501 mapping for
    optional extras is ``except ImportError`` (see the [pdf] export path in
    server.py), so the media routes return the same clean 501 + install hint without
    a bespoke except clause. Carries an actionable install hint."""


_INSTALL_HINT = "install the multimodal extra:  pip install 'agency-studio[media]'"


# ── result types ────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ImageResult:
    path: Path
    prompt: str
    seed: int
    seconds: float
    model: str


@dataclass(frozen=True)
class TranscriptResult:
    text: str
    seconds: float


@dataclass(frozen=True)
class SpeechResult:
    path: Path
    voice: str
    seconds: float


# ── back-end adapters (lazy, defensive, monkeypatchable) ──────────────────────
# Split into three roles so the ModelManager can keep memory safe AND fail fast:
#   _probe_*  — CHEAP import check (raises MediaUnavailable if the [media] extra is
#               absent), loading NO weights and touching NO network. Run BEFORE
#               evicting the warm model, so a missing extra can't destroy a good
#               model that was working.
#   _load_*   — the heavy load (weights into memory / file downloads); the warm
#               object the manager holds.
#   _run_*    — one inference call on a loaded model.
# All are module-level so tests monkeypatch them with stubs — the suite never
# touches real MLX, real weights, or the network.

def _pinned_repo(repo: "str | None", revision: "str | None") -> "str | None":
    """Resolve a HF ``repo`` to a local snapshot dir pinned to an immutable commit SHA, so
    a backend that takes a repo id (mflux ``model_path``, mlx_whisper ``path_or_hf_repo``)
    loads the exact reviewed weights even if the repo later moves/force-pushes. A falsy
    ``revision`` (or ``repo``) returns the input unchanged — no pin, current behaviour.
    Uses huggingface_hub (already pulled in by the media backends)."""
    if not repo or not revision:
        return repo
    from huggingface_hub import snapshot_download
    return snapshot_download(repo, revision=revision)


def _resolve_mflux(entry: "models.ImageModel"):
    """Resolve the (class, ModelConfig factory) an mflux entry names — exactly the
    symbols ``_mflux_load`` needs — importing NO weights. A missing/renamed module,
    class, or factory raises MediaUnavailable (the server maps it to 501). Shared by
    probe and load so the two can never drift apart (the probe-before-evict invariant)."""
    try:
        cls = getattr(importlib.import_module(entry.module), entry.class_name)
        from mflux.models.common.config import ModelConfig
        config_factory = getattr(ModelConfig, entry.config_factory)
    except (ImportError, AttributeError) as exc:
        raise MediaUnavailable(f"image generation needs mflux — {_INSTALL_HINT}") from exc
    return cls, config_factory


def _mflux_probe(entry: "models.ImageModel") -> None:
    # Validate the SAME symbols _mflux_load resolves, loading no weights — so a missing
    # class/factory fails the cheap probe (→ 501) BEFORE the warm model is evicted.
    _resolve_mflux(entry)


def _mflux_load(entry: "models.ImageModel"):
    """Construct an mflux model from its registry entry: the named class + ModelConfig
    factory, with the entry's ``model_path`` override (None → mflux's default non-gated
    repo) and ``quantize`` (None for an already-pre-quantized mirror like flux-schnell;
    8 for the full-precision default repos so a 6B/4B model fits the 16 GB Mac)."""
    cls, config_factory = _resolve_mflux(entry)
    model_path = _pinned_repo(entry.model_path, entry.revision)  # pin the mirror; None → mflux default
    return cls(model_config=config_factory(), model_path=model_path, quantize=entry.quantize)


def _mflux_run(model, entry, *, prompt, steps, seed, width, height, out_path) -> None:
    # The three mflux generators share generate_image(seed, prompt,
    # num_inference_steps, width, height) — verified live on the target Mac — so one
    # run adapter serves every mflux image model.
    image = model.generate_image(
        seed=seed, prompt=prompt,
        num_inference_steps=steps, width=width, height=height,
    )
    image.save(path=str(out_path))


# ── boogu backend (experimental, the [boogu] extra) ──────────────────────────
# Boogu-Image-0.1 via the community MLX port (boogu_image_mlx) + a Qwen3-VL
# conditioner (mlx-vlm). Heaviest + slowest image option; isolated behind its own
# extra and dispatch so it never touches the lean mflux path.
_BOOGU_HINT = "install the Boogu extra:  pip install 'agency-studio[boogu]'"


def _boogu_probe(entry: "models.ImageModel") -> None:
    # Validate the SAME symbols _boogu_load uses — the real pipeline class (the WIP
    # port can drift) + the Qwen3-VL runtime + huggingface_hub — loading no weights, so
    # a moved/renamed symbol fails the probe (→ MediaUnavailable/501) BEFORE eviction,
    # not after with a raw 500. Catch AttributeError too (a renamed class import-resolves
    # the module but not the attr).
    try:
        from boogu_image_mlx.pipeline_mlx import BooguImagePipeline  # noqa: F401
        import mlx_vlm  # noqa: F401  (Qwen3-VL conditioner)
        import huggingface_hub  # noqa: F401  (snapshot_download in _boogu_load)
    except (ImportError, AttributeError) as exc:
        raise MediaUnavailable(f"Boogu image generation needs the [boogu] extra — {_BOOGU_HINT}") from exc


def _boogu_load(entry: "models.ImageModel"):
    """Resolve both weight repos to local dirs and build the Boogu pipeline."""
    from boogu_image_mlx.pipeline_mlx import BooguImagePipeline
    from huggingface_hub import snapshot_download
    base = snapshot_download(entry.base_repo, revision=entry.base_revision)
    qwen = snapshot_download(entry.qwen_repo, revision=entry.qwen_revision)
    return BooguImagePipeline.from_pretrained(base, qwen)


def _boogu_run(pipe, entry, *, prompt, steps, seed, width, height, out_path) -> None:
    import numpy as np
    from PIL import Image
    arr = np.asarray(pipe.generate(
        prompt, height=height, width=width, steps=steps, guidance=3.5, seed=seed,
    ))
    if arr.ndim == 4:  # drop a leading batch dim if present
        arr = arr[0]
    if np.issubdtype(arr.dtype, np.floating):
        # Diffusion pipelines emit a normalized [0,1] float image; clip (numerical
        # overshoot like 1.02 is just noise) and scale. Don't guess [0,255]-by-max:
        # a [0,1] image with one pixel >1.0 would otherwise collapse to near-black.
        arr = (arr.clip(0, 1) * 255).round().astype("uint8")
    else:  # already integer pixels
        arr = arr.clip(0, 255).astype("uint8")
    Image.fromarray(arr).save(str(out_path))


# Image-backend dispatch table keyed by the registry's ``backend`` discriminator. Each
# entry is a (probe, load, run) triple. Adding a backend is a new triple here + rows in
# the registry — ModelManager and the routes stay untouched.
_IMAGE_BACKENDS: "dict[str, tuple[Callable, Callable, Callable]]" = {
    "mflux": (_mflux_probe, _mflux_load, _mflux_run),
    "boogu": (_boogu_probe, _boogu_load, _boogu_run),
}


def _image_backend(entry: "models.ImageModel") -> "tuple[Callable, Callable, Callable]":
    try:
        return _IMAGE_BACKENDS[entry.backend]
    except KeyError:
        raise MediaUnavailable(
            f"unknown image backend {entry.backend!r} — {_INSTALL_HINT}"
        ) from None


def _probe_image(entry: "models.ImageModel") -> None:
    """Cheap availability probe for the model's backend (run BEFORE eviction)."""
    _image_backend(entry)[0](entry)


def _load_image_backend(entry: "models.ImageModel"):
    """Heavy load of the selected image model via its backend's loader."""
    return _image_backend(entry)[1](entry)


def _run_image_backend(entry: "models.ImageModel", model, *, prompt, steps, seed, width, height, out_path) -> None:
    """One inference call, dispatched to the model's backend run adapter."""
    _image_backend(entry)[2](model, entry, prompt=prompt, steps=steps, seed=seed,
                             width=width, height=height, out_path=out_path)


def _probe_stt() -> None:
    try:
        import mlx_whisper  # noqa: F401
    except ImportError as exc:
        raise MediaUnavailable(f"speech-to-text needs mlx-whisper — {_INSTALL_HINT}") from exc


def _load_stt_backend():
    """STT 'model' is the ``mlx_whisper`` module itself; the turbo weights are fetched +
    cached by HF on first ``transcribe``, pinned to ``STT_HF_REVISION`` (see
    ``_run_stt_backend``) so the resolved commit can't silently move."""
    import mlx_whisper
    return mlx_whisper


def _run_stt_backend(mlx_whisper, *, audio_path) -> str:
    repo = _pinned_repo(models.STT_HF_REPO, models.STT_HF_REVISION)  # pin the turbo weights
    result = mlx_whisper.transcribe(str(audio_path), path_or_hf_repo=repo)
    return (result.get("text") or "").strip()


def _probe_tts() -> None:
    # Gate BOTH the TTS dependencies up front (one altitude): if either is missing,
    # fail before any weight download or model load — never leave a warm-but-useless
    # Kokoro that can load yet can't write its output.
    try:
        import kokoro_onnx  # noqa: F401
    except ImportError as exc:
        raise MediaUnavailable(f"text-to-speech needs kokoro-onnx — {_INSTALL_HINT}") from exc
    try:
        import soundfile  # noqa: F401
    except ImportError as exc:
        raise MediaUnavailable(f"text-to-speech needs soundfile — {_INSTALL_HINT}") from exc


def _load_tts_backend():
    from kokoro_onnx import Kokoro
    model_path, voices_path = models.ensure_kokoro_files()
    return Kokoro(str(model_path), str(voices_path))


def _run_tts_backend(kokoro, *, text, voice, out_path) -> None:
    import soundfile as sf
    samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
    sf.write(str(out_path), samples, sample_rate)


def _free_metal_cache() -> None:
    """Best-effort release of MLX's Metal buffer cache after evicting a model, so the
    freed weights actually return to the OS (critical on a 16 GB Mac — a stale buffer
    cache could OOM the next load). The API moved between MLX versions, so try each
    spelling and move on if one raises; ignore absence (MLX may not be installed)."""
    gc.collect()
    try:
        import mlx.core as mx
    except ImportError:
        return
    for clear in (getattr(mx, "clear_cache", None), getattr(getattr(mx, "metal", None), "clear_cache", None)):
        if callable(clear):
            try:
                clear()
                return  # only stop once a spelling actually succeeded
            except Exception:
                continue


# ── the manager ───────────────────────────────────────────────────────────────
TTS_DEFAULT_VOICE = "af_heart"


class ModelManager:
    """Single-resident, warm holder for the local multimodal models.

    At most one model is loaded at a time; loading a different one evicts the
    current one first (and frees its Metal buffers). A lock serialises the actual
    inference so the threaded server can't run two generations on the device at once.
    Repeat calls of the SAME kind reuse the warm model — that's the fast path.
    """

    def __init__(self, assets_dir: "str | Path"):
        self._assets = Path(assets_dir)
        self._lock = threading.Lock()
        self._resident: Optional[str] = None
        self._model = None

    # -- model residency (caller holds self._lock) -----------------------------
    def _ensure(self, key: str, probe: Callable[[], None], loader: Callable[[], object]) -> object:
        """Make the model identified by ``key`` warm and return it. ``key`` is a model
        id ('flux-schnell', 'flux2-klein-4b', …) or a modality ('stt'/'tts'). Switching
        keys (image↔voice OR image↔image) evicts the previous model first; the same key
        is a warm hit."""
        if self._resident == key and self._model is not None:
            return self._model  # warm hit
        # Probe the new back-end's availability FIRST (cheap import, no weights). If
        # the extra is missing this raises MediaUnavailable here — before we evict —
        # so a request for an uninstalled modality never destroys a working warm model.
        probe()
        if self._model is not None:
            self._evict()  # at most one model resident (16 GB): evict on any switch
        self._model = loader()
        self._resident = key
        return self._model

    def _evict(self) -> None:
        self._model = None
        self._resident = None
        _free_metal_cache()

    @property
    def resident(self) -> Optional[str]:
        """The currently-warm model key: an image-model id ('flux-schnell', …), or
        ``'stt'`` / ``'tts'``, or ``None``. Drives the GUI's model panel + /api/models."""
        return self._resident

    # Back-compat alias: earlier code/tests referred to the warm slot as resident_kind.
    @property
    def resident_kind(self) -> Optional[str]:
        return self._resident

    def _asset_path(self, sub: str, ext: str, out_dir: "str | Path | None" = None) -> Path:
        # ``out_dir`` (Wave 3 per-mission writer) overrides the manager's default assets
        # dir so a mission's assets land under studio_assets/missions/<id>/. Filenames stay
        # uuid-only (traversal-safe); the marker parser already dropped any path/filename
        # field, so out_dir is only ever a trusted caller-supplied dir (the server scopes it
        # under the served assets root — the manager does not re-validate a trusted path).
        base = Path(out_dir) if out_dir is not None else self._assets
        directory = base / sub
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{uuid.uuid4().hex}.{ext}"

    # -- operations -------------------------------------------------------------
    def generate_image(
        self, prompt: str, *, model: str = models.DEFAULT_IMAGE_MODEL,
        steps: Optional[int] = None, seed: Optional[int] = None,
        width: int = 1024, height: int = 1024,
        out_dir: "str | Path | None" = None,
    ) -> ImageResult:
        """Generate one image from ``prompt`` with the selected ``model`` and write it
        under assets/images/.

        ``model`` is a registry id (default ``flux-schnell``); an unknown id raises
        ``ValueError``. ``steps`` defaults to the model's own ``steps_default`` (e.g. 4
        for the distilled FLUX models, 16 for Boogu). The model is keyed by its id, so a
        switch to a different image model evicts the previous one (image↔image is
        mutually exclusive, like image↔voice) while a repeat of the same id reuses the
        warm model.
        """
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        entry = models.image_model(model)  # ValueError on unknown id (re-validated here)
        steps = entry.steps_default if steps is None else steps
        seed = random.randint(0, 2**31 - 1) if seed is None else seed
        out = self._asset_path("images", "png", out_dir)
        started = time.monotonic()
        with self._lock:
            backend = self._ensure(
                entry.id, lambda: _probe_image(entry), lambda: _load_image_backend(entry),
            )
            _run_image_backend(
                entry, backend, prompt=prompt, steps=steps, seed=seed,
                width=width, height=height, out_path=out,
            )
        return ImageResult(
            path=out, prompt=prompt, seed=seed,
            seconds=round(time.monotonic() - started, 2), model=entry.id,
        )

    def transcribe(self, audio_path: "str | Path") -> TranscriptResult:
        """Transcribe an existing audio file to text (speech-to-text)."""
        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"audio file not found: {audio_path}")
        started = time.monotonic()
        with self._lock:
            model = self._ensure("stt", _probe_stt, _load_stt_backend)
            text = _run_stt_backend(model, audio_path=audio_path)
        return TranscriptResult(text=text, seconds=round(time.monotonic() - started, 2))

    def synthesize(
        self, text: str, *, voice: str = TTS_DEFAULT_VOICE,
        out_dir: "str | Path | None" = None,
    ) -> SpeechResult:
        """Synthesize speech from ``text`` and write it under assets/audio/.

        ``voice`` must be in ``models.ALLOWED_VOICES`` — an unlisted voice raises
        ``ValueError`` (the /api/tts route maps it to 400) rather than being forwarded to
        the backend. This re-validates what the route already checked, so a direct caller
        can't reach the backend with an unlisted voice (mirrors the model-id double-check
        in generate_image)."""
        if not text.strip():
            raise ValueError("text must not be empty")
        if voice not in models.ALLOWED_VOICES:
            raise ValueError(f"unknown voice {voice!r} (allowed: {sorted(models.ALLOWED_VOICES)})")
        out = self._asset_path("audio", "wav", out_dir)
        started = time.monotonic()
        with self._lock:
            model = self._ensure("tts", _probe_tts, _load_tts_backend)
            _run_tts_backend(model, text=text, voice=voice, out_path=out)
        return SpeechResult(path=out, voice=voice, seconds=round(time.monotonic() - started, 2))

    def embed(
        self, texts: "list[str]", *, model: str = models.DEFAULT_EMBED_MODEL,
        kind: str = "document",
    ) -> "list[list[float]]":
        """Embed ``texts`` with the selected embedding model (Wave 4 — RAG). ``kind`` is
        ``"document"`` (chunks being ingested) or ``"query"`` (the mission goal at retrieval
        time) — it selects the model's retrieval instruction prefix.

        Keyed by ``embed:<id>`` so a switch to a different embedding model — or to/from an
        image or voice model — evicts the previous one (the 16 GB mutual-exclusion rule),
        while repeat calls with the same model reuse the warm one (the fast path across a
        whole ingest, and again at query time). An empty list is a no-op that never touches
        the device, so it can't evict a warm image model for nothing."""
        if not texts:
            return []
        # Lazy import: embeddings imports MediaUnavailable/_pinned_repo from this module, so
        # importing it at module load would be circular. Deferring to call time also keeps
        # the [studio] extra fully optional (the import only runs when an embed is requested).
        from . import embeddings
        entry = models.embed_model(model)  # ValueError on unknown id (re-validated here)
        with self._lock:
            backend = self._ensure(
                f"embed:{entry.id}",
                embeddings._probe_embed,
                lambda: embeddings._load_embed(entry),
            )
            return embeddings._run_embed(backend, entry, texts=texts, kind=kind)

    def caption(
        self, images: "list[bytes]", *, model: "Optional[str]" = None, cloud: bool = False,
    ) -> "list[str]":
        """Caption ``images`` with a vision-language model (Wave 6 — visual RAG). ``cloud`` selects
        the OPTIONAL off-machine backend for this call — default ``False`` keeps captioning on the
        local MLX VLM, so nothing leaves the machine unless the caller explicitly opts in.

        Keyed by ``visual:<id>`` so loading the VLM evicts a warm image/embed/voice model (the
        16 GB mutual-exclusion rule) and repeat calls reuse the warm one. An empty list is a no-op
        that never touches the device — mirrors ``embed``. The VLM backend is lazy-imported, so a
        missing ``[visual]`` extra raises ``VisualUnavailable`` (→ 501) from the probe, before any
        eviction."""
        if not images:
            return []
        from .. import visual  # lazy: keeps [visual] optional + avoids a load-time cycle
        chosen = model or ("qwen3-vl-cloud" if cloud else visual.DEFAULT_VISUAL_MODEL)
        entry = visual.visual_model(chosen)   # ValueError on unknown id (re-validated here)
        probe, load, run = visual._backend(entry)
        # The local probe takes no args; the cloud probe needs the entry (endpoint + env key).
        with self._lock:
            backend = self._ensure(
                f"visual:{entry.id}",
                (lambda: probe(entry)) if entry.backend == "cloud" else probe,
                lambda: load(entry),
            )
            return run(backend, entry, images=images)
