import pytest

from agency_studio.engines import embeddings, models, portable
from agency_studio.engines.local_media import MediaUnavailable


ENTRY = models.EMBED_MODELS["nomic-embed-gguf"]


def test_gateway_url_rejects_non_loopback(monkeypatch):
    monkeypatch.setenv(ENTRY.gateway_env, "http://example.com:8080")
    with pytest.raises(ValueError):
        embeddings._gateway_url(ENTRY)


def test_gateway_probe_maps_connection_failure(monkeypatch):
    monkeypatch.setattr(portable, "get_json", lambda *a, **k: (_ for _ in ()).throw(OSError("down")))
    with pytest.raises(MediaUnavailable) as exc:
        embeddings._probe_gateway(ENTRY)
    assert "embedding gateway unavailable" in str(exc.value)


def test_gateway_run_posts_embeddings_and_validates_length(monkeypatch):
    seen = {}

    def fake_post(url, payload, timeout):
        seen.update(url=url, payload=payload, timeout=timeout)
        return {"data": [{"embedding": [0.1] * ENTRY.ndim}, {"embedding": [0.2] * ENTRY.ndim}]}

    monkeypatch.setattr(portable, "post_json", fake_post)
    out = embeddings._run_gateway("http://127.0.0.1:8080", ENTRY, texts=["a", "b"], kind="document")
    assert seen["url"].endswith("/v1/embeddings")
    assert seen["payload"] == {"input": ["a", "b"]}
    assert len(out) == 2 and len(out[0]) == ENTRY.ndim


def test_gateway_run_rejects_wrong_dimension(monkeypatch):
    monkeypatch.setattr(portable, "post_json", lambda *a, **k: {"data": [{"embedding": [1.0]}]})
    with pytest.raises(MediaUnavailable):
        embeddings._run_gateway("http://127.0.0.1:8080", ENTRY, texts=["a"], kind="query")
