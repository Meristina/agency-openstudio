"""Offline tests for the OpenMontage local video backend (the fusion brick A1).

Fully offline and Node-free: the Remotion subprocess is never actually spawned — the boundary
(`openmontage_backend._spawn_render`) is the monkeypatch seam (the `seedance._run_cloud` /
`_stub_ark` pattern), so these tests assert the *gates* around it: the local-first probe (node +
subtree + an EXISTING node_modules, so `npx` can never fall through to a registry fetch), the
fixed compute caps (timings are the renderer's, never the marker's), the marker `cuts` whitelist
(no media references, ever), the atomic complete-or-absent output, cancellation, and the
`AGENCY_STUDIO_VIDEO_BACKEND` dispatch through `ModelManager.generate_video`.
"""

import json
from pathlib import Path

import pytest

from agency_studio import assets, openmontage_backend as om, seedance
from agency_studio.engines.local_media import ModelManager, VideoResult


def _fake_composer(tmp_path, monkeypatch, *, node_modules=True, which=True):
    """Point the module at a fake remotion-composer checkout under tmp_path."""
    composer = tmp_path / "openmontage" / "remotion-composer"
    composer.mkdir(parents=True)
    (composer / "package.json").write_text("{}")
    if node_modules:
        (composer / "node_modules").mkdir()
    monkeypatch.setattr(om, "COMPOSER_DIR", composer)
    if which:
        monkeypatch.setattr(om.shutil, "which", lambda name: f"/usr/bin/{name}")
    return composer


ENTRY = seedance.VIDEO_MODELS["openmontage-remotion"]


# ── the probe: every missing prerequisite is a clean 501, never a network fetch ──
def test_unavailable_is_an_importerror():
    # So the server's optional-extra handler maps it to a 501 + hint (like SeedanceUnavailable).
    assert issubclass(om.OpenMontageUnavailable, ImportError)


def test_probe_without_node_raises(monkeypatch, tmp_path):
    _fake_composer(tmp_path, monkeypatch, which=False)
    monkeypatch.setattr(om.shutil, "which", lambda name: None)
    with pytest.raises(om.OpenMontageUnavailable, match="Node"):
        om._probe_local(ENTRY)


