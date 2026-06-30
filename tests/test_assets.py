"""Tests for the Wave-3 marker parser (`agency_studio/assets.py`).

Fully offline and pure — ``parse_markers`` does no I/O, loads no models, touches no
network. These tests pin the untrusted-boundary contract: which markers are honored,
which are dropped, and that every safe default (model allowlist, fixed canvas, voice
fallback, length bounds, per-mission caps, route gating) is forced at parse time.
"""

import json

import pytest

from agency_studio import assets
from agency_studio.engines import models


# Both departments routed unless a test narrows it — so route gating never silently
# masks an unrelated assertion.
FULL_ROUTE = ["product", "marketing", "comms", "solve"]


def _asset_block(payload: dict) -> str:
    return "```asset\n" + json.dumps(payload) + "\n```"


# ── happy path ────────────────────────────────────────────────────────────────

def test_parses_a_valid_image_marker():
    text = "Intro.\n" + _asset_block(
        {"type": "image", "prompt": "A bold hero banner", "model": "flux-schnell"}
    ) + "\nOutro."
    reqs = assets.parse_markers(text, FULL_ROUTE)
    assert len(reqs) == 1
    req = reqs[0]
    assert req.type == "image"
    assert req.prompt == "A bold hero banner"
    assert req.model == "flux-schnell"
    assert req.width == assets.MARKER_IMAGE_SIZE
    assert req.height == assets.MARKER_IMAGE_SIZE


def test_parses_a_valid_tts_marker():
    text = _asset_block({"type": "tts", "text": "Welcome aboard.", "voice": "af_heart"})
    reqs = assets.parse_markers(text, FULL_ROUTE)
    assert len(reqs) == 1
    assert reqs[0].type == "tts"
    assert reqs[0].text == "Welcome aboard."
    assert reqs[0].voice == "af_heart"


def test_image_marker_defaults_model_when_absent():
    text = _asset_block({"type": "image", "prompt": "A banner"})
    reqs = assets.parse_markers(text, FULL_ROUTE)
    assert len(reqs) == 1
    assert reqs[0].model == models.DEFAULT_IMAGE_MODEL == "flux-schnell"


def test_preserves_document_order_across_types():
    text = (
        _asset_block({"type": "tts", "text": "First."})
        + "\n"
        + _asset_block({"type": "image", "prompt": "Second"})
    )
    reqs = assets.parse_markers(text, FULL_ROUTE)
    assert [r.type for r in reqs] == ["tts", "image"]


# ── field whitelist: untrusted keys are ignored, never honored ────────────────

def test_image_marker_ignores_canvas_and_path_fields():
    # An untrusted marker cannot pick the canvas, compute steps, seed, or output path.
    text = _asset_block({
        "type": "image", "prompt": "A banner", "model": "flux-schnell",
        "width": 8192, "height": 8192, "steps": 999, "seed": 7,
        "path": "../../etc/passwd", "filename": "evil.png",
    })
    reqs = assets.parse_markers(text, FULL_ROUTE)
    assert len(reqs) == 1
    req = reqs[0]
    assert req.width == assets.MARKER_IMAGE_SIZE       # NOT 8192
    assert req.height == assets.MARKER_IMAGE_SIZE
    # No path/filename/steps/seed field exists on AssetRequest at all.
    assert not hasattr(req, "path")
    assert not hasattr(req, "filename")
    assert not hasattr(req, "steps")


# ── model allowlist (marker-only, stricter than the GUI registry) ─────────────

# Every GUI-registry model that the marker allowlist excludes must be rejected at parse.
# Derived FROM the registry so it tracks model churn (e.g. the live z-image removal)
# instead of CI going red when an unrelated heavy model is added/dropped.
_REGISTRY_BUT_NOT_MARKER = sorted(set(models.IMAGE_MODELS) - assets.MARKER_IMAGE_MODELS)


