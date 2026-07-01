"""Offline tests for the Wave-6 visual-RAG brick (`agency_studio/visual.py`).

Fully offline, the exact parallel of `test_rag.py`: visual RAG adds ONE new stubbable model
boundary (the VLM caption) in FRONT of the existing embed boundary. Both are stubbed via a
duck-typed manager; the real chunking, the real SQLite store (pure-Python cosine fallback), and
the real retrieve/context-clause logic run end-to-end — no MLX, no VLM weights, no network. The
cloud backend's safety gates (https-only, env-key, explicit consent) are asserted without ever
touching the network.
"""

import math

import pytest

from agency_studio import rag, visual
from agency_studio.engines import models
from agency_studio.engines.local_media import ModelManager


def _hash_embed(text: str, dim: int):
    v = [0.0] * dim
    for word in text.lower().split():
        v[hash(word) % dim] += 1.0
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


class _FakeManager:
    """Duck-typed ModelManager: captions an image as its decoded bytes (the stub VLM), and embeds
    with the deterministic hash-embed. Records the cloud flag of the last caption call so a test
    can assert the off-machine consent threads correctly."""

    def __init__(self):
        self.caption_calls = []

    def caption(self, images, *, model=None, cloud=False):
        self.caption_calls.append({"n": len(images), "cloud": cloud})
        return [img.decode("utf-8") for img in images]

    def embed(self, texts, *, model=models.DEFAULT_EMBED_MODEL, kind="document"):
        dim = models.embed_model(model).ndim
        return [_hash_embed(t, dim) for t in texts]


@pytest.fixture
def visual_retriever(tmp_path):
    return visual.VisualRetriever(_FakeManager(), db_path=tmp_path / "visual.db")


def _img(caption: str) -> bytes:
    """A fake image whose bytes ARE its stub caption (the stub VLM decodes them back)."""
    return caption.encode("utf-8")


# ── the retriever satisfies the seam + reuses the RAG store ───────────────────
def test_visual_retriever_satisfies_the_retriever_protocol(visual_retriever):
    assert isinstance(visual_retriever, rag.Retriever)   # the @runtime_checkable Wave-6 seam


def test_visual_store_uses_pure_python_fallback_offline(visual_retriever):
    assert visual_retriever._store.has_vec is False


def test_ingest_captions_via_the_manager_and_stores_it(visual_retriever):
    meta = visual_retriever.ingest(_img("a red bicycle by a brick wall"), "bike.png")
    assert meta.filename == "bike.png" and meta.n_chunks >= 1
    # The caption reached the store (retrievable + shown in list_docs).
    docs = visual_retriever.list_docs()
    assert len(docs) == 1
    assert visual_retriever._manager.caption_calls == [{"n": 1, "cloud": False}]


def test_ingest_then_retrieve_returns_the_relevant_image(visual_retriever):
    visual_retriever.ingest(_img("solar panels converting sunlight into electricity"), "solar.png")
    visual_retriever.ingest(_img("a yellow banana tropical fruit rich in potassium"), "fruit.png")
    visual_retriever._manager.caption_calls.clear()   # forget the ingest-time caption calls
    hits = visual_retriever.retrieve("how do solar panels generate electricity", k=1)
    # The caption has no heading, so its chunk is titled by the filename (never a bare uuid).
    assert hits and hits[0].title == "solar.png" and "solar" in hits[0].text
    # Mission-time retrieval is a pure-local vector lookup — it must NEVER run the VLM (no caption,
    # so no possible off-machine call). This is the mission-path-can't-network safety invariant.
    assert visual_retriever._manager.caption_calls == []


def test_retrieve_empty_without_images_or_query(tmp_path):
    r = visual.VisualRetriever(_FakeManager(), db_path=tmp_path / "v.db")
    assert r.retrieve("anything") == []          # no images
    r.ingest(_img("a caption"), "x.png")
    assert r.retrieve("   ") == []               # blank query


def test_delete_removes_the_image_and_is_idempotent(visual_retriever):
    meta = visual_retriever.ingest(_img("a network diagram"), "diagram.png")
    assert visual_retriever.delete(meta.id) is True
    assert visual_retriever.list_docs() == []
    assert visual_retriever.delete(meta.id) is False


