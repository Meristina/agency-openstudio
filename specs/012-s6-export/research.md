# Phase 0 Research: S6 Export

**Feature**: Export — Turn Finished Work into Shareable Bundles (Brick 7 · Screen S6)
**Date**: 2026-07-06
**Method**: Direct inspection of the existing studio code + agency-kit exporter; every decision
is grounded in a real file/line, and every unknown from Technical Context is resolved here.

---

## D1 — Where the new media-zip / bundle packaging logic lives

**Decision**: Add a new **studio-core** module `agency_studio/bundler.py` (Python stdlib
`zipfile`). Do **not** edit `agencykit/agency_cli/exporter.py`; instead **call**
`exporter.export_pdf` from the bundler for the bundle's document piece.

**Rationale**: `agencykit/` is a **pinned vendored subtree** (Constitution Principle V; AGENTS.md
subtree rules) updated only via `git subtree pull` — editing its `exporter.py` risks merge
divergence and violates the subtree rule. The studio already imports agency-kit's exporter across
the package boundary (`from agency_cli import exporter` at `server.py:1032`), so calling
`export_pdf` for the bundle's PDF is the established, permitted seam. Keeping the zip/bundle logic
in `agency_studio/` (stdlib-only core) satisfies the zero-dependency mandate and lets it reuse the
studio's own `path_inside`/assets-root confinement.

**Alternatives considered**:
- *Extend `agencykit/exporter.py` with `export_media_zip`/`export_bundle`* — rejected: local edit
  to a pinned subtree (Principle V), merge divergence, and the media lives under the **studio's**
  `studio_assets/`, which agency-kit does not own.
- *Assemble the zip in the browser (JS zip lib)* — rejected: adds a frontend runtime dependency
  (against stdlib-core spirit), and would re-implement the `path_inside`/scope guards the server
  already owns; downloading many `/media` files client-side is slower and more error-prone.

---

## D2 — HTTP surface for the two new formats

**Decision**: Two new **GET** endpoints mirroring the existing PDF handler exactly:
- `GET /api/mission/{id}/media.zip` → `_handle_mission_media_zip`
- `GET /api/mission/{id}/bundle.zip` → `_handle_mission_bundle`

Dispatched from `_route_get` alongside the existing `/pdf` branch (`server.py:868–871`), each:
(1) `_safe_mission_id` the id, (2) `_load_scoped_dossier` (foreign/corrupt → clean 404,
`server.py:992–1008`), (3) build the zip via `bundler`, (4) stream via `_send_bytes(body,
"application/zip", extra_headers={"Content-Disposition": 'attachment; filename="…"'})` exactly as
`_handle_mission_pdf` does (`server.py:1048–1051`).

**Rationale**: The PDF handler (`server.py:1019–1051`) is the proven template for "scope a mission,
produce a downloadable artifact, stream it, map a missing optional extra to 501". Mirroring it
gives identical confinement, identical error semantics, and a frontend that reuses the
`fetchMissionPdf` pattern verbatim.

**Alternatives considered**: a single `?format=` query on one endpoint — rejected: three distinct
content types / filenames / capability-gates read more clearly as three sibling routes (`/pdf`
already exists), and keeps each handler small.

---

## D3 — Media enumeration + zip layout + path confinement

**Decision**: A mission's produced media lives under `assets_root/missions/<mission_id>/`
(`server.py:233`, served via `/media/…` guarded by `path_inside`, `server.py:2140`).
`build_media_zip` walks that directory, and for **each** file resolves it through
`path_inside(assets_root, "missions/<id>/<rel>")` before adding it, with a **sanitized relative
arcname** (`missions/<id>/…` stripped to the media-relative path; never absolute, never `..`).
The bundle zip nests media under `media/` and adds `deliverable.pdf` at the root plus `sources.md`.

**Rationale**: Reusing `path_inside` per file (defence in depth even though the tree is ours)
guarantees FR-018 — a bundle can never include a file outside its own mission tree — and matches
exactly how `/media` already serves those files. Sanitized arcnames close zip-slip on our own
output.

**Alternatives considered**: trusting the directory walk without per-file `path_inside` — rejected:
a stray symlink or crafted path in the assets tree must not escape; the guard is cheap and the
constitution treats path confinement as non-negotiable.

---

## D4 — The bundle's document, and how `[pdf]` gates formats

**Decision**: The bundle's document is the **PDF**, produced by the existing
`exporter.export_pdf(mission_id, assets_root=…)` (`exporter.py:21`, `server.py:1036`). When the
`[pdf]` extra is absent, `export_pdf` raises `ImportError`; the bundle handler maps that to **501
with the install hint** — exactly as `_handle_mission_pdf` does (`server.py:1038–1039`). Therefore
the **document** and **full-bundle** formats are `[pdf]`-gated; the **media pack** is not (pure
`zipfile`, always available when media exists). This realizes FR-012 precisely.

**Rationale**: One capability (`[pdf]`) already gates the polished document today; the bundle's
"readable deliverable" is that same PDF, so it inherits the same gate. The media pack needs only
stdlib `zipfile`, so it keeps working on a machine without `[pdf]` (FR-012: still-available
formats keep working).

**Alternatives considered**: degrade the bundle to raw `deliverable.md` when `[pdf]` is absent —
rejected for v1: it muddies the "document = the polished PDF" contract; a clean 501 with an install
hint (and the media pack still working) is more honest.

---

