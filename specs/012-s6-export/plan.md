# Implementation Plan: Export — Turn Finished Work into Shareable Bundles (Brick 7 · Screen S6)

**Branch**: `012-s6-export` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/012-s6-export/spec.md`

## Summary

S6 replaces the `#/export` coming-soon placeholder with the Export screen: the operator-facing
surface that turns a **finished deliverable** into a **shareable bundle** — a **document
(PDF)**, a **media pack (zip of the produced images/videos/audio)**, or a **full dossier
bundle** (document + media + a human-readable sources list, self-contained). It builds on
**S4 Deliverable Library** (which already exposes the single per-deliverable PDF and hands
off to S6 for richer bundles) and reuses the shell/i18n/design-system umbrella.

Per the spec Clarifications (2026-07-06): **v1 formats = all three** (document / media pack /
full dossier bundle); **bulk per-client / per-campaign export is deferred** — v1 exports one
finished deliverable at a time; and the **full dossier bundle is client-facing** — document +
media + a *human-readable* sources list, **no** raw machine-readable dossier snapshot in v1.

Unlike S4 and S5 — which were **pure frontend** layers over existing endpoints — S6 adds a
**small, additive server surface**, because only the single-deliverable **PDF** path exists
today (`GET /api/mission/{id}/pdf` → `agency_cli.exporter.export_pdf`, the `[pdf]` extra). The
**media pack** and **full dossier bundle** are assembled **server-side with Python stdlib
`zipfile`** in a new studio-core module `agency_studio/bundler.py`, exposed by two new GET
endpoints that mirror the existing PDF handler exactly:
`GET /api/mission/{id}/media.zip` and `GET /api/mission/{id}/bundle.zip`. Both **reuse the
existing scope confinement** (`_load_scoped_dossier` — a foreign/corrupt mission is a clean
404) and package only files under that mission's own `studio_assets/missions/<id>/` tree via
the existing `path_inside()` guard. The bundle's document is produced by the **existing**
`export_pdf` (so the `[pdf]` extra gates the document + full-bundle formats exactly as it
gates the PDF today — FR-012); the sources list is generated read-only from `dossier["sources"]`.

Two deliberate design choices keep the constitution intact: (1) the new packaging logic lives
in **`agency_studio/` (stdlib-only core)**, **not** in the pinned `agencykit/` subtree —
editing the vendored exporter would violate the subtree rule (Principle V) and risk merge
divergence; (2) the zip is built **server-side with stdlib `zipfile`**, **not** in the browser
with a bundled JS zip library — which would breach the zero-dependency/stdlib-core mandate and
duplicate the `path_inside`/scope guards the server already owns. Exporting is **read-only and
fully on-machine**: no dossier is mutated, no new store is added, no outbound network is
triggered (FR-008, FR-016, FR-019). The existing `/pdf` endpoint and the developer console
stay byte-identical; S6 is the plain-language, WCAG 2.1 AA operator surface over them.

## Technical Context

**Language/Version**: TypeScript ~5.7 (frontend); Python 3.11+ (server — small additive surface).

**Primary Dependencies**: React 19, Vite 6 (frontend, pre-existing); Python **stdlib only**
(`zipfile`, `io`/`tempfile`, `pathlib`) for the new bundler — **zero new runtime dependencies**.
The bundle's PDF piece reuses the **existing** optional `[pdf]` extra (WeasyPrint + Markdown)
via `agency_cli.exporter.export_pdf`; no new optional extra is introduced.

**Storage**: None added. Exports are **transient downloads** streamed to the operator's
machine; S6 persists **no** new server store and **no** export history (FR-006). Bundles read
only the **existing** saved dossier (`~/.agency/missions/<id>/`) and the **existing** on-disk
media (`<project>/studio_assets/missions/<id>/`). No new persisted field; the saved-dossier
shape is unchanged.

**Testing**: `pytest` (root `tests/`) for the new bundler + server handlers — fully offline,
`export_pdf` monkeypatched (no WeasyPrint/Node/network), zip assembly exercised over a temp
mission dir; Vitest 3 + @testing-library/react + jsdom for the Export screen, with
`fetchMissionPdf`/`fetchMissionMediaZip`/`fetchMissionBundle` mocked via the existing `api.ts`
test doubles.

