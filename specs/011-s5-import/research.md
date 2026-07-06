# Phase 0 Research — S5 Import

All decisions below are grounded in direct inspection of the existing studio code, the
spec Clarifications (2026-07-06), and the Constitution (v1.0.0). No open
`NEEDS CLARIFICATION` remains.

## R1 — Reuse the existing ingestion endpoints; add zero server code

- **Decision**: Bring-in reuses the existing `POST /api/docs` (documents) and `POST /api/visual` (images); listing reuses `GET /api/docs` + `GET /api/visual`; removal reuses `DELETE /api/docs/{id}` + `DELETE /api/visual/{id}`. Client wrappers already exist in `api.ts` (`ingestDoc`, `listDocs`, `deleteDoc`, `uploadVisual`, `listVisual`, `deleteVisual`). **No server file is modified.**
- **Rationale**: `agency_studio/server.py` already implements the full lifecycle with the hard parts done: bodies are streamed to a bounded temp file (`_stream_body_to_file`, caps `_MAX_DOC_BYTES` / `_MAX_IMAGE_BYTES`), filenames sanitized (`_safe_upload_filename` — basename-only, NUL/control-stripped, length-bounded), a clean **501** when the optional extra (`[studio]` / `[visual]`) is absent, **400** for empty/unreadable input, **500** never a socket drop, and **201** with a stable-id meta on success. This is exactly the FR-002/FR-003/FR-004/FR-011/FR-018 surface. Adding server code would duplicate a hardened path and violate Principle X (additive).
- **Alternatives considered**: (a) a new `/api/import` endpoint that unifies kinds — rejected: pure duplication, new attack surface, no capability gained. (b) a per-client server-side store — rejected: invasive, and the spec resolved client scope to organizational metadata (R4).

## R2 — v1 kinds = documents + images; video/audio deferred

- **Decision**: v1 supports two kinds — **document** (routed to `/api/docs`; markitdown converts text/PDF/office/etc.) and **image** (routed to `/api/visual`). Video and audio are **not** offered; the screen states the limitation plainly (FR-012).
- **Rationale**: The studio has a local ingestion path *only* for documents and images that yields **stored, mission-consumable** material (retrieved via the mission `knowledge`/`visual` opt-ins). `/api/stt` exists but returns a **transient** transcript to the caller (live-session use) — it is not wired as importable material — so audio has no import path today; video has none at all. Accepting them would either silently store unusable files or require a new ingestion/analysis capability (out of an additive presentation-layer cycle). Confirmed in spec Clarifications (2026-07-06).
- **Alternatives considered**: (a) accept video/audio as inert stored attachments — rejected: introduces a brand-new stored-attachment concept the studio lacks, and gives the operator material nothing can use. (b) build deep AV ingestion — rejected: a large new capability, its own future cycle.

## R3 — Kind routing & client-side validation, server as authority

- **Decision**: The `BringInPanel` classifies each chosen file by kind from a small allow-list (document extensions vs image extensions), routes to `ingestDoc` or `uploadVisual`, and shows progress. Unsupported kinds are rejected **client-side** with a plain reason naming what *is* supported (FR-003/FR-012). For accepted kinds, the **server remains the authority**: a `400` (empty/unreadable/no caption) or `501` (extra absent) is surfaced as a plain-language reason / capability-absent state; a `201` is an accept.
- **Rationale**: Client-side kind filtering gives instant, friendly feedback and avoids a pointless upload; but only the server can truly validate convertibility/size, and it already returns precise codes. Mapping `501 → "not available here + how to enable"` (FR-011) and `400 → "couldn't read this file"` (FR-003) reuses the studio's established 501/400 contract (same pattern the models/docs surfaces already use).
- **Alternatives considered**: MIME-sniffing in the browser — rejected: unreliable and would surface MIME strings; extension + server-authority is simpler and honest.

## R4 — Client association = frontend-owned localStorage map (organizational metadata)

