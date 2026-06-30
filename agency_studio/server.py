"""server — stdlib HTTP/SSE server for the Agency Studio Mission Console.

Zero runtime dependencies (Python ``http.server``), mirroring agency-kit's
stdlib-only ethos. It wraps ``agency_cli.runner_bridge.run`` and streams the
mission's live progress to the GUI using agency-kit's observational ``on_event``
hook — the veto loop and ``_short_verdict`` are never touched.

Security (non-negotiable, from Wave 0 — see docs/SECURITY.md):
  * Binds 127.0.0.1 only (never 0.0.0.0).
  * No ``Access-Control-Allow-Origin: *`` — CORS is echoed back only for
    loopback origins (the Vite dev server on 127.0.0.1 / localhost).
  * Every static file is served through ``path_inside()`` — a request that
    escapes the GUI root (``/../../etc/passwd``) gets a 404, not the file.

Endpoints:
  POST /api/mission           run a mission, stream SSE progress
  GET  /api/missions          list saved missions (JSON)
  GET  /api/mission/{id}      load one saved dossier (JSON)
  GET  /api/mission/{id}/pdf  export the deliverable as PDF ([pdf] extra)
  GET  /  /<static>           serve the built GUI (app/studio/dist)
"""

from __future__ import annotations

import json
import queue
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

# Loopback hosts the studio is allowed to bind — enforced at the bind point.
_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")

# A saved mission id is new_mission_id() output: a timestamp + slug, i.e. only
# [A-Za-z0-9_-]. Anything else (a slash or dot) is rejected before it can reach
# store.load(), which builds a filesystem path from the id — so the GET-mission
# route cannot be turned into a path-traversal read.
_MISSION_ID_RE = re.compile(r"\A[A-Za-z0-9_-]+\Z")

# Content types for the few static extensions the GUI build emits.
_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".map": "application/json; charset=utf-8",
}


def path_inside(root: Path, requested: str) -> Path | None:
    """Resolve ``requested`` (a URL path) under ``root`` and reject any escape.

    Returns the resolved absolute path when it is genuinely inside ``root``,
    otherwise ``None``. Defends against ``..`` traversal and absolute-path
    injection: the request path is always treated as relative to the GUI root,
    and the *resolved* result must still be within the *resolved* root.
    """
    root = root.resolve()
    rel = requested.lstrip("/")
    candidate = (root / rel).resolve()
    if candidate == root or root in candidate.parents:
        return candidate
    return None


def _is_loopback_origin(origin: str) -> bool:
    """True only for http(s) origins whose host is loopback (127.0.0.1 / localhost).

    Used to scope CORS: we echo the request Origin back only when it is local,
    so the Vite dev server can call the API without ever opening the door to ``*``.
    """
    if not origin:
        return False
    try:
        parsed = urlparse(origin)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and parsed.hostname in _LOOPBACK_HOSTS


