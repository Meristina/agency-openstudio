"""Tests for the Wave-6 knowledge-graph brick (`agency_studio/knowledge.py`).

Fully offline, mirroring the Wave 2/3/4/5 pattern: the only boundary stubbed is the one
reasoning piece — the `Extractor` (text→triples, default via the `claude` CLI brain) — injected
as a deterministic stub (or, for the default extractor's own tests, its subprocess boundary is
stubbed). The real graph store (upsert/dedup/weight), token seeding, 1-hop neighbourhood, and
context-clause formatting all run end-to-end without any model and without invoking the CLI.
"""

from pathlib import Path

import pytest

from agency_studio import knowledge as kg


# ── helpers ─────────────────────────────────────────────────────────────────────

class _StubExtractor:
    """A deterministic stand-in for the live extractor (the `claude` CLI path): returns a fixed
    triple list per call, recording every (text, source_ref) it saw."""

    def __init__(self, triples, record=None):
        self._triples = triples
        self.record = record if record is not None else []

    def extract(self, text, source_ref):
        self.record.append((text, source_ref))
        return list(self._triples)


def _retriever(tmp_path, triples, record=None) -> kg.GraphRetriever:
    return kg.GraphRetriever(_StubExtractor(triples, record), db_path=tmp_path / "kg.db")


_TRIPLES = [
    kg.Triple("Acme Corp", "acquired", "Beta Labs"),
    kg.Triple("Beta Labs", "builds", "Widget Engine"),
    kg.Triple("Widget Engine", "depends on", "Rust Toolchain"),
]


# ── text helpers (pure) ──────────────────────────────────────────────────────────

def test_tokens_drops_stopwords_and_short_tokens():
    assert kg._tokens("The Widget Engine and a Rust toolchain") == ["widget", "engine", "rust", "toolchain"]


def test_norm_collapses_whitespace_and_caps_length():
    assert kg._norm("  a   b\n c ", 100) == "a b c"
    assert kg._norm("x" * 500, 10) == "x" * 10


def test_norm_empty_is_empty():
    assert kg._norm("", 100) == ""
    assert kg._norm(None, 100) == ""


# ── store: upsert / dedup / weight ───────────────────────────────────────────────

def test_build_stores_triples(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)
    n = gr.build_from_texts([("Acme news", "doc:1")])
    assert n == 3
    stats = gr.stats()
    assert stats["nodes"] == 4   # Acme, Beta Labs, Widget Engine, Rust Toolchain
    assert stats["edges"] == 3


def test_repeat_triple_bumps_weight_not_count(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)
    gr.build_from_texts([("t1", "doc:1"), ("t2", "doc:2")])  # same triples twice
    stats = gr.stats()
    assert stats["edges"] == 3            # deduped, not doubled
    # Beta Labs appears in two triples per pass × two passes = weight 4; it tops the list.
    assert stats["top_entities"][0]["label"] == "Beta Labs"
    assert stats["top_entities"][0]["weight"] == 4.0


def test_case_folds_to_one_entity(tmp_path):
    gr = _retriever(tmp_path, [kg.Triple("Acme", "is", "X"), kg.Triple("acme", "is", "Y")])
    gr.build_from_texts([("t", "doc:1")])
    # "Acme"/"acme" collapse to one node; first-seen casing kept.
    labels = [e["label"] for e in gr.stats()["top_entities"]]
    assert labels.count("Acme") == 1
    assert "acme" not in labels


def test_blank_and_self_loop_and_partial_triples_skipped(tmp_path):
    gr = _retriever(tmp_path, [
        kg.Triple("", "rel", "B"),         # empty subject
        kg.Triple("A", "", "B"),           # empty relation
        kg.Triple("A", "rel", ""),         # empty object
        kg.Triple("Node", "rel", "node"),  # self-loop (case-insensitive)
        kg.Triple("A", "rel", "B"),        # the one good triple
    ])
    assert gr.build_from_texts([("t", "doc:1")]) == 1


def test_blank_text_is_not_extracted(tmp_path):
    rec = []
    gr = _retriever(tmp_path, _TRIPLES, rec)
    assert gr.build_from_texts([("   ", "doc:1"), ("", "doc:2")]) == 0
    assert rec == []   # extractor never called on blank text


# ── seeding + neighbourhood ──────────────────────────────────────────────────────

def test_retrieve_seeds_and_expands_one_hop(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)
    gr.build_from_texts([("t", "doc:1")])
    sub = gr.retrieve("what does the Widget Engine depend on")
    labels = {n.label for n in sub.nodes}
    assert "Widget Engine" in labels
    assert "Rust Toolchain" in labels   # 1-hop neighbour via "depends on"
    assert "Beta Labs" in labels        # 1-hop neighbour via "builds"


