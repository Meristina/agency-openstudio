"""Tests for the Wave-3 asset render half — ``assets.render`` and ``rewrite_delivered``.

Fully offline: a fake ModelManager records calls and returns canned results (no real
model loads, no GPU). These pin the render contract — document-order manifest, images
rendered before TTS, never-raises per-asset isolation, cancel→skip, SSE event frames —
and the cosmetic rewrite (match each block by its source-block ordinal — rendered → clean
reference, attempted-but-failed/skipped → neutral placeholder, parse-dropped → stripped, so
no raw ```asset fence ever survives into the deliverable).
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


def test_partial_cancel_keeps_rendered_and_latches_skip_for_the_rest():
    # The realistic Stop: the user clicks mid-batch. Assets already rendered stay 'ok';
    # the rest become 'skipped'. Polls go False (before the image) then True (from the
    # first tts on), and the latch skips the SECOND tts WITHOUT re-polling.
    mgr = _FakeManager()
    events = []
    polls = {"n": 0}

    def should_cancel():
        polls["n"] += 1
        return polls["n"] > 1

    tts2 = assets.AssetRequest(type="tts", text="world", voice="af_heart")
    manifest = assets.render(
        mgr, [IMG, TTS, tts2], out_dir="/m", to_url=_to_url,
        should_cancel=should_cancel, on_event=events.append,
    )
    assert mgr.calls == [("image", "hero")], "only the pre-Stop image spent GPU time"
    assert [(m["type"], m["status"]) for m in manifest] == [
        ("image", "ok"), ("tts", "skipped"), ("tts", "skipped"),
    ]  # document order, partial manifest
    assert all(m["reason"] == "cancelled" for m in manifest if m["status"] == "skipped")
    assert polls["n"] == 2, "the latch skips the rest without re-polling should_cancel"
    asset_frames = {(e["status"], e["kind"]) for e in events if e.get("phase") == "asset"}
    assert ("done", "image") in asset_frames and ("skipped", "tts") in asset_frames


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
    manifest = [{"type": "image", "status": "ok", "url": "/media/a.png", "prompt": "hero", "block": 0}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "![hero](/media/a.png)" in out
    assert "```asset" not in out
    assert "Intro" in out and "Outro" in out  # surrounding prose intact


def test_rewrite_swaps_rendered_tts_for_a_caption():
    delivered = _block({"type": "tts", "text": "hello"})
    manifest = [{"type": "tts", "status": "ok", "url": "/media/a.wav", "text": "hello", "seconds": 2.0, "block": 0}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "/media/a.wav" in out and "```asset" not in out
    assert "audio" in out.lower()  # a reader can't play sound → labelled link


def test_rewrite_replaces_failed_block_with_a_placeholder_not_raw():
    # A render that was ATTEMPTED but failed (backend crash) leaves a neutral breadcrumb, not
    # the raw JSON fence — the prose may reference the asset, so a silent hole would dangle.
    delivered = _block({"type": "image", "prompt": "hero"})
    manifest = [{"type": "image", "status": "failed", "reason": "x", "prompt": "hero", "block": 0}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "```asset" not in out, "no raw fence survives"
    assert out == "_[image unavailable]_"


def test_rewrite_replaces_skipped_block_with_a_placeholder():
    # A Stop mid-render records status='skipped'; that attempted asset also gets a placeholder.
    delivered = _block({"type": "tts", "text": "hello"})
    manifest = [{"type": "tts", "status": "skipped", "reason": "cancelled", "block": 0}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "```asset" not in out
    assert out == "_[audio narration unavailable]_"


def test_rewrite_strips_parse_dropped_block_with_no_manifest_entry():
    # A marker dropped at the parse boundary (off-route / over-cap / non-allowlisted / malformed)
    # has NO manifest entry — an illegitimate marker the reader should never see. It is stripped
    # entirely (not placeholdered): removing the fence line collapses it out of the deliverable.
    delivered = "Before\n" + _block({"type": "tts", "text": "off route"}) + "\nAfter"
    out = assets.rewrite_delivered(delivered, [])  # empty manifest = nothing rendered/attempted
    assert "```asset" not in out and "off route" not in out
    assert out == "Before\nAfter"


def test_rewrite_collapses_the_blank_a_stripped_block_leaves_behind():
    # A parse-dropped block wrapped in blank lines (the markdown norm) must not fuse the two
    # surrounding blanks into a double gap once its fence is stripped — one blank is swallowed.
    delivered = "Lead.\n\n" + _block({"type": "tts", "text": "off route"}) + "\n\nTail."
    out = assets.rewrite_delivered(delivered, [])
    assert out == "Lead.\n\nTail."


def test_rewrite_surgically_strips_an_unterminated_opener_keeping_trailing_prose():
    # #23: a ```asset opener with NO closing fence is stripped surgically — the opener + its
    # leading marker JSON go, the unbounded prose that follows is preserved.
    delivered = ("Intro\n```asset\n" + json.dumps({"type": "image", "prompt": "hero"})
                 + "\ntrailing prose the reader still needs")
    out = assets.rewrite_delivered(delivered, [])
    assert "```asset" not in out and '"prompt"' not in out, "opener + marker JSON removed"
    assert out == "Intro\ntrailing prose the reader still needs", "trailing prose kept"


def test_rewrite_strips_unterminated_opener_with_multiline_marker_json():
    # The marker may be pretty-printed across lines; _marker_end accumulates until the object
    # closes, so the whole marker (and only the marker) is removed.
    delivered = 'Lead.\n```asset\n{\n  "type": "tts",\n  "text": "hi"\n}\nAfter the marker.'
    out = assets.rewrite_delivered(delivered, [])
    assert "```asset" not in out and '"text"' not in out
    assert out == "Lead.\nAfter the marker."


def test_rewrite_strips_first_of_back_to_back_openers_and_renders_the_second():
    # Back-to-back openers: the first is unterminated (bounded by the 2nd), the second is a
    # well-formed rendered block. The stray first is stripped; the valid second becomes an embed.
    delivered = (
        "```asset\n" + json.dumps({"type": "image", "prompt": "stray"}) + "\n"
        + _block({"type": "image", "prompt": "real"})
    )
    reqs = assets.parse_markers(delivered, ["marketing"])
    assert [r.prompt for r in reqs] == ["real"], "only the well-formed block parses to a request"
    manifest = [{"type": "image", "status": "ok", "url": "/media/r.png", "prompt": "real",
                 "block": reqs[0].block_index}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "```asset" not in out and "stray" not in out, "the stray first opener is stripped"
    assert out.count("![real](/media/r.png)") == 1, "the well-formed second block is the only embed"


def test_rewrite_strips_only_the_first_object_marker_preserving_following_content():
    # Per the marker convention (one opener → one object), an unterminated opener strips the
    # opener + the FIRST JSON object only. Any further JSON the model wrote (legit data, or a
    # second object) is PRESERVED, never guessed-away — the fence goes, real content stays.
    delivered = ('Intro\n```asset\n' + json.dumps({"type": "image", "prompt": "hero"}) + "\n"
                 + json.dumps({"revenue": 1000, "users": 42}) + "\ntrailing")
    out = assets.rewrite_delivered(delivered, [])
    assert "```asset" not in out, "the fence is stripped"
    assert '"prompt"' not in out, "the first object (the marker) is removed"
    assert '"revenue": 1000' in out, "a following data object is preserved, not deleted"
    assert out.endswith("trailing")


def test_rewrite_preserves_prose_on_the_markers_closing_line():
    # Char-precise: text after the closing brace ON THE SAME LINE is preserved, not eaten with
    # the marker line.
    delivered = 'A\n```asset\n{"type": "tts", "text": "hi"} Here is the narration.\nnext'
    out = assets.rewrite_delivered(delivered, [])
    assert "```asset" not in out and '"text"' not in out
    assert "Here is the narration." in out and out.endswith("next")


def test_rewrite_strips_bare_back_to_back_openers_without_leaking_a_fence():
    # A bare stray opener immediately followed by a well-formed block (empty region between the
    # two openers): the bare first opener is stripped, so no raw fence leaks.
    delivered = "Intro\n```asset\n" + _block({"type": "image", "prompt": "real"}) + "\nEnd"
    reqs = assets.parse_markers(delivered, ["marketing"])
    assert [r.prompt for r in reqs] == ["real"]
    manifest = [{"type": "image", "status": "ok", "url": "/media/r.png", "prompt": "real",
                 "block": reqs[0].block_index}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "```asset" not in out, "the bare first opener is stripped, no fence leaks"
    assert out.count("![real](/media/r.png)") == 1


def test_rewrite_does_not_over_strip_prose_after_the_marker():
    # raw_decode stops at the first value's end, so reader-facing prose after the marker — even a
    # line that is itself valid JSON — is never scanned into the stripped region.
    delivered = 'A\n```asset\n{"type":"tts","text":"hi"}\nThe result was [1, 2, 3] items.'
    out = assets.rewrite_delivered(delivered, [])
    assert out == "A\nThe result was [1, 2, 3] items.", "trailing prose (incl. bracketed text) kept"


def test_rewrite_leaves_unterminated_opener_with_non_marker_first_object_verbatim():
    # The first object after a stray opener is stripped ONLY if it is a real asset marker
    # (type image/tts). A legitimate non-marker data object must NOT be deleted — the opener
    # falls to verbatim, losing no reader content (fence survives, documented residual).
    delivered = 'Intro\n```asset\n' + json.dumps({"revenue": 1000, "users": 42}) + "\ntrailing"
    out = assets.rewrite_delivered(delivered, [])
    assert out == delivered, "a non-marker data object is preserved verbatim, never stripped"


def test_rewrite_leaves_unterminated_opener_with_malformed_json_verbatim():
    # Residual: an unterminated opener whose region doesn't begin with a parseable object can't
    # be bounded (stripping would eat the unbounded tail), so it is left verbatim — the edge.
    delivered = "Intro\n```asset\n{not valid json,, no close\nmore prose"
    out = assets.rewrite_delivered(delivered, [])
    assert out == delivered, "malformed unterminated marker stays verbatim (can't bound the strip)"


def test_rewrite_leaves_unterminated_opener_not_beginning_with_an_object_verbatim():
    # If a non-object line precedes the marker, the region doesn't *begin* with an object, so we
    # can't safely bound it — fall back to verbatim rather than delete-until-a-later-brace.
    delivered = 'Intro\n```asset\n[1, 2, 3]\n{"type": "image", "prompt": "hero"}\ntail'
    out = assets.rewrite_delivered(delivered, [])
    assert out == delivered, "region not starting with an object → verbatim (documented residual)"


def test_rewrite_strips_over_cap_block_while_swapping_the_rendered_ones():
    # Mixed mission: two rendered images (ok) + a third over-cap block with no manifest entry.
    delivered = (
        _block({"type": "image", "prompt": "one"}) + "\n"
        + _block({"type": "image", "prompt": "two"}) + "\n"
        + _block({"type": "image", "prompt": "three"})  # over MAX_IMAGES → dropped, no entry
    )
    manifest = [
        {"type": "image", "status": "ok", "url": "/media/1.png", "prompt": "one", "block": 0},
        {"type": "image", "status": "ok", "url": "/media/2.png", "prompt": "two", "block": 1},
    ]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "```asset" not in out and "three" not in out, "the over-cap fence is stripped"
    assert "![one](/media/1.png)" in out and "![two](/media/2.png)" in out


def test_rewrite_pairs_by_block_ordinal_independent_of_manifest_order():
    delivered = (
        "A\n" + _block({"type": "image", "prompt": "first"}) + "\n"
        + _block({"type": "image", "prompt": "second"}) + "\nB"
    )
    # Manifest order independent of document order — pairing is by the source-block ordinal
    # (block 0 = "first", block 1 = "second"), not by manifest position or prompt content.
    manifest = [
        {"type": "image", "status": "ok", "url": "/media/2.png", "prompt": "second", "block": 1},
        {"type": "image", "status": "ok", "url": "/media/1.png", "prompt": "first", "block": 0},
    ]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "![first](/media/1.png)" in out and "![second](/media/2.png)" in out


def test_rewrite_keeps_identical_prompt_blocks_distinct_by_ordinal():
    # Two blocks with the SAME prompt each pair to their own entry by block ordinal — they
    # can never collapse onto one url or cross-match (the old content-matching failure mode).
    delivered = _block({"type": "image", "prompt": "hero"}) + "\n" + _block({"type": "image", "prompt": "hero"})
    manifest = [
        {"type": "image", "status": "ok", "url": "/media/1.png", "prompt": "hero", "block": 0},
        {"type": "image", "status": "ok", "url": "/media/2.png", "prompt": "hero", "block": 1},
    ]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "![hero](/media/1.png)" in out and "![hero](/media/2.png)" in out
    assert out.count("/media/1.png") == 1 and out.count("/media/2.png") == 1
    assert "```asset" not in out


def test_parser_and_rewrite_agree_on_crlf_fences_no_drift():
    # Anti-drift: a block the parser detects (and renders) must be the SAME block rewrite
    # swaps — including under CRLF. Both now walk one shared scanner; previously the two
    # used different splitters (splitlines vs split("\n")) and could disagree, leaving raw
    # JSON of an already-rendered asset visible.
    delivered = 'Intro\r\n```asset\r\n{"type": "image", "prompt": "hero"}\r\n```\r\nOutro'
    reqs = assets.parse_markers(delivered, ["marketing"])
    assert [r.type for r in reqs] == ["image"], "parser detects the CRLF-fenced block"
    assert reqs[0].block_index == 0, "parser stamps the source-block ordinal"
    manifest = [{"type": "image", "status": "ok", "url": "/media/a.png", "prompt": "hero", "block": 0}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "![hero](/media/a.png)" in out and "```asset" not in out, "rewrite swaps the same block"


def test_rewrite_escapes_untrusted_caption_so_it_cannot_inject_a_link():
    # A crafted prompt must not break out of ![alt](url) and splice in an external image.
    evil = "x](http://evil/p.png)![y"
    delivered = _block({"type": "image", "prompt": evil})
    manifest = [{"type": "image", "status": "ok", "url": "/media/a.png", "prompt": evil, "block": 0}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "](http://evil/p.png)" not in out  # the injected url never becomes an active ref
    assert out.count("](/media/a.png)") == 1  # the real, server-generated url is the only embed
    assert "\\]" in out and "\\(" in out  # the metacharacters were escaped, not left active


def test_rewrite_no_markers_returns_input_unchanged():
    # A deliverable with no ```asset fence at all is returned byte-for-byte (fast path),
    # regardless of what the manifest happens to contain.
    delivered = "no markers here\n"
    assert assets.rewrite_delivered(delivered, []) == delivered
    assert assets.rewrite_delivered(delivered, [{"type": "image", "status": "failed"}]) == delivered


def test_rewrite_ignores_ok_entry_without_a_block_ordinal():
    # Defensive: an ok entry that carries no (or a non-int) ``block`` cannot be paired to a
    # source block safely, so it is left out of the index — its block then has no pairable
    # entry and is stripped like any parse-dropped fence (never guessed onto by content, and
    # never left as a raw fence).
    delivered = _block({"type": "image", "prompt": "hero"})
    manifest = [{"type": "image", "status": "ok", "url": "/media/a.png", "prompt": "hero"}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert "```asset" not in out and "/media/a.png" not in out  # not paired → fence stripped
    assert out == ""


def test_rewrite_does_not_cross_match_a_rejected_block_onto_a_valid_twin():
    # End-to-end regression: a REJECTED image marker (non-allowlisted model → dropped at
    # parse, no manifest entry) immediately followed by a VALID marker with the SAME prompt.
    # The old content-matcher gave the rejected block's slot the rendered url and left the
    # real block raw. Ordinal pairing keeps the rendered embed on the valid block (#1) only.
    delivered = (
        _block({"type": "image", "prompt": "hero", "model": "boogu-base"}) + "\n"
        + _block({"type": "image", "prompt": "hero", "model": "flux-schnell"})
    )
    reqs = assets.parse_markers(delivered, ["marketing"])
    assert [r.block_index for r in reqs] == [1], "only the valid block survives parse, at ordinal 1"
    mgr = _FakeManager()
    manifest = assets.render(mgr, reqs, out_dir="/m", to_url=_to_url)
    assert manifest[0]["block"] == 1 and manifest[0]["status"] == "ok"
    out = assets.rewrite_delivered(delivered, manifest)
    # block 0 (rejected, no manifest entry) is stripped; block 1 (valid) becomes the only embed.
    assert "```asset" not in out and '"boogu-base"' not in out, "the rejected block is stripped"
    assert out.count("![hero](") == 1, "exactly one embed, on the valid block"


def test_rewrite_preserves_trailing_newline_and_prose_byte_faithfully():
    # split("\n")/join round-trip: a swap must not normalize trailing newlines or the
    # surrounding prose (verbatim except the swapped block).
    delivered = "Lead in.\n\n" + _block({"type": "image", "prompt": "hero"}) + "\n\nTail.\n"
    manifest = [{"type": "image", "status": "ok", "url": "/media/a.png", "prompt": "hero", "block": 0}]
    out = assets.rewrite_delivered(delivered, manifest)
    assert out == "Lead in.\n\n![hero](/media/a.png)\n\nTail.\n"
