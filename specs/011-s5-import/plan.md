# Implementation Plan: Import — The Front Door for the Operator's Own Material (Brick 7 · Screen S5)

**Branch**: `011-s5-import` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-s5-import/spec.md`

## Summary

S5 replaces the `#/import` coming-soon placeholder with the Import screen: the
operator-facing front door through which a non-technical user brings **their own existing
material** (documents — incl. text/PDF briefs — and images) into the studio so a production
can build on it as **input/context**. It is a **pure presentation + orchestration layer**
over infrastructure that already exists — it reuses the existing local ingestion endpoints
(`ingestDoc`/`listDocs`/`deleteDoc` over `POST/GET/DELETE /api/docs`, and
`uploadVisual`/`listVisual`/`deleteVisual` over `POST/GET/DELETE /api/visual` in `api.ts`),
the shell's client-context selector (`useClientContext()`), and the mission's existing
`knowledge`/`visual` opt-ins (already accepted by `runMission`) — and adds an **import
model** that merges the two ingestion stores into one plain-language "imported material"
list, grouped by a lightweight client association, plus the everyday actions (bring-in with
validation & feedback · organize/re-associate · remove).

Per the spec Clarifications (2026-07-06): **v1 kinds = documents + images** (video/audio
deep-import deferred — no local path exists); **client association is organizational
metadata** persisted client-side (it does not isolate mission context); **brief attachment
is whole-set** (directing a brief to use imported material enables the existing
`knowledge`/`visual` opt-ins so the mission draws on the imported material — no per-item
curation, no mission-bridge change); and imported source material is **removable** via the
existing delete endpoints (never touching any produced deliverable).

