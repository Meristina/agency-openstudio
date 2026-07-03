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


def test_within_call_duplicate_triple_counts_once(tmp_path):
    # A single source that asserts the SAME triple twice (an LLM restating a fact, or overlapping
    # GLiNER2 windows re-surfacing a boundary relation) must bump weight ONCE — weight counts
    # sources, not restatements. This lives in the store so every backend shares it.
    gr = _retriever(tmp_path, [])
    dup = [kg.Triple("Acme", "owns", "Beta"), kg.Triple("acme", "OWNS", "beta")]  # same, case-folded
    n = gr._store.add_triples(dup, "doc:1")
    assert n == 1
    stats = gr.stats()
    assert stats["edges"] == 1
    assert stats["top_entities"][0]["weight"] == 1.0


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


# ── clear / rebuild: a re-run REPLACES, it does not re-count ──────────────────────

class _FakeChunkRetriever:
    """A stand-in for rag.LocalRetriever exposing all_chunks()."""

    def __init__(self, chunks):
        self._chunks = chunks

    def all_chunks(self):
        return list(self._chunks)


def test_clear_empties_the_graph(tmp_path):
    gr = _retriever(tmp_path, _TRIPLES)
    gr.build_from_texts([("t", "doc:1")])
    assert gr.stats()["nodes"] and gr.stats()["edges"]
    gr._store.clear()
    stats = gr.stats()
    assert stats["nodes"] == 0 and stats["edges"] == 0 and stats["top_entities"] == []


def test_rebuild_is_idempotent_over_unchanged_sources(tmp_path):
    from agency_studio.rag import Chunk

    docs = _FakeChunkRetriever([Chunk("d1", 0, "T", "Acme chunk")])
    store = _FakeStore({"m1": {"goal": "Ship Widget", "delivered": "Done."}})
    gr = _retriever(tmp_path, _TRIPLES)

    first = gr.rebuild(docs, store)
    s1 = gr.stats()
    # A SECOND rebuild over the exact same sources must REPLACE, not accumulate: same counts,
    # same weights — an unchanged source is not re-counted (the bug this guards against inflated
    # every weight on each build).
    second = gr.rebuild(docs, store)
    s2 = gr.stats()

    assert first == second
    assert s1["nodes"] == s2["nodes"] and s1["edges"] == s2["edges"]
    assert s1["top_entities"] == s2["top_entities"]   # identical weights, not doubled


def test_rebuild_prunes_triples_from_removed_sources(tmp_path):
    from agency_studio.rag import Chunk

    store = _FakeStore({})   # no missions
    gr = _retriever(tmp_path, _TRIPLES)

    gr.rebuild(_FakeChunkRetriever([Chunk("d1", 0, "T", "Acme chunk")]), store)
    assert gr.stats()["edges"] == 3

    # The doc is gone on the next build → its triples must not linger (append-only would keep them).
    gr.rebuild(_FakeChunkRetriever([]), store)
    stats = gr.stats()
    assert stats["nodes"] == 0 and stats["edges"] == 0


def test_rebuild_failure_leaves_previous_graph_intact(tmp_path):
    from agency_studio.rag import Chunk

    class _BoomExtractor:
        """Raises during extraction — the fallible step (an unreachable brain / a runtime error)."""

        def extract(self, text, source_ref):
            raise kg.KnowledgeUnavailable("brain unreachable")

    docs = _FakeChunkRetriever([Chunk("d1", 0, "T", "Acme chunk")])
    store = _FakeStore({})

    # A good graph exists.
    gr = kg.GraphRetriever(_StubExtractor(_TRIPLES), db_path=tmp_path / "kg.db")
    gr.rebuild(docs, store)
    before = gr.stats()
    assert before["edges"] == 3

    # Now the extractor fails: the rebuild must raise WITHOUT clearing the good graph (clear happens
    # only after all extraction succeeds).
    gr._extractor = _BoomExtractor()
    with pytest.raises(kg.KnowledgeUnavailable):
        gr.rebuild(docs, store)
    assert gr.stats() == before   # untouched — no wipe on a failed build


