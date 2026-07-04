# Security — Agency Studio

Non-negotiable posture, applied **from Wave 0**. It deliberately takes the opposite stance
of the flaws found in existing local runners (notably Uncensored-Local-Studio: server
exposed on `0.0.0.0` + path traversal).

## Hard rules

| # | Rule | Why |
|---|---|---|
| 1 | **Bind `127.0.0.1` only** (never `0.0.0.0`). | Avoids silent LAN exposure. A "privacy" studio must not be drivable from another machine on the network. |
| 2 | **No `Access-Control-Allow-Origin: *`.** Local origin only. | Prevents a third-party website from calling the local API from the browser. |
| 3 | **`path_inside()` on 100% of static file serving.** | Blocks path traversal (`GET /../../etc/passwd`). Resolve the path and verify it stays under `dist/`. |
| 4 | **Validate scheme/host of download URLs.** | Prevents downloading arbitrary URLs (SSRF / untrusted content). |
| 5 | **Verify checksums of downloaded binaries/models.** | Supply-chain guard before executing a local binary. |
| 6 | **No telemetry, no secrets in plaintext.** | Consistent with the local-first ethos. |

## Source verification probes (Brick 3)

Mission source verification is offline by default. The default gate counts cited URLs in
department outputs without touching the network. Online URL liveness checks run only when
the operator opts in for that mission (`--resolve-sources` / GUI "Verify sources online").

When enabled, probes are bounded and low-trust by design:

- HTTPS-only URL policy before any socket work.
- Literal private, loopback, link-local, reserved IPs and `localhost` are refused before fetch.
- HEAD only, 5 s per URL, no body read, no credentials, cookies, API keys, or request fields.
- Every redirect hop is re-checked against the same policy (https-only, no private/loopback
  targets) and stays a HEAD — a chain that leaves the secure public web is refused and the
  source classified unresolved.
- At most 50 unique URLs per cycle, with a small worker pool and a cycle wall-time clamp.
- Total network outage degrades to "unverified" instead of pretending URLs are dead.

Accepted residual: no DNS-rebinding pinning. The probe sends no secrets and reads no body;
literal private/loopback targets are blocked pre-socket, so full DNS pinning is deferred until
there is evidence it is needed.

## Regression test (from Wave 0)

```bash
# Path traversal blocked
curl --path-as-is http://127.0.0.1:<port>/../../../../etc/passwd   # → expect 404

# The server listens ONLY on loopback
lsof -iTCP -sTCP:LISTEN | grep <port>                              # → 127.0.0.1 only
```

Both checks are part of Wave 0's definition of done and must be covered by
`tests/test_server.py`.

## Wave 2 — model downloads (rules #4 & #5, implemented)

The local multimodal layer downloads model weights at runtime; the supply-chain rules
are enforced in `agency_studio/engines/models.py` (covered by `tests/test_local_media.py`):

- **Hub-managed models** (mflux / mlx-whisper) are pulled by repo id through `huggingface_hub`,
  which stores blobs in a **content-addressed cache** — integrity comes from the content hash.
