# Phase 1 Data Model: S6 Export

**Feature**: Export — Turn Finished Work into Shareable Bundles (Brick 7 · Screen S6)
**Date**: 2026-07-06

S6 introduces **no new persisted entity**. Every entity below is either (a) a **read-only view**
over the existing saved dossier and on-disk media, or (b) an **ephemeral, in-memory** UI/packaging
construct that exists only for the duration of one export. No new server store, no new persisted
mission field, no change to the saved-dossier shape (FR-006, FR-016, FR-019).

---

## Exportable deliverable (read-only view)

The operator-facing representation of one **finished** production available to export.

| Attribute | Source (existing) | Notes |
|---|---|---|
| plain-language name / what-it-is | mission summary / dossier goal | never the mission id as identity (FR-013) |
| client / project / campaign placement | S4 taxonomy resolution (`taxonomy.resolve`) | scopes which deliverables the screen lists |
| finished? | mission summary status | **only finished** deliverables are offered (FR-004) |
| hasMedia | `dossier["assets"]` non-empty (`server.py:1630`) | gates the media-pack format (FR-009) |
| availableFormats | derived (see below) | which of the 3 formats this deliverable can produce |

**Validation / rules**:
- A deliverable is exportable **iff** it is finished. Running/failed → not listed, plain reason (FR-004).
- `hasMedia == false` → the media-pack format is unavailable ("no media to pack"); document + full
  bundle remain offered (FR-009).
- Backed entirely by the existing saved dossier + mission listing; S6 defines no new stored entity.

---

## Export format (enumeration + availability)

The shareable form the operator chooses.

| Format | Contents (plain language) | Server route | Capability gate |
|---|---|---|---|
| `document` | the written deliverable, laid out for reading/printing | `GET /api/mission/{id}/pdf` (existing) | `[pdf]` extra |
| `mediaPack` | the produced images / videos / audio | `GET /api/mission/{id}/media.zip` (new) | none (stdlib) — needs `hasMedia` |
| `fullBundle` | document + media + a human-readable sources list, self-contained | `GET /api/mission/{id}/bundle.zip` (new) | `[pdf]` extra |

**Availability state per format**: `available` · `unavailable-here` (capability absent → the
localized "not available — how to enable" state, FR-012) · `no-media-to-pack` (media pack only,
when `hasMedia == false`, FR-009).

**Rules**:
- `document` and `fullBundle` require the `[pdf]` extra; absent → `unavailable-here` (501 from the
  endpoint) while `mediaPack` still works (FR-012).
- `mediaPack` requires `hasMedia`; absent → `no-media-to-pack`.

---

## Export bundle (transient artifact)

The produced downloadable file — a document (`.pdf`), a media archive (`.zip`), or a
self-contained dossier package (`.zip`). Assembled **on demand** by read-only packaging and
streamed to the machine; **not persisted** by S6 (FR-006). Re-exporting produces a fresh file.

| Attribute | Value |
|---|---|
| content type | `application/pdf` (document) / `application/zip` (media pack, full bundle) |
| filename | friendly, human-meaningful (via `Content-Disposition`), never the raw mission id as identity (FR-013) |
| lifetime | transient — built in a temp file, streamed, then discarded; no export store/history |

### Full-bundle internal layout (`bundle.zip`)

```text
<friendly-name>/               # (arcname prefix; client-facing)
├── deliverable.pdf            # the document, via exporter.export_pdf ([pdf] extra)
├── media/                     # produced images/videos/audio (present only if hasMedia)
│   └── …                      # each file resolved through path_inside; sanitized relative arcname
└── sources.md                 # human-readable sources list from dossier["sources"] (D5) — NO raw dossier.json (Q3)
```

`media.zip` contains just the `media/…` files (no PDF, no sources).

---

## Bundle composition (plain-language pre-flight)

The statement of what a chosen format will contain, shown **before** the bundle is produced (FR-005),
so the operator knows what they are about to hand over. Ephemeral UI text derived from the format +
`hasMedia`; carries no internal machinery terms.

---

## Export result (per-request outcome)

The outcome of one export request.

| State | Trigger | Operator-facing |
|---|---|---|
| `ready` | 200 + blob | download begins with a friendly filename; plain "ready" confirmation (FR-011) |
| `capability-absent` | 501 (no `[pdf]`) | "not available on this machine — how to enable it" for that format (FR-012) |
| `no-media` | 404 (media pack, empty media) | media pack disabled with "no media to pack" (FR-009) — surfaced pre-flight from `hasMedia` |
| `failed` | 500 (render/packaging failure) | plain "couldn't build — retry or choose another format" (FR-011) |
| `not-found` | 404 (missing/foreign/corrupt mission) | same confinement as viewing the deliverable (FR-018) |

---

## Export scope (v1: single deliverable)

What the operator is exporting. **v1 = a single finished deliverable** (bulk deferred — spec
Clarifications). Resolved from S4's finished-deliverable listing + the Brick 6 taxonomy, scoped by
the shell client-context (which finished deliverables are listed). Per-client / per-campaign bulk
scope is a post-v1 refinement.

---

## Entity relationships

```text
Exportable deliverable (read-only view over saved dossier + mission listing)
   │  offers
   ▼
Export format {document | mediaPack | fullBundle}  ──(availability)── [pdf] extra / hasMedia
   │  produce (on demand, read-only)
   ▼
Export bundle (transient download)  ──(layout)──►  deliverable.pdf + media/ + sources.md
   │  yields
   ▼
Export result {ready | capability-absent | no-media | failed | not-found}
```

No node in this graph is persisted by S6. The saved dossier, its media, and its taxonomy placement
are all **read-only inputs**; the deliverable is byte-for-byte unchanged after any export (SC-003,
FR-016).