# ── strict project scope: the KG must not absorb other projects' missions ─────────

def _scoped_store():
    return _FakeStore({
        "m_a": {"goal": "alpha", "delivered": "x", "project_root": "/proj/a"},
        "m_legacy": {"goal": "beta", "delivered": "y"},                       # unstamped (legacy)
        "m_b": {"goal": "gamma", "delivered": "z", "project_root": "/proj/b"},
    })


def test_history_strict_scope_includes_only_explicitly_stamped_project(tmp_path):
    rec = []
    gr = _retriever(tmp_path, _TRIPLES, rec)
    gr.build_from_history(_scoped_store(), project_root="/proj/a", strict_scope=True)
    # Only the mission stamped to /proj/a is extracted — the unstamped legacy mission and the
    # /proj/b mission are both excluded (the KG is injected as context, so it must not leak).
    assert [ref for _, ref in rec] == ["mission:m_a"]


def test_history_default_scope_still_includes_unstamped(tmp_path):
    # Default (non-strict) keeps the history-list leniency: an unstamped mission belongs everywhere,
    # so this behaviour is byte-identical to before the strict-scope option.
    rec = []
    gr = _retriever(tmp_path, _TRIPLES, rec)
    gr.build_from_history(_scoped_store(), project_root="/proj/a")
    assert sorted(ref for _, ref in rec) == ["mission:m_a", "mission:m_b", "mission:m_legacy"]


def test_rebuild_threads_strict_scope_to_history(tmp_path):
    rec = []
    gr = _retriever(tmp_path, _TRIPLES, rec)
    gr.rebuild(_FakeChunkRetriever([]), _scoped_store(), project_root="/proj/a", strict_scope=True)
    assert [ref for _, ref in rec] == ["mission:m_a"]


def test_canon_normalizes_equivalent_paths():
    # A stamp and a project root that name the same dir compare equal however typed.
    assert kg._canon("/proj/a") == kg._canon("/proj/./a") == kg._canon("/proj/a/")
    assert kg._canon("/proj/a") != kg._canon("/proj/b")


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


def test_graph_retriever_defaults_to_claude_cli_extractor(tmp_path, monkeypatch):
    monkeypatch.delenv(kg.KG_BACKEND_ENV, raising=False)
    gr = kg.GraphRetriever(db_path=tmp_path / "kg.db")
    # The extractor is resolved lazily (not in __init__), so it is None until first needed.
    assert gr._extractor is None
    assert isinstance(gr._get_extractor(), kg.ClaudeCliExtractor)


def test_graph_retriever_read_paths_work_with_invalid_backend_env(tmp_path, monkeypatch):
    # A bad AGENCY_STUDIO_KG_BACKEND must not break the dependency-free READ paths (retrieve /
    # stats): the extractor is only resolved on a build, so constructing + querying still works.
    monkeypatch.setenv(kg.KG_BACKEND_ENV, "not-a-real-backend")
    gr = kg.GraphRetriever(db_path=tmp_path / "kg.db")
    assert gr.stats()["nodes"] == 0
    assert gr.retrieve("anything").nodes == []          # empty graph → empty subgraph, no raise
    with pytest.raises(ValueError, match="unknown"):
        gr._get_extractor()                              # a build WOULD surface the bad env


# ── optional on-device backend: GLiNER2 (the [kg] extra; model boundary stubbed) ─────────

class _FakeGliner:
    """Stand-in for a loaded GLiNER2 model: returns a fixed extract_relations payload, recording
    the (text, relation_types) it saw."""

    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def extract_relations(self, text, relation_types, include_confidence=True):
        self.calls.append((text, tuple(relation_types), include_confidence))
        return self._payload