## D5 — The bundle's sources list (client-facing, human-readable)

**Decision**: `bundler.sources_markdown(dossier)` renders a plain, human-readable `sources.md`
from `dossier["sources"]` (the dossier's own cited sources; the dossier also carries
`open_to_verify`). Each entry becomes a readable line (title/label — URL — access date when
present). Per the Q3 clarification, the bundle includes **no** raw machine-readable dossier
snapshot (no `dossier.json`) in v1.

**Rationale**: The dossier already carries `sources` (agency-kit dossier shape; `server.py`
serializes `dossier["sources"]`). Rendering them read-only as markdown keeps the bundle
client-facing and self-contained (FR-010) without exposing internal structure (FR-013). No
mission-time verification is performed or weakened (Principle III) — it is a verbatim copy.

**Alternatives considered**: extract-and-resolve URLs at export time (verification.py) — rejected:
that is mission-time behavior; S6 must not perform or weaken verification, only package what
exists.

---

## D6 — Streaming vs buffering a potentially large bundle

**Decision**: Assemble the zip into a **temp file** (`tempfile`) and stream its bytes back via
`_send_bytes`. Note the existing large-payload-to-disk convention (`server.py:66` — bounded,
streamed to disk) as precedent for bounding memory on large media bundles. `_send_bytes` emits
`Connection: close` (`server.py:703`), matching the existing binary-download path.

**Rationale**: A media bundle can be tens of MB; buffering an unbounded archive fully in memory is
avoidable. A temp file keeps peak memory bounded and matches how the server already handles large
binaries; the existing `_serve_file` reads whole files, but bundles are the larger, streamed case.

**Alternatives considered**: `io.BytesIO` in-memory zip — acceptable at expected local volumes and
simpler, but rejected as the default for large media bundles; a temp file is the safer bound and is
cleaned up after send.

---

## D7 — Only finished deliverables are exportable; how the screen lists them

**Decision**: The Export screen reuses **S4's finished-deliverable listing** (the existing
`listMissions` / mission-summary path the Library already renders) scoped by the shell client
context; only **finished** deliverables are offered (FR-004). A still-running or failed mission is
not listed as exportable. `hasMedia` (whether the media-pack format is offered) is derived from the
dossier's `assets` manifest (`dossier["assets"]`, `server.py:1630`).

**Rationale**: S4 already resolves, scopes, and dedupes finished deliverables by client → project →
campaign; S6 is the "export" verb over that same finished set, so it consumes S4's model rather
than rebuilding it (spec: "builds on S4"). Reading `assets` presence tells the UI whether there is
media to pack (FR-009) without a server round-trip.

**Alternatives considered**: a dedicated `/api/exportable` endpoint — rejected: the finished-mission
listing already exists; adding an endpoint duplicates it and widens the server surface for no gain.

---

## D8 — Frontend download + error handling

**Decision**: Add `fetchMissionMediaZip(id)` and `fetchMissionBundle(id)` to `api.ts`, each a
`fetch → Blob` wrapper that throws on non-`ok` (surfacing 501/404/500 as catchable errors),
mirroring the existing `fetchMissionPdf` (`api.ts:133–136`). A shared `download.ts` turns a Blob +
`Content-Disposition` filename into a browser download. The Export screen translates the error at
render time (501 → "not available — how to enable"; 404 → "no deliverable/media"; 500 → "couldn't
build — retry").

**Rationale**: `fetchMissionPdf` already established the "fetch as Blob so a 501/404/500 is a
catchable error, not a broken `<a href>` navigation" pattern (its own docstring, `api.ts:128–132`).
Reusing it keeps all three formats consistent and gives FR-011/FR-012 states for free.

**Alternatives considered**: plain `<a download>` links — rejected: they can't surface a 501/500 as
a friendly in-app state (the whole reason `fetchMissionPdf` exists).

---

## D9 — Integration edits (screen lifecycle) + i18n

**Decision**: Flip the `export` route `status: "placeholder" → "shipped"` and `taxonomyScoped:
false → true` in `shell/router.ts`; mount `<Export />` in `Shell.tsx`'s `Outlet`; remove the
`export` entry from `screens/placeholders.tsx` (leaving `settings`); add `export.*` typed keys to
`i18n/catalog.ts` with EN (`en.ts`, source of truth) + FR (`fr.ts`) strings.

**Rationale**: This is the umbrella's designed screen lifecycle (placeholder → shipped), identical
to how S4/S5 shipped; it is byte-identical with the screen unused, satisfying Principle X.

**Alternatives considered**: none — this is the established, mandated pattern.

---

## Resolved unknowns

| Technical Context item | Resolution |
|---|---|
| Server change needed? | Yes — small, additive: 1 stdlib module (`bundler.py`) + 2 GET endpoints; `/pdf` and `agencykit/` untouched (D1, D2). |
| New runtime dependency? | No — stdlib `zipfile`/`io`/`tempfile`; PDF reuses the pre-existing `[pdf]` extra (D1, D4). |
| Storage/persistence? | None — transient downloads; reads existing dossier + `studio_assets/missions/<id>/` (D3, D6). |
| Testing strategy | Offline pytest (bundler + handlers, `export_pdf` monkeypatched) + Vitest (screen, mocked api) (Technical Context; D8). |
| Security posture | Scope confinement + per-file `path_inside` + sanitized arcnames + no secrets (D2, D3). |
| Bulk export | Deferred (spec Clarifications) — v1 single deliverable (D7). |
