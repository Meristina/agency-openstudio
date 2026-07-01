"""Tests for the Wave-4 local retriever (`agency_studio/rag.py`).

Fully offline, mirroring the Wave 2/3 pattern: the only boundaries stubbed are the two
heavy/optional pieces — the embedding model (a deterministic hash-embed stands in for
MLX) and markitdown (the ingest text is provided directly). The real chunking, the real
SQLite store (its pure-Python cosine fallback — sqlite-vec is absent here), and the real
retrieve/context-clause logic run end-to-end without MLX, without markitdown, and without
network.
"""

import math

import pytest

from agency_studio import rag
from agency_studio.engines import models


# ── chunking ──────────────────────────────────────────────────────────────────

def test_chunk_markdown_is_heading_aware():
    md = "# Alpha\nfirst body line\n## Beta\nsecond body line"
    chunks = rag.chunk_markdown(md, target_words=200, overlap_words=20)
    titles = [t for t, _ in chunks]
    assert titles == ["Alpha", "Beta"]
    assert chunks[0][1] == "first body line"
    assert chunks[1][1] == "second body line"


def test_chunk_markdown_splits_long_section_with_overlap():
    body = " ".join(f"w{i}" for i in range(500))
    chunks = rag.chunk_markdown("# Big\n" + body, target_words=200, overlap_words=40)
    assert len(chunks) >= 2
    assert all(t == "Big" for t, _ in chunks)
    # The tail of chunk 0 reappears at the head of chunk 1 (the overlap carry).
    tail = chunks[0][1].split()[-40:]
    head = chunks[1][1].split()[:40]
    assert tail == head


def test_chunk_markdown_subdivides_a_single_long_line():
    # markitdown emits each PDF/docx paragraph as ONE physical line; a long one must be
    # split into target-sized chunks (not one oversized chunk the embedder would truncate).
    one_long_line = " ".join(f"w{i}" for i in range(500))
    chunks = rag.chunk_markdown("# Doc\n" + one_long_line, target_words=200, overlap_words=40)
    assert len(chunks) >= 3
    assert all(len(text.split()) <= 200 for _, text in chunks)  # none exceeds the budget


def test_chunk_markdown_rejects_overlap_ge_target():
    with pytest.raises(ValueError):
        rag.chunk_markdown("# x\nbody", target_words=50, overlap_words=50)


def test_chunk_markdown_ignores_blank_lines_and_pre_heading_text():
    md = "loose intro\n\n# Head\n\nreal body"
    chunks = rag.chunk_markdown(md)
    assert ("", "loose intro") in chunks
    assert ("Head", "real body") in chunks


# ── context clause ────────────────────────────────────────────────────────────

def test_build_context_clause_none_when_empty():
    assert rag.build_context_clause([]) is None


def test_build_context_clause_formats_numbered_excerpts():
    chunks = [
        rag.Chunk("d1", 0, "Solar Basics", "Panels convert sunlight.", score=0.9),
        rag.Chunk("d1", 1, "Costs", "Prices fell 90%.", score=0.7),
    ]
    clause = rag.build_context_clause(chunks)
    assert clause is not None
    assert "REFERENCE DOCUMENTS" in clause
    assert "[1] Solar Basics" in clause and "Panels convert sunlight." in clause
    assert "[2] Costs" in clause
    assert "do not invent" in clause.lower() or "not invent" in clause.lower()


# ── ingest → retrieve round-trip (fallback store) ─────────────────────────────

def _hash_embed(text: str, dim: int):
    """Deterministic bag-of-words embedding: bucket each lowercased word into ``dim`` and
    L2-normalize. Texts that share words end up close, so retrieval is meaningful without
    a real model."""
    v = [0.0] * dim
    for word in text.lower().split():
        v[hash(word) % dim] += 1.0
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


class _FakeManager:
    """Duck-typed stand-in for ModelManager: embeds with the hash-embed, honoring the
    model's dimensionality."""

    def embed(self, texts, *, model=models.DEFAULT_EMBED_MODEL, kind="document"):
        dim = models.embed_model(model).ndim
        return [_hash_embed(t, dim) for t in texts]