**Target Platform**: Desktop browser on the operator's machine, served by the local stdlib
server at `127.0.0.1` from `app/studio/dist`; bundles streamed as file downloads.

**Project Type**: Web application feature (one inventoried screen) with a small additive
server-side packaging surface over the existing local HTTP server.

**Performance Goals**: A single-deliverable export begins downloading within a few seconds for
typical media sizes; the screen shows honest progress while a bundle is assembled and never
freezes. Zip assembly streams to a temp file rather than buffering an unbounded archive fully
in memory (mirroring the existing large-upload-to-disk pattern). The Export list (finished
deliverables, scoped by client context) resolves within one render frame at local single-user
volume (tens–low hundreds).

**Constraints**: Constitution I–XI; umbrella cross-cutting rules (EN/FR catalogs; design
system + WCAG 2.1 AA incl. keyboard-operable choose-deliverable / choose-format / download and
screen-reader labels; shared loading/empty/error/connection states; tone of voice — zero
machinery terms, never a mission id / store id / MIME type / file path as identity); additive
delivery — the existing `/pdf` endpoint and dev console byte-identical, the `agencykit/`
subtree untouched; spec clarifications (2026-07-06): **all three formats**, **bulk deferred**,
**client-facing bundle** (human-readable sources, no raw dossier snapshot). Local-first &
on-machine: export triggers **no** outbound network at all (no cloud opt-in exists for S6).
Security: new endpoints scope-confined + `path_inside()` on every packaged file + sanitized
zip entry names + no secret entry/display.

**Scale/Scope**: 1 screen; 3 export formats over a **single finished deliverable** (bulk
deferred); 1 new stdlib server module (`bundler.py`) + 2 new GET endpoints (2 route lines) +
2 new `api.ts` wrappers; a new self-contained `screens/export/` frontend module; router status
flip (`placeholder → shipped`) + placeholder-list removal + Shell `Outlet` mount; ~30–45 new
EN/FR catalog keys; ~4–5 Python test additions + ~4–5 Vitest files. Mission loop, routing,
synthesis, asset rendering, inspector veto loop, dossier persistence/shape: **untouched**.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — no reasoning path added; S6 only reads a
  finished deliverable + its on-disk media and packages them. No engine call, no API call, no
  mission-loop touch; the marginal cost of an export is zero.
- [x] **II. Engine neutrality**: PASS — Export never names or assumes an engine; packaging is
  engine-agnostic and reads only already-produced artifacts. The Engine contract and
  production-engine guard are untouched.
- [x] **III. No invented information**: PASS — S6 packages exactly what was produced (read-only,
  no re-render, no rewrite); it fabricates nothing and neither performs nor weakens mission-time
  verification. The bundle's sources list is copied verbatim from the dossier's own cited
  sources; the inspector veto loop is untouched.
- [x] **IV. Local-first & offline-by-default**: PASS — every bundle is assembled from local
  artifacts and streamed to the machine; export triggers **no** outbound network of its own
  (FR-008). Unlike S5, there is no cloud opt-in path at all. Non-Mac not regressed (stdlib
  `zipfile`, no platform-specific code).
- [x] **V. Subprocess boundaries**: PASS — no `openmontage/` import; the new packaging logic
  lives in `agency_studio/bundler.py` (studio core), **not** in the pinned `agencykit/` subtree
  (which stays untouched — its `exporter.export_pdf` is only *called*, not edited). Vendored
  subtrees unchanged.
- [x] **VI. Security**: PASS — the two new endpoints reuse `_load_scoped_dossier` (foreign /
  corrupt mission → clean 404, same confinement as `/pdf` and GET-by-id); every packaged media
  file is resolved through the existing `path_inside(assets_root, …)` guard so a bundle can
  never include a file outside its own mission tree (FR-018); zip entry names are sanitized
  (relative, no `..`, no absolute paths); bind `127.0.0.1` / no CORS `*` / https-only-outbound
  (n/a — no outbound) preserved; no secret accepted, persisted, displayed, or packaged.