- **Direct-URL files** (the two Kokoro-onnx artifacts) go through `models.ensure_file`, which:
  - **validates the URL** — `https` only, host on a fixed **allowlist**, re-checked on
    **every redirect hop** (`_AllowlistRedirectHandler`) so an allowlisted host can't bounce
    the bytes elsewhere (rule #4);
  - **verifies SHA-256** against a pinned digest on **every load** (cache hits included),
    removing and rejecting a file that fails (rule #5);
  - bounds the download size and time, and writes atomically (temp + rename).
- Generated assets are served read-only under `/media/`, guarded by the same
  `path_inside()` as the GUI; a traversal attempt is a 404 (asserted in `tests/test_server_media.py`).
- The image model is loaded from a **non-gated, Apache-2.0** pre-quantized mirror, so no
  Hugging Face token or credential is stored anywhere (consistent with rule #6).

## Wave 4 — RAG / LocalDocs (rules #1, #3, #4, #5, implemented)

The local-docs layer ingests user documents and stores their text + vectors; it applies the
same posture as the media layer (covered by `tests/test_server.py` + `tests/test_rag.py`):

- **The document store is never web-served.** Ingested text + embeddings live in a SQLite
  DB under `<project>/.agency-studio/` — deliberately **outside** `studio_assets/`, the only
  root the `/media` route serves. So no `/media/...` request can ever reach a document's text
  (rule #3, by construction — the DB is not under the served root at all).
- **The upload body is bounded and streamed.** `POST /api/docs` streams the raw file to a
  short-lived temp file capped at `_MAX_DOC_BYTES` (64 MiB) in `_READ_CHUNK` pieces (never
  held whole in RAM), then deletes it; `rag.MAX_DOC_CHARS` bounds the extracted text before
  chunking. The uploaded `filename` is reduced to its basename (`Path(...).name`) so it can't
  carry a path (defense in depth — it's only used for a suffix + a display title).
- **The embedding model download is pinned** (rules #4/#5): pulled by repo id through
  `huggingface_hub` (allowlisted host, content-addressed cache) and pinned to an immutable
  commit SHA in `engines/models.py` (`EMBED_MODELS[...].revision`), so a moved/force-pushed
  repo can't swap the weights on the next load — the same guarantee as the Wave-2 STT/image
  pins.
- **`sqlite-vec` is a local file extension only** — no network, no server; loaded via
  `sqlite3.enable_load_extension`, and if that is unavailable the pure-Python fallback runs
  (no native code loaded at all).
- **Retrieval is best-effort and never weakens the gate.** Retrieved excerpts are injected
  as an additive `context_clause` (see `docs/WAVE4-PLAN.md`); they reach the department +
  synthesis prompts only, never the router or Inspector, and the veto loop is unchanged.

## Wave 6 — Visual RAG / PixelRAG (rules #1, #3, #4, #5, #6, implemented)

Visual RAG captions uploaded images with a vision-language model and stores the caption + its
vector, so a text goal can retrieve image content the text pipeline is blind to. It reuses the
Wave-4 store discipline, and adds the **studio's first (opt-in) off-machine data flow** — fenced
so the default remains fully local (covered by `tests/test_visual.py` + `tests/test_server.py`):

- **The caption store is never web-served.** Captions + embeddings live in a SQLite DB
  (`visual-<model>.db`) under `<project>/.agency-studio/` — outside `studio_assets/`, so no
  `/media/...` request can reach an image's derived caption (rule #3, by construction). The raw
  image is captioned to a short-lived temp file capped at `_MAX_IMAGE_BYTES` (32 MiB), streamed,
  then deleted — never persisted; the `filename` is reduced to its basename.
- **Local by default — the mission path can never touch the network.** The default backend is a
  local MLX Qwen3-VL (the `[visual]` extra); captioning is the ONLY model-bearing step and it
  happens at **ingest** time (`POST /api/visual`), never during a mission. At mission time the
  `visual` flag only retrieves already-stored local caption vectors — a pure-local lookup that is
  structurally incapable of a network call.
- **The optional cloud VLM is fenced by three independent gates.** It is reachable only when the
  user (a) supplies an API key in the environment (`AGENCY_STUDIO_VISUAL_API_KEY` — never a
  request field, never persisted, never returned by an endpoint, never logged), (b) gives
  **explicit per-upload consent** via `?cloud=1` on the ingest request (a checkbox in the GUI,
  never a saved default), and (c) has the endpoint pass an **https-only** check before any socket
  (rule #4). Absent any of these, the cloud backend raises `VisualUnavailable` (→ 501) — a clean
  error, never a silent network attempt — and the local backend is used. The API key is read from
  the environment at call time and never appears in an error/SSE frame (rule #6).
- **The local VLM download is pinned** (rules #4/#5): pulled by repo id through `huggingface_hub`
  (allowlisted host, content-addressed cache) and pinned to an immutable commit SHA in
  `agency_studio/visual.py` (`VISUAL_MODELS["qwen3-vl-local"].revision` — the same
  `mlx-community/Qwen3-VL-8B-Instruct-4bit` repo + reviewed SHA the Boogu conditioner pins in
  `engines/models.py`), like the Wave-2/4 pins, so a moved/force-pushed mirror can't swap the
  weights on the next download.
- **Retrieval is best-effort and never weakens the gate.** Image captions are injected as an
  additive `context_clause` (composed after RAG/web/MCP/knowledge); they reach the department +
  synthesis prompts only, never the router or Inspector, and the veto loop is unchanged.

## Wave 6 — Cloud video / seedance (rules #4, #5, #6, implemented)

Cloud video (`seedance-2.0`) renders a short marketing clip as a department deliverable, via an
off-machine API. It is the studio's **first *mission-time* off-machine flow** — a video marker is
MODEL OUTPUT (untrusted) rendered *during* a mission, categorically different from Visual RAG's
ingest-only, user-consented upload. So it carries a **stricter, triple gate** (covered by
`tests/test_seedance.py` + video cases in `tests/test_assets.py` / `test_server.py`):

- **A per-mission `video` opt-in flag is the primary gate.** It is threaded straight into the
  untrusted-boundary parser — `assets.parse_markers(..., allow_video=<flag>)`. With it off (the
  default), every `video` marker is dropped *at parse time*, before a request is ever built, so the
  render path — and any network call — is structurally unreachable and the mission is byte-identical
  to one with no video markers. This means **an untrusted marker alone can never decide to
  network**: a human must have opted this specific mission into cloud video.
- **An env-only API key** (`AGENCY_STUDIO_VIDEO_API_KEY`) is read at call time in
  `seedance._probe_cloud` / `_run_cloud` — never a request field, never persisted, never returned by
  an endpoint, never logged or placed in an error/SSE frame (rule #6). Absent ⇒ a clean
  `SeedanceUnavailable` (→ 501), never a silent attempt.
- **An https-only endpoint** is enforced in `_probe_cloud` before any socket (rule #4); every entry
  in `VIDEO_MODELS` is asserted https in the suite. Video is **cloud-only** (no local backend — the
  model doesn't fit the 16 GB Mac), so there is no local-fallback path to reason about.
- **The marker never chooses compute.** Model tier, clip duration, and resolution are fixed safe
  caps (`MAX_VIDEO = 1`, a short 720p render) in the parser — an untrusted marker can't weaponise a
  long/4k clip as a cost-DoS, the same discipline as the image model/canvas allowlist. Video is also
  route-gated to `marketing`, like an image.
- **Rendered clips live under the served assets root** (`studio_assets/missions/<id>/videos/`,
  reached only through the existing `path_inside`-guarded `/media` route with a `video/mp4` MIME);
  a failed render leaves no file, only a `_[video unavailable]_` placeholder in the deliverable.

## `path_inside()` reference implementation

Mirrors the shipped guard in `agency_studio/server.py` (the source of truth). It takes the
GUI root first and the requested URL path second, treats the request as relative to the
root, and returns the resolved absolute path when it genuinely stays inside the root —
otherwise `None`, so the caller serves a 404 instead of the file.

```python
from pathlib import Path

def path_inside(root: Path, requested: str) -> Path | None:
    """Resolve `requested` under `root`; return the path if inside, else None."""
    root = root.resolve()
    candidate = (root / requested.lstrip("/")).resolve()
    if candidate == root or root in candidate.parents:
        return candidate
    return None
```