def test_gliner2_extractor_maps_relations_to_triples():
    payload = {"relation_extraction": {
        "acquired": [{"head": {"text": "Acme Corp", "confidence": 0.95},
                      "tail": {"text": "Beta Labs", "confidence": 0.92}}],
        "part of": [{"head": {"text": "Beta Labs", "confidence": 0.8},
                     "tail": {"text": "Acme Group", "confidence": 0.85}}],
    }}
    model = _FakeGliner(payload)
    ext = kg.GLiNER2Extractor(model=model)
    triples = ext.extract("Acme Corp acquired Beta Labs, part of Acme Group.", "doc:1")
    assert sorted((t.subject, t.relation, t.object) for t in triples) == [
        ("Acme Corp", "acquired", "Beta Labs"), ("Beta Labs", "part of", "Acme Group"),
    ]
    # It searches for the configured relation vocabulary (closed-vocabulary trade-off).
    _text, rel_types, _conf = model.calls[0]
    assert set(rel_types) == set(kg.DEFAULT_RELATION_TYPES)


def test_gliner2_extractor_drops_low_confidence_pairs():
    payload = {"relation_extraction": {"depends on": [
        {"head": {"text": "Widget", "confidence": 0.4}, "tail": {"text": "Rust", "confidence": 0.9}},
    ]}}
    # min(head, tail) = 0.4 < the 0.5 default threshold → dropped.
    ext = kg.GLiNER2Extractor(model=_FakeGliner(payload))
    assert ext.extract("Widget depends on Rust.", "doc:1") == []


def test_gliner2_extractor_handles_bare_tuple_pairs():
    # GLiNER2 returns bare (head, tail) tuples when include_confidence is off — these must NOT be
    # silently dropped (the dual-shape hardening).
    payload = {"relation_extraction": {"acquired": [("Acme", "Beta"), ("Beta", "Gamma")]}}
    ext = kg.GLiNER2Extractor(model=_FakeGliner(payload))
    triples = ext.extract("Acme acquired Beta; Beta acquired Gamma.", "doc:1")
    assert sorted((t.subject, t.relation, t.object) for t in triples) == [
        ("Acme", "acquired", "Beta"), ("Beta", "acquired", "Gamma"),
    ]


def test_gliner2_extractor_tolerates_malformed_pairs():
    # Bare-string endpoints inside a dict, wrong-arity tuples, None text, and non-pairs are all
    # dropped — never raised.
    payload = {"relation_extraction": {"x": [
        {"head": "PlainStr", "tail": "Other"},          # string endpoints (no confidence dict)
        ("only-one",),                                   # wrong arity
        "garbage",                                       # not a pair
        {"head": {"text": None}, "tail": {"text": "Z"}},  # None head text
    ]}}
    ext = kg.GLiNER2Extractor(model=_FakeGliner(payload))
    triples = ext.extract("t", "doc:1")
    assert [(t.subject, t.relation, t.object) for t in triples] == [("PlainStr", "x", "Other")]


def test_gliner2_extractor_windows_long_text_no_window_exceeds_encoder(monkeypatch):
    # GLiNER2 is a bounded-window encoder — long text is SLID over in windows, none larger than
    # the window, and together they cover the whole (globally-capped) input (no silent tail loss).
    monkeypatch.setattr(kg, "MAX_GLINER_CHARS", 50)
    monkeypatch.setattr(kg, "GLINER_OVERLAP_CHARS", 10)
    monkeypatch.setattr(kg, "MAX_EXTRACT_CHARS", 500)
    model = _FakeGliner({"relation_extraction": {}})
    kg.GLiNER2Extractor(model=model).extract("x" * 5000, "doc:1")
    windows = [c[0] for c in model.calls]
    assert len(windows) > 1                                  # it actually windowed
    assert all(len(w) <= 50 for w in windows)                # none exceeds the encoder window
    assert sum(len(w) for w in windows) >= 500               # covers the full capped input (with overlap)