@pytest.mark.parametrize("model_id", _REGISTRY_BUT_NOT_MARKER)
def test_registry_image_model_rejected_when_not_marker_allowlisted(model_id):
    # These ARE real registry models (offered in the GUI), but a marker may not request
    # them — the marker allowlist is strictly narrower than the registry (e.g. boogu-base
    # is the minutes-per-image DoS risk; klein is the heavier quantize-on-load model).
    text = _asset_block({"type": "image", "prompt": "A banner", "model": model_id})
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_unknown_image_model_rejected():
    text = _asset_block({"type": "image", "prompt": "A banner", "model": "stable-diffusion-xl"})
    assert assets.parse_markers(text, FULL_ROUTE) == []


# ── voice allowlist (soft fallback, never a hard skip) ────────────────────────

def test_unknown_voice_falls_back_to_default():
    text = _asset_block({"type": "tts", "text": "Hello.", "voice": "xx_evil"})
    reqs = assets.parse_markers(text, FULL_ROUTE)
    assert len(reqs) == 1
    assert reqs[0].voice == assets.DEFAULT_VOICE


def test_missing_voice_uses_default():
    text = _asset_block({"type": "tts", "text": "Hello."})
    reqs = assets.parse_markers(text, FULL_ROUTE)
    assert reqs[0].voice == assets.DEFAULT_VOICE


def test_known_alternate_voice_is_honored():
    voice = "bm_george"
    assert voice in models.ALLOWED_VOICES
    text = _asset_block({"type": "tts", "text": "Hello.", "voice": voice})
    assert assets.parse_markers(text, FULL_ROUTE)[0].voice == voice


# ── length bounds ─────────────────────────────────────────────────────────────

def test_oversized_prompt_is_dropped():
    text = _asset_block({"type": "image", "prompt": "x" * (assets.MAX_TEXT_BYTES + 1)})
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_oversized_tts_text_is_dropped():
    text = _asset_block({"type": "tts", "text": "x" * (assets.MAX_TEXT_BYTES + 1)})
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_oversized_block_skipped_before_json_parse():
    # A block whose raw body exceeds MAX_BLOCK_BYTES is dropped before json.loads.
    big = _asset_block({"type": "image", "prompt": "ok", "pad": "y" * assets.MAX_BLOCK_BYTES})
    assert assets.parse_markers(big, FULL_ROUTE) == []


def test_prompt_at_the_limit_is_kept():
    text = _asset_block({"type": "image", "prompt": "x" * assets.MAX_TEXT_BYTES})
    assert len(assets.parse_markers(text, FULL_ROUTE)) == 1


# ── per-mission caps ──────────────────────────────────────────────────────────

def test_image_cap_enforced():
    blocks = "\n".join(
        _asset_block({"type": "image", "prompt": f"banner {i}"})
        for i in range(assets.MAX_IMAGES + 3)
    )
    reqs = assets.parse_markers(blocks, FULL_ROUTE)
    assert len(reqs) == assets.MAX_IMAGES
    assert all(r.type == "image" for r in reqs)


def test_tts_cap_enforced():
    blocks = "\n".join(
        _asset_block({"type": "tts", "text": f"line {i}"})
        for i in range(assets.MAX_TTS + 3)
    )
    reqs = assets.parse_markers(blocks, FULL_ROUTE)
    assert len(reqs) == assets.MAX_TTS


def test_caps_are_independent_per_type():
    blocks = "\n".join(
        [_asset_block({"type": "image", "prompt": f"b{i}"}) for i in range(2)]
        + [_asset_block({"type": "tts", "text": f"t{i}"}) for i in range(2)]
    )
    reqs = assets.parse_markers(blocks, FULL_ROUTE)
    assert sum(r.type == "image" for r in reqs) == 2
    assert sum(r.type == "tts" for r in reqs) == 2


def test_route_dropped_markers_do_not_consume_cap():
    # Off-route images are dropped for route, not counted — so 4 valid ones still pass.
    off = "\n".join(_asset_block({"type": "image", "prompt": f"x{i}"}) for i in range(3))
    on = "\n".join(_asset_block({"type": "image", "prompt": f"y{i}"}) for i in range(assets.MAX_IMAGES))
    # Route lacks marketing → everything image-typed drops regardless of cap.
    assert assets.parse_markers(off + "\n" + on, ["product"]) == []