def test_empty_caption_raises(visual_retriever):
    with pytest.raises(ValueError):
        visual_retriever.ingest(_img("   "), "blank.png")


def test_build_visual_context_clause_labels_by_filename(visual_retriever):
    visual_retriever.ingest(_img("a bar chart of quarterly revenue growth"), "chart.png")
    chunks = visual_retriever.retrieve("quarterly revenue", k=1)
    clause = visual.build_visual_context_clause(chunks)
    assert clause is not None
    assert "chart.png" in clause                 # cited by a human label, never a bare uuid
    assert visual.build_visual_context_clause([]) is None   # None-contract (byte-identical no-op)


# ── off-machine consent threads through ingest → caption ──────────────────────
def test_cloud_consent_threads_to_the_caption_call(visual_retriever):
    visual_retriever.ingest(_img("an off-machine caption"), "cloud.png", cloud=True)
    assert visual_retriever._manager.caption_calls == [{"n": 1, "cloud": True}]


# ── [visual] absent + the real caption dispatch degrade cleanly ───────────────
def test_visual_unavailable_is_an_importerror():
    assert issubclass(visual.VisualUnavailable, ImportError)


def _force_mlx_absent(monkeypatch):
    """Make ``import mlx_vlm`` fail, so ``visual._probe_local`` raises ``VisualUnavailable`` on ANY
    machine — the offline-CI condition these tests assert — whether or not the ``[visual]`` extra is
    actually installed (it IS, on the Apple-Silicon target Mac, which would otherwise load a real 7B
    VLM and fail deep inside mlx-vlm). Patches ``builtins.__import__`` (process-global, so it also
    covers a caption running on the server's worker thread), NOT ``visual._probe_local`` — the
    ``_VISUAL_BACKENDS`` dispatch table binds a direct reference to the probe that a module-attr
    patch would never reach. Returns nothing; the patch auto-reverts at test teardown."""
    import builtins
    real_import = builtins.__import__

    def _no_mlx(name, *a, **k):
        if name == "mlx_vlm":
            raise ImportError("no mlx_vlm")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _no_mlx)


def test_local_backend_absent_raises_visual_unavailable(monkeypatch):
    # The real local probe: mlx_vlm forced absent → VisualUnavailable (→ 501).
    _force_mlx_absent(monkeypatch)
    with pytest.raises(visual.VisualUnavailable):
        visual._probe_local()


def test_real_manager_caption_local_default_hits_the_local_backend(monkeypatch, tmp_path):
    # A REAL ModelManager + cloud=False must dispatch to the LOCAL backend (which, with mlx_vlm
    # forced absent, raises VisualUnavailable) — never a cloud/network attempt.
    _force_mlx_absent(monkeypatch)

    def _boom_cloud(*a, **k):
        raise AssertionError("the cloud backend must not run without explicit consent")

    monkeypatch.setattr(visual, "_run_cloud", _boom_cloud)
    monkeypatch.setattr(visual, "_probe_cloud", _boom_cloud)
    mgr = ModelManager(tmp_path)
    with pytest.raises(visual.VisualUnavailable):     # from the local probe (mlx_vlm absent)
        mgr.caption([b"an image"], cloud=False)


def test_real_manager_caption_dispatches_on_the_cloud_flag(monkeypatch, tmp_path):
    # A REAL ModelManager must route on the `cloud` flag. With no API key set (and mlx_vlm forced
    # absent), each backend's probe raises a DISTINCT message — cloud=True hits the cloud probe
    # (API key), cloud=False hits the local probe (mlx-vlm) — proving the dispatch actually selects
    # the backend from the flag, deterministically whether or not the [visual] extra is installed.
    _force_mlx_absent(monkeypatch)
    monkeypatch.delenv(visual.CLOUD_API_KEY_ENV, raising=False)
    mgr = ModelManager(tmp_path)
    with pytest.raises(visual.VisualUnavailable, match=visual.CLOUD_API_KEY_ENV):
        mgr.caption([b"an image"], cloud=True)     # → _probe_cloud (missing API key)
    with pytest.raises(visual.VisualUnavailable, match="mlx-vlm"):
        mgr.caption([b"an image"], cloud=False)    # → _probe_local (missing [visual] extra)