def test_gliner2_extractor_caps_whole_input_to_max_extract_chars(monkeypatch):
    # The whole input is bounded by MAX_EXTRACT_CHARS (the same cap the CLI path uses) so a
    # pathological dossier can't spawn unbounded model calls — windows never reach past it.
    monkeypatch.setattr(kg, "MAX_GLINER_CHARS", 50)
    monkeypatch.setattr(kg, "GLINER_OVERLAP_CHARS", 0)
    monkeypatch.setattr(kg, "MAX_EXTRACT_CHARS", 120)
    model = _FakeGliner({"relation_extraction": {}})
    kg.GLiNER2Extractor(model=model).extract("x" * 5000, "doc:1")
    # step == size (no overlap) → ceil(120/50) = 3 windows, together exactly the 120-char cap.
    assert [len(c[0]) for c in model.calls] == [50, 50, 20]


def test_gliner2_extractor_captures_relation_in_the_tail(monkeypatch):
    # The regression this feature fixes: a relation living PAST the first window must still be
    # extracted (head-truncation would have dropped it). A content-aware fake returns a relation
    # only for the window that contains its marker.
    monkeypatch.setattr(kg, "MAX_GLINER_CHARS", 50)
    monkeypatch.setattr(kg, "GLINER_OVERLAP_CHARS", 5)
    monkeypatch.setattr(kg, "MAX_EXTRACT_CHARS", 500)

    class _TailFake:
        calls = []
        def extract_relations(self, text, relation_types, include_confidence=True):
            self.calls.append(text)
            if "TAILMARK" in text:
                return {"relation_extraction": {"owns": [("Acme", "TailCo")]}}
            return {"relation_extraction": {}}

    text = ("x" * 200) + "TAILMARK" + ("y" * 200)            # marker only in a late window
    triples = kg.GLiNER2Extractor(model=_TailFake()).extract(text, "doc:1")
    assert [(t.subject, t.relation, t.object) for t in triples] == [("Acme", "owns", "TailCo")]


def test_gliner2_windows_repeat_a_relation_but_store_dedups_to_weight_one(tmp_path, monkeypatch):
    # A relation surfacing in every overlapping window is emitted once PER WINDOW by extract (no
    # extract-level dedup — the store owns that so all backends share it); once stored under one
    # source it is a single edge of weight 1 (weight counts sources, not windows).
    monkeypatch.setattr(kg, "MAX_GLINER_CHARS", 50)
    monkeypatch.setattr(kg, "GLINER_OVERLAP_CHARS", 10)
    monkeypatch.setattr(kg, "MAX_EXTRACT_CHARS", 500)
    model = _FakeGliner({"relation_extraction": {"owns": [("Acme", "Beta")]}})
    triples = kg.GLiNER2Extractor(model=model).extract("x" * 400, "doc:1")
    assert len(model.calls) > 1                               # it windowed (so the relation repeated)
    assert len(triples) > 1                                   # extract does NOT dedup — the store does
    assert all((t.subject, t.relation, t.object) == ("Acme", "owns", "Beta") for t in triples)
    gr = _retriever(tmp_path, [])
    assert gr._store.add_triples(triples, "doc:1") == 1       # per-source dedup → one edge
    assert gr.stats()["edges"] == 1
    assert gr.stats()["top_entities"][0]["weight"] == 1.0


def test_sliding_windows_pure_behaviour():
    # Empty → no windows; a short string → one window unchanged.
    assert kg._sliding_windows("", 50, 10) == []
    assert kg._sliding_windows("short", 50, 10) == ["short"]
    # Overlapping coverage: consecutive windows share `overlap` chars and cover the whole string.
    text = "abcdefghij"                                       # 10 chars
    wins = kg._sliding_windows(text, 4, 2)                    # size 4, step 2
    assert wins == ["abcd", "cdef", "efgh", "ghij"]
    # Overlap ≥ size is clamped to size-1 so the step stays ≥ 1 (never an infinite loop): here
    # step becomes 1, and the windows still cover the whole string.
    assert kg._sliding_windows("abcdef", 3, 99) == ["abc", "bcd", "cde", "def"]