def test_probe_without_subtree_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(om.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(om, "COMPOSER_DIR", tmp_path / "missing" / "remotion-composer")
    with pytest.raises(om.OpenMontageUnavailable, match="remotion-composer"):
        om._probe_local(ENTRY)


def test_probe_without_node_modules_raises(monkeypatch, tmp_path):
    # Local-first: the studio never runs `npm install` itself, and an uninstalled composer must
    # 501 rather than let `npx remotion` fall through to a registry fetch mid-mission.
    _fake_composer(tmp_path, monkeypatch, node_modules=False)
    with pytest.raises(om.OpenMontageUnavailable, match="npm install"):
        om._probe_local(ENTRY)


def test_probe_passes_when_installed(monkeypatch, tmp_path):
    _fake_composer(tmp_path, monkeypatch)
    om._probe_local(ENTRY)  # no raise, no subprocess, no network


# ── fixed compute caps: props timings are the renderer's, never the marker's ─────
def test_build_props_prompt_only_fallback():
    props = om._build_props("why the sky is blue", None)
    assert props["theme"] == om.THEME
    assert len(props["cuts"]) == 1
    cut = props["cuts"][0]
    assert cut["type"] == "text_card" and cut["text"] == "why the sky is blue"
    assert (cut["in_seconds"], cut["out_seconds"]) == (0.0, om.FIXED_CUT_SECONDS)
    assert cut["source"] == ""   # a composition cut never references media


def test_build_props_assigns_fixed_sequential_slots():
    cuts = [{"type": "text_card", "text": f"scene {i}",
             "in_seconds": 0, "out_seconds": 9999} for i in range(3)]
    props = om._build_props("p", cuts)
    for i, cut in enumerate(props["cuts"]):
        # Marker-supplied timings are overwritten wholesale — duration is compute, i.e. cost.
        assert cut["in_seconds"] == i * om.FIXED_CUT_SECONDS
        assert cut["out_seconds"] == (i + 1) * om.FIXED_CUT_SECONDS
        assert cut["source"] == ""


def test_build_props_caps_cut_count():
    cuts = [{"type": "text_card", "text": "x"}] * (om.MAX_CUTS + 20)
    props = om._build_props("p", cuts)
    assert len(props["cuts"]) == om.MAX_CUTS
    assert props["cuts"][-1]["out_seconds"] == om.MAX_CUTS * om.FIXED_CUT_SECONDS


# ── the render: atomic output, cancel, failure → placeholder path ────────────────
def test_run_local_happy_path(monkeypatch, tmp_path):
    composer = _fake_composer(tmp_path, monkeypatch)
    calls = {}

    def fake_spawn(cmd, cwd, should_cancel=None):
        calls["cmd"], calls["cwd"] = cmd, cwd
        Path(cmd[5]).write_bytes(b"MP4DATA")     # remotion writes the .part target

    monkeypatch.setattr(om, "_spawn_render", fake_spawn)
    out = tmp_path / "videos" / "clip.mp4"
    om._run_local(om._load_local(ENTRY), ENTRY, prompt="a launch teaser", out_path=out)
    assert out.read_bytes() == b"MP4DATA"
    assert list(out.parent.glob("*.part.mp4")) == []          # renamed, not copied
    assert calls["cwd"] == str(composer)
    assert calls["cmd"][1:5] == ["remotion", "render", om._ENTRY, om._COMPOSITION]
    assert "--codec" in calls["cmd"] and "h264" in calls["cmd"]
    # The props temp file existed during the render and is gone after it.
    props_path = Path(calls["cmd"][calls["cmd"].index("--props") + 1])
    assert not props_path.exists()


def test_run_local_writes_sanitized_props(monkeypatch, tmp_path):
    _fake_composer(tmp_path, monkeypatch)
    seen = {}

    def fake_spawn(cmd, cwd, should_cancel=None):
        seen["props"] = json.loads(Path(cmd[cmd.index("--props") + 1]).read_text())
        Path(cmd[5]).write_bytes(b"MP4")

    monkeypatch.setattr(om, "_spawn_render", fake_spawn)
    om._run_local(om._load_local(ENTRY), ENTRY, prompt="p", out_path=tmp_path / "c.mp4",
                  cuts=[{"type": "stat_card", "stat": "8.1B", "subtitle": "people"}])
    cut = seen["props"]["cuts"][0]
    assert cut["type"] == "stat_card" and cut["stat"] == "8.1B"
    assert seen["props"]["audio"] == {} and seen["props"]["overlays"] == []


def test_run_local_failed_render_leaves_no_output(monkeypatch, tmp_path):
    _fake_composer(tmp_path, monkeypatch)

    def fake_spawn(cmd, cwd, should_cancel=None):
        Path(cmd[5]).write_bytes(b"HALF")        # a partial landed, then the child died
        raise RuntimeError("openmontage: remotion render failed — boom")

    monkeypatch.setattr(om, "_spawn_render", fake_spawn)
    out = tmp_path / "clip.mp4"
    with pytest.raises(RuntimeError, match="failed"):
        om._run_local(om._load_local(ENTRY), ENTRY, prompt="p", out_path=out)
    assert not out.exists()                       # complete or absent, never truncated
    assert list(tmp_path.glob("*.part.mp4")) == []


def test_run_local_no_output_file_raises(monkeypatch, tmp_path):
    _fake_composer(tmp_path, monkeypatch)
    monkeypatch.setattr(om, "_spawn_render", lambda cmd, cwd, should_cancel=None: None)
    with pytest.raises(RuntimeError, match="without producing"):
        om._run_local(om._load_local(ENTRY), ENTRY, prompt="p", out_path=tmp_path / "c.mp4")


def test_run_local_cancel_before_spawn(monkeypatch, tmp_path):
    _fake_composer(tmp_path, monkeypatch)
    monkeypatch.setattr(om, "_spawn_render",
                        lambda *a, **k: pytest.fail("spawned despite a pending cancel"))
    with pytest.raises(RuntimeError, match="cancelled"):
        om._run_local(om._load_local(ENTRY), ENTRY, prompt="p",
                      out_path=tmp_path / "c.mp4", should_cancel=lambda: True)


# ── the real subprocess primitive (no Node needed — plain Python children, so the
# same tests run on Windows CI where /bin/sh does not exist) ─────────────────────
def test_spawn_render_nonzero_exit_raises_with_stderr_tail(tmp_path):
    import sys
    with pytest.raises(RuntimeError, match="exploded"):
        om._spawn_render(
            [sys.executable, "-c", "import sys; print('exploded', file=sys.stderr); sys.exit(3)"],
            cwd=str(tmp_path))


def test_spawn_render_success_returns(tmp_path):
    import sys
    om._spawn_render([sys.executable, "-c", "raise SystemExit(0)"], cwd=str(tmp_path))


@pytest.mark.skipif(__import__("sys").platform == "win32",
                    reason="cancel kill uses POSIX process groups (os.killpg) — the "
                           "openmontage local renderer is POSIX-only; on Windows the "
                           "video family runs through the cloud backend (Brick 5 scope)")
def test_spawn_render_cancel_kills_promptly(tmp_path):
    import sys
    import time
    started = time.monotonic()
    with pytest.raises(RuntimeError, match="cancelled"):
        om._spawn_render([sys.executable, "-c", "import time; time.sleep(30)"],
                         cwd=str(tmp_path), should_cancel=lambda: True)
    assert time.monotonic() - started < 10   # killed at the first poll, not after 30 s


# ── the marker `cuts` whitelist (assets._clean_cuts) ─────────────────────────────
def test_clean_cuts_whitelists_content_fields_only():
    cuts = assets._clean_cuts({"cuts": [{
        "type": "hero_title", "text": "T", "subtitle": "S",
        "source": "/etc/passwd", "backgroundVideo": "secret.mp4",
        "backgroundImage": "x.png", "images": ["a.png"], "audio": {"src": "x.wav"},
        "in_seconds": 0, "out_seconds": 9999,
    }]})
    assert cuts == ({"type": "hero_title", "text": "T", "subtitle": "S"},)


def test_clean_cuts_drops_unknown_type_and_bad_shape():
    cuts = assets._clean_cuts({"cuts": [
        {"type": "screenshot_scene", "backgroundImage": "x.png"},   # media scene → never allowed
        "not-a-dict",
        {"text": "no type"},
        {"type": "text_card", "text": "kept"},
    ]})
    assert cuts == ({"type": "text_card", "text": "kept"},)


def test_clean_cuts_requires_the_scene_required_field():
    assert assets._clean_cuts({"cuts": [{"type": "stat_card", "subtitle": "no stat"}]}) == ()


def test_clean_cuts_invalid_callout_type_is_soft_dropped():
    cuts = assets._clean_cuts({"cuts": [{"type": "callout", "text": "t",
                                         "callout_type": "evil"}]})
    assert cuts == ({"type": "callout", "text": "t"},)


def test_clean_cuts_non_list_and_oversized_are_bounded():
    assert assets._clean_cuts({"cuts": "nope"}) == ()
    assert assets._clean_cuts({}) == ()
    many = [{"type": "text_card", "text": "x"}] * (assets.MARKER_MAX_CUTS + 5)
    assert len(assets._clean_cuts({"cuts": many})) == assets.MARKER_MAX_CUTS


def test_parse_markers_carries_cuts_through(tmp_path):
    delivered = (
        "Intro\n```asset\n"
        + json.dumps({"type": "video", "prompt": "teaser",
                      "cuts": [{"type": "text_card", "text": "Hello"}]})
        + "\n```\n"
    )
    reqs = assets.parse_markers(delivered, ["marketing"], allow_video=True)
    assert len(reqs) == 1
    assert reqs[0].type == "video" and reqs[0].cuts == ({"type": "text_card", "text": "Hello"},)
    # And without the opt-in, the marker is still dropped wholesale (backend-independent gate).
    assert assets.parse_markers(delivered, ["marketing"], allow_video=False) == []


def test_assets_render_forwards_cuts_to_the_manager(tmp_path):
    captured = {}

    class FakeManager:
        def generate_video(self, prompt, *, out_dir, should_cancel=None, cuts=None):
            captured["cuts"] = cuts
            out = Path(out_dir) / "v.mp4"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"MP4")
            return VideoResult(path=out, prompt=prompt, seconds=0.1, model="openmontage-remotion")

    req = assets.AssetRequest(type="video", prompt="p",
                              cuts=({"type": "text_card", "text": "Hello"},), block_index=0)
    manifest = assets.render(FakeManager(), [req], out_dir=tmp_path,
                             to_url=lambda p: f"/media/{Path(p).name}")
    assert manifest[0]["status"] == "ok"
    assert captured["cuts"] == [{"type": "text_card", "text": "Hello"}]


