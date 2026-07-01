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

  * which **type** is allowed (``image`` / ``tts`` / ``video``; STT is never marker-triggered).
    ``video`` is the studio's only *cloud* render (seedance, off-machine) so it carries an EXTRA
    gate on top of everything below — the per-mission ``allow_video`` opt-in — without which every
    video marker is dropped here, so an untrusted marker alone can never trigger an off-machine call;
  * which **model** an image marker may name (a tiny allowlist — never ``boogu-base``,
    the minutes-per-image model, which an untrusted marker could weaponise as a DoS);
  * the **fixed, safe canvas** (untrusted output never chooses compute size);
  * the **voice** (must be a known Kokoro voice, else the default);
  * **length** bounds (a marker can't smuggle a multi-KB prompt);
  * **per-mission caps** (≤4 images, ≤2 TTS, ≤1 video) and **route gating** (an image or
    video only when the mission actually ran ``marketing``; TTS only when it ran ``comms``).

``parse_markers`` is **pure** — no I/O, no model loading, no network. It is fully
offline-testable, and rendering (which needs a warm ``ModelManager`` and a per-mission
output dir) is a separate, later step that consumes this module's output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
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
# Video is a CLOUD render (seedance) — slow and metered — so at most one per mission. An
# untrusted marker can't raise this, and video is additionally gated by the per-mission
# ``allow_video`` opt-in (see ``parse_markers``): both must hold before a single clip renders.
MAX_VIDEO = 1

# Byte bounds. A whole fenced block over this is skipped *before* ``json.loads`` (a
# cheap DoS guard against a giant blob). A prompt/text over its bound skips that one
# marker (a truncated prompt would generate a garbled image / cut-off narration).
MAX_BLOCK_BYTES = 8 * 1024
MAX_TEXT_BYTES = 2 * 1024

# Which department must be in the mission's route for a marker type to be honored. An
# image is a marketing deliverable; a narration is a comms deliverable; a video is a
# marketing deliverable. A marker for a type whose department didn't run is dropped (robust
# to *where* the marker sits — the gate reads the route, not the marker's location).
_ROUTE_FOR_TYPE = {"image": "marketing", "tts": "comms", "video": "marketing"}

# A fence line is exactly ``` (optionally indented / trailing-spaced); an opener also
# carries the ``asset`` info-string. Compared against each stripped line by the scanner.
_FENCE_OPEN = "```asset"
_FENCE_CLOSE = "```"


def _first_nonspace(s: str) -> int:
    """Index of the first non-whitespace char in ``s`` (``len(s)`` if all-whitespace), by a
    forward scan — no throwaway stripped copy of the (up to block-size) region."""
    i, n = 0, len(s)
    while i < n and s[i].isspace():
        i += 1
    return i


_JSON_DECODER = json.JSONDecoder()  # stateless for raw_decode; one shared instance


def _marker_end(region: str) -> Optional[int]:
    """Char offset in ``region`` (the text right after an unterminated opener) just past the
    leading marker — the **first** complete JSON object the region begins with, after any leading
    whitespace, *when that object is a recognized asset marker* — or None otherwise.

    The marker convention is *one opener → one object*, so exactly that first object is the marker.
    Guards, each closing an edge the reviews surfaced:

      * a single ``raw_decode`` pass finds the object's end (O(region), no growing re-parse) and
        stops there, so content after it — prose OR further JSON the model wrote — is never scanned
        into the strip and is **preserved** by the caller (we don't guess later JSON is a 2nd marker);
      * the object must be a real asset marker (``dict`` with a known ``type``), so a legitimate
        *non-marker* data object right after a stray opener is **not** deleted — it falls to the
        verbatim path with the fence, losing no reader content;
      * the region is byte-bounded (matching the parser's ``MAX_BLOCK_BYTES`` *byte* budget, not a
        char count) before decoding, so a giant unclosed object can't make the scan super-linear;
      * a region that doesn't begin with ``{`` (prose / array / scalar) or whose object is malformed
        / over-budget returns None → the caller leaves it verbatim rather than bound the strip unsafely.
    """
    # Byte-bound the region: at most MAX_BLOCK_BYTES chars ⊇ the first MAX_BLOCK_BYTES bytes, then
    # trim to that byte budget (dropping a split trailing char). A char-prefix of ``region``, so an
    # offset into ``head`` maps straight back onto ``region``.
    head = region[:MAX_BLOCK_BYTES].encode("utf-8")[:MAX_BLOCK_BYTES].decode("utf-8", "ignore")
    idx = _first_nonspace(head)
    if idx >= len(head) or head[idx] != "{":
        return None  # must begin with a JSON object to be a bounded marker
    try:
        value, end = _JSON_DECODER.raw_decode(head, idx)
    except (ValueError, RecursionError):
        return None  # malformed, or larger than the byte bound → can't bound the strip
    if not (isinstance(value, dict) and value.get("type") in _ROUTE_FOR_TYPE):
        return None  # a valid JSON object but not an asset marker → preserve it, don't strip
    return end


def _scan_asset_blocks(delivered: str):
    """The single fence scanner shared by the parser and ``rewrite_delivered``, so the two
    can never drift on what counts as a block. Splits on ``\\n`` (byte-faithful: rewrite
    rejoins the same way) and matches each *stripped* line — a CRLF's trailing ``\\r`` is
    dropped by ``.strip()``, so ``\\r\\n`` fences still match. Yields, in document order:

      ``("text", line)``    — a passthrough line (not part of an ``asset`` marker)
      ``("block", body)``   — a complete ```asset…``` block (opener + close both seen), as its
                              joined body; both consumers replace the whole block — the parser
                              with a request, ``rewrite_delivered`` with a reference /
                              placeholder / nothing — so a well-formed block's fences are
                              never re-emitted.
      ``("stray_open", None)`` — an *unterminated* opener (no closing fence, or a second opener
                              before the close). ``rewrite_delivered`` strips it; the parser
                              ignores it (a malformed marker is never a request). When the region
                              after the opener begins with a recognized asset marker, only the opener
                              + that first marker object are stripped and everything after them
                              (:func:`_marker_end`) is emitted as ordinary ``text`` (char-precise, so
                              prose on the marker's closing line survives); a bare / whitespace-only
                              region (e.g. back-to-back openers) strips just the opener.

    An unterminated opener whose non-empty region does *not begin* with a recognized asset marker (a
    non-marker JSON object, a malformed payload, or a prose / array / scalar line) is left verbatim,
    fence and all (documented residual) — chosen over stripping, which would either delete legitimate
    reader content or run to the next opener/EOF and eat an unbounded tail of real prose.

    Deliberately line-oriented rather than one regex: a non-greedy regex body lets an
    *unterminated* opener run forward and swallow a later, well-formed block (its opening
    backticks read as the first opener's close). Here an unterminated opener's own lines are
    handled locally and the scan *restarts* at the next opener, so a malformed marker can never
    consume a valid one that follows it.
    """
    lines = delivered.split("\n")
    i, n = 0, len(lines)
    while i < n:
        if lines[i].strip() != _FENCE_OPEN:
            yield ("text", lines[i])
            i += 1
            continue
        body, j = [], i + 1
        while j < n and lines[j].strip() not in (_FENCE_CLOSE, _FENCE_OPEN):
            body.append(lines[j])
            j += 1
        if j < n and lines[j].strip() == _FENCE_CLOSE:
            yield ("block", "\n".join(body))
            i = j + 1  # resume past the closing fence
        else:  # unterminated opener — its region is the already-accumulated ``body``
            region = "\n".join(body)
            end = _marker_end(region)
            if end is not None:  # strip opener + the leading marker object; keep the rest as text
                yield ("stray_open", None)
                for line in region[end:].split("\n"):
                    yield ("text", line)  # content after the marker, char-precise (prose preserved)
            elif not region or region.isspace():  # bare/whitespace opener (e.g. back-to-back) → drop
                yield ("stray_open", None)
                for line in body:
                    yield ("text", line)  # the blank region lines (swallow_blank collapses them)
            else:  # region doesn't begin with an asset marker → can't bound → leave verbatim
                for k in range(i, j):
                    yield ("text", lines[k])
            i = j


def _iter_asset_blocks(delivered: str):
    """Yield the raw body text of each well-formed ```asset block, in order — the parser's
    view of the shared :func:`_scan_asset_blocks` (it ignores passthrough and ``stray_open``)."""
    for kind, *rest in _scan_asset_blocks(delivered):
        if kind == "block":
            yield rest[0]


@dataclass(frozen=True)
class AssetRequest:
    """One validated, ready-to-render asset request — the *only* shape the render step
    sees. Every field here has already passed the parse-time gate, so the renderer never
    re-validates. ``type`` discriminates which fields are meaningful: ``image`` →
    ``prompt``/``model``/``width``/``height`` (the latter two are the fixed safe canvas,
    never marker-supplied); ``tts`` → ``text``/``voice``.

    ``block_index`` is the request's ordinal among *all* well-formed ```asset blocks in the
    source document (0-based), set by :func:`parse_markers`. It is carried into the render
    manifest so :func:`rewrite_delivered` can pair each manifest entry back to its exact
    source block by position — never by content, which collides when two markers share a
    prompt/text (e.g. a rejected block followed by a valid one)."""
    type: str
    prompt: str = ""
    model: str = ""
    width: int = 0
    height: int = 0
    text: str = ""
    voice: str = ""
    block_index: int = -1


def parse_markers(
    delivered: str, route: Sequence[str], *, allow_video: bool = False,
) -> "list[AssetRequest]":
    """Extract, validate, route-gate and cap the asset markers in ``delivered``.

    ``delivered`` is the inspected mission text (model output — untrusted). ``route`` is
    the mission's department route (``dossier['route']``); a marker type is honored only
    when its department actually ran. Returns at most ``MAX_IMAGES`` image requests,
    ``MAX_TTS`` TTS requests, and ``MAX_VIDEO`` video requests, in document order, each
    already safe to render. Pure: never raises, never does I/O — a malformed/oversized/
    over-cap/off-route marker is silently dropped, not an error.

    ``allow_video`` is the per-mission cloud-video opt-in (default ``False``). Video is the
    studio's only *cloud* asset render (seedance, an off-machine call), so — unlike image/tts
    — it is gated on an explicit per-mission flag ON TOP OF the route gate: with ``allow_video``
    false, every ``video`` marker is dropped here, before it is ever built, so an untrusted
    marker alone can never trigger an off-machine call and a mission without the opt-in is
    byte-identical to one with no video markers at all.
    """
    requests: "list[AssetRequest]" = []
    if not isinstance(delivered, str) or not delivered:
        return requests
    # A bare string is iterable char-by-char — wrap it so a single-department route passed
    # as "marketing" (rather than ["marketing"]) doesn't silently drop every marker.
    if isinstance(route, str):
        route = [route]
    allowed = {str(dept).strip().lower() for dept in (route or [])}
    counts = {"image": 0, "tts": 0, "video": 0}
    caps = {"image": MAX_IMAGES, "tts": MAX_TTS, "video": MAX_VIDEO}

    # ``block_index`` counts EVERY well-formed block (incl. dropped ones), so a kept
    # request's ordinal matches the same block's position when ``rewrite_delivered`` later
    # re-walks the shared scanner — the two enumerations can never drift.
    for block_index, block in enumerate(_iter_asset_blocks(delivered)):
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
        if kind == "video" and not allow_video:  # cloud opt-in off → drop (rewrite strips the fence)
            continue
        if _ROUTE_FOR_TYPE[kind] not in allowed:  # route gate
            continue
        if counts[kind] >= caps[kind]:  # per-mission cap (drop the overflow)
            continue
        if kind == "image":
            req = _build_image(marker)
        elif kind == "tts":
            req = _build_tts(marker)
        else:  # video
            req = _build_video(marker)
        if req is None:  # failed field validation → drop this marker
            continue
        requests.append(replace(req, block_index=block_index))
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


def _build_video(marker: dict) -> Optional[AssetRequest]:
    """Validate a video marker's single whitelisted field (``prompt``). The cloud model, the
    clip duration, and the resolution are NOT the marker's to choose — the model is fixed to the
    seedance registry default and the render params are its fixed safe caps — so an untrusted
    marker can't select an expensive tier / long clip as a cost-DoS. Every other key
    (``model``/``duration``/``resolution``/``path``/``filename``) is ignored. Returns None (drop)
    on a bad/oversized prompt. The per-mission ``allow_video`` gate has already been applied in
    ``parse_markers`` — reaching here means the mission opted into cloud video."""
    prompt = _clean_text(marker, "prompt")
    if prompt is None:
        return None
    return AssetRequest(type="video", prompt=prompt)


# ── render (step 5 — the consumer half: needs a warm ModelManager) ────────────

# Render order: local GPU models first (image, then TTS — grouped to avoid warm-slot thrash),
# the cloud video call last. An unknown type sorts last too (defensive; never reached).
_RENDER_ORDER = {"image": 0, "tts": 1, "video": 2}


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
    (image↔voice are mutually exclusive), but the manifest is returned in document order.
    Each entry carries its request's ``block`` ordinal (the source ```asset block's
    position) so ``rewrite_delivered`` can pair entries back to their exact source block by
    position rather than by content.

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
    # Render images first, then TTS, then video last — but keep each result at its original
    # index. Images/TTS are the local, mutually-exclusive GPU models (grouped to avoid warm-slot
    # thrash); video is a cloud call (no residency) so it goes last, after the fast local renders.
    order = sorted(range(len(requests)), key=lambda i: _RENDER_ORDER.get(requests[i].type, 9))
    cancelled = False
    for i in order:
        req = requests[i]
        if cancelled or (should_cancel is not None and should_cancel()):
            cancelled = True  # once cancelled, skip the rest without re-polling
            manifest[i] = {"type": req.type, "status": "skipped", "reason": "cancelled",
                           "block": req.block_index}
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
                    "block": req.block_index,
                }
            elif req.type == "video":
                result = manager.generate_video(req.prompt, out_dir=out_dir)
                entry = {
                    "type": "video", "status": "ok", "url": to_url(result.path),
                    "model": result.model, "seconds": result.seconds, "prompt": req.prompt,
                    "block": req.block_index,
                }
            else:
                result = manager.synthesize(req.text, voice=req.voice, out_dir=out_dir)
                entry = {
                    "type": "tts", "status": "ok", "url": to_url(result.path),
                    "voice": result.voice, "seconds": result.seconds, "text": req.text,
                    "block": req.block_index,
                }
        except Exception as exc:  # best-effort: one bad asset never aborts the batch
            manifest[i] = {"type": req.type, "status": "failed", "reason": str(exc),
                           "block": req.block_index}
            _emit(on_event, {"phase": "asset", "status": "failed", "kind": req.type, "reason": str(exc)})
            continue
        manifest[i] = entry
        _emit(on_event, {"phase": "asset", "status": "done", "kind": req.type, "url": entry["url"]})
    return [m for m in manifest if m is not None]


