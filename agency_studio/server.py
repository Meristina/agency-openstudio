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
import socket
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

# Upper bound on a request body the studio will read. A mission request is a tiny
# JSON object ({goal, engine}); capping the read defends the handler thread from a
# lying/oversized Content-Length that would otherwise block it on rfile.read().
_MAX_BODY_BYTES = 1 << 20  # 1 MiB

# Upper bound on an uploaded audio body for speech-to-text (POST /api/stt). Audio
# clips are larger than a JSON mission request, so STT gets its own (still bounded)
# ceiling rather than relaxing _MAX_BODY_BYTES for every route. The body is streamed
# straight to disk in _READ_CHUNK pieces (never held whole in RAM).
_MAX_AUDIO_BYTES = 32 << 20  # 32 MiB

# Chunk size for streaming a large request body to disk (STT upload).
_READ_CHUNK = 1 << 16  # 64 KiB

# Bounds on image-generation parameters (POST /api/image). The request BYTE size is
# bounded, but the COMPUTE it triggers is not — an unclamped width/height/steps could
# allocate a huge tensor that OOMs the 16 GB Mac while holding the shared media lock,
# wedging every media route. So dimensions + step count are range-checked; a value
# outside the envelope is a 400, never silently accepted. The per-model step ceiling
# lives on each registry entry (ImageModel.steps_max); dimensions are bounded here.
_IMAGE_MIN_DIM = 256
_IMAGE_MAX_DIM = 1536

# Wall-clock bound on reading a request body. Without it a client that declares a
# Content-Length but withholds the bytes (slowloris) would pin a handler thread
# forever — ThreadingHTTPServer spawns one unbounded thread per connection.
_BODY_READ_TIMEOUT = 15.0  # seconds

# How often the SSE drain loop emits a heartbeat while no mission event is pending.
# A long engine call emits no events, so without a periodic write a mid-call "Stop"
# (the GUI aborting the fetch) would go unnoticed until the call finished. The
# heartbeat is an SSE comment line — ignored by clients — whose WRITE failing is the
# reliable "client gone" signal (a failed write, not a fragile read-side peek). On
# failure we set cancel_event so the engine kills the in-flight subprocess promptly.
_HEARTBEAT_SECONDS = 1.0

# Send deadline for the SSE streaming phase. `_read_body` restores settimeout(None)
# after the bounded body read, so without this every wfile.write during the stream is
# fully blocking — a client that opens the connection but stops reading (a full TCP
# receive window) would pin the handler thread AND let the worker's event queue grow
# unbounded, while also starving the in-flight kill (a stuck write never sets
# cancel_event). A bounded send timeout turns that stall into a detected "client gone".
_STREAM_SEND_TIMEOUT = 30.0

# Loopback hosts the studio is allowed to bind — enforced at the bind point.
_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")

# A saved mission id is new_mission_id() output: a timestamp + slug, i.e. only
# [A-Za-z0-9_-]. Anything else (a slash or dot) is rejected before it can reach
# store.load(), which builds a filesystem path from the id — so the GET-mission
# route cannot be turned into a path-traversal read.
_MISSION_ID_RE = re.compile(r"\A[A-Za-z0-9_-]+\Z")

# Shape of an ephemeral run id (uuid4().hex, 32 lowercase hex chars) — the in-memory
# handle for an in-flight mission, announced as the first SSE frame. A run id is only
# ever a dict key in the run registry, never a filesystem path, so the cancel route
# needs no separate validation: any unknown/malformed id simply misses the registry
# and 404s. This pattern documents the emitted shape (asserted in tests).
_RUN_ID_RE = re.compile(r"\A[a-f0-9]{32}\Z")

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
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".avif": "image/avif",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".flac": "audio/flac",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".wasm": "application/wasm",
    ".txt": "text/plain; charset=utf-8",
    ".webmanifest": "application/manifest+json",
    ".map": "application/json; charset=utf-8",
}


# Generic capability clause appended to department/synthesis prompts (Wave 3) so a
# department MAY request a multimodal asset. Deliberately small and protocol-only: it is
# advisory model-facing text, NOT trusted — every constraint (type/model/voice allowlists,
# fixed canvas, length + per-mission caps, route gate) is enforced at the untrusted
# boundary in ``assets.parse_markers``, never here.
ASSET_CLAUSE = (
    "OPTIONAL MULTIMODAL ASSETS: if a visual or spoken deliverable genuinely helps the "
    "mission, you may embed fenced ```asset blocks — a marketing image, a comms narration. "
    "Each is a single JSON object on its own fenced lines:\n"
    "```asset\n"
    '{"type": "image", "prompt": "<concise description of the image>"}\n'
    "```\n"
    "or\n"
    "```asset\n"
    '{"type": "tts", "text": "<the exact words to speak>"}\n'
    "```\n"
    "Only `type` and `prompt`/`text` are honored; keep prompts concise. Omit entirely when "
    "no asset is warranted — never invent one to fill space."
)


