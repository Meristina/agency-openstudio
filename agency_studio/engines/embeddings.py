"""embeddings — local text-embedding backend for Wave 4 (RAG / LocalDocs).

The retriever (``agency_studio/rag.py``) turns document chunks and the mission goal into
vectors with a small MLX-native embedding model (``mlx_embedding_models``, MIT), all on
the Mac — nothing leaves the machine. Like the Wave-2 media backends, this lives in an
optional extra (``[studio]``) and is imported **lazily**: the stdlib server boots and
missions run with the extra absent, and an embedding request without it raises
``MediaUnavailable`` → the server's HTTP 501 + install hint (same contract as ``[media]``).

Structure mirrors ``local_media`` exactly so the ``ModelManager`` can stay memory-safe and
fail fast:

  * ``_probe_embed`` — CHEAP import check (no weights, no network). Run BEFORE the manager
    evicts its warm model, so a missing extra can't destroy a working one.
  * ``_load_embed``  — the heavy load (weights into memory, HF download pinned to the
    reviewed commit SHA, exactly like the STT weights).
  * ``_run_embed``   — one encode() call, returning plain Python float lists.

All three are module-level so the test suite monkeypatches them with stubs — it never
touches real MLX, real weights, or the network (mirrors the Wave 2/3 offline pattern).
"""

from __future__ import annotations

from typing import List

from . import models
from .local_media import MediaUnavailable, _pinned_repo

# The retriever installs the embedding model via the same extra as the rest of the local
# layer, so the hint points there (``mlx_embedding_models`` ships in ``[studio]``).
_STUDIO_HINT = "install the local-docs extra:  pip install 'agency-studio[studio]'"


def _probe_embed() -> None:
    """Cheap availability check for the embedding backend — imports nothing heavy and
    touches no network. Raises ``MediaUnavailable`` (an ``ImportError`` subclass → 501)
    if the ``[studio]`` extra is not installed."""
    try:
        import mlx_embedding_models  # noqa: F401
    except ImportError as exc:
        raise MediaUnavailable(f"text embeddings need mlx-embedding-models — {_STUDIO_HINT}") from exc


def _load_embed(entry: "models.EmbedModel"):
    """Load the embedding model from its registry entry. The weights are fetched + cached
    by HF and PINNED to ``entry.revision`` (via ``_pinned_repo`` → a local snapshot dir),
    so the exact reviewed commit loads even if the repo later moves. Passing the pinned dir
    as ``model_path`` keeps the per-model pooling from the registry entry (``from_registry``
    would re-resolve the repo at HEAD, unpinned)."""
    from mlx_embedding_models.embedding import EmbeddingModel
    model_path = _pinned_repo(entry.repo, entry.revision)  # local snapshot dir (pinned), or repo id
    return EmbeddingModel(
        model_path=model_path,
        pooling_strategy=entry.pooling_strategy,
        normalize=entry.normalize,
        max_length=entry.max_length,
        nomic_bert=entry.nomic_bert,
        apply_ln=entry.apply_ln,
    )


def _run_embed(model, entry: "models.EmbedModel", *, texts: "List[str]", kind: str) -> "List[List[float]]":
    """Embed ``texts`` with a loaded model, applying the model's retrieval instruction
    prefix (``kind`` = ``"query"`` or ``"document"``). Returns plain Python float lists
    (JSON/sqlite-friendly), never numpy — the store and tests stay backend-agnostic."""
    prefix = entry.query_prefix if kind == "query" else entry.doc_prefix
    prepared = [f"{prefix}{t}" for t in texts] if prefix else list(texts)
    vectors = model.encode(prepared)  # numpy array, shape (len(texts), entry.ndim)
    return [[float(x) for x in row] for row in vectors]