- [x] **VII. Offline tests**: PASS — the bundler is tested with stdlib `zipfile` over a temp
  mission dir and a monkeypatched `export_pdf` (no WeasyPrint, no network, no Node, no GPU);
  server-handler tests cover scope confinement, Content-Disposition, empty-media 404, and the
  `[pdf]`-absent → 501 path; the Export screen is covered by Vitest with mocked api wrappers.
- [x] **VIII. End-user simplicity**: PASS — S6 *is* the "hand it to my client" promise: plain
  language ("a polished document", "a media pack", "the whole thing as one bundle"), never a
  mission id / MIME / path as identity (FR-013, SC-004), keyboard-operable, friendly capability-
  absent ("not available — how to enable") and empty states, honest progress, never a dead end.
- [x] **IX. License**: PASS — new code uses only the Python stdlib (`zipfile`, `io`,
  `tempfile`, `pathlib`); no new third-party component, nothing to add to `docs/LICENSES.md`.
  The `[pdf]` extra (WeasyPrint/Markdown) is pre-existing and already recorded.
- [x] **X. Additive over invasive**: PASS — a placeholder route becomes a shipped screen (the
  umbrella's designed lifecycle); the two new GET endpoints are purely additive (existing routes,
  including `/pdf`, byte-identical); the new `bundler.py` is a new file; no mission loop / store /
  saved-dossier / veto-loop change; the `agencykit/` exporter is called, not modified. Behavior
  is byte-identical with the screen unused.
- [x] **XI. English everywhere**: PASS — code/docs/commits in English; operator-facing strings
  live only in the EN/FR end-user catalogs (explicitly permitted).

**Post-Phase-1 re-check (2026-07-06)**: design artifacts (research, data-model, contracts,
quickstart) confirm the server surface is exactly two additive, scope-confined,
`path_inside`-guarded GET endpoints backed by a stdlib-only `bundler.py`; the `agencykit/`
subtree and the existing `/pdf` endpoint are untouched; no mission-loop / store / dossier-shape
change; the frontend is a self-contained `screens/export/` module plus the declared integration
edits; all outbound-network and secret invariants hold. All gates hold as marked.

## Project Structure

### Documentation (this feature)

