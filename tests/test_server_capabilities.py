import http.client
import json
import threading

from agency_studio import capabilities, server
from agency_studio.engines import models


def _start(project_root):
    httpd = server.make_server(host="127.0.0.1", port=0, project_root=str(project_root))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    return httpd, host, port


def _request(host, port, method, path, body=None):
    conn = http.client.HTTPConnection(host, port)
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    conn.request(method, path, body=payload, headers=headers)
    resp = conn.getresponse()
    raw = resp.read()
    return resp.status, json.loads(raw or b"{}")


def test_capabilities_get_put_delete(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENCY_STUDIO_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(capabilities, "production_tool_entries", lambda refresh=False: [])
    monkeypatch.setitem(capabilities.BUILDERS, "production-tools", capabilities.production_tool_entries)
    monkeypatch.setattr(capabilities, "mcp_entries", lambda: [])
    monkeypatch.setitem(capabilities.BUILDERS, "mcp", capabilities.mcp_entries)
    monkeypatch.setattr(capabilities, "image_entries", lambda: [
        capabilities.CapabilityEntry(
            id="flux-schnell",
            label="FLUX.1-schnell",
            family="image",
            cost="free",
            availability="available",
            default=True,
        )
    ])
    monkeypatch.setitem(capabilities.BUILDERS, "image", capabilities.image_entries)

    monkeypatch.setenv("AGENCY_STUDIO_VIDEO_API_KEY", "sk-secret-123")

    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(host, port, "GET", "/api/capabilities")
        assert status == 200
        assert [f["family"] for f in body["families"]] == list(capabilities.FAMILIES)
        # SC-007: a present key is reported as presence + var name only — never its value.
        assert "sk-secret-123" not in json.dumps(body)

        status, body = _request(host, port, "PUT", "/api/capabilities/selection", {"family": "image", "id": "flux-schnell"})
        assert status == 200
        assert body["selected"] == "flux-schnell"

        status, body = _request(host, port, "DELETE", "/api/capabilities/selection/image")
        assert status == 204

        # The clear must actually land: the selection is gone on the next read.
        status, body = _request(host, port, "GET", "/api/capabilities")
        image = next(f for f in body["families"] if f["family"] == "image")
        assert image["selected"] is None
    finally:
        httpd.shutdown()


def test_embedding_selection_change_drops_cached_retrievers(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENCY_STUDIO_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(capabilities, "production_tool_entries", lambda refresh=False: [])
    monkeypatch.setitem(capabilities.BUILDERS, "production-tools", capabilities.production_tool_entries)
    monkeypatch.setattr(capabilities, "embedding_entries", lambda: [
        capabilities.CapabilityEntry(
            id=e.id, label=e.label, family="embedding", cost="free",
            availability="available", default=e.default,
        )
        for e in models.EMBED_MODELS.values()
    ])
    monkeypatch.setitem(capabilities.BUILDERS, "embedding", capabilities.embedding_entries)

    httpd, host, port = _start(tmp_path)
    try:
        httpd.retriever = object()  # simulate a warm, model-bound retriever
        httpd.visual = object()
        entry_id = next(iter(capabilities.embedding_entries())).id
        status, _ = _request(host, port, "PUT", "/api/capabilities/selection",
                             {"family": "embedding", "id": entry_id})
        assert status == 200
        # FR-006: the change takes effect without a restart — the lazy singletons
        # bound to the previous embedding model are dropped.
        assert httpd.retriever is None
        assert httpd.visual is None
    finally:
        httpd.shutdown()


def test_capabilities_selection_refuses_inventory_only_and_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENCY_STUDIO_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(capabilities, "production_tool_entries", lambda refresh=False: [])
    monkeypatch.setitem(capabilities.BUILDERS, "production-tools", capabilities.production_tool_entries)
    monkeypatch.setattr(capabilities, "image_entries", lambda: [
        capabilities.CapabilityEntry(
            id="x",
            label="X",
            family="image",
            cost="free",
            availability="unavailable",
            reason="missing_extra",
            enablement="install it",
        )
    ])
    monkeypatch.setitem(capabilities.BUILDERS, "image", capabilities.image_entries)

    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(host, port, "PUT", "/api/capabilities/selection", {"family": "mcp", "id": "x"})
        assert status == 400
        assert "inventory-only" in body["error"]

        status, body = _request(host, port, "PUT", "/api/capabilities/selection", {"family": "image", "id": "x"})
        assert status == 409
        assert body["reason"] == "missing_extra"
        assert body["enablement"] == "install it"
    finally:
        httpd.shutdown()