@pytest.fixture
def local_retriever(tmp_path, monkeypatch):
    # markitdown is optional + absent offline: stub the converter to return the raw bytes
    # as text, so ingest exercises everything downstream of the conversion.
    monkeypatch.setattr(rag, "_markitdown_to_text", lambda b, f: b.decode("utf-8"))
    return rag.LocalRetriever(_FakeManager(), db_path=tmp_path / "docs.db")


def test_store_uses_pure_python_fallback_when_sqlite_vec_absent(monkeypatch, tmp_path):
    # When sqlite-vec can't load, the store falls back to pure-Python cosine. Force the loader to
    # fail so this exercises the fallback deterministically whether or not sqlite-vec is installed
    # (it IS, via [studio], on the target Mac — same robustness fix as #36/#38).
    monkeypatch.setattr(rag, "_try_load_sqlite_vec", lambda conn: False)
    store = rag._VectorStore(tmp_path / "fallback.db", 8)
    assert store.has_vec is False


def test_ingest_then_retrieve_returns_the_relevant_chunk(local_retriever):
    doc = (
        "# Solar\nSolar panels convert sunlight into electricity efficiently.\n"
        "# Bananas\nBananas are a yellow tropical fruit rich in potassium.\n"
    )
    meta = local_retriever.ingest(doc.encode("utf-8"), "notes.md")
    assert meta.n_chunks == 2
    assert local_retriever.list_docs()[0].title == "Solar"

    hits = local_retriever.retrieve("how do solar panels use sunlight", k=1)
    assert len(hits) == 1
    assert hits[0].title == "Solar"
    assert "sunlight" in hits[0].text.lower()


def test_headingless_doc_cites_by_filename_not_uuid(local_retriever):
    # A document with no leading markdown heading yields empty section titles; the citation
    # label must fall back to the filename (a human label), never a bare uuid doc_id.
    local_retriever.ingest(b"plain text about wind turbines, no heading at all", "energy.txt")
    hits = local_retriever.retrieve("wind turbines", k=1)
    assert hits and hits[0].title == "energy.txt"
    clause = rag.build_context_clause(hits)
    assert "[1] energy.txt" in clause


def test_retrieve_is_empty_when_no_docs(local_retriever):
    assert local_retriever.retrieve("anything") == []


def test_retrieve_is_empty_for_blank_query(local_retriever):
    local_retriever.ingest(b"# H\nsome content here", "a.md")
    assert local_retriever.retrieve("   ") == []


def test_delete_removes_doc_and_its_chunks(local_retriever):
    meta = local_retriever.ingest(b"# H\nremovable content about turbines", "a.md")
    assert local_retriever.delete(meta.id) is True
    assert local_retriever.list_docs() == []
    assert local_retriever.retrieve("turbines") == []
    assert local_retriever.delete(meta.id) is False   # idempotent: already gone


def test_ingest_empty_document_raises(local_retriever):
    with pytest.raises(ValueError):
        local_retriever.ingest(b"   \n\n  ", "blank.md")


def test_store_is_usable_across_threads(local_retriever):
    # The server caches one retriever and calls it from different request threads. A
    # thread-bound sqlite connection (check_same_thread default) would raise here; the
    # store opens with check_same_thread=False + a lock, so cross-thread use is safe.
    import threading
    local_retriever.ingest(b"# H\nsolar panels and sunlight", "a.md")
    errors = []

    def _worker():
        try:
            local_retriever.list_docs()
            local_retriever.ingest(b"# H2\nwind turbines", "b.md")
            local_retriever.retrieve("solar sunlight", k=1)
        except Exception as exc:  # a thread-binding violation would land here
            errors.append(exc)

    t = threading.Thread(target=_worker)
    t.start()
    t.join()
    assert errors == []
    assert len(local_retriever.list_docs()) == 2


def test_markitdown_absent_raises_media_unavailable(monkeypatch):
    # markitdown ships in [studio]; when absent, the real converter must raise MediaUnavailable
    # (→ the server's 501). Force the import to fail so this holds whether or not [studio] is
    # installed — it IS on the target Mac, which would otherwise make this assertion fail (same
    # robustness fix as the visual/embed tests, #36/#38).
    import builtins
    from agency_studio.engines.local_media import MediaUnavailable
    real_import = builtins.__import__

    def _no_markitdown(name, *a, **k):
        if name == "markitdown":
            raise ImportError("no markitdown")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _no_markitdown)
    with pytest.raises(MediaUnavailable):
        rag._markitdown_to_text(b"data", "x.pdf")
