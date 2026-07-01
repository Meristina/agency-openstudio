# Wave 4 — RAG / LocalDocs · Implementation Plan

> Status: **SHIPPED** (offline-first slice — all engine/store/hook/server steps landed;
> the GUI "Docs" tab is a tracked follow-up). Produced after a read-only investigation
> pass + fresh web research on the 2026 local-embedding / vector-store landscape, with
> decisions locked with the maintainer. This plan supersedes the naive sketch in
> `ROADMAP.md §Wave 4` with the corrections that research surfaced.

## Goal (ROADMAP, verbatim)

> Ingestion via `microsoft/markitdown` (MIT) → Markdown. `agency_studio/rag.py`: markitdown
> → chunking → embeddings → **SQLite vector store**. Endpoint `/api/docs` + inject relevant
> chunks into `_dept_prompt`. ❌ Not `chunkr` (AGPL + Rust/Docker too heavy).

## What the research pass corrected (load-bearing)

1. **"nomic-embed via llama.cpp" → MLX.** The rest of the local layer is MLX/Metal, and
   MLX beats llama.cpp ~50% on embedding workloads (Contra Collective, M-series, Jun 2026).
   → embeddings run on MLX via `mlx_embedding_models` (MIT), consistent with the Wave-2
   warm `ModelManager`. The literal "llama.cpp" is dropped.
2. **The obvious MLX embedding lib is GPL.** `Blaizzy/mlx-embeddings` (the most-starred) is
   **GPL-3.0** → forbidden by the repo constitution (MIT/Apache only). → use the MIT
   `taylorai/mlx_embedding_models`, whose registry already carries nomic-embed & bge-m3.
3. **The store must not be web-served.** The `/media` route serves `studio_assets/`. If the
   document DB lived there, ingested document text would be downloadable. → the store lives
   under `<project>/.agency-studio/`, **outside** `assets_root` — never reachable via `/media`.
4. **The offline suite must run without the extra.** `sqlite-vec` is in `[studio]`, but the
   CI-equivalent runs anywhere without extras. → `_VectorStore` has two paths: sqlite-vec's
   `vec0` KNN when the loadable extension is present (the fast path on the Mac), else a
   pure-Python cosine fallback over the same stdlib `sqlite3` DB. Same "degrade cleanly"
   contract the media layer uses.
5. **The four repos the maintainer surfaced don't belong in Wave 4.** `chunkr` = AGPL +
   Docker/Postgres/Rust server (the ROADMAP already rejected it, confirmed); `PixelRAG`
   (visual RAG) and `Hyper-Extract` (knowledge graphs) are **Wave 6**; `voidzero-dev` is JS
   tooling, unrelated. → Wave 4 stays the text-RAG core, behind a **pluggable `Retriever`**
   so the Wave-6 approaches slot in with no rewrite.

## The decisions (final, sourced)

- **Ingestion:** `microsoft/markitdown` (MIT).
- **Embeddings:** `mlx_embedding_models` (MIT); model **nomic-embed-text-v1.5** default
  (Apache-2.0, 768-dim, ~0.4 GB), **bge-m3** option (MIT, 1024-dim). Both pinned to an
  immutable HF commit SHA (SECURITY.md #4/#5). EmbeddingGemma rejected — Gemma license.
- **Store:** `sqlite-vec` (Apache-2.0/MIT) with a stdlib pure-Python cosine fallback.
- **D1 — clause injection:** additive default-None `context_clause: Optional[str] = None`
  on `run_mission_cli`, appended in `_dept_prompt`/`_synth_prompt` only when set (before
  `asset_clause`, so the two compose). NOT given to the router/inspector/slug. Byte-identical
  to standalone agency-kit when None — the veto loop / `_short_verdict` logic is untouched
  (Constitution Art. IX). Mirrors the shipped Wave-3 `asset_clause` contract exactly.
- **D2 — bridge threading:** `context_clause` forwarded through `runner_bridge`
  `_run_and_persist` / `run` / `resume`.
- **Retrieval is best-effort:** no ingested docs ⇒ instant no-op (no model load); a missing
  `[studio]` extra or any failure ⇒ RAG is skipped and the mission still runs.

## File-by-file (as built)

- `agency_studio/engines/models.py` — `EmbedModel` registry (nomic default, bge-m3), pinned
  SHAs, `embed_model()` / `embed_models_payload()`.
- `agency_studio/engines/embeddings.py` (NEW) — `_probe/_load/_run` MLX adapters, reusing
  `MediaUnavailable`/`_pinned_repo` from `local_media` (→ same 501 contract).
- `agency_studio/engines/local_media.py` — `ModelManager.embed()` keyed `embed:<id>`
  through the existing `_ensure()` (mutual exclusion with image/voice; warm reuse).
- `agency_studio/rag.py` (NEW) — `chunk_markdown`, `_VectorStore` (sqlite-vec + fallback),
  `Retriever` protocol, `LocalRetriever`, `build_context_clause`.
- `agency-kit` `engines/cli_engine.py` + `runner_bridge.py` — D1/D2 (additive, default-None).
- `agency_studio/server.py` — `POST/GET /api/docs` + `do_DELETE`, `_retriever()`,
  `_retrieve_context()` injection + `retrieval` SSE phase, `embed_models` in `/api/models`,
  docs store under `<project>/.agency-studio/`.
- `pyproject.toml` — `[studio]` extra: markitdown, mlx-embedding-models, sqlite-vec.

## Test plan (offline, network/MLX/markitdown/sqlite-vec stubbed — mirrors Wave 2/3)

- `tests/test_local_media.py` — embed registry, warm reuse, model-switch eviction,
  embed↔image mutual exclusion, kind=query/document prefixes, absent-extra probe.
- `tests/test_rag.py` — chunking + overlap, context-clause formatting/None, ingest→retrieve
  relevance round-trip (fallback store), delete, blank/no-doc guards, absent-markitdown 501.
- `tests/test_server.py` — /api/docs ingest/list/delete + empty-body 400 + absent-extra 501,
  embed_models in /api/models, retrieval injection emits the phase + non-None clause, no-docs
  injects nothing.
- `agency-kit` `tests/test_engine.py` + `tests/test_cli.py` — context_clause byte-identity,
  verbatim append, context+asset composition order, router/inspector isolation, bridge threading.

## Live validation (Apple Silicon Mac only — deferred, like Wave 2)

- `pip install -e ".[studio]"`; `POST /api/docs` a real PDF → `GET /api/docs` lists it;
  `GET /api/models` shows `embed:<id>` warm after a mission; run a mission on that topic →
  the deliverable cites sourced excerpts; Wave-3 image rendering still works after (the
  mutual-exclusion eviction path).

## Non-goals (deferred — do not build here)

- GUI "Docs" tab → follow-up PR (upload / list / delete / per-mission "sources used").
- Visual RAG (PixelRAG) + knowledge graphs (Hyper-Extract) → **Wave 6** (the `Retriever`
  protocol is the seam).
- Reranking / hybrid search / LanceDB → unneeded for a single-user local corpus.