def _build_render_assets(server, events: "queue.Queue", cancel_event: threading.Event):
    """Build the best-effort asset renderer the headless bridge calls after a clean PASS,
    closed over the long-lived ``server`` (its single warm ``ModelManager`` + assets root),
    this run's SSE ``events`` queue, and its ``cancel_event``.

    Defined at module scope and over ``server`` (never the request handler) so the daemon
    worker can't pin the handler's dead socket buffers alive. Returns a ``render_assets``
    callable matching the bridge's hook contract: it mutates ``dossier['assets']`` (manifest)
    and cosmetically rewrites ``dossier['delivered']`` — building both before assigning, so a
    failure can't persist a half-rewritten dossier. Assets are written under
    ``studio_assets/missions/<mission_id>/`` (a subtree of the assets root the existing
    ``/media`` route already serves through ``path_inside``)."""
    def render_assets(dossier: dict) -> None:
        from agency_studio import assets
        delivered = dossier.get("delivered") or ""
        requests = assets.parse_markers(delivered, dossier.get("route") or [])
        # Render only when there is something to render — spinning up the warm ModelManager
        # (and importing the [media] backends) is gated on a non-empty request set.
        manifest: "list[dict]" = []
        if requests:
            from agency_studio.engines.local_media import ModelManager
            with server.media_lock:  # reuse the ONE warm manager (16 GB mutual-exclusivity)
                if server.media is None:
                    server.media = ModelManager(server.assets_root)
                manager = server.media
            assets_root = Path(server.assets_root).resolve()
            out_dir = assets_root / "missions" / str(dossier.get("mission_id"))

            def to_url(path) -> str:
                return _media_url(assets_root, path)

            manifest = assets.render(
                manager, requests, out_dir=out_dir, to_url=to_url,
                should_cancel=cancel_event.is_set, on_event=events.put,
            )
        # Always rewrite — even with no requests, a marker dropped at the parse boundary
        # (off-route / over-cap / malformed) leaves a raw fence that must be stripped from the
        # deliverable/PDF. rewrite_delivered is pure and a no-op when no ```asset block exists.
        new_delivered = assets.rewrite_delivered(delivered, manifest)
        if manifest:
            dossier["assets"] = manifest
        if new_delivered != delivered:
            dossier["delivered"] = new_delivered
    return render_assets


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


def _media_url(assets_root: "str | Path", path: "str | Path") -> str:
    """Map a generated asset's filesystem ``path`` to its public ``/media/...`` URL, relative
    to ``assets_root``. The single home for that mapping so the HTTP image/TTS handlers and the
    marker-render bridge (``_build_render_assets``) can never drift on how a ``/media`` URL is
    formed — a drift the ``/media`` route (guarded by :func:`path_inside`) would then have to
    reconcile. Both sides are resolved before the relative-path computation."""
    rel = Path(path).resolve().relative_to(Path(assets_root).resolve())
    return "/media/" + rel.as_posix()


def _require_int_in_range(value: object, lo: int, hi: int, name: str) -> int:
    """Coerce ``value`` to int and require ``lo <= n <= hi``. Raises ``ValueError``
    (or ``TypeError`` on a non-numeric value) — the caller maps that to a 400. Used
    to bound image-generation params so a request can't trigger unbounded compute."""
    n = int(value)
    if not (lo <= n <= hi):
        raise ValueError(f"'{name}' must be between {lo} and {hi}")
    return n


def _safe_mission_id(raw: str) -> "str | None":
    """Clean a request-supplied mission id and reject anything that could escape
    the store's filesystem path. Returns the validated id, or ``None``.

    Single source for the filesystem-traversal defense on every id→path route:
    strip the URL path wrapper, then require the strict ``[A-Za-z0-9_-]`` shape
    (new_mission_id() output) before the id can ever reach ``store.load`` /
    ``exporter.export_pdf``.
    """
    cleaned = urlparse(raw).path.strip("/")
    return cleaned if _MISSION_ID_RE.match(cleaned) else None


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