# ── ModelManager dispatch: the env selector reaches the local triple ─────────────
def test_generate_video_env_selects_local_backend(monkeypatch, tmp_path):
    monkeypatch.setenv(seedance.VIDEO_BACKEND_ENV, "openmontage-remotion")
    seen = {}

    def fake_run(backend, entry, *, prompt, out_path, should_cancel=None, cuts=None):
        seen["entry_id"], seen["cuts"] = entry.id, cuts
        out_path.write_bytes(b"MP4")

    monkeypatch.setattr(om, "_probe_local", lambda entry: None)
    monkeypatch.setattr(om, "_load_local", lambda entry: {"stub": True})
    monkeypatch.setattr(om, "_run_local", fake_run)
    mgr = ModelManager(tmp_path)
    result = mgr.generate_video("a teaser", cuts=[{"type": "text_card", "text": "Hi"}])
    assert result.model == "openmontage-remotion"
    assert seen["entry_id"] == "openmontage-remotion"
    assert seen["cuts"] == [{"type": "text_card", "text": "Hi"}]


def test_generate_video_cloud_never_receives_cuts(monkeypatch, tmp_path):
    # The cloud run() signature is untouched by the fusion: a cuts-bearing request against the
    # cloud default must not explode on an unexpected kwarg (cuts are composition-only).
    def fake_run(backend, entry, *, prompt, out_path, should_cancel=None):  # no cuts param
        out_path.write_bytes(b"MP4")

    monkeypatch.delenv(seedance.VIDEO_BACKEND_ENV, raising=False)
    monkeypatch.setattr(seedance, "_backend",
                        lambda entry: (lambda e: None, lambda e: {}, fake_run))
    mgr = ModelManager(tmp_path)
    result = mgr.generate_video("x", cuts=[{"type": "text_card", "text": "ignored"}])
    assert result.model == seedance.DEFAULT_VIDEO_MODEL


def test_generate_video_env_typo_fails_loud_before_any_render(monkeypatch, tmp_path):
    monkeypatch.setenv(seedance.VIDEO_BACKEND_ENV, "openmontage-typo")
    mgr = ModelManager(tmp_path)
    with pytest.raises(ValueError, match=seedance.VIDEO_BACKEND_ENV):
        mgr.generate_video("a clip")