```text
specs/012-s6-export/
├── spec.md              # Feature spec (clarified 2026-07-06)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── bundle-endpoints.md    # GET /api/mission/{id}/media.zip + /bundle.zip: request/response, status codes, scope + path_inside + [pdf]-gating, zip layout, sources.md format
│   └── export-model.md        # Finished-deliverable → available-formats model (which formats a deliverable offers), catalog-key contract, download/filename convention
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
agency_studio/
├── bundler.py            # NEW (stdlib zipfile): build_media_zip(mission_id, assets_root) and
│                         #   build_bundle(mission_id, assets_root) → temp zip path; sources_markdown(dossier);
│                         #   packages only files under studio_assets/missions/<id>/ (path_inside), sanitized
│                         #   arcnames; calls exporter.export_pdf for the bundle's document (raises ImportError
│                         #   when [pdf] absent → handler maps to 501); pure/read-only, never mutates a dossier
└── server.py             # EDITED (additive): _route_get gains two lines dispatching
                          #   /api/mission/{id}/media.zip → _handle_mission_media_zip and
                          #   /api/mission/{id}/bundle.zip → _handle_mission_bundle; both mirror
                          #   _handle_mission_pdf (scope via _load_scoped_dossier, stream via _send_bytes with
                          #   Content-Disposition, 501 for absent [pdf] on the bundle, 404 for no media/deliverable)

app/studio/src/
├── screens/
│   └── export/
│       ├── Export.tsx               # Screen: lists finished deliverables (reuses S4's finished-mission listing),
│       │                            #   scoped by active client context; empty (first-run) + empty-for-context +
│       │                            #   connection-lost states; a11y/keyboard operable
│       ├── ExportPanel.tsx          # Per-deliverable: format chooser (document / media pack / full bundle) with
│       │                            #   plain-language contents description; produce + download; progress; per-format
│       │                            #   availability (no-media → media pack disabled; [pdf] absent → capability-absent)
│       ├── FormatCard.tsx           # One export format: plain-language name + contents + availability/CTA
│       ├── exportModel.ts           # Pure model: (dossier/MissionSummary) → available formats + contents description;
│       │                            #   hasMedia (from dossier.assets) gates the media-pack format; friendly filename
│       └── download.ts              # Blob → browser download helper (Content-Disposition-aware filename), shared by
│                                    #   all three formats; catchable-error handling (501/404/500) mirroring fetchMissionPdf
├── screens/
│   └── placeholders.tsx            # `export` entry removed (settings remains)
├── shell/
│   ├── router.ts                   # `export` route: status "placeholder" → "shipped", taxonomyScoped false → true
│   └── Shell.tsx                   # Outlet: mount <Export /> for route id "export"
├── i18n/
│   ├── catalog.ts                  # + export.* typed keys (formats, contents descriptions, produce/download,
│   │                               #   progress, capability-absent, no-media, empty/context/connection states)
│   ├── en.ts                       # + EN strings (fallback source of truth)
│   └── fr.ts                       # + FR strings
└── api.ts                          # + fetchMissionMediaZip(id) and fetchMissionBundle(id) (Blob, catchable errors),
                                    #   mirroring the existing fetchMissionPdf; fetchMissionPdf reused as-is

Co-located tests (existing convention):
├── screens/export/exportModel.test.ts   # Available-formats derivation, hasMedia gating (assets present/absent),
│                                         #   contents description, friendly filename, single-deliverable scope
├── screens/export/Export.test.tsx        # Load + list finished deliverables, empty (first-run) & empty-for-context,
│                                         #   connection-lost, a11y/keyboard; only finished deliverables offered
├── screens/export/ExportPanel.test.tsx   # Choose each format, produce + download, progress; media-pack disabled when
│                                         #   no media; [pdf]-absent → capability-absent state; render/packaging failure → plain retry
└── screens/export/download.test.ts       # Blob → download filename from Content-Disposition; 501/404/500 surfaced as catchable errors

tests/                                     # Python suite (server surface — additive)
├── test_bundler.py                        # NEW: build_media_zip over a temp mission media dir (correct entries, sanitized
│                                          #   arcnames, path_inside confinement, empty-media → signalled); build_bundle
│                                          #   (document via monkeypatched export_pdf + media + sources.md); sources_markdown
│                                          #   from dossier["sources"]; [pdf] absent → ImportError; read-only (no dossier mutation)
└── test_server.py                         # EXTENDED: /media.zip + /bundle.zip route dispatch, scope confinement (foreign/
                                           #   corrupt mission → 404), Content-Disposition + application/zip, no-media → 404,
                                           #   [pdf] absent on bundle → 501; existing /pdf tests stay green (byte-identical)
```

**Structure Decision**: one new self-contained frontend module `screens/export/` inside the
existing app, consuming the umbrella's shell/i18n/design-system layers, the shell's
`useClientContext()` selector, and S4's finished-deliverable listing; plus one new **stdlib-only**
server module `agency_studio/bundler.py` and **two additive GET endpoints** in `server.py` that
mirror the existing `_handle_mission_pdf` (scope confinement, `path_inside`, `_send_bytes`
streaming, 501-on-absent-extra). The `agencykit/` subtree is **not** edited — its
`exporter.export_pdf` is called for the bundle's document. The existing `/pdf` endpoint, the
mission loop, the store, the saved-dossier shape, and the developer console are left
byte-identical. Bulk per-client/campaign export is deferred (spec Clarifications); v1 exports one
finished deliverable at a time.

## Complexity Tracking

> No constitution violations — table intentionally empty. The new server surface is purely
> additive (two scope-confined, `path_inside`-guarded, stdlib-`zipfile` GET endpoints mirroring
> the existing PDF handler); the vendored `agencykit/` exporter is called, not modified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