def test_sliding_windows_snaps_cut_to_whitespace():
    # A window end is snapped back to whitespace so a token isn't split across the boundary into a
    # junk fragment; the windows still overlap and cover the whole string.
    text = "aaa bbb ccc ddd eee"           # spaces at 3, 7, 11, 15
    wins = kg._sliding_windows(text, 10, 4)
    assert wins == ["aaa bbb", "b ccc ddd", "ddd eee"]
    assert not any(w.endswith(" ") for w in wins)   # no window ends on the snapped space


def test_gliner2_extractor_honours_custom_relation_types():
    model = _FakeGliner({"relation_extraction": {}})
    ext = kg.GLiNER2Extractor(model=model, relation_types=["mentors"])
    ext.extract("some text", "doc:1")
    assert model.calls[0][1] == ("mentors",)


def test_gliner2_extractor_blank_text_makes_no_model_call():
    class _Boom:
        def extract_relations(self, *a, **k):
            raise AssertionError("must not call the model on blank text")
    assert kg.GLiNER2Extractor(model=_Boom()).extract("   ", "doc:1") == []


def test_gliner2_extractor_junk_output_yields_no_triples():
    # A payload missing 'relation_extraction' (or shaped wrong) is not an error — yields nothing.
    assert kg.GLiNER2Extractor(model=_FakeGliner({})).extract("t", "doc:1") == []
    assert kg.GLiNER2Extractor(model=_FakeGliner("garbage")).extract("t", "doc:1") == []


def test_gliner2_extractor_runtime_error_propagates_as_itself():
    class _Failing:
        def extract_relations(self, *a, **k):
            raise RuntimeError("model OOM")
    with pytest.raises(RuntimeError, match="OOM"):
        kg.GLiNER2Extractor(model=_Failing()).extract("some text", "doc:1")


def test_gliner2_extractor_absent_extra_raises_knowledge_unavailable(monkeypatch):
    # No injected model + gliner2 not importable ⇒ KnowledgeUnavailable → 501 + hint.
    import builtins

    real_import = builtins.__import__

    def _no_gliner(name, *a, **k):
        if name == "gliner2":
            raise ImportError("no gliner2")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _no_gliner)
    with pytest.raises(kg.KnowledgeUnavailable, match="kg"):
        kg.GLiNER2Extractor().extract("some text", "doc:1")


# ── backend selection: make_extractor ────────────────────────────────────────────

def test_make_extractor_defaults_to_claude(monkeypatch):
    monkeypatch.delenv(kg.KG_BACKEND_ENV, raising=False)
    assert isinstance(kg.make_extractor(), kg.ClaudeCliExtractor)


def test_make_extractor_selects_gliner2_by_name_and_env(monkeypatch):
    monkeypatch.delenv(kg.KG_BACKEND_ENV, raising=False)
    assert isinstance(kg.make_extractor("gliner2"), kg.GLiNER2Extractor)
    monkeypatch.setenv(kg.KG_BACKEND_ENV, "gliner2")
    assert isinstance(kg.make_extractor(), kg.GLiNER2Extractor)


def test_make_extractor_rejects_unknown_backend(monkeypatch):
    monkeypatch.delenv(kg.KG_BACKEND_ENV, raising=False)
    with pytest.raises(ValueError, match=kg.KG_BACKEND_ENV):
        kg.make_extractor("bogus")


def test_graph_retriever_honours_backend_env(tmp_path, monkeypatch):
    monkeypatch.setenv(kg.KG_BACKEND_ENV, "gliner2")
    gr = kg.GraphRetriever(db_path=tmp_path / "kg.db")
    # The extractor is resolved lazily (on first build), so assert the env is honoured there.
    assert isinstance(gr._get_extractor(), kg.GLiNER2Extractor)


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
