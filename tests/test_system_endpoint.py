import http.client
import json
import threading

from agency_studio import __version__, rag, server


def _start(project_root):
    httpd = server.make_server(host="127.0.0.1", port=0, project_root=str(project_root))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    return httpd, host, port


def _request(host, port, method, path):
    conn = http.client.HTTPConnection(host, port)
    conn.request(method, path)
    resp = conn.getresponse()
    raw = resp.read()
    return resp.status, json.loads(raw or b"{}")


def test_system_endpoint_returns_version_and_data_dir(monkeypatch, tmp_path):
    data = tmp_path / "data"
    monkeypatch.setattr(rag, "data_dir", lambda: data)
    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(host, port, "GET", "/api/system")
        assert status == 200
        assert body == {"version": __version__, "data_dir": str(data)}
        assert not any("key" in k.lower() or "token" in k.lower() or "secret" in k.lower() for k in body)
    finally:
        httpd.shutdown()


def test_system_endpoint_is_get_only(monkeypatch, tmp_path):
    data = tmp_path / "data"
    monkeypatch.setattr(rag, "data_dir", lambda: data)
    httpd, host, port = _start(tmp_path)
    try:
        status, body = _request(host, port, "POST", "/api/system")
        assert status == 404
        assert body.get("error") == "not found"
        assert not data.exists()
    finally:
        httpd.shutdown()