Technically: a new self-contained `screens/import/` module in the React 19 + Vite app
(`app/studio/`), new `import.*` EN/FR catalog keys, a frontend-owned client-association map
(localStorage, mirroring the shell's existing preference persistence), and a small set of
declared integration edits (router status flip `placeholder → shipped` + `taxonomyScoped
true`, Shell `Outlet` mount, placeholder-list removal, i18n catalog additions, and the S2
brief "use my imported material" affordance that sets the `knowledge`/`visual` opt-ins —
FR-007). **Zero server changes, zero new runtime dependencies**: the import model
(merge/group/validate-result) is a pure function over the existing `DocMeta[]` + `VisualMeta[]`;
bring-in reuses `ingestDoc`/`uploadVisual`; remove reuses `deleteDoc`/`deleteVisual`;
association is local, ephemeral-to-the-machine metadata. The developer console's existing
docs/visual management stays byte-identical; S5 is the plain-language, WCAG 2.1 AA operator
sibling built from the same endpoints.

## Technical Context

**Language/Version**: TypeScript ~5.7 (frontend only); Python 3.11+ server **unchanged**.

**Primary Dependencies**: React 19, Vite 6 (all pre-existing). **Zero new runtime or dev dependencies** — the import model (merge two stores → grouped/validated list) is a pure function over the existing `DocMeta[]` / `VisualMeta[]`; ingestion, listing, and deletion reuse the existing `api.ts` wrappers.

**Storage**: None added server-side. Imported material lives in the **existing** local document- and image-RAG stores (via the unchanged `/api/docs` and `/api/visual` endpoints). The only new persistence is a frontend-owned **client-association map** (imported-item id → client/project/campaign) in `localStorage`, mirroring the shell's existing `localStorage`-backed client-context and preferences. No new server store, no new persisted mission field, no change to the saved-dossier shape.

**Testing**: Vitest 3 + @testing-library/react + jsdom (existing setup); `ingestDoc`/`listDocs`/`deleteDoc`/`uploadVisual`/`listVisual`/`deleteVisual` mocked via the existing `api.ts` test doubles; the client-association map tested against a mocked `localStorage`; root `pytest` suite untouched and stays green (server not modified).

**Target Platform**: Desktop browser on the operator's machine, served by the local stdlib server at `127.0.0.1` from `app/studio/dist` (existing static route).

**Project Type**: Web application frontend feature (one inventoried screen) over the existing local HTTP server.

**Performance Goals**: Merge/group/validate over the full imported set resolves within one render frame (< ~100 ms; pure local fold, no per-keystroke network) at the expected local single-user volume (tens–low hundreds of items); a bring-in reflects its accepted/rejected result within one frame of the ingest call returning; a remove reflects the item's disappearance within one frame of the delete call returning.

**Constraints**: Constitution I–XI; umbrella cross-cutting rules (i18n catalogs; design system + WCAG 2.1 AA incl. keyboard-operable bring-in/associate/attach/organize/remove and screen-reader labels; shared loading/empty/error/connection states; tone of voice — zero machinery terms, no store IDs / MIME types / file paths as identity); additive delivery — server and the dev console's docs/visual surfaces byte-identical; spec clarifications (2026-07-06): **documents + images only** (video/audio deferred), **client association = organizational metadata (client-side)**, **whole-set brief attachment** (no mission-bridge change), **removable source material** (never touches deliverables). Local-first: default bring-in stays on-machine; the existing optional cloud image-captioning stays per-item opt-in and OFF by default.

**Scale/Scope**: 1 screen; a merge/group/validate model over `DocMeta` + `VisualMeta`; client-context-scoped grouping (client → project → campaign + unassigned); 2 v1 kinds (document / image); 3 action families (bring-in with validation · organize/re-associate · remove); a whole-set brief-attachment affordance (sets `knowledge`/`visual`); 2 locales (~35–50 new catalog keys); ~5–6 test files. No backend files touched.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — no reasoning path added; S5 only lists, groups, and ingests the operator's files through the existing endpoints; a production that later consumes them runs on the unchanged mission loop via its existing `knowledge`/`visual` opt-ins.
- [x] **II. Engine neutrality**: PASS — Import never names or assumes an engine; ingestion/retrieval are engine-agnostic; the Engine contract and production-engine guard are untouched.
- [x] **III. No invented information**: PASS — S5 brings in only real files the operator chose and shows only their real ingestion result; it fabricates no content, and neither performs nor weakens mission-time verification; the veto loop is untouched. Imported material is retrieved into a mission through the same cited-RAG path that already exists.
- [x] **IV. Local-first & offline-by-default**: PASS — default bring-in is entirely local (docs are converted/embedded on-machine; images are captioned locally by default). The only off-machine path — the pre-existing optional cloud image-captioning (`?cloud=1`) — stays explicit, per-item opt-in, and OFF by default (FR-010). No new outbound network, no mission-time network, non-Mac not regressed.
- [x] **V. Subprocess boundaries**: PASS — frontend-only; no `openmontage/` import, no subtree edits; ingestion is driven by the unchanged server across its existing HTTP boundary.
- [x] **VI. Security**: PASS — server byte-identical (bind `127.0.0.1`/no CORS `*`/`path_inside()`/https-only/`_safe_upload_filename`/streamed size caps all unchanged); no secret entry or display (FR-018); ingest/list/delete go through the existing validated endpoints; the client-association map holds only ids ↔ taxonomy labels (never secrets, never paths surfaced as identity). No new persisted server data.
- [x] **VII. Offline tests**: PASS — all new behavior covered by Vitest with mocked `ingestDoc`/`listDocs`/`deleteDoc`/`uploadVisual`/`listVisual`/`deleteVisual` and mocked `localStorage` (merge/group model, kind validation, accept/reject feedback, 501-capability-absent state, client association + re-associate, unassigned shelf, remove, empty & connection-lost states, whole-set brief-attachment opt-in wiring, a11y/keyboard); no network/CLI/live server. Root pytest suite unaffected.
- [x] **VIII. End-user simplicity**: PASS — S5 *is* the "bring my own material in" promise: plain-language ("bring in a document / an image"), never MIME/paths/store IDs (FR-013, wording audit SC-004), keyboard-operable, forgiving validation with plain reasons, friendly empty and capability-absent states, never a dead end.
- [x] **IX. License**: PASS — zero new components; nothing to add to `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — a placeholder route becomes a shipped screen (the umbrella's designed lifecycle); server, mission loop, store, veto loop, and the dev console's docs/visual surfaces are untouched; bring-in/remove reuse the pre-existing ingest/delete endpoints; the brief affordance only flips the already-existing `knowledge`/`visual` opt-ins (byte-identical with the affordance unused); the client-association map is a purely additive local layer.
- [x] **XI. English everywhere**: PASS — code/docs/commits in English; operator-facing strings live only in the EN/FR end-user catalogs (explicitly permitted).

**Post-Phase-1 re-check (2026-07-06)**: design artifacts (research, data-model, contracts,
quickstart) confirm zero server changes, zero new dependencies, no engine/mission-loop/store
surface, a presentation+orchestration layer over the existing ingest/list/delete endpoints,
a frontend-only local association map, and a whole-set brief affordance that only toggles
pre-existing opt-ins — all gates hold as marked.

## Project Structure

### Documentation (this feature)

```text
specs/011-s5-import/
├── spec.md              # Feature spec (clarified 2026-07-06)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── import-model.md          # DocMeta[]+VisualMeta[] → merged/grouped/validated ImportModel; kind validation; client-association map; catalog-key contract
│   └── brief-attachment.md      # Whole-set brief attachment: how "use my imported material" sets knowledge/visual opt-ins over the existing runMission path
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
app/studio/src/
├── screens/
│   ├── brief/
│   │   ├── composeMission.ts        # S2 (edited): MissionDraft.opts gains knowledge/visual; set when the brief is directed to use imported material (FR-007) — rest byte-identical
│   │   ├── briefDraft.ts            # S2 (edited): Brief gains an optional `useImportedMaterial` flag (default off) persisted with the draft
│   │   └── Review.tsx               # S2 (edited): a plain-language "this production will use your imported material" affordance/summary; visible only when imported material exists
│   ├── import/
│   │   ├── Import.tsx               # Screen: loads listDocs + listVisual, renders grouped shelves / bring-in / capability-absent / empty / connection states; reads active client context
│   │   ├── BringInPanel.tsx         # File picker + drag-drop; per-item validation (kind/size) → ingestDoc/uploadVisual; progress + accept/reject feedback; cloud-captioning opt-in (default off)
│   │   ├── MaterialShelf.tsx        # Grouped client → project → campaign shelves + unassigned shelf; renders MaterialCard list
│   │   ├── MaterialCard.tsx         # One imported item: plain-language name, kind badge, when imported; triggers re-associate + remove
│   │   ├── AssociateControl.tsx     # Plain-language attach/move client association / return-to-unassigned; reuses taxonomy from useClientContext; writes the local association map
│   │   ├── importModel.ts           # Pure model: (DocMeta[], VisualMeta[], associationMap, scope) → ImportModel (kind-tagged, grouped, deduped); kind validation; accept/reject classifier
│   │   └── associationStore.ts      # localStorage-backed client-association map (itemId → {client,project,campaign}); read/write/remove; mirrors the shell preference-persistence pattern
│   └── placeholders.tsx            # `import` entry removed (export, settings remain)
├── shell/
│   └── router.ts                   # `import` route: status "placeholder" → "shipped", taxonomyScoped false → true
│   └── Shell.tsx                   # Outlet: mount <Import /> for route id "import"
├── i18n/
│   ├── catalog.ts                  # + import.* typed keys (bring-in, kinds, validation, shelves, unassigned, associate, remove, capability-absent, empty, states, brief affordance)
│   ├── en.ts                       # + EN strings (fallback source of truth)
│   └── fr.ts                       # + FR strings
└── api.ts                          # REUSED as-is: ingestDoc, listDocs, deleteDoc, uploadVisual, listVisual, deleteVisual (+ runMission knowledge/visual opts)

Co-located tests (existing convention):
├── screens/import/importModel.test.ts        # Merge docs+visual, kind tagging, grouping (client→project→campaign + unassigned) via association map, client-context scoping, accept/reject classification, dedup
├── screens/import/associationStore.test.ts   # localStorage read/write/remove of the association map; orphaned id (deleted item) cleanup; unassigned default
├── screens/import/Import.test.tsx             # Load + render shelves, empty (first-run) & empty-for-context states, connection-lost, capability-absent (501) state, a11y/keyboard
├── screens/import/BringInPanel.test.tsx       # Accept a supported doc/image, reject unsupported kind / oversized / unreadable with plain reason, progress, cloud opt-in default off, 501 → capability-absent
├── screens/import/AssociateControl.test.tsx   # Associate unassigned, move mis-filed, return to unassigned; immediate reflect; reversible; plain feedback
├── screens/brief/composeMission.test.ts       # UPDATED: knowledge/visual opts set when useImportedMaterial is on; unchanged (byte-identical opts) when off
└── (existing brief tests stay green — affordance is additive and default-off)

tests/                                          # Python suite — no changes (server untouched)
```

**Structure Decision**: one new self-contained module `screens/import/` inside the existing
frontend project, consuming the umbrella's shell/i18n/design-system layers, the shell's
`useClientContext()` selector, and the existing `api.ts` ingest/list/delete wrappers. The
only edits outside the new module are the declared integration points: the router status +
taxonomyScoped flip, the Shell `Outlet` mount, the placeholder-list removal, the i18n
catalog additions, and the S2 brief "use my imported material" affordance (a default-off
flag on the brief draft that flips the pre-existing `knowledge`/`visual` opt-ins at compose
time — FR-007). The developer console's docs/visual management surfaces are left
byte-identical; S5 is the operator-facing sibling. No backend directories are touched.

## Complexity Tracking

> No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