def test_visual_model_unknown_id_raises():
    with pytest.raises(ValueError, match="unknown visual model"):
        visual.visual_model("nope")


def test_run_local_call_surface(monkeypatch):
    """Lock in the mlx-vlm 0.6.3 caption call surface (the live-validated fix): bytes → a temp file
    PATH (never raw bytes), prompt via apply_chat_template(num_images=1) so the image placeholder is
    inserted, generate(image=[path]).text, and the temp file unlinked afterwards. Stubs the two
    mlx-vlm entry points via sys.modules so no model loads — deterministic on any machine. Guards
    the exact regression this replaced ('tuple index out of range' from passing bytes + a
    non-templated prompt)."""
    import os
    import sys
    import types
    seen = {}

    def _fake_apply(processor, config, prompt, *, num_images=0, **k):
        seen.update(num_images=num_images, config=config)
        return f"<img*{num_images}> {prompt}"

    def _fake_generate(model, processor, prompt, image=None, verbose=False, max_tokens=None, **k):
        seen.update(prompt=prompt, image=image, max_tokens=max_tokens,
                    path_exists=bool(image) and all(os.path.isfile(p) for p in image))
        return types.SimpleNamespace(text="  a lake at sunset  ")

    fake_mlx = types.ModuleType("mlx_vlm")
    fake_mlx.generate = _fake_generate
    fake_pu = types.ModuleType("mlx_vlm.prompt_utils")
    fake_pu.apply_chat_template = _fake_apply
    monkeypatch.setitem(sys.modules, "mlx_vlm", fake_mlx)
    monkeypatch.setitem(sys.modules, "mlx_vlm.prompt_utils", fake_pu)

    model = types.SimpleNamespace(config={"model_type": "qwen2_5_vl"})
    out = visual._run_local((model, object()), visual.VISUAL_MODELS["qwen3-vl-local"], images=[b"\x89PNGfake"])

    assert out == ["a lake at sunset"]                         # GenerationResult.text, stripped
    assert seen["num_images"] == 1                             # image placeholder inserted
    assert seen["config"] is model.config                     # model.config threaded to the template
    assert isinstance(seen["image"], list) and len(seen["image"]) == 1   # image=[path], NOT bytes
    assert seen["path_exists"]                                 # a real file path existed during the call
    assert seen["max_tokens"] == visual._CAPTION_MAX_TOKENS
    assert not os.path.isfile(seen["image"][0])               # temp file unlinked afterwards


# ── the OPTIONAL cloud backend's safety gates (network-free) ──────────────────
def test_cloud_backend_requires_https_endpoint():
    bad = visual.VisualModel(id="x", label="x", backend="cloud",
                             endpoint="http://insecure.example/v1", api_model="m")
    with pytest.raises(ValueError, match="https"):
        visual._probe_cloud(bad)


def test_cloud_backend_requires_env_key(monkeypatch):
    monkeypatch.delenv(visual.CLOUD_API_KEY_ENV, raising=False)
    with pytest.raises(visual.VisualUnavailable):
        visual._probe_cloud(visual.VISUAL_MODELS["qwen3-vl-cloud"])


def test_cloud_run_never_leaks_the_key(monkeypatch):
    # PLACEHOLDER coverage: _run_cloud is a deferred stub that raises before building any request,
    # so this can only catch a hardcoded secret in that one message — it does NOT exercise a real
    # request/logging path (there is none yet). The genuine no-leak guarantee MUST be re-audited
    # with a redaction test when the live cloud POST lands (see docs/WAVE6-PLAN.md Brick 4).
    monkeypatch.setenv(visual.CLOUD_API_KEY_ENV, "super-secret-key-value")
    entry = visual.VISUAL_MODELS["qwen3-vl-cloud"]
    visual._probe_cloud(entry)   # passes (https + key present), no network
    with pytest.raises(visual.VisualUnavailable) as exc:
        visual._run_cloud(visual._load_cloud(entry), entry, images=[b"img"])
    assert "super-secret-key-value" not in str(exc.value)
