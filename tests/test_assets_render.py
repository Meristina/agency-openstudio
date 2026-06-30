"""Tests for the Wave-3 asset render half — ``assets.render`` and ``rewrite_delivered``.

Fully offline: a fake ModelManager records calls and returns canned results (no real
model loads, no GPU). These pin the render contract — document-order manifest, images
rendered before TTS, never-raises per-asset isolation, cancel→skip, SSE event frames —
and the cosmetic rewrite (match a rendered block by its prompt/text, leave every other
block verbatim).
"""

import json
from types import SimpleNamespace

from agency_studio import assets


class _FakeManager:
    """Records each call and returns a canned result; raises for any prompt/text in
    ``fail_on`` so the failure-isolation path is exercised without a real backend."""

    def __init__(self, fail_on=None):
        self.calls = []
        self._fail_on = set(fail_on or ())

    def generate_image(self, prompt, *, model, width, height, out_dir):
        self.calls.append(("image", prompt))
        if prompt in self._fail_on:
            raise RuntimeError("metal command buffer crashed")
        return SimpleNamespace(
            path=f"{out_dir}/images/{len(self.calls)}.png", model=model, seconds=1.0
        )

    def synthesize(self, text, *, voice, out_dir):
        self.calls.append(("tts", text))
        if text in self._fail_on:
            raise RuntimeError("kokoro crashed")
        return SimpleNamespace(
            path=f"{out_dir}/audio/{len(self.calls)}.wav", voice=voice, seconds=2.0
        )


IMG = assets.AssetRequest(type="image", prompt="hero", model="flux-schnell", width=1024, height=1024)
TTS = assets.AssetRequest(type="tts", text="hello", voice="af_heart")


def _to_url(path):
    return "/media/" + str(path)


# ── render: manifest shape, order, batching ───────────────────────────────────

def test_manifest_is_document_order_but_images_render_first():
    mgr = _FakeManager()
    manifest = assets.render(mgr, [TTS, IMG], out_dir="/m", to_url=_to_url)  # doc order: tts, image
    # Manifest preserves the document order the parser produced...
    assert [m["type"] for m in manifest] == ["tts", "image"]
    assert all(m["status"] == "ok" for m in manifest)
    # ...but rendering batched images BEFORE tts (one warm GPU slot, no evict/reload thrash).
    assert [c[0] for c in mgr.calls] == ["image", "tts"]


def test_manifest_records_url_and_metadata():
    mgr = _FakeManager()
    manifest = assets.render(mgr, [IMG, TTS], out_dir="/m", to_url=_to_url)
    img = next(m for m in manifest if m["type"] == "image")
    tts = next(m for m in manifest if m["type"] == "tts")
    assert img["url"].startswith("/media/") and img["model"] == "flux-schnell" and img["prompt"] == "hero"
    assert img["seconds"] == 1.0
    assert tts["url"].startswith("/media/") and tts["voice"] == "af_heart" and tts["text"] == "hello"
    assert tts["seconds"] == 2.0


# ── render: never-raises isolation + cancel ───────────────────────────────────

def test_one_asset_failure_does_not_abort_the_batch():
    mgr = _FakeManager(fail_on={"hero"})
    manifest = assets.render(mgr, [IMG, TTS], out_dir="/m", to_url=_to_url)
    by_type = {m["type"]: m for m in manifest}
    assert by_type["image"]["status"] == "failed" and "metal" in by_type["image"]["reason"]
    assert by_type["tts"]["status"] == "ok"  # the other asset still rendered


def test_render_never_raises_even_when_all_fail():
    mgr = _FakeManager(fail_on={"hero", "hello"})
    manifest = assets.render(mgr, [IMG, TTS], out_dir="/m", to_url=_to_url)
    assert all(m["status"] == "failed" for m in manifest)