def test_retrieve_blank_query_is_empty(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)
    gr.build_from_texts([("t", "doc:1")])
    sub = gr.retrieve("   ")
    assert sub.nodes == [] and sub.edges == []


def test_retrieve_no_match_is_empty(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)
    gr.build_from_texts([("t", "doc:1")])
    sub = gr.retrieve("completely unrelated xylophone topic")
    assert sub.nodes == [] and sub.edges == []


def test_retrieve_over_unbuilt_graph_is_empty(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)  # never built
    assert gr.retrieve("Widget Engine").nodes == []


def test_neighborhood_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(kg, "MAX_NEIGHBORS", 2)
    hub = [kg.Triple("Hub", "links", f"Leaf{i}") for i in range(10)]
    gr = _retriever(tmp_path, hub)
    gr.build_from_texts([("t", "doc:1")])
    sub = gr.retrieve("Hub")
    assert len(sub.edges) == 2   # capped, even though Hub has 10 edges


# ── context clause (default-None contract + formatting) ──────────────────────────

def test_clause_none_when_subgraph_empty():
    assert kg.build_kg_context_clause(kg.Subgraph([], [])) is None


def test_clause_none_when_nodes_have_no_edges():
    # A node with no relation in the subgraph is not worth a citation → still None.
    lone = kg.Subgraph([kg.Node(1, "Lonely", "entity", 1.0)], [])
    assert kg.build_kg_context_clause(lone) is None


def test_clause_formats_entities_and_relations(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)
    gr.build_from_texts([("t", "doc:1")])
    clause = kg.build_kg_context_clause(gr.retrieve("Widget Engine"))
    assert clause is not None
    assert "KNOWLEDGE GRAPH" in clause
    assert "[1]" in clause and "[2]" in clause
    assert "—depends on→ Rust Toolchain" in clause


def test_clause_carries_do_not_obey_guidance(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)
    gr.build_from_texts([("t", "doc:1")])
    clause = kg.build_kg_context_clause(gr.retrieve("Widget Engine"))
    assert "Do NOT invent" in clause


def test_clause_respects_max_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(kg, "MAX_CLAUSE_ENTRIES", 2)
    ring = [kg.Triple(f"Ent{i}", "links", f"Ent{(i + 1) % 6}") for i in range(6)]
    gr = _retriever(tmp_path, ring)
    gr.build_from_texts([("t", "doc:1")])
    # Seed broadly so the neighbourhood spans many entities, then cap the rendered entries.
    clause = kg.build_kg_context_clause(gr.retrieve("Ent0 Ent1 Ent2 Ent3 Ent4 Ent5"))
    assert clause is not None
    assert clause.count("] Ent") == 2   # only MAX_CLAUSE_ENTRIES citations rendered


# ── build_from_history / build_from_docs ─────────────────────────────────────────

class _FakeStore:
    """A stand-in for agency_kit.store: a fixed set of dossiers."""

    def __init__(self, dossiers):
        self._d = dossiers

    def list_missions(self, project_root=None):
        return [{"mission_id": mid} for mid in self._d]

    def load(self, mission_id):
        d = self._d[mission_id]
        if d is None:
            raise FileNotFoundError(mission_id)
        return d


def test_build_from_history_reads_dossiers(tmp_path):
    rec = []
    gr = _retriever(tmp_path, _TRIPLES, rec)
    store = _FakeStore({
        "m1": {"goal": "Ship Widget", "delivered": "Done.", "dept_outputs": {"product": "Acme plan"}},
    })
    n = gr.build_from_history(store)
    assert n == 3
    text, ref = rec[0]
    assert ref == "mission:m1"
    assert "Ship Widget" in text and "Acme plan" in text   # goal + dept output both extracted


def test_build_from_history_skips_corrupt_dossier(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)
    store = _FakeStore({"ok": {"goal": "g", "delivered": "d"}, "bad": None})
    # 'bad' raises on load and is skipped; 'ok' still contributes its 3 triples.
    assert gr.build_from_history(store) == 3


def test_build_from_docs_reads_all_chunks(tmp_path):
    from agency_studio.rag import Chunk

    class _FakeRetriever:
        def all_chunks(self):
            return [Chunk("d1", 0, "T", "Acme chunk"), Chunk("d1", 1, "T", "Widget chunk")]

    rec = []
    gr = _retriever(tmp_path, _TRIPLES, rec)
    gr.build_from_docs(_FakeRetriever())
    assert [ref for _, ref in rec] == ["doc:d1", "doc:d1"]


def test_build_from_docs_without_all_chunks_builds_nothing(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)
    assert gr.build_from_docs(object()) == 0


# ── extractor seam: default = the `claude` CLI brain (subprocess boundary stubbed) ───────