def _is_loopback_host(host: str) -> bool:
    """True only when the ``Host`` header names a loopback host (port ignored).

    Pairs with the loopback bind + Origin allowlist to close DNS-rebinding: a remote
    page on evil.com that rebinds its A record to 127.0.0.1 is treated by the browser
    as *same-origin* with the studio (so CORS never applies and no preflight is sent),
    but its request still carries ``Host: evil.com`` — so rejecting a non-loopback Host
    blocks it even though the loopback bind accepted the connection.
    """
    if not host:
        return False
    try:
        hostname = urlparse("//" + host).hostname  # //host[:port] → hostname, port dropped
    except ValueError:
        return False
    return hostname in _LOOPBACK_HOSTS


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
        # When we're about to drop the socket (e.g. an unread body), tell HTTP/1.1
        # keep-alive clients so they don't reuse a connection we're closing.
        if self.close_connection:
            self.send_header("Connection", "close")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, obj: object, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status)

    def _send_error_json(self, status: int, message: str) -> None:
        self._send_json({"error": message}, status=status)

    def _reject(self, status: int, message: str) -> None:
        """Send an error response AND close the connection. The single way to reject
        a request whose body was not (fully) read: an unread body left in the socket
        would desync the next request on a kept-alive HTTP/1.1 connection, so the
        socket must not be reused (``_send_bytes`` emits ``Connection: close``)."""
        self.close_connection = True
        self._send_error_json(status, message)

    def _host_allowed(self) -> bool:
        """Reject (403) any request whose Host header isn't loopback — the DNS-rebinding
        guard, enforced before any route runs. Returns False (and answers) when blocked."""
        if _is_loopback_host(self.headers.get("Host", "")):
            return True
        self._reject(403, "forbidden host")
        return False

    def _read_body(self) -> "bytes | None":
        """Read the request body, bounded in size and time. Returns the body bytes,
        or ``None`` after rejecting + closing the connection (400 malformed length,
        413 too large, 408 read timeout, 411 chunked-unsupported).

        Defends the handler thread two ways: ``_MAX_BODY_BYTES`` caps a lying-large
        Content-Length, and ``_BODY_READ_TIMEOUT`` stops a withheld/slow body
        (slowloris) from blocking ``rfile.read`` forever. (A large audio upload does
        NOT use this — POST /api/stt streams to disk via ``_stream_body_to_file``.)
        """
        # http.server does not decode chunked bodies; an unread chunk-framed body
        # would desync the socket, so reject Transfer-Encoding outright.
        if self.headers.get("Transfer-Encoding"):
            self._reject(411, "Transfer-Encoding unsupported — send Content-Length")
            return None
        raw_len = self.headers.get("Content-Length")
        if raw_len is None:
            return b""
        try:
            length = int(raw_len)
        except ValueError:
            length = -1
        if length < 0:
            self._reject(400, "invalid Content-Length")
            return None
        if length > _MAX_BODY_BYTES:
            self._reject(413, "request body too large")
            return None
        if length == 0:
            return b""
        # Bound the body read so a stalled client can't pin the thread. The timeout
        # is scoped to this read and cleared afterwards — the SSE stream that follows
        # only writes, and the reject response below must not write under a deadline.
        self.connection.settimeout(_BODY_READ_TIMEOUT)
        try:
            body: "bytes | None" = self.rfile.read(length)
        except (TimeoutError, socket.timeout):
            body = None
        finally:
            self.connection.settimeout(None)
        if body is None:
            self._reject(408, "request body read timed out")
            return None
        return body

    def _stream_body_to_file(self, dest: Path, max_bytes: int) -> "int | None":
        """Stream the request body to ``dest`` in bounded chunks, never holding it whole
        in RAM (used for the STT audio upload). Same guards as ``_read_body`` —
        reject chunked / malformed / oversized, and time-bound the read — but writes
        straight to disk. Returns the number of bytes written, or ``None`` after
        sending the matching error + closing (and removing any partial file)."""
        if self.headers.get("Transfer-Encoding"):
            self._reject(411, "Transfer-Encoding unsupported — send Content-Length")
            return None
        raw_len = self.headers.get("Content-Length")
        if raw_len is None:
            return 0
        try:
            length = int(raw_len)
        except ValueError:
            length = -1
        if length < 0:
            self._reject(400, "invalid Content-Length")
            return None
        if length > max_bytes:
            self._reject(413, "request body too large")
            return None
        if length == 0:
            return 0
        self.connection.settimeout(_BODY_READ_TIMEOUT)
        remaining = length
        try:
            with open(dest, "wb") as out:
                while remaining > 0:
                    chunk = self.rfile.read(min(_READ_CHUNK, remaining))
                    if not chunk:
                        break  # client closed early — body is short of the declared length
                    out.write(chunk)
                    remaining -= len(chunk)
        except (TimeoutError, socket.timeout):
            dest.unlink(missing_ok=True)
            self._reject(408, "request body read timed out")
            return None
        finally:
            self.connection.settimeout(None)
        if remaining > 0:  # fewer bytes arrived than Content-Length promised → truncated.
            dest.unlink(missing_ok=True)  # never hand a partial clip downstream as if whole.
            self._reject(400, "request body shorter than Content-Length")
            return None
        return length

    # ── routing ─────────────────────────────────────────────────────────────
    def do_OPTIONS(self) -> None:  # noqa: N802 (stdlib naming)
        if not self._host_allowed():
            return
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if not self._host_allowed():
            return
        path = urlparse(self.path).path
        if path == "/api/missions":
            return self._handle_list_missions()
        if path == "/api/models":
            return self._handle_models_status()
        if path.startswith("/api/mission/"):
            rest = path[len("/api/mission/"):]
            if rest.endswith("/pdf"):
                return self._handle_mission_pdf(rest[: -len("/pdf")])
            return self._handle_get_mission(rest)
        if path.startswith("/media/"):
            return self._handle_media_asset(path)
        return self._handle_static(path)

    def do_POST(self) -> None:  # noqa: N802
        if not self._host_allowed():
            return
        path = urlparse(self.path).path
        if path == "/api/mission":
            return self._handle_run_mission()
        if path == "/api/image":
            return self._handle_generate_image()
        if path == "/api/tts":
            return self._handle_synthesize()
        if path == "/api/stt":
            return self._handle_transcribe()
        if path.startswith("/api/mission/") and path.endswith("/cancel"):
            run_id = path[len("/api/mission/"):-len("/cancel")]
            return self._handle_cancel_mission(run_id)
        # Unknown POST: the body is never read, so close to avoid a keep-alive desync.
        self._reject(404, "not found")

    # ── API: list / get saved missions ───────────────────────────────────────
    def _handle_list_missions(self) -> None:
        from agency_kit import store
        # Scope history to THIS project (the server's --path), not the global store —
        # so the GUI doesn't list every mission ever run on the machine.
        project_root = self.server.project_root  # type: ignore[attr-defined]
        self._send_json({"missions": store.list_missions(project_root=project_root)})

    def _load_scoped_dossier(self, mission_id: str) -> "dict | None":
        """Load a saved dossier and confirm it belongs to THIS project (the server's
        --path). Sends a 404 and returns None for a missing/unreadable/corrupt
        dossier or a mission from another project; otherwise returns the dossier.
        Shared by GET-by-id and PDF so both scope identically — a foreign mission is
        never disclosed, and a corrupt dossier.json is a clean 404, not a dropped
        connection (do_GET has no top-level handler)."""
        from agency_kit import store
        try:
            dossier = store.load(mission_id)
        except (OSError, ValueError):  # missing/unreadable file, or invalid JSON
            self._send_error_json(404, f"mission '{mission_id}' not found")
            return None
        if not store.mission_in_project(dossier, self.server.project_root):  # type: ignore[attr-defined]
            self._send_error_json(404, f"mission '{mission_id}' not found")
            return None
        return dossier

    def _handle_get_mission(self, mission_id: str) -> None:
        # Reject traversal / malformed ids before they reach the filesystem.
        mission_id = _safe_mission_id(mission_id)
        if mission_id is None:
            return self._send_error_json(404, "mission not found")
        dossier = self._load_scoped_dossier(mission_id)
        if dossier is not None:
            self._send_json(dossier)

    def _handle_mission_pdf(self, mission_id: str) -> None:
        """Export a mission's deliverable to PDF and stream it back.

        Uses agency-kit's ``exporter.export_pdf`` (the ``[pdf]`` extra). A missing
        extra yields 501 (with install guidance) rather than a 500 traceback.
        """
        mission_id = _safe_mission_id(mission_id)
        if mission_id is None:
            return self._send_error_json(404, "mission not found")
        # Scope before rendering: don't export another project's deliverable into a
        # shareable PDF (same confinement + corrupt-dossier handling as GET-by-id).
        if self._load_scoped_dossier(mission_id) is None:
            return
        from agency_cli import exporter
        try:
            # Pass the assets root so the exporter can resolve any /media asset
            # reference in the deliverable back to its on-disk file (Wave 3).
            pdf_path = exporter.export_pdf(mission_id, assets_root=self.server.assets_root)  # type: ignore[attr-defined]
            body = Path(pdf_path).read_bytes()
        except ImportError as exc:  # [pdf] extra not installed
            return self._send_error_json(501, str(exc))
        except OSError:  # no deliverable, or the file vanished/unreadable before we read it
            return self._send_error_json(404, f"no deliverable for mission '{mission_id}'")
        except Exception:  # a render failure (e.g. WeasyPrint) — clean 500, not a dropped socket
            # Log the full trace to the operator (log_message is silenced), but return
            # a generic message so internal paths in the exception don't leak.
            import traceback
            traceback.print_exc()
            return self._send_error_json(500, "PDF export failed")
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
        # Register an ephemeral run id BEFORE streaming, and announce it as the first
        # frame, so the GUI can stop this exact run via POST /api/mission/{id}/cancel
        # without relying on a connection drop. Always unregistered on the way out.
        run_id = uuid.uuid4().hex
        cancel_event = threading.Event()
        self._register_run(run_id, cancel_event)
        try:
            self._write_sse({"phase": "run", "run_id": run_id})
            result_box = self._stream_mission(goal, engine, cancel_event)
        finally:
            # Deregister the instant the run is over — BEFORE writing the terminal
            # frame — so a cancel arriving during that (socket-write) window gets a
            # clean 404, not a misleading 202 'cancelling' for an already-finished run.
            self._unregister_run(run_id)
        if result_box is not None:  # None ⇒ client disconnected mid-stream
            self._send_terminal_frame(result_box)

    def _register_run(self, run_id: str, cancel_event: threading.Event) -> None:
        server = self.server  # type: ignore[attr-defined]
        with server.runs_lock:
            server.runs[run_id] = cancel_event

    def _unregister_run(self, run_id: str) -> None:
        server = self.server  # type: ignore[attr-defined]
        with server.runs_lock:
            server.runs.pop(run_id, None)

    def _handle_cancel_mission(self, run_id: str) -> None:
        """Cancel an in-flight mission by its run id (POST /api/mission/{id}/cancel).

        Sets the run's cancel_event and answers 202. The worker polls that event
        (via ``should_cancel``) and stops the mission — killing any in-flight engine
        subprocess — before any persistence, so a cancelled run leaves no trace. An
        unknown or already-finished run is a 404 (a run is unregistered the moment it
        ends, so any malformed/stale id simply misses the registry). Idempotent: a
        second cancel of the same run is just another 404."""
        if self._read_body() is None:
            return  # malformed/oversized body: _read_body already answered + closed
        server = self.server  # type: ignore[attr-defined]
        with server.runs_lock:
            cancel_event = server.runs.get(run_id)
        if cancel_event is None:
            return self._send_error_json(404, "unknown run")
        cancel_event.set()
        self._send_json({"status": "cancelling", "run_id": run_id}, status=202)

    def _parse_mission_request(self) -> "tuple[str, str] | None":
        """Read + validate the JSON body. Returns ``(goal, engine)``, or ``None``
        after sending the matching error: a 400 for bad JSON / a non-object body /
        missing goal, or the error ``_read_body`` already sent (400/408/411/413) for a
        malformed, withheld, chunked, or oversized body."""
        payload = self._read_json_body()
        if payload is None:
            return None  # _read_json_body already sent the error (and closed if needed)
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

    def _stream_mission(
        self, goal: str, engine: str, cancel_event: threading.Event
    ) -> "dict | None":
        """Run the mission on a worker thread and stream its progress events.

        Returns the result box (carrying ``result``, ``error``, or ``cancelled``)
        once the worker signals completion, or ``None`` if the client disconnected
        mid-stream.

        ``cancel_event`` is shared with the run registry: it is set either by the
        explicit cancel endpoint (the GUI's "Stop mission") or by a detected
        disconnect (a failed event/heartbeat write). The worker polls it via
        ``should_cancel`` both at phase boundaries AND inside the engine's in-flight
        subprocess call — so the running child is killed promptly and the mission
        raises ``MissionCancelled`` before any persistence.
        """
        events: "queue.Queue[dict | None]" = queue.Queue()
        result_box: dict = {}
        project_root = self.server.project_root  # type: ignore[attr-defined]
        # Built over the server (never `self`) so the daemon worker doesn't pin the handler.
        render_assets = _build_render_assets(self.server, events, cancel_event)  # type: ignore[attr-defined]

        def _worker() -> None:
            # Capture only `project_root` (a str) + `render_assets` (closed over the server,
            # not `self`): this daemon thread can outlive the request after a disconnect, and
            # capturing the handler would pin its dead socket buffers alive until the worker
            # reaches a boundary.
            from agency_cli import runner_bridge
            from agency_cli.engines.cli_engine import MissionCancelled
            try:
                result_box["result"] = runner_bridge.run(
                    goal,
                    project_root=project_root,
                    engine=engine,
                    on_event=events.put,
                    should_cancel=cancel_event.is_set,
                    asset_clause=ASSET_CLAUSE,
                    render_assets=render_assets,
                )
            except MissionCancelled:
                # Stopped before any persistence. Recorded so that — when the client
                # is still connected (an explicit endpoint cancel) — the drain loop
                # can emit a `cancelled` terminal frame; on a disconnect the drain
                # has already returned None and no frame is sent.
                result_box["cancelled"] = True
            except Exception as exc:  # surfaced to the client as an SSE error event
                result_box["error"] = str(exc)
            finally:
                events.put(None)  # sentinel: worker finished

        threading.Thread(target=_worker, daemon=True).start()

        # Bound every streaming write: _read_body left settimeout(None), so without this
        # a non-draining client makes wfile.write block forever. A timed-out write is
        # treated as a gone client (sets cancel_event below), the same as a broken pipe.
        self.connection.settimeout(_STREAM_SEND_TIMEOUT)

        # Drain progress events until the worker signals completion. The get() is
        # bounded so a long, event-silent engine call can't hide a disconnect: on
        # each idle tick we send a heartbeat, and a failed write (client gone) sets
        # cancel_event — which the engine reads mid-call to kill the in-flight tree.
        while True:
            try:
                event = events.get(timeout=_HEARTBEAT_SECONDS)
            except queue.Empty:
                if not self._write_heartbeat():
                    cancel_event.set()
                    return None
                continue
            if event is None:
                break
            if not self._write_sse(event):
                # Client gone: ask the worker to cancel. The queue is unbounded so the
                # worker's remaining put()s never block — no need to keep draining; the
                # daemon thread unwinds once the engine raises MissionCancelled.
                cancel_event.set()
                return None
        return result_box

    def _write_heartbeat(self) -> bool:
        """Write an SSE comment line as a liveness probe. Returns False once the
        client has gone — a failed write is the reliable disconnect signal (the GUI
        aborted the fetch / closed the connection), unlike a read-side EOF which a
        client that half-closes its write half but keeps reading would trip falsely.
        Comment lines (``:`` prefix) carry no ``data:`` field, so the GUI's SSE
        parser ignores them. Mirrors ``_write_sse``'s gone-client handling."""
        try:
            self.wfile.write(b": heartbeat\n\n")
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            return False

    def _send_terminal_frame(self, result_box: dict) -> None:
        """Emit the final SSE frame: an ``error`` frame, a ``cancelled`` frame (an
        explicit endpoint stop landed while the client was still connected), or a
        ``done`` frame with the saved mission's id / verdict / path / residual risk."""
        if "error" in result_box:
            self._write_sse({"phase": "error", "message": result_box["error"]})
            return
        if result_box.get("cancelled"):
            self._write_sse({"phase": "cancelled"})
            return
        result = result_box.get("result")
        if result is None:
            return
        dossier = result.dossier
        verdicts = dossier.get("verdicts") or []
        manifest = dossier.get("assets") or []
        rendered = sum(1 for a in manifest if isinstance(a, dict) and a.get("status") == "ok")
        self._write_sse({
            "phase": "done",
            "mission_id": dossier.get("mission_id"),
            "verdict": verdicts[-1].get("verdict") if verdicts else None,
            "path": str(result.path),
            "residual_risk": dossier.get("residual_risk"),
            # Wave 3: the asset manifest + partial-render summary (empty for non-asset runs).
            "assets": manifest,
            "assets_rendered": rendered,
            "assets_total": len(manifest),
        })

    def _write_sse(self, event: dict) -> bool:
        """Write one SSE ``data:`` frame. Returns False if the client has gone."""
        frame = f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8")
        try:
            self.wfile.write(frame)
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            return False

    # ── API: local multimodal (Wave 2 — image / TTS / STT) ────────────────────
    # Audio Content-Type → file extension for an STT upload (ffmpeg, under mlx-
    # whisper, keys decode off the extension). Default .wav for an unknown type.
    _AUDIO_EXT = {
        "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/wave": ".wav",
        "audio/mpeg": ".mp3", "audio/mp3": ".mp3",
        "audio/mp4": ".m4a", "audio/x-m4a": ".m4a",
        "audio/ogg": ".ogg", "audio/webm": ".webm", "audio/flac": ".flac",
    }

    def _media_manager(self):
        """Lazily build + cache the one ModelManager for this server. Created on the
        first multimodal request (not at startup) so the [media] extra is only needed
        when a media route is actually used — the core server boots without it."""
        server = self.server  # type: ignore[attr-defined]
        with server.media_lock:
            if server.media is None:
                from agency_studio.engines.local_media import ModelManager
                server.media = ModelManager(server.assets_root)
            return server.media

    def _read_json_body(self) -> "dict | None":
        """Read + parse a small JSON object body. Returns the dict, or ``None`` after
        sending the matching error (the one ``_read_body`` already sent, or a 400)."""
        raw = self._read_body()
        if raw is None:
            return None  # _read_body already sent + closed
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send_error_json(400, "body must be JSON")
            return None
        if not isinstance(payload, dict):
            self._send_error_json(400, "body must be a JSON object")
            return None
        return payload

    def _media_url(self, path: "str | Path") -> str:
        """Map a generated asset's filesystem path to its public ``/media/...`` URL (relative
        to the server's assets root). Thin wrapper over the module-level :func:`_media_url`,
        shared with the marker-render bridge so the two can't drift."""
        return _media_url(self.server.assets_root, path)  # type: ignore[attr-defined]

    def _handle_generate_image(self) -> None:
        payload = self._read_json_body()
        if payload is None:
            return
        prompt = (payload.get("prompt") or "").strip()
        if not prompt:
            return self._send_error_json(400, "missing 'prompt'")
        # Validate client params up front (→ 400). With inputs already bounded here,
        # any exception from the manager call below is necessarily a back-end failure
        # (→ 500), not a mislabeled client error — and clamped dims/steps mean a
        # request can't trigger an unbounded-compute OOM that wedges the media lock.
        from agency_studio.engines import models as media_models
        try:
            # Resolve the model first (unknown id → 400) so `steps` is bounded by THAT
            # model's own ceiling — not a one-size cap that would clamp the slower,
            # higher-quality models. width/height stay globally bounded (compute guard).
            model = payload.get("model") or media_models.DEFAULT_IMAGE_MODEL
            entry = media_models.image_model(model)  # raises ValueError on unknown id
            raw_steps = payload.get("steps")
            steps = _require_int_in_range(raw_steps, 1, entry.steps_max, "steps") \
                if raw_steps is not None else None
            width = _require_int_in_range(payload.get("width", 1024), _IMAGE_MIN_DIM, _IMAGE_MAX_DIM, "width")
            height = _require_int_in_range(payload.get("height", 1024), _IMAGE_MIN_DIM, _IMAGE_MAX_DIM, "height")
            raw_seed = payload.get("seed")
            seed = int(raw_seed) if raw_seed is not None else None
        except (ValueError, TypeError) as exc:
            return self._send_error_json(400, str(exc))
        kwargs = {"steps": steps, "seed": seed, "width": width, "height": height, "model": model}
        try:
            result = self._media_manager().generate_image(prompt, **kwargs)
            url = self._media_url(result.path)  # inside the guard: a mapping error is a 500, not a dropped socket
        except ImportError as exc:  # MediaUnavailable — [media] extra not installed
            return self._send_error_json(501, str(exc))
        except Exception:  # inference / model-fetch failure — clean 500, never a 400 leak
            import traceback
            traceback.print_exc()
            return self._send_error_json(500, "image generation failed")
        self._send_json({
            "url": url, "prompt": result.prompt,
            "seed": result.seed, "seconds": result.seconds, "model": result.model,
        })

    def _handle_synthesize(self) -> None:
        payload = self._read_json_body()
        if payload is None:
            return
        text = (payload.get("text") or "").strip()
        if not text:
            return self._send_error_json(400, "missing 'text'")
        # Validate a client-supplied voice up front (→ 400 with the allowlist), so an
        # unknown voice is an actionable client error — not the generic 500 the manager's
        # ValueError would otherwise become under the `except Exception` below. A
        # falsy/omitted voice falls through to synthesize's default (af_heart).
        from agency_studio.engines import models as media_models
        voice = payload.get("voice")
        if voice and voice not in media_models.ALLOWED_VOICES:
            return self._send_error_json(
                400, f"unknown voice {voice!r} (allowed: {sorted(media_models.ALLOWED_VOICES)})"
            )
        try:
            kwargs = {"voice": voice} if voice else {}
            result = self._media_manager().synthesize(text, **kwargs)
            url = self._media_url(result.path)
        except ImportError as exc:  # [media] extra not installed
            return self._send_error_json(501, str(exc))
        except Exception:  # synthesis / model-fetch failure — clean 500
            import traceback
            traceback.print_exc()
            return self._send_error_json(500, "speech synthesis failed")
        self._send_json({"url": url, "voice": result.voice, "seconds": result.seconds})

    def _handle_transcribe(self) -> None:
        """Transcribe a raw audio body (POST /api/stt). The body is streamed straight
        to a short-lived upload file (never held whole in RAM), transcribed, then
        removed — it is transient input, not a gallery asset."""
        ctype = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        suffix = self._AUDIO_EXT.get(ctype, ".wav")
        uploads = Path(self.server.assets_root) / "uploads"  # type: ignore[attr-defined]
        uploads.mkdir(parents=True, exist_ok=True)
        upload = uploads / f"{uuid.uuid4().hex}{suffix}"
        written = self._stream_body_to_file(upload, max_bytes=_MAX_AUDIO_BYTES)
        if written is None:
            return  # _stream_body_to_file already sent the error + cleaned up the partial
        if written == 0:
            upload.unlink(missing_ok=True)
            return self._send_error_json(400, "empty audio body")
        try:
            result = self._media_manager().transcribe(upload)
        except ImportError as exc:  # [media] extra not installed
            return self._send_error_json(501, str(exc))
        except Exception:  # transcription / model-fetch failure — clean 500
            import traceback
            traceback.print_exc()
            return self._send_error_json(500, "transcription failed")
        finally:
            upload.unlink(missing_ok=True)  # the upload is transient input, not output
        self._send_json({"text": result.text, "seconds": result.seconds})

    def _handle_models_status(self) -> None:
        """Report which model (if any) is currently warm + the configured model ids.
        Feeds the GUI's ModelManager panel (Wave 2.3). Loads nothing."""
        from agency_studio.engines import models as media_models
        # Read under media_lock so a concurrent first-request lazy-init can't be seen
        # half-built (the manager reference is set under this same lock).
        with self.server.media_lock:  # type: ignore[attr-defined]
            mgr = self.server.media  # type: ignore[attr-defined]  # None until first media op
        self._send_json({
            "resident": mgr.resident if mgr is not None else None,
            "image_models": media_models.image_models_payload(),
            "models": {
                "stt": media_models.STT_HF_REPO,
                "tts": "kokoro-v1.0",
            },
        })

    def _handle_media_asset(self, path: str) -> None:
        """Serve a generated asset from the assets root, guarded by ``path_inside()``
        (same traversal defense as the static GUI). 404 for an escape or a miss."""
        root: Path = self.server.assets_root  # type: ignore[attr-defined]
        target = path_inside(root, path[len("/media/"):])
        if target is None or not target.is_file():
            return self._send_error_json(404, "not found")
        self._serve_file(target)

    def _serve_file(self, target: Path) -> None:
        """Read a file and send it with its content type. Single implementation shared
        by the generated-asset route (/media) and the static GUI handler."""
        body = target.read_bytes()
        content_type = _CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        self._send_bytes(body, content_type)

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
            # SPA fallback: a client-side route → index.html. A missing path whose
            # suffix is a KNOWN asset type is a real asset (e.g. a stale hashed bundle)
            # — 404 it, never serve index.html as that type (the browser would reject
            # the module script and the GUI would blank-screen). Keying on known types
            # (not "any dot") means a route segment with a dot still falls back.
            if Path(path).suffix.lower() in _CONTENT_TYPES:
                return self._send_error_json(404, "not found")
            target = root / "index.html"
            if not target.is_file():
                return self._send_error_json(404, "not found")
        self._serve_file(target)

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
    # Resolve once at startup so history scoping is bound to a fixed directory, not
    # re-derived from the process CWD on each request (a default --path "." would
    # otherwise drift if the server's CWD ever changed).
    httpd.project_root = str(Path(project_root).resolve())  # type: ignore[attr-defined]
    httpd.static_root = Path(static_root) if static_root else None  # type: ignore[attr-defined]
    # Registry of in-flight missions: run_id → cancel_event. The explicit cancel
    # endpoint looks a run up here and sets its event; the SSE handler registers on
    # start and removes on finish. A lock guards it because ThreadingHTTPServer runs
    # each request (run + cancel) on its own thread.
    httpd.runs = {}  # type: ignore[attr-defined]
    httpd.runs_lock = threading.Lock()  # type: ignore[attr-defined]
    # Wave 2 — local multimodal. Generated assets land under <project>/studio_assets/
    # (served read-only via /media/, path_inside-guarded). The ModelManager is built
    # lazily on the first media request (see _media_manager) so the [media] extra is
    # only required when a media route is actually used.
    httpd.assets_root = Path(project_root).resolve() / "studio_assets"  # type: ignore[attr-defined]
    httpd.media = None  # type: ignore[attr-defined]
    httpd.media_lock = threading.Lock()  # type: ignore[attr-defined]
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