def test_cancel_skips_remaining_without_spending_gpu():
    mgr = _FakeManager()
    events = []
    manifest = assets.render(
        mgr, [IMG, TTS], out_dir="/m", to_url=_to_url,
        should_cancel=lambda: True, on_event=events.append,
    )
    assert mgr.calls == [], "a cancel before the first asset must render nothing"
    assert all(m["status"] == "skipped" and m["reason"] == "cancelled" for m in manifest)
    assert [m["type"] for m in manifest] == ["image", "tts"]  # document order preserved
    # A skipped SSE frame is emitted for each skipped asset (the GUI shows partial state).
    assert {(e["status"], e["kind"]) for e in events if e.get("phase") == "asset"} == {
        ("skipped", "image"), ("skipped", "tts"),
    }


def test_render_emits_sse_event_frames():
    mgr = _FakeManager(fail_on={"hello"})
    events = []
    assets.render(mgr, [IMG, TTS], out_dir="/m", to_url=_to_url, on_event=events.append)
    seen = {(e["status"], e["kind"]) for e in events if e.get("phase") == "asset"}
    assert ("start", "image") in seen and ("done", "image") in seen
    assert ("start", "tts") in seen and ("failed", "tts") in seen


def test_render_empty_requests_is_empty_manifest():
    assert assets.render(_FakeManager(), [], out_dir="/m", to_url=_to_url) == []


# ── rewrite_delivered: cosmetic swap ──────────────────────────────────────────

def _block(payload):
    return "```asset\n" + json.dumps(payload) + "\n```"


def test_rewrite_swaps_rendered_image_for_an_embed():
    delivered = "Intro\n" + _block({"type": "image", "prompt": "hero"}) + "\nOutro"
    manifest = [{"type": "image", "status": "ok", "url": "/media/a.png", "prompt": "hero"}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "![hero](/media/a.png)" in out
    assert "```asset" not in out
    assert "Intro" in out and "Outro" in out  # surrounding prose intact


def test_rewrite_swaps_rendered_tts_for_a_caption():
    delivered = _block({"type": "tts", "text": "hello"})
    manifest = [{"type": "tts", "status": "ok", "url": "/media/a.wav", "text": "hello", "seconds": 2.0}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "/media/a.wav" in out and "```asset" not in out
    assert "audio" in out.lower()  # a reader can't play sound → labelled link


def test_rewrite_leaves_failed_or_unmatched_blocks_verbatim():
    delivered = _block({"type": "image", "prompt": "hero"})
    manifest = [{"type": "image", "status": "failed", "reason": "x", "prompt": "hero"}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "```asset" in out, "only successfully-rendered blocks are swapped"


def test_rewrite_matches_by_content_robust_to_order():
    delivered = (
        "A\n" + _block({"type": "image", "prompt": "first"}) + "\n"
        + _block({"type": "image", "prompt": "second"}) + "\nB"
    )
    # Manifest order independent of document order — pairing is by prompt, not position.
    manifest = [
        {"type": "image", "status": "ok", "url": "/media/2.png", "prompt": "second"},
        {"type": "image", "status": "ok", "url": "/media/1.png", "prompt": "first"},
    ]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "![first](/media/1.png)" in out and "![second](/media/2.png)" in out


def test_rewrite_no_ok_entries_returns_input_unchanged():
    delivered = "no markers here\n"
    assert assets.rewrite_delivered(delivered, []) == delivered
    assert assets.rewrite_delivered(delivered, [{"type": "image", "status": "failed"}]) == delivered


def test_rewrite_preserves_trailing_newline_and_prose_byte_faithfully():
    # split("\n")/join round-trip: a swap must not normalize trailing newlines or the
    # surrounding prose (verbatim except the swapped block).
    delivered = "Lead in.\n\n" + _block({"type": "image", "prompt": "hero"}) + "\n\nTail.\n"
    manifest = [{"type": "image", "status": "ok", "url": "/media/a.png", "prompt": "hero"}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert out == "Lead in.\n\n![hero](/media/a.png)\n\nTail.\n"