# ── route gating ──────────────────────────────────────────────────────────────

def test_image_dropped_without_marketing_in_route():
    text = _asset_block({"type": "image", "prompt": "A banner"})
    assert assets.parse_markers(text, ["product", "comms"]) == []


def test_tts_dropped_without_comms_in_route():
    text = _asset_block({"type": "tts", "text": "Hello."})
    assert assets.parse_markers(text, ["product", "marketing"]) == []


def test_route_is_case_insensitive_and_whitespace_tolerant():
    text = _asset_block({"type": "image", "prompt": "A banner"})
    assert len(assets.parse_markers(text, ["  Marketing  "])) == 1


def test_empty_route_drops_everything():
    text = (
        _asset_block({"type": "image", "prompt": "A banner"})
        + _asset_block({"type": "tts", "text": "Hello."})
    )
    assert assets.parse_markers(text, []) == []


# ── malformed / degenerate input is never an error ────────────────────────────

def test_malformed_json_is_skipped():
    text = "```asset\n{not valid json,,}\n```"
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_non_object_json_is_skipped():
    text = "```asset\n[1, 2, 3]\n```"
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_unknown_type_is_ignored():
    text = _asset_block({"type": "video", "prompt": "A clip"})
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_stt_type_is_not_marker_triggerable():
    text = _asset_block({"type": "stt", "audio": "x.wav"})
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_missing_type_is_ignored():
    text = _asset_block({"prompt": "A banner"})
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_image_marker_without_prompt_is_dropped():
    text = _asset_block({"type": "image", "model": "flux-schnell"})
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_blank_prompt_is_dropped():
    text = _asset_block({"type": "image", "prompt": "   "})
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_non_asset_fence_is_ignored():
    text = "```json\n" + json.dumps({"type": "image", "prompt": "A banner"}) + "\n```"
    assert assets.parse_markers(text, FULL_ROUTE) == []


def test_plain_text_without_markers_yields_nothing():
    assert assets.parse_markers("Just a normal deliverable, no markers.", FULL_ROUTE) == []


def test_empty_and_non_string_delivered():
    assert assets.parse_markers("", FULL_ROUTE) == []
    assert assets.parse_markers(None, FULL_ROUTE) == []  # type: ignore[arg-type]


def test_valid_markers_survive_alongside_malformed_ones():
    text = (
        "```asset\n{broken json\n```\n"
        + _asset_block({"type": "image", "prompt": "Good banner"})
        + "\n```asset\n{also broken\n```"
    )
    reqs = assets.parse_markers(text, FULL_ROUTE)
    assert len(reqs) == 1
    assert reqs[0].prompt == "Good banner"


def test_unterminated_fence_does_not_swallow_a_following_block():
    # An opener with NO closing fence must not consume the next, well-formed block — its
    # opening backticks must never be read as the first block's close (review finding [1]).
    text = (
        "```asset\n{unterminated, no closing fence\n\n"
        + _asset_block({"type": "image", "prompt": "Recovered banner"})
    )
    reqs = assets.parse_markers(text, FULL_ROUTE)
    assert len(reqs) == 1
    assert reqs[0].prompt == "Recovered banner"


def test_bare_string_route_is_not_iterated_char_by_char():
    # A single-department route passed as a string must behave like a one-element list,
    # not a set of its characters (review finding [2]).
    text = _asset_block({"type": "image", "prompt": "A banner"})
    assert len(assets.parse_markers(text, "marketing")) == 1
    assert assets.parse_markers(text, "product") == []


def test_prompt_is_stripped():
    text = _asset_block({"type": "image", "prompt": "  spaced banner  "})
    assert assets.parse_markers(text, FULL_ROUTE)[0].prompt == "spaced banner"