class StudioHandler(BaseHTTPRequestHandler):
    server_version = "AgencyStudio/0.0.0"
    protocol_version = "HTTP/1.1"

    # ── small response helpers ─────────────────────────────────────────────
    def _cors(self) -> None:
        origin = self.headers.get("Origin", "")
        if _is_loopback_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def _send_bytes(
        self, body: bytes, content_type: str, status: int = 200,
        extra_headers: "dict[str, str] | None" = None,
    ) -> None:
        """Send a complete byte body with Content-Length + CORS. The single way
        non-streaming responses are written (JSON, static files, PDF)."""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status)

    def _send_error_json(self, status: int, message: str) -> None:
        self._send_json({"error": message}, status=status)

    # ── routing ─────────────────────────────────────────────────────────────
    def do_OPTIONS(self) -> None:  # noqa: N802 (stdlib naming)
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/missions":
            return self._handle_list_missions()
        if path.startswith("/api/mission/"):
            rest = path[len("/api/mission/"):]
            if rest.endswith("/pdf"):
                return self._handle_mission_pdf(rest[: -len("/pdf")])
            return self._handle_get_mission(rest)
        return self._handle_static(path)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/mission":
            return self._handle_run_mission()
        self._send_error_json(404, "not found")

    # ── API: list / get saved missions ───────────────────────────────────────
    def _handle_list_missions(self) -> None:
        from agency_kit import store
        self._send_json({"missions": store.list_missions()})

    def _handle_get_mission(self, mission_id: str) -> None:
        from agency_kit import store
        mission_id = urlparse(mission_id).path.strip("/")
        if not _MISSION_ID_RE.match(mission_id):
            # Reject traversal / malformed ids before they reach the filesystem.
            return self._send_error_json(404, "mission not found")
        try:
            self._send_json(store.load(mission_id))
        except FileNotFoundError:
            self._send_error_json(404, f"mission '{mission_id}' not found")

    def _handle_mission_pdf(self, mission_id: str) -> None:
        """Export a mission's deliverable to PDF and stream it back.

        Uses agency-kit's ``exporter.export_pdf`` (the ``[pdf]`` extra). A missing
        extra yields 501 (with install guidance) rather than a 500 traceback.
        """
        mission_id = urlparse(mission_id).path.strip("/")
        if not _MISSION_ID_RE.match(mission_id):
            return self._send_error_json(404, "mission not found")
        from agency_cli import exporter
        try:
            pdf_path = exporter.export_pdf(mission_id)
        except ImportError as exc:  # [pdf] extra not installed
            return self._send_error_json(501, str(exc))
        except FileNotFoundError:
            return self._send_error_json(404, f"no deliverable for mission '{mission_id}'")
        body = Path(pdf_path).read_bytes()
        self._send_bytes(
            body, "application/pdf",
            extra_headers={"Content-Disposition": f'attachment; filename="{mission_id}.pdf"'},
        )

    # ── API: run a mission, stream SSE ────────────────────────────────────────
    def _handle_run_mission(self) -> None:
        request = self._parse_mission_request()
        if request is None:
            return  # a 400 was already sent
        goal, engine = request
        self._begin_sse()
        result_box = self._stream_mission(goal, engine)
        if result_box is not None:  # None ⇒ client disconnected mid-stream
            self._send_terminal_frame(result_box)

    def _parse_mission_request(self) -> "tuple[str, str] | None":
        """Read + validate the JSON body. Returns ``(goal, engine)``, or ``None``
        after sending the matching 400 (bad JSON / missing goal)."""
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send_error_json(400, "body must be JSON")
            return None
        goal = (payload.get("goal") or "").strip()
        if not goal:
            self._send_error_json(400, "missing 'goal'")
            return None
        return goal, payload.get("engine") or "claude-code"

    def _begin_sse(self) -> None:
        """Emit the SSE response headers. The Mission Console consumes this via
        fetch() streaming (it is a POST, so EventSource can't be used and won't
        auto-reconnect); the stream ends at connection close — hence
        ``Connection: close``."""
        self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("X-Accel-Buffering", "no")
        self._cors()
        self.end_headers()

    def _stream_mission(self, goal: str, engine: str) -> "dict | None":
        """Run the mission on a worker thread and stream its progress events.

        Returns the result box (carrying ``result`` or ``error``) once the worker
        signals completion, or ``None`` if the client disconnected mid-stream.
        """
        events: "queue.Queue[dict | None]" = queue.Queue()
        result_box: dict = {}

        def _worker() -> None:
            from agency_cli import runner_bridge
            try:
                result_box["result"] = runner_bridge.run(
                    goal,
                    project_root=self.server.project_root,  # type: ignore[attr-defined]
                    engine=engine,
                    on_event=events.put,
                )
            except Exception as exc:  # surfaced to the client as an SSE error event
                result_box["error"] = str(exc)
            finally:
                events.put(None)  # sentinel: worker finished

        threading.Thread(target=_worker, daemon=True).start()

        # Drain progress events until the worker signals completion.
        while True:
            event = events.get()
            if event is None:
                break
            if not self._write_sse(event):
                return None  # client disconnected mid-stream
        return result_box

    def _send_terminal_frame(self, result_box: dict) -> None:
        """Emit the final SSE frame: an ``error`` frame, or a ``done`` frame with
        the saved mission's id / verdict / path / residual risk."""
        if "error" in result_box:
            self._write_sse({"phase": "error", "message": result_box["error"]})
            return
        result = result_box.get("result")
        if result is None:
            return
        dossier = result.dossier
        verdicts = dossier.get("verdicts") or []
        self._write_sse({
            "phase": "done",
            "mission_id": dossier.get("mission_id"),
            "verdict": verdicts[-1].get("verdict") if verdicts else None,
            "path": str(result.path),
            "residual_risk": dossier.get("residual_risk"),
        })

    def _write_sse(self, event: dict) -> bool:
        """Write one SSE ``data:`` frame. Returns False if the client has gone."""
        frame = f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8")
        try:
            self.wfile.write(frame)
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError):
            return False

    # ── static GUI ────────────────────────────────────────────────────────────
    def _handle_static(self, path: str) -> None:
        root: Path = self.server.static_root  # type: ignore[attr-defined]
        if root is None:
            return self._send_error_json(404, "GUI not built — run the Vite build first")
        target = path_inside(root, path)
        if target is None:
            return self._send_error_json(404, "not found")  # traversal blocked
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            # SPA fallback: unknown non-API route → index.html (client-side routing).
            target = root / "index.html"
            if not target.is_file():
                return self._send_error_json(404, "not found")
        body = target.read_bytes()
        content_type = _CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        self._send_bytes(body, content_type)

    # Quieter logging — one line per request is enough for a local tool.
    def log_message(self, fmt: str, *args) -> None:  # noqa: A002
        return