def _fake_call(response, record=None):
    """A stand-in for cli_engine._call: returns a fixed response, recording (cmd, prompt, timeout)."""
    def _call(cmd, prompt, timeout=None):
        if record is not None:
            record.append((cmd, prompt, timeout))
        return response
    return _call


def test_claude_cli_extractor_parses_triples_from_messy_cli_output():
    # A real `claude -p` response can wrap the JSON in prose + a markdown fence — the extractor
    # must recover the triples anyway (the router's tolerant-parse discipline).
    rec = []
    response = 'Sure, here you go:\n```json\n[["Acme","acquired","Beta"],["Beta","builds","Widget"]]\n```\nDone.'
    ext = kg.ClaudeCliExtractor(call=_fake_call(response, rec))
    triples = ext.extract("Acme acquired Beta which builds Widget.", "doc:1")
    assert [(t.subject, t.relation, t.object) for t in triples] == [
        ("Acme", "acquired", "Beta"), ("Beta", "builds", "Widget"),
    ]
    # The prompt carries the extraction doctrine + the text, sent to the `claude -p` command.
    cmd, prompt, _timeout = rec[0]
    assert cmd == ["claude", "-p"]
    assert "Acme acquired Beta" in prompt and "JSON array" in prompt


def test_claude_cli_extractor_blank_text_makes_no_cli_call():
    def _boom(*a, **k):
        raise AssertionError("must not invoke the CLI on blank text")
    assert kg.ClaudeCliExtractor(call=_boom).extract("   ", "doc:1") == []


def test_claude_cli_extractor_junk_output_yields_no_triples():
    # No JSON array in the response is NOT an error — it just yields nothing (drop-never-raise).
    ext = kg.ClaudeCliExtractor(call=_fake_call("I could not find any relations."))
    assert ext.extract("some text", "doc:1") == []


def test_claude_cli_extractor_empty_array_yields_no_triples():
    ext = kg.ClaudeCliExtractor(call=_fake_call("[]"))
    assert ext.extract("some text", "doc:1") == []


def test_claude_cli_extractor_runtime_error_propagates_as_itself():
    # A CLI that RAN but failed (rate limit, timeout, non-zero exit) is a genuine error: it must
    # propagate as itself, never be relabelled KnowledgeUnavailable (Wave-5 'accurate skip reasons').
    def _failing(*a, **k):
        raise RuntimeError("CLI engine 'claude' exited 1: rate limited")
    with pytest.raises(RuntimeError, match="rate limited"):
        kg.ClaudeCliExtractor(call=_failing).extract("some text", "doc:1")


def test_claude_cli_extractor_missing_cli_raises_knowledge_unavailable(monkeypatch):
    # Brain UNREACHABLE (the `claude` CLI is not on PATH) ⇒ KnowledgeUnavailable → 501 + hint.
    monkeypatch.setattr(kg.shutil, "which", lambda name: None)
    with pytest.raises(kg.KnowledgeUnavailable, match="claude"):
        kg.ClaudeCliExtractor().extract("some text", "doc:1")


def test_claude_cli_extractor_missing_agency_kit_raises_knowledge_unavailable(monkeypatch):
    # `claude` on PATH but agency-kit (which owns the subprocess boundary) not importable ⇒
    # KnowledgeUnavailable, not an opaque ImportError.
    import builtins

    monkeypatch.setattr(kg.shutil, "which", lambda name: "/usr/local/bin/claude")
    real_import = builtins.__import__

    def _no_cli_engine(name, *a, **k):
        if name.startswith("agency_cli"):
            raise ImportError("no agency_cli")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _no_cli_engine)
    with pytest.raises(kg.KnowledgeUnavailable):
        kg.ClaudeCliExtractor().extract("some text", "doc:1")


def test_graph_retriever_defaults_to_claude_cli_extractor(tmp_path):
    gr = kg.GraphRetriever(db_path=tmp_path / "kg.db")
    assert isinstance(gr._extractor, kg.ClaudeCliExtractor)


def test_knowledge_unavailable_is_an_importerror():
    assert issubclass(kg.KnowledgeUnavailable, ImportError)


def test_coerce_triples_accepts_dicts_tuples_and_objects():
    class _Obj:
        subject, relation, object = "S", "r", "O"

    raw = [
        {"subject": "A", "relation": "r", "object": "B"},
        {"head": "C", "predicate": "p", "tail": "D"},
        ("E", "q", "F"),
        _Obj(),
        {"subject": "A", "object": "B"},   # missing relation → dropped
        "garbage",                          # unrecognised → dropped
    ]
    out = kg._coerce_triples(raw)
    assert [(t.subject, t.relation, t.object) for t in out] == [
        ("A", "r", "B"), ("C", "p", "D"), ("E", "q", "F"), ("S", "r", "O"),
    ]


def test_coerce_triples_empty_input():
    assert kg._coerce_triples(None) == []
    assert kg._coerce_triples([]) == []
