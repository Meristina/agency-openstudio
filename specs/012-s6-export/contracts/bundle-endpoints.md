# Contract: Bundle export endpoints

**Feature**: S6 Export · **Date**: 2026-07-06
**Scope**: The two **new**, additive server endpoints that produce the media pack and the full
dossier bundle, plus the `bundler.py` functions behind them. The existing
`GET /api/mission/{id}/pdf` is **unchanged** and reused for the document format and the bundle's
document piece.

---

## Endpoint: `GET /api/mission/{id}/media.zip`

Produce a zip of a finished mission's **produced media** and stream it as a download.

**Handler**: `_handle_mission_media_zip(mission_id)` in `agency_studio/server.py`
(dispatched from `_route_get` next to the existing `/pdf` branch).

**Preconditions / flow** (mirrors `_handle_mission_pdf`):
1. `mission_id = _safe_mission_id(mission_id)` → `None` ⇒ **404** (`mission not found`).
2. `_load_scoped_dossier(mission_id)` → `None` ⇒ response already sent (**404** for missing /
   corrupt / foreign-project mission — identical confinement to `/pdf` and GET-by-id).
3. `bundler.build_media_zip(mission_id, assets_root=self.server.assets_root)`.

**Responses**:

| Status | When | Body |
|---|---|---|
| `200` | media zip built | `application/zip`; `Content-Disposition: attachment; filename="<friendly>.zip"` |
| `404` | no media for this mission (empty/absent `studio_assets/missions/<id>/`) | JSON error (`no media for mission '<id>'`) |
| `404` | missing / corrupt / foreign mission | JSON error (`mission '<id>' not found`) |
| `500` | packaging failure | JSON error (`media export failed`) — generic; full trace logged, no internal paths leaked |

Notes: the frontend does **not** normally hit the `404 no media` path — it derives `hasMedia` from
the dossier's `assets` manifest and disables the media pack pre-flight (FR-009) — but the endpoint
still guards it.

---

## Endpoint: `GET /api/mission/{id}/bundle.zip`

Produce a **self-contained, client-facing** dossier bundle (document + media + human-readable
sources) and stream it as a download.

**Handler**: `_handle_mission_bundle(mission_id)` in `agency_studio/server.py`.

**Preconditions / flow**: same 1–2 as above, then
`bundler.build_bundle(mission_id, assets_root=self.server.assets_root)`.

**Responses**:

| Status | When | Body |
|---|---|---|
| `200` | bundle built | `application/zip`; `Content-Disposition: attachment; filename="<friendly>.zip"` |
| `501` | `[pdf]` extra not installed (document piece unavailable) | JSON error with the install hint (`pip install -e ".[pdf]"`), identical to `/pdf` |
| `404` | no deliverable for this mission | JSON error (`no deliverable for mission '<id>'`) |
| `404` | missing / corrupt / foreign mission | JSON error (`mission '<id>' not found`) |
| `500` | render/packaging failure | JSON error (`bundle export failed`) — generic; trace logged |

Notes: because the bundle's document is the PDF, the bundle is `[pdf]`-gated exactly as `/pdf`
(FR-012). A bundle for a media-less deliverable still succeeds (document + sources; empty/omitted
`media/`).

---

## Module: `agency_studio/bundler.py` (stdlib `zipfile`)

Pure, read-only packaging helpers. **Never** mutates a dossier or writes into `studio_assets/`
(temp output only). No network, no engine, no API.

### `build_media_zip(mission_id, assets_root) -> Path`
- Media root = `Path(assets_root) / "missions" / mission_id`.
- Walk the media root; for **each** file, resolve through `path_inside(assets_root,
  "missions/<id>/<rel>")` and add only if it stays inside the assets root (defence in depth,
  FR-018). Skip anything that escapes.
- **Arcname**: media-relative path (e.g. `media/<rel>`), sanitized — relative only, no leading `/`,
  no `..`.
- If the media root is absent or contains no files ⇒ signal "no media" (handler → **404**).
- Returns a temp `.zip` path (caller streams then discards).

### `build_bundle(mission_id, assets_root) -> Path`
- `deliverable.pdf` ← `agency_cli.exporter.export_pdf(mission_id, assets_root=assets_root)`
  (raises `ImportError` when `[pdf]` absent ⇒ handler → **501**; `FileNotFoundError`/`OSError` when
  no deliverable ⇒ handler → **404**).
- `media/…` ← same confined walk as `build_media_zip` (omitted entirely if no media).
- `sources.md` ← `sources_markdown(dossier)`.
- No raw `dossier.json` / machine-readable snapshot in v1 (Q3 clarification).
- Returns a temp `.zip` path.

### `sources_markdown(dossier) -> str`
- Render `dossier.get("sources") or []` as a human-readable markdown list (title/label — URL —
  access date when present). Verbatim copy — performs **no** URL resolution or verification
  (Principle III). Empty sources ⇒ a plain "no sources cited" line, never a crash.

**Security invariants (all MUST hold)**:
- Every packaged media file passes `path_inside(assets_root, …)` — a bundle can never include a
  file outside its own mission tree (FR-018, Constitution VI).
- Zip entry names are sanitized (relative, no `..`, no absolute) — no zip-slip in our output.
- No secret is read, packaged, logged, or surfaced; no outbound network (FR-008, FR-010, FR-018).
- Temp artifacts are created outside `studio_assets/` (never re-served via `/media`) and discarded
  after streaming.

---

## Test contract (offline)

`tests/test_bundler.py` (new):
- `build_media_zip` over a temp mission media dir → correct entries, sanitized arcnames,
  `path_inside` confinement (a planted out-of-tree/symlink file is excluded), empty media → signal.
- `build_bundle` → contains `deliverable.pdf` (via **monkeypatched** `export_pdf`, no WeasyPrint),
  `media/…`, and `sources.md`; media-less mission → bundle without `media/`; `[pdf]` absent
  (monkeypatched `export_pdf` raising `ImportError`) → propagates for the handler's 501.
- `sources_markdown` from `dossier["sources"]`; empty sources → graceful line; read-only (input
  dossier unchanged).

`tests/test_server.py` (extended):
- `/media.zip` + `/bundle.zip` route dispatch; scope confinement (foreign/corrupt mission → 404);
  `application/zip` + `Content-Disposition`; no-media → 404; `[pdf]` absent on bundle → 501.
- Existing `/pdf` tests stay green (byte-identical handler).
