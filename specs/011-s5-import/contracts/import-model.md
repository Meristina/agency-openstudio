# Contract — Import Model, Bring-In & Association

Frontend contracts for S5. No server contract is added — S5 consumes the **existing**
`/api/docs` and `/api/visual` endpoints exactly as they are today.

## 1. Reused server endpoints (unchanged — for reference only)

| Method | Path | Used by | Success | Failure the UI maps |
|--------|------|---------|---------|---------------------|
| POST | `/api/docs?filename=<name>` (raw bytes body) | `ingestDoc(file)` | `201 {id,filename,title,n_chunks,created}` | `501` extra absent · `400` empty/unreadable · `500` |
| GET | `/api/docs` | `listDocs()` | `200 {docs: DocMeta[]}` | connection error |
| DELETE | `/api/docs/{id}` | `deleteDoc(id)` | `200 {deleted}` | `404` unknown (idempotent) |
| POST | `/api/visual?filename=<name>[&cloud=1]` (raw bytes body) | `uploadVisual(file,{cloud})` | `201 VisualMeta` | `501` extra absent · `400` empty/no-caption · `500` |
| GET | `/api/visual` | `listVisual()` | `200 {docs: VisualMeta[]}` | connection error |
| DELETE | `/api/visual/{id}` | `deleteVisual(id)` | `200 {deleted}` | `404` unknown (idempotent) |

**Contract guarantee**: S5 sends nothing these endpoints don't already accept and adds no
new query param, header, or body shape. `cloud` defaults to `0` (local captioning) and is
set to `1` **only** on explicit per-item operator opt-in (FR-010).

## 2. `importModel.ts` — pure projection

```
buildImportModel(
  docs: DocMeta[],
  visuals: VisualMeta[],
  assoc: AssociationMap,
  scope: { client?: string } // active client context from the shell
): ImportModel
```

- **MUST** tag each record with its `kind` (`document` for docs, `image` for visuals) and
  build `ImportedMaterial` with a plain `name` (prefer `title`, fall back to `filename`) —
  never surfacing `id`, path, or MIME as identity (FR-013).
- **MUST** group into `shelves` (client → project → campaign) via `assoc`, with an
  `unassigned` bucket for ids absent from `assoc`.
- **MUST** scope to `scope.client` when set (only that client's shelves), else show all.
- **MUST** be a pure function of its inputs (no I/O) — fully unit-testable offline.
- **MUST** de-dup by `id` within a kind; an item appears exactly once.

## 3. `associationStore.ts` — localStorage association map

```
getAssociation(id): ClientAssociation | null
setAssociation(id, assoc: ClientAssociation): void   // associate / move
clearAssociation(id): void                            // return to unassigned
pruneAssociations(knownIds: string[]): void           // drop entries whose id no longer exists
```

- **MUST** persist under a namespaced `localStorage` key (shell preference prefix), holding
  only `id → {client, project?, campaign?}` — **never** a secret, never a file path.
- **MUST** default an item with no entry to the **unassigned** shelf (FR-006).
- **MUST** be reversible: `setAssociation` then `clearAssociation` returns to unassigned; a
  second `setAssociation` overwrites (FR-008).
- **MUST** prune orphaned ids after a load so removed items leave no ghost shelf (R6).
- **MUST** degrade gracefully if `localStorage` is unavailable (treat all as unassigned; no
  crash), mirroring the shell's preference handling.

## 4. Bring-in flow (`BringInPanel`)

For each chosen file:
1. **Classify kind** from an allow-list (document exts vs image exts). Unknown → emit
   `BringInResult{status:"rejected", reason:"unsupportedKind"}` **without** a network call,
   naming what *is* supported (FR-003/FR-012).
2. **Route**: `document → ingestDoc(file)`, `image → uploadVisual(file, {cloud})` where
   `cloud` is the per-item opt-in (default off).
3. **Progress** shown while the request is in flight (FR-004).
4. **Map the response** to `BringInResult` (see data-model): `201 → accepted` (+ default
   association = active client context, written to the map); `413 → rejected` (`tooLarge` —
   the server's streamed size cap); `400 → rejected` (`unreadable`); `501 → capabilityAbsent`
   (enable hint, FR-011); `500`/other → `rejected` (generic plain reason). The status is read
   from the `errorText` delimiter (`<label> → <status>`), never a bare substring. **Never** a
   silent drop, never a raw error (FR-003).
5. **Reflect** an accepted item on its shelf within one frame; the imported list re-reads
   `listDocs`/`listVisual` (or optimistically appends) and re-runs `buildImportModel`.

## 5. Catalog-key contract (`import.*`)

All operator-facing strings are `import.*` catalog keys present in **both** `en.ts` and
`fr.ts`, keyed identically (umbrella i18n rule; SC-004). Required groups (illustrative — final
list fixed in tasks):

- `import.title`, `import.subtitle`
- `import.bringIn.cta`, `import.bringIn.docHint`, `import.bringIn.imageHint`, `import.bringIn.progress`
- `import.kind.document`, `import.kind.image`
- `import.reject.unsupportedKind`, `import.reject.tooLarge`, `import.reject.unreadable`, `import.reject.generic`
- `import.capabilityAbsent.title`, `import.capabilityAbsent.body`, `import.capabilityAbsent.hint`
- `import.cloud.optInLabel`, `import.cloud.offMachineWarning`
- `import.shelf.unassigned`, `import.card.importedOn`, `import.card.remove`
- `import.associate.attach`, `import.associate.move`, `import.associate.unassign`, `import.associate.success`, `import.associate.failed`
- `import.remove.confirm`, `import.remove.success`, `import.remove.failed`
- `import.empty.firstRun.title/body/cta`, `import.empty.context.title/body`
- `import.state.loadError`
- `import.brief.useMaterialLabel`, `import.brief.willUseSummary` (S2 affordance — §brief-attachment.md)

**No raw key may render** (SC-004): every used key exists in both catalogs and is covered by
the existing i18n completeness check.

## 6. Non-negotiables (verified against source)

- **Zero server change** — endpoints reused verbatim; `pytest` untouched and green.
- **Local-first** — `cloud` off by default; no mission-time network added (FR-010).
- **Security** — server keeps `_safe_upload_filename` + streamed size caps; the association
  map never holds or displays a secret; no path/store-id shown as identity (FR-013/FR-018).
- **Additive** — with no material imported and the brief affordance unused, behavior is
  byte-identical to pre-S5 (Principle X).