def _escape_caption(text: str) -> str:
    """Neutralize an UNTRUSTED caption so it cannot break out of an ``![alt](url)`` link
    and splice in an attacker-chosen image/URL. The marker ``prompt`` is model output:
    a value like ``x](http://evil/p.png)![y`` would otherwise terminate the alt segment
    and inject an external embed into the deliverable (and the PDF rendered from it).
    Backslash-escapes the link-delimiter set ``[ ] ( )`` (markdown reads ``\\[`` as a
    literal ``[``) and flattens newlines. Escape the backslash first so the ones we add
    aren't re-escaped."""
    out = text.replace("\\", "\\\\")
    for ch in "[]()":
        out = out.replace(ch, "\\" + ch)
    return out.replace("\n", " ").replace("\r", " ")


def _reference(entry: dict) -> str:
    """The clean markdown reference that replaces a rendered ``asset`` block: an image embed, or
    a labelled link for audio/video (a PDF/markdown reader can't play either, so each gets a
    link the same way — the caption is the untrusted prompt, escaped)."""
    url = entry.get("url", "")
    kind = entry.get("type")
    if kind == "image":
        caption = _escape_caption((entry.get("prompt") or "generated image").strip())
        return f"![{caption}]({url})"
    secs = entry.get("seconds")
    dur = f" ({secs}s)" if secs is not None else ""
    if kind == "video":
        caption = _escape_caption((entry.get("prompt") or "generated video").strip())
        return f"[Generated video — {caption}]({url}){dur}"
    return f"[Generated audio narration]({url}){dur}"


