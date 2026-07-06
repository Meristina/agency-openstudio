# Quickstart: S6 Export

**Feature**: Export — Turn Finished Work into Shareable Bundles (Brick 7 · Screen S6)
**Date**: 2026-07-06 · **Branch**: `012-s6-export`

How to build, run, and verify S6. S6 adds a **small additive server surface** (one stdlib
`bundler.py` + two GET endpoints) plus a **new frontend screen** (`screens/export/`). The
`agencykit/` subtree, the existing `/pdf` endpoint, the mission loop, and the saved-dossier shape
are **untouched**.

---

## Build

```bash
# Frontend (React 19 + Vite) — from the studio GUI dir
cd app/studio
npm install            # if not already
npm run build          # emits app/studio/dist (served by the local server)

# Server — stdlib core; the PDF/bundle document needs the [pdf] extra
pip install -e "./agencykit[pdf]"    # WeasyPrint + Markdown (already used by /pdf today)
```

The media pack (`media.zip`) needs **no** extra — it is pure stdlib `zipfile`. The document and
full bundle need the `[pdf]` extra (same gate as the existing `/pdf`).

---

## Run

```bash
# Launch the local studio server (binds 127.0.0.1 only)
python -m agency_studio.server --path /path/to/project
# open the printed http://127.0.0.1:<port>/ and go to the Export screen (nav: "export")
```

---

## Test (fully offline — Constitution VII)

```bash
# Python server surface — bundler + handlers, export_pdf monkeypatched (no WeasyPrint/network)
pytest tests/test_bundler.py tests/test_server.py -q

# Frontend screen — Vitest + jsdom, api wrappers mocked
cd app/studio && npm run test -- src/screens/export
```

No network, no CLI engine, no Node-in-Python, no GPU. `export_pdf` is monkeypatched in the bundler
tests so WeasyPrint is not required to run the suite.

---

## Manual verification (maps to acceptance scenarios & success criteria)

Prereq: at least one **finished** deliverable, produced **with** media and one **without**.

1. **Export a document (US1-AC1, SC-001)** — open Export, pick a finished deliverable, choose "a
   polished document", download; confirm a `.pdf` opens correctly and downloaded in seconds, with a
   friendly filename (no mission id shown as identity, SC-004).
2. **Export a media pack (US1-AC1)** — for a deliverable with media, choose "a media pack";
   confirm the `.zip` contains the produced images/videos/audio and opens off the studio.
3. **Export the full bundle (US2-AC2, SC-009)** — choose "the whole thing as one bundle"; **stop
   the studio server**, then open the `.zip`: confirm it is self-contained — `deliverable.pdf`, a
   `media/` folder, and a human-readable `sources.md` — with no raw dossier JSON (Q3).
4. **No-media deliverable (US1-AC2, FR-009)** — for a media-less deliverable, confirm the media
   pack is disabled with "no media to pack" while document + full bundle still work.
5. **`[pdf]` absent (US1-AC3, SC-008, FR-012)** — in an env without the `[pdf]` extra, confirm the
   document and full bundle show "not available on this machine — how to enable it" while the media
   pack still works.
6. **Only finished exportable (US1-AC4)** — confirm a still-running/failed mission is not offered
   for export, with a plain reason.
7. **Empty state (US1-AC5, FR-014)** — with nothing produced yet, confirm the friendly empty state.
8. **Read-only (SC-003, FR-016)** — after exporting, confirm the deliverable is byte-for-byte
   intact in the S4 Library (no mutation).
9. **On-machine (SC-007, FR-008)** — with a network monitor, confirm an export triggers **no**
   outbound request.
10. **Confinement (FR-018)** — `GET /api/mission/<foreign-or-bogus-id>/bundle.zip` returns a clean
    404; no file outside the mission's own `studio_assets/missions/<id>/` tree appears in any zip.
11. **i18n + a11y (SC-004, SC-005)** — switch EN⇄FR: all Export chrome updates immediately;
    operate choose-deliverable / choose-format / download entirely by keyboard with visible focus.

---

## What changed (integration map)

| Area | Change |
|---|---|
| `agency_studio/bundler.py` | **new** — stdlib `zipfile` media-zip + bundle assembly + `sources_markdown` |
| `agency_studio/server.py` | **+2 routes / +2 handlers** — `/media.zip`, `/bundle.zip` (mirror `/pdf`); `/pdf` byte-identical |
| `app/studio/src/screens/export/` | **new** module — `Export`, `ExportPanel`, `FormatCard`, `exportModel`, `download` |
| `app/studio/src/api.ts` | **+2** — `fetchMissionMediaZip`, `fetchMissionBundle` (mirror `fetchMissionPdf`) |
| `shell/router.ts`, `Shell.tsx`, `placeholders.tsx` | `export` route `placeholder → shipped` + `taxonomyScoped true`; Outlet mount; placeholder entry removed |
| `i18n/catalog.ts` + `en.ts` + `fr.ts` | `export.*` keys (EN source of truth + FR) |
| `agencykit/` subtree | **untouched** — `exporter.export_pdf` is called, not edited |
| mission loop / store / saved dossier | **untouched** |