- **Decision**: An imported item's client/project/campaign association is stored in a **frontend-owned `localStorage` map** (`associationStore.ts`): `itemId → {client, project?, campaign?}`. It defaults to the shell's active client context at bring-in time (FR-006) and is re-associable/removable. It is **organizational metadata only** — it does **not** filter which material a mission retrieves (the RAG stores stay shared; per-client isolation is deferred — spec Clarifications).
- **Rationale**: The existing `DocMeta`/`VisualMeta` carry a stable `id` but no client field, and the RAG stores are global. Persisting association client-side mirrors the umbrella's existing pattern (the shell already persists client-context and User Preferences in `localStorage`), keeps S5 a pure presentation layer (Principle X), and adds no server store or mission-loop change. For a local single-user agency this is sufficient and robust; a server-side association field can be introduced later without redesign if multi-machine sync is ever needed.
- **Alternatives considered**: (a) a new server-side association field on the ingestion records — rejected: server change, invasive, unnecessary for a single local user. (b) encoding client in the filename — rejected: leaks into the RAG title and surfaces machinery.

## R5 — Whole-set brief attachment via the existing knowledge/visual opt-ins

- **Decision**: "Direct a brief to use my imported material" (FR-007) is realized by setting the mission's **existing** `knowledge` (and `visual`, when images are imported) opt-ins at launch. Implemented as a default-off `useImportedMaterial` flag on the brief draft (`briefDraft.ts`) that `composeMission.ts` maps to `opts.knowledge` / `opts.visual`; `Review.tsx` shows a plain-language "this production will use your imported material" summary, visible only when imported material exists. **No per-item selection**, no mission-bridge change (spec Clarifications — whole-set).
- **Rationale**: `runMission` already accepts `knowledge`/`visual` booleans and the mission draws on the global docs/visual RAG store when they are on — this is the sanctioned, byte-identical-when-off consumption path (Principle X). Whole-set attachment is forced into consistency with R4 (shared, non-isolated stores): per-item filtering would need the very context-scoping mechanism deferred for clients. This keeps the mission loop and veto path untouched (Principle III/X).
- **Alternatives considered**: (a) per-item brief attachment — rejected: requires filtering mission retrieval by selected ids (mission-bridge change), contradicts the deferred per-client isolation. (b) auto-enabling knowledge whenever any material exists — rejected: removes operator intent; an explicit default-off affordance is clearer and safer.

## R6 — Dedup, orphan cleanup, and the merged model

- **Decision**: `importModel.ts` is a pure function merging `DocMeta[]` + `VisualMeta[]` into one kind-tagged list, grouped by the association map (client → project → campaign + unassigned), scoped by the active client context. De-dup is by store `id` (docs and images share the same id space semantics but never collide across stores; kind disambiguates). When an association-map entry points at an `id` no longer present in either store (item removed), `associationStore` prunes it (orphan cleanup) so no ghost shelves appear.
- **Rationale**: A pure fold keeps grouping/scoping testable offline (Principle VII) and fast (< one frame, R-perf). Orphan cleanup keeps the local map honest without a server round-trip. Load-all client-side matches the modest local volume (mirrors S4's decision).
- **Alternatives considered**: server-side pagination — rejected: unnecessary at v1 scale, and the list endpoints return the full set cheaply.

## R7 — Integration edits kept minimal and additive

- **Decision**: Outside the new `screens/import/` module, the edits are: `router.ts` (`import`: `placeholder → shipped`, `taxonomyScoped false → true` so the shell client-context selector shows for association), `Shell.tsx` (mount `<Import/>` for `import`), `placeholders.tsx` (remove the `import` entry), the i18n catalogs (`import.*` keys), and the three S2 brief files for the default-off affordance (R5).
- **Rationale**: This mirrors S4's proven integration shape (router flip + Shell mount + placeholder removal + i18n), plus the one new dimension S5 owns — the brief affordance. Every edit is additive and byte-identical when the new surface is unused (Principle X). Flipping `taxonomyScoped` to true is required because association defaults to the active client context (FR-006).
- **Alternatives considered**: leaving `import` non-taxonomy-scoped and adding an in-screen client picker — rejected: duplicates the shell selector, contradicts the umbrella "single client context from the shell" assumption.

## Cross-cutting confirmations

- **Local-first (Principle IV)**: default document ingestion converts/embeds on-machine; default image captioning is local; the only off-machine path is the pre-existing `?cloud=1` image-captioning, kept per-item opt-in and OFF by default (FR-010). No mission-time network is added.
- **Security (Principle VI)**: server byte-identical; all uploads keep the existing `_safe_upload_filename` + streamed size caps; the association map stores only ids ↔ taxonomy labels (no secret, no path shown as identity); no secret entry/display anywhere (FR-018).
- **Offline tests (Principle VII)**: every new unit is exercised with mocked `api.ts` wrappers and mocked `localStorage`; no network/CLI/live server; root `pytest` untouched.
