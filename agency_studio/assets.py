"""assets — the marker parser: the untrusted-boundary gate for Wave-3 assets.

A department (or the final synthesis) may embed a fenced ``asset`` block in the
mission's ``delivered`` text to request a generated asset (a campaign image, a TTS
narration). That text is **model output** — untrusted — so every field it carries is
suspect: it may try to pick an expensive model, an enormous canvas, a traversal path,
or a multi-megabyte prompt. ``parse_markers`` is the chokepoint that turns those raw
fenced blocks into a **small, validated, capped** list of ``AssetRequest`` the render
step (a later wave step) can run without re-checking anything.

Why all the safety lives here, at parse time
---------------------------------------------
This is the **untrusted boundary** (the `/code-review` finding that re-scoped Wave 3):
the safe defaults are forced *here*, not silently inside the shared ``ModelManager``
(which also serves the trusted HTTP routes and must not have its callers' inputs
quietly rewritten). So this module — not the manager — decides:

  * which **type** is allowed (``image`` / ``tts``; STT is never marker-triggered);
  * which **model** an image marker may name (a tiny allowlist — never ``boogu-base``,
    the minutes-per-image model, which an untrusted marker could weaponise as a DoS);
  * the **fixed, safe canvas** (untrusted output never chooses compute size);
  * the **voice** (must be a known Kokoro voice, else the default);
  * **length** bounds (a marker can't smuggle a multi-KB prompt);
  * **per-mission caps** (≤4 images, ≤2 TTS) and **route gating** (an image only when
    the mission actually ran ``marketing``; TTS only when it ran ``comms``).

``parse_markers`` is **pure** — no I/O, no model loading, no network. It is fully
offline-testable, and rendering (which needs a warm ``ModelManager`` and a per-mission
output dir) is a separate, later step that consumes this module's output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from .engines import local_media, models


# ── marker-only allowlists / caps (the safe defaults forced at parse time) ────

# The ONLY image models an untrusted marker may request. A strict subset of the GUI
# registry: ``flux-schnell`` is the fast, distilled, 16 GB-friendly default. Excludes
# ``flux2-klein-4b`` (heavier, quantize-on-load) and especially ``boogu-base`` — the
# non-distilled 10B+conditioner model that takes minutes per image, which an untrusted
# marker could otherwise use to lock the single warm GPU slot for the whole mission.
MARKER_IMAGE_MODELS: "frozenset[str]" = frozenset({"flux-schnell"})

# Fixed, safe canvas for every marker-driven image. Untrusted output never picks the
# compute size; 1024² is FLUX-schnell's native, live-validated (Wave 2.4) resolution.
MARKER_IMAGE_SIZE = 1024

# The default voice when a TTS marker omits ``voice`` or names an unknown one (the
# parser falls back rather than skipping — an unknown voice is a soft error). Single
# source of truth: the same default the manager and /api/tts use.
DEFAULT_VOICE = local_media.TTS_DEFAULT_VOICE


def _check_invariants() -> None:
    """Fail fast at import if this module's allowlists have drifted out of sync with the
    model registry / TTS defaults. These are *internal code* invariants (a marker pointing
    at a model the registry doesn't have, or a default that its own allowlist rejects) —
    a code-level mistake, not a missing optional dependency. So the correct response is a
    loud RuntimeError here, NOT the graceful media-501 path (which is only for an absent
    ``[media]`` extra): every one of these would otherwise surface as a confusing
    silent-drop or mid-mission crash. Raises (never ``assert``) so they hold under
    ``python -O`` too."""
    unregistered = MARKER_IMAGE_MODELS - set(models.IMAGE_MODELS)
    if unregistered:
        raise RuntimeError(
            f"MARKER_IMAGE_MODELS contains ids not in models.IMAGE_MODELS: {sorted(unregistered)}"
        )
    # _build_image falls back to the registry default for a model-less marker, then
    # requires it to be marker-allowlisted — so the default must itself be allowlisted,
    # else the common (model-omitted) image marker would silently drop.
    if models.DEFAULT_IMAGE_MODEL not in MARKER_IMAGE_MODELS:
        raise RuntimeError(
            f"DEFAULT_IMAGE_MODEL {models.DEFAULT_IMAGE_MODEL!r} is not in MARKER_IMAGE_MODELS "
            f"{sorted(MARKER_IMAGE_MODELS)} — a model-less image marker would always drop"
        )
    if DEFAULT_VOICE not in models.ALLOWED_VOICES:
        raise RuntimeError(
            f"DEFAULT_VOICE {DEFAULT_VOICE!r} is not in models.ALLOWED_VOICES — the TTS "
            f"fallback voice would be rejected at synthesis time"
        )


_check_invariants()

# Per-mission caps (honored in document order; markers past the cap are dropped).
MAX_IMAGES = 4
MAX_TTS = 2

# Byte bounds. A whole fenced block over this is skipped *before* ``json.loads`` (a
# cheap DoS guard against a giant blob). A prompt/text over its bound skips that one
# marker (a truncated prompt would generate a garbled image / cut-off narration).
MAX_BLOCK_BYTES = 8 * 1024
MAX_TEXT_BYTES = 2 * 1024

# Which department must be in the mission's route for a marker type to be honored. An
# image is a marketing deliverable; a narration is a comms deliverable. A marker for a
# type whose department didn't run is dropped (robust to *where* the marker sits — the
# gate reads the route, not the marker's location).
_ROUTE_FOR_TYPE = {"image": "marketing", "tts": "comms"}

# A fence line is exactly ``` (optionally indented / trailing-spaced); an opener also
# carries the ``asset`` info-string. Compared against each stripped line by the scanner.
_FENCE_OPEN = "```asset"
_FENCE_CLOSE = "```"


def _iter_asset_blocks(delivered: str):
    """Yield the raw body text of each well-formed ```asset fenced block, in order.

    A block opens on a line that is exactly ``` ``` ``asset`` and closes on the next line
    that is exactly ``` ``` ``. Deliberately line-oriented rather than a single regex: a
    non-greedy regex body lets an *unterminated* opener run forward and swallow a later,
    well-formed block (its opening backticks read as the first opener's closing fence).
    Here an unterminated opener instead yields nothing and the scan *restarts* at the next
    opener, so a malformed marker can never consume a valid one that follows it.
    """
    lines = delivered.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if lines[i].strip() != _FENCE_OPEN:
            i += 1
            continue
        body, j = [], i + 1
        while j < n and lines[j].strip() not in (_FENCE_CLOSE, _FENCE_OPEN):
            body.append(lines[j])
            j += 1
        if j < n and lines[j].strip() == _FENCE_CLOSE:
            yield "\n".join(body)
            i = j + 1  # resume past the closing fence
        else:
            i = j  # unterminated: resume *at* the next opener (or EOF), never past it


@dataclass(frozen=True)
class AssetRequest:
    """One validated, ready-to-render asset request — the *only* shape the render step
    sees. Every field here has already passed the parse-time gate, so the renderer never
    re-validates. ``type`` discriminates which fields are meaningful: ``image`` →
    ``prompt``/``model``/``width``/``height`` (the latter two are the fixed safe canvas,
    never marker-supplied); ``tts`` → ``text``/``voice``."""
    type: str
    prompt: str = ""
    model: str = ""
    width: int = 0
    height: int = 0
    text: str = ""
    voice: str = ""


def parse_markers(delivered: str, route: Sequence[str]) -> "list[AssetRequest]":
    """Extract, validate, route-gate and cap the asset markers in ``delivered``.

    ``delivered`` is the inspected mission text (model output — untrusted). ``route`` is
    the mission's department route (``dossier['route']``); a marker type is honored only
    when its department actually ran. Returns at most ``MAX_IMAGES`` image requests and
    ``MAX_TTS`` TTS requests, in document order, each already safe to render. Pure: never
    raises, never does I/O — a malformed/oversized/over-cap/off-route marker is silently
    dropped, not an error.
    """
    requests: "list[AssetRequest]" = []
    if not isinstance(delivered, str) or not delivered:
        return requests
    # A bare string is iterable char-by-char — wrap it so a single-department route passed
    # as "marketing" (rather than ["marketing"]) doesn't silently drop every marker.
    if isinstance(route, str):
        route = [route]
    allowed = {str(dept).strip().lower() for dept in (route or [])}
    counts = {"image": 0, "tts": 0}
    caps = {"image": MAX_IMAGES, "tts": MAX_TTS}

    for block in _iter_asset_blocks(delivered):
        # Cheap DoS guard: never hand a giant blob to json.loads.
        if len(block.encode("utf-8")) > MAX_BLOCK_BYTES:
            continue
        try:
            marker = json.loads(block)
        except (ValueError, RecursionError):  # JSONDecodeError ⊂ ValueError
            continue
        if not isinstance(marker, dict):
            continue
        kind = marker.get("type")
        if kind not in _ROUTE_FOR_TYPE:  # unknown / missing type → ignore
            continue
        if _ROUTE_FOR_TYPE[kind] not in allowed:  # route gate
            continue
        if counts[kind] >= caps[kind]:  # per-mission cap (drop the overflow)
            continue
        req = _build_image(marker) if kind == "image" else _build_tts(marker)
        if req is None:  # failed field validation → drop this marker
            continue
        requests.append(req)
        counts[kind] += 1
    return requests


def _clean_text(marker: dict, key: str) -> Optional[str]:
    """Return the marker's whitelisted text field (``prompt`` / ``text``) stripped, or
    None if it is absent, not a string, empty, or over the 2 KB untrusted-input bound.
    The single home for that bound so image prompts and TTS text can never drift apart."""
    value = marker.get(key)
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value.encode("utf-8")) > MAX_TEXT_BYTES:
        return None
    return value


def _build_image(marker: dict) -> Optional[AssetRequest]:
    """Validate an image marker's whitelisted fields (``prompt``, ``model``). Every other
    key — ``path``/``filename``/``width``/``height``/``steps``/``seed`` — is ignored: the
    canvas is fixed, the output path is the renderer's, and compute size is not the
    marker's to choose. Returns None (drop) on a bad prompt or a non-allowlisted model."""
    prompt = _clean_text(marker, "prompt")
    if prompt is None:
        return None
    model = marker.get("model")
    if model in (None, ""):
        model = models.DEFAULT_IMAGE_MODEL  # 'flux-schnell' — in MARKER_IMAGE_MODELS
    if not isinstance(model, str) or model not in MARKER_IMAGE_MODELS:
        return None  # boogu-base / klein / anything off-allowlist → rejected at parse
    return AssetRequest(
        type="image", prompt=prompt, model=model,
        width=MARKER_IMAGE_SIZE, height=MARKER_IMAGE_SIZE,
    )


def _build_tts(marker: dict) -> Optional[AssetRequest]:
    """Validate a TTS marker's whitelisted fields (``text``, ``voice``). An unknown or
    missing voice falls back to ``DEFAULT_VOICE`` (soft error); a bad/oversized ``text``
    drops the marker. All other keys (incl. ``path``/``filename``) are ignored."""
    text = _clean_text(marker, "text")
    if text is None:
        return None
    voice = marker.get("voice")
    if not isinstance(voice, str) or voice not in models.ALLOWED_VOICES:
        voice = DEFAULT_VOICE
    return AssetRequest(type="tts", text=text, voice=voice)


# ── render (step 5 — the consumer half: needs a warm ModelManager) ────────────

def _emit(on_event: "Optional[Callable[[dict], None]]", event: dict) -> None:
    """Fire an optional progress callback, swallowing any error — purely observational
    (SSE streaming), so a misbehaving sink can never break a render. No-op when None."""
    if on_event is None:
        return
    try:
        on_event(event)
    except Exception:
        pass


def render(
    manager,
    requests: "Sequence[AssetRequest]",
    *,
    out_dir,
    to_url: "Callable[[object], str]",
    should_cancel: "Optional[Callable[[], bool]]" = None,
    on_event: "Optional[Callable[[dict], None]]" = None,
) -> "list[dict]":
    """Render each validated ``AssetRequest`` via the injected ``manager`` into ``out_dir``,
    returning a manifest — one dict per request, in the original document order.

    Images are rendered before TTS to avoid evict/reload thrash on the single warm GPU slot
    (image↔voice are mutually exclusive), but the manifest is returned in document order so
    ``rewrite_delivered`` can pair entries back to their source blocks.

    **Never raises.** A per-asset backend failure (a Metal crash, a missing weight) is caught
    and recorded ``status='failed'`` with the reason — the other assets still render and the
    mission's deliverable is never lost. If ``should_cancel()`` fires, the current and all
    remaining assets are recorded ``status='skipped'`` (reason ``cancelled``) WITHOUT spending
    GPU time, so a Stop aborts a multi-minute render promptly.

    ``to_url`` maps a written asset's filesystem path to its public ``/media/...`` URL (the
    server injects its assets-root-relative mapper; tests inject a stub). ``on_event`` (optional)
    receives a ``{phase:'asset', status:'start'|'done'|'failed'|'skipped', kind, url?}`` frame
    per asset for live SSE streaming. ``manager`` / ``to_url`` are injected so this stays
    offline-testable with stubbed backends.
    """
    manifest: "list[Optional[dict]]" = [None] * len(requests)
    # Render images first, then TTS — but keep each result at its original index.
    order = sorted(range(len(requests)), key=lambda i: 0 if requests[i].type == "image" else 1)
    cancelled = False
    for i in order:
        req = requests[i]
        if cancelled or (should_cancel is not None and should_cancel()):
            cancelled = True  # once cancelled, skip the rest without re-polling
            manifest[i] = {"type": req.type, "status": "skipped", "reason": "cancelled"}
            _emit(on_event, {"phase": "asset", "status": "skipped", "kind": req.type})
            continue
        _emit(on_event, {"phase": "asset", "status": "start", "kind": req.type})
        try:
            if req.type == "image":
                result = manager.generate_image(
                    req.prompt, model=req.model,
                    width=req.width, height=req.height, out_dir=out_dir,
                )
                entry = {
                    "type": "image", "status": "ok", "url": to_url(result.path),
                    "model": result.model, "seconds": result.seconds, "prompt": req.prompt,
                }
            else:
                result = manager.synthesize(req.text, voice=req.voice, out_dir=out_dir)
                entry = {
                    "type": "tts", "status": "ok", "url": to_url(result.path),
                    "voice": result.voice, "seconds": result.seconds, "text": req.text,
                }
        except Exception as exc:  # best-effort: one bad asset never aborts the batch
            manifest[i] = {"type": req.type, "status": "failed", "reason": str(exc)}
            _emit(on_event, {"phase": "asset", "status": "failed", "kind": req.type, "reason": str(exc)})
            continue
        manifest[i] = entry
        _emit(on_event, {"phase": "asset", "status": "done", "kind": req.type, "url": entry["url"]})
    return [m for m in manifest if m is not None]


def _reference(entry: dict) -> str:
    """The clean markdown reference that replaces a rendered ``asset`` block: an image embed
    or an audio caption (a PDF/markdown reader can't play audio, so it gets a labelled link)."""
    url = entry.get("url", "")
    if entry.get("type") == "image":
        caption = (entry.get("prompt") or "generated image").strip().replace("\n", " ")
        return f"![{caption}]({url})"
    secs = entry.get("seconds")
    dur = f" ({secs}s)" if secs is not None else ""
    return f"[Generated audio narration]({url}){dur}"


def rewrite_delivered(delivered: str, manifest: "Sequence[dict]") -> str:
    """Cosmetically replace each successfully-rendered ```asset block with a clean reference
    (image embed / audio caption), leaving blocks that were dropped, failed, or skipped
    verbatim. Pairs a block to a manifest entry by matching the block's ``prompt``/``text``
    against the entry's — robust to render reordering and to rejected blocks. Pure: no I/O,
    never raises; an unmatched or unparseable block is left untouched.
    """
    if not isinstance(delivered, str) or not delivered:
        return delivered
    ok = [m for m in (manifest or []) if isinstance(m, dict) and m.get("status") == "ok"]
    if not ok:
        return delivered
    consumed = [False] * len(ok)

    def _swap(body: str) -> "Optional[str]":
        if len(body.encode("utf-8")) > MAX_BLOCK_BYTES:  # mirror parse_markers' DoS guard
            return None
        try:
            marker = json.loads(body)
        except (ValueError, RecursionError):
            return None
        if not isinstance(marker, dict):
            return None
        kind = marker.get("type")
        key = {"image": "prompt", "tts": "text"}.get(kind)
        if key is None or not isinstance(marker.get(key), str):
            return None
        target = marker[key].strip()
        for idx, entry in enumerate(ok):
            if not consumed[idx] and entry.get("type") == kind \
                    and (entry.get(key) or "").strip() == target:
                consumed[idx] = True
                return _reference(entry)
        return None

    # split("\n") (not splitlines) so join("\n") round-trips byte-faithfully — trailing
    # newlines and \r\n survive verbatim in every non-swapped region (a fence line's
    # trailing \r is ignored by the .strip() comparison, so detection still works).
    lines = delivered.split("\n")
    out: "list[str]" = []
    i, n = 0, len(lines)
    while i < n:
        if lines[i].strip() != _FENCE_OPEN:
            out.append(lines[i])
            i += 1
            continue
        body, j = [], i + 1
        while j < n and lines[j].strip() not in (_FENCE_CLOSE, _FENCE_OPEN):
            body.append(lines[j])
            j += 1
        if j < n and lines[j].strip() == _FENCE_CLOSE:
            ref = _swap("\n".join(body))
            out.extend([ref] if ref is not None else lines[i:j + 1])  # swap, else keep verbatim
            i = j + 1
        else:
            out.extend(lines[i:j])  # unterminated opener: keep as-is up to the next opener/EOF
            i = j
    return "\n".join(out)
