# Contract — Preview, Actions & Filing

The per-deliverable surfaces (in-place preview + the three everyday actions) and their
reuse of existing endpoints. S4 adds **no new endpoint** and performs **exactly one**
mutation (taxonomy filing). All behavior is offline-testable with the existing `api.ts`
mocks.

## Endpoints reused (all pre-existing — none modified)

| Purpose | `api.ts` fn | HTTP | Notes |
|---------|-------------|------|-------|
| List deliverables | `listMissions({client?,project?,campaign?})` | `GET /api/missions` | Optional taxonomy filter; also used unfiltered for the full library. |
| Taxonomy tree | (via `useClientContext`) `fetchTaxonomy()` | `GET /api/taxonomy` | Shelf labels + filing choices. |
| Preview / open detail | `getMission(id)` | `GET /api/mission/{id}` | Full `Dossier`; preview uses a subset, open renders `MissionDetail`. |
| Download PDF | `fetchMissionPdf(id)` | `GET /api/mission/{id}/pdf` | Returns a `Blob`; `[pdf]` extra may be absent ⇒ graceful failure. |
| File / refile | `assignMission(id, fields \| {clear:true})` | `POST /api/mission/{id}/assign` | The **only** mutation S4 performs. |

## In-place preview (FR-008 / R5)

- Triggered on a card without navigating away; lazily calls `getMission(id)` once, caches
  the resulting `DeliverablePreview` on the Deliverable.
- Renders: headline, outcome badge, first N `sources` (safe-URL links), first N
  `decisions`, and media thumbnails via the existing `AssetGallery` over `assets[]`.
- **No-media dossier** (research/strategy only) ⇒ media section omitted; **no broken
  thumbnail placeholders** (edge case).
- Fully keyboard-operable and screen-reader-labeled; opening/closing the preview announces
  via the shared live-region pattern (WCAG 2.1 AA).

## Actions (`DeliverableActions.tsx`)

### Open full detail (FR-005)
- Renders the existing `components/MissionDetail` for the loaded `Dossier` — the dossier is
  **not** mutated. Presented in plain language; sources open with `rel="noopener
  noreferrer"`.

### Download PDF (FR-011)
- Calls `fetchMissionPdf(id)`; shows in-progress feedback; on success offers the `Blob` for
  download.
- On failure (e.g. `[pdf]` extra missing, render error) shows a **plain-language** message
  with an enable/install hint where relevant — the rest of the deliverable stays usable.
  Never a raw error, never a silent no-op.

### File / refile (FR-009 / FR-010 / R6)
- See Filing below. This is the third action.

### Explicitly absent: **Delete / remove** (clarify — non-destructive v1)
- `DeliverableActions` renders **no** delete/remove control. Asserted by
  `DeliverableActions.test.tsx` (a no-delete guard test), so a future accidental
  re-introduction fails CI. Removal is deferred to a later, guarded capability.

## Filing (`FilingControl.tsx`) — the only mutation

- Attach an **unassigned** deliverable, **move** a mis-filed one, or **return** one to
  unassigned — all via `assignMission`:
  - attach / move ⇒ `assignMission(id, { client, project?, campaign? })`
  - return to unassigned ⇒ `assignMission(id, { clear: true })`
- Filing choices come from the shell's `useClientContext().taxonomy` (existing clients /
  projects / campaigns) — S4 does **not** create/rename/delete taxonomy nodes (FR-018).
- **Immediate reflection (FR-010)**: on success the deliverable's `placement` updates and
  the grouped model re-folds so the card appears on its new shelf within one frame
  (optimistic update reconciled with the response, or a targeted re-`listMissions`).
- **Reversible (FR-010)**: filing again (including `{clear:true}`) undoes it — no separate
  undo machinery needed.
- **Feedback (FR-011)**: success and failure both surface a plain-language message; a failed
  assign leaves the prior placement intact (no partial move).

## Guarantees (asserted by tests)

1. Open renders `MissionDetail` without mutating the dossier.
2. PDF success downloads the blob; PDF failure shows a localized hint, deliverable stays
   usable.
3. Filing attach/move/clear each call `assignMission` with the correct body and reflect the
   new shelf immediately; a second filing reverses it.
4. **No delete control exists** anywhere in the Library (guard test).
5. Every action path emits localized success/failure feedback — no silent no-op, no raw
   technical error (FR-011).
6. Server stays byte-identical; the developer console's `TaxonomyBrowser` is untouched.