class _QuietThreadingHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer that doesn't dump a traceback when a local client
    disconnects mid-response (broken pipe / reset). For a loopback dev tool a
    client closing the tab is normal, not an error worth a stack trace."""

    daemon_threads = True

    def handle_error(self, request, client_address) -> None:  # noqa: D102
        import sys
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


def _require_loopback(host: str) -> None:
    """Refuse any non-loopback bind — Agency Studio is local-first (docs/SECURITY.md).

    Enforced at the bind point so neither ``serve`` nor a direct ``make_server``
    caller can ever expose the studio beyond loopback.
    """
    if host not in _LOOPBACK_HOSTS:
        raise ValueError(
            f"refusing to bind host '{host}' — Agency Studio is local-first and binds "
            f"loopback only (127.0.0.1). Set --host 127.0.0.1."
        )


def make_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    project_root: str = ".",
    static_root: "str | Path | None" = None,
) -> ThreadingHTTPServer:
    """Build (but do not start) the Studio HTTP server.

    ``static_root`` defaults to ``app/studio/dist`` next to ``project_root`` when
    that build exists; otherwise static serving is disabled (API still works).
    Refuses to bind any non-loopback host (``_require_loopback``).
    """
    _require_loopback(host)
    if static_root is None:
        candidate = Path(project_root).resolve() / "app" / "studio" / "dist"
        static_root = candidate if candidate.is_dir() else None
    httpd = _QuietThreadingHTTPServer((host, port), StudioHandler)
    httpd.project_root = str(project_root)          # type: ignore[attr-defined]
    httpd.static_root = Path(static_root) if static_root else None  # type: ignore[attr-defined]
    return httpd


def serve(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    project_root: str = ".",
    static_root: "str | Path | None" = None,
) -> None:
    """Start the Studio server and serve forever (Ctrl-C to stop).

    The loopback bind is enforced inside ``make_server`` (``_require_loopback``).
    """
    httpd = make_server(host, port, project_root, static_root)
    where = httpd.static_root if httpd.static_root else "(GUI not built)"  # type: ignore[attr-defined]
    print(f"Agency Studio → http://{host}:{port}   serving {where}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down…")
    finally:
        httpd.server_close()
