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

def _import_flux():
    """Return mflux's ``Flux1`` class. mflux reorganised its import path across
    versions, so try the current location then the older top-level export."""
    try:
        from mflux.models.flux.variants.txt2img.flux import Flux1  # mflux >= 0.6 layout
        return Flux1
    except ImportError:
        pass
    try:
        from mflux import Flux1  # older top-level export
        return Flux1
    except ImportError as exc:
        raise MediaUnavailable(f"image generation needs mflux — {_INSTALL_HINT}") from exc


def _probe_image() -> None:
    _import_flux()


def _load_image_backend():
    """Load FLUX.1-schnell (mflux). Quantized to 8-bit to fit comfortably in RAM."""
    Flux1 = _import_flux()
    return Flux1.from_name(model_name=models.IMAGE_MODEL_NAME, quantize=8)


def _run_image_backend(model, *, prompt, steps, seed, width, height, out_path) -> None:
    # mflux's Flux1.generate_image takes the per-generation settings as direct
    # keyword arguments (verified against the installed mflux on the target Mac in
    # Phase 2.4 — there is no Config object in this version).
    image = model.generate_image(
        seed=seed, prompt=prompt,
        num_inference_steps=steps, width=width, height=height,
    )
    image.save(path=str(out_path))


def _probe_stt() -> None:
    try:
        import mlx_whisper  # noqa: F401
    except ImportError as exc:
        raise MediaUnavailable(f"speech-to-text needs mlx-whisper — {_INSTALL_HINT}") from exc


def _load_stt_backend():
    """STT 'model' is the ``mlx_whisper`` module itself; the turbo weights are
    fetched + cached by HF on first ``transcribe`` (content-addressed, no manifest)."""
    import mlx_whisper
    return mlx_whisper


def _run_stt_backend(mlx_whisper, *, audio_path) -> str:
    result = mlx_whisper.transcribe(str(audio_path), path_or_hf_repo=models.STT_HF_REPO)
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
        self._resident_kind: Optional[str] = None
        self._model = None

    # -- model residency (caller holds self._lock) -----------------------------
    def _ensure(self, kind: str, probe: Callable[[], None], loader: Callable[[], object]) -> object:
        if self._resident_kind == kind and self._model is not None:
            return self._model  # warm hit
        # Probe the new back-end's availability FIRST (cheap import, no weights). If
        # the extra is missing this raises MediaUnavailable here — before we evict —
        # so a request for an uninstalled modality never destroys a working warm model.
        probe()
        if self._model is not None:
            self._evict()  # keep image and voice models never co-resident (16 GB)
        self._model = loader()
        self._resident_kind = kind
        return self._model

    def _evict(self) -> None:
        self._model = None
        self._resident_kind = None
        _free_metal_cache()

    @property
    def resident_kind(self) -> Optional[str]:
        """Which model is currently warm (``'image'`` / ``'stt'`` / ``'tts'`` / None).
        Exposed for the GUI's ModelManager panel and for tests."""
        return self._resident_kind

    def _asset_path(self, sub: str, ext: str) -> Path:
        directory = self._assets / sub
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{uuid.uuid4().hex}.{ext}"

    # -- operations -------------------------------------------------------------
    def generate_image(
        self, prompt: str, *, steps: int = 4, seed: Optional[int] = None,
        width: int = 1024, height: int = 1024,
    ) -> ImageResult:
        """Generate one image from ``prompt`` and write it under assets/images/.

        ``steps`` defaults to 4: FLUX.1-schnell is distilled for 1-4 steps, and 4
        gives the best quality of that range while staying fast on Apple Silicon.
        """
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        seed = random.randint(0, 2**31 - 1) if seed is None else seed
        out = self._asset_path("images", "png")
        started = time.monotonic()
        with self._lock:
            model = self._ensure("image", _probe_image, _load_image_backend)
            _run_image_backend(
                model, prompt=prompt, steps=steps, seed=seed,
                width=width, height=height, out_path=out,
            )
        return ImageResult(path=out, prompt=prompt, seed=seed, seconds=round(time.monotonic() - started, 2))

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

    def synthesize(self, text: str, *, voice: str = TTS_DEFAULT_VOICE) -> SpeechResult:
        """Synthesize speech from ``text`` and write it under assets/audio/."""
        if not text.strip():
            raise ValueError("text must not be empty")
        out = self._asset_path("audio", "wav")
        started = time.monotonic()
        with self._lock:
            model = self._ensure("tts", _probe_tts, _load_tts_backend)
            _run_tts_backend(model, text=text, voice=voice, out_path=out)
        return SpeechResult(path=out, voice=voice, seconds=round(time.monotonic() - started, 2))