def _placeholder(entry: dict) -> str:
    """The neutral inline marker that replaces an ``asset`` block whose render was *attempted*
    but produced no usable file — ``status`` ``failed`` (a backend crash / missing weight) or
    ``skipped`` (the mission was Stopped mid-render). Unlike a parse-dropped block (which is
    removed outright), an attempted-then-failed asset was legitimately expected, and the
    surrounding prose may reference it ("see the image below"); a small neutral breadcrumb
    keeps that reference from dangling at nothing, without leaking the raw JSON fence."""
    kind = entry.get("type")
    if kind == "image":
        return "_[image unavailable]_"
    if kind == "tts":
        return "_[audio narration unavailable]_"
    if kind == "video":
        return "_[video unavailable]_"
    return "_[asset unavailable]_"


def rewrite_delivered(delivered: str, manifest: "Sequence[dict]") -> str:
    """Rewrite every well-formed ```asset block out of ``delivered`` so no raw marker fence
    survives into the deliverable, the persisted dossier, or the exported PDF. Each block is
    paired to its manifest entry by the ``block`` ordinal — the source block's position,
    stamped by :func:`parse_markers` and carried through :func:`render` — so two markers
    sharing a prompt/text (e.g. a rejected block immediately followed by a valid one) can
    never cross-match. By that pairing a block becomes one of three things:

      * a clean **reference** (image embed / audio caption) when its render succeeded (``ok``);
      * a neutral **placeholder** (``_[… unavailable]_``) when a render was *attempted* but
        ``failed`` / was ``skipped`` — the entry carries a ``reason``, so the asset was
        legitimately expected and the prose around it may point at it;
      * **nothing** (the fence is stripped, and one blank line it would leave behind is
        collapsed) when the block has *no* manifest entry at all — it was dropped at the parse
        boundary (off-route, over-cap, non-allowlisted model, malformed): an illegitimate
        marker the reader should never have seen.

    An *unterminated* opener (a ```asset with no closing fence, or a second opener before the
    close) is stripped **surgically**: :func:`_scan_asset_blocks` removes just the opener + the
    single leading asset-marker object (via :func:`_marker_end`), keeping everything after it —
    prose *and* any further JSON the model wrote — so the fence goes without deleting real content.
    The residual is an unterminated opener whose region doesn't *begin* with a recognized marker
    (a non-marker data object, malformed JSON, or a prose line): it is left verbatim, fence and
    all, rather than risk content loss (documented in ``docs/WAVE3-PLAN.md``).

    Pure: no I/O, never raises.
    """
    if not isinstance(delivered, str) or not delivered:
        return delivered
    # Fast path: no line can equal the ``asset`` opener if its info-string isn't even present.
    # Keeps the common no-marker deliverable free of a needless split/rejoin.
    if _FENCE_OPEN not in delivered:
        return delivered
    # Index every *pairable* manifest entry by its source-block ordinal (``ok`` → reference,
    # ``failed``/``skipped`` → placeholder). An entry without a valid int ``block`` can't be
    # paired safely, so it's left out — its block then falls through to the strip path rather
    # than being guessed onto some block by content.
    by_block = {
        m["block"]: m
        for m in (manifest or [])
        if isinstance(m, dict) and isinstance(m.get("block"), int)
    }

    # Walk the SAME scanner the parser used, counting blocks in the SAME order, so the Nth
    # block here is the request parse_markers stamped block_index=N. Passthrough lines round-
    # trip byte-faithfully; every ```asset block is replaced (reference / placeholder / removed).
    out: "list[str]" = []
    block_ordinal = -1
    swallow_blank = False  # after stripping a block, drop one blank line it would leave behind
    for kind, *rest in _scan_asset_blocks(delivered):
        if kind == "text":
            line = rest[0]
            # A stripped block sat between blank lines (the markdown norm): emitting nothing
            # would fuse those two blanks into a double gap. Swallow exactly one to avoid it.
            if swallow_blank and not line.strip():
                swallow_blank = False
                continue
            swallow_blank = False
            out.append(line)
            continue
        if kind == "stray_open":
            swallow_blank = True  # unterminated opener + its marker JSON → strip (prose kept)
            continue
        block_ordinal += 1
        entry = by_block.get(block_ordinal)
        if entry is None:
            swallow_blank = True  # parse-dropped (no manifest entry) → strip the fence entirely
            continue
        swallow_blank = False
        out.append(_reference(entry) if entry.get("status") == "ok" else _placeholder(entry))
    return "\n".join(out)
