# Contract: Export model + frontend surface

**Feature**: S6 Export · **Date**: 2026-07-06
**Scope**: The frontend-owned pure model (which formats a finished deliverable offers), the
`api.ts` download wrappers, and the i18n catalog-key contract. Purely presentation +
orchestration over the endpoints in `bundle-endpoints.md`.

---

## Pure model: `screens/export/exportModel.ts`

Deterministic, no I/O. Turns a finished deliverable (mission summary + optional loaded dossier)
into the formats it offers and their availability.

```text
availableFormats(deliverable, { pdfCapable }) -> FormatView[]
```

- Input: a **finished** deliverable (running/failed are never passed in — FR-004), its `hasMedia`
  (from the dossier `assets` manifest), and whether the machine has the `[pdf]` extra (`pdfCapable`,
  discovered lazily from a format's 501 response — the screen does not pre-probe).
- Output, per format:

| Format | offered when | availability |
|---|---|---|
| `document` | always | `available` → `unavailable-here` if a produce attempt returns 501 |
| `mediaPack` | always listed | `available` if `hasMedia` else `no-media-to-pack` |
| `fullBundle` | always | `available` → `unavailable-here` if a produce attempt returns 501 |

- `contentsDescription(format)` → plain-language string key (no machinery terms; FR-005).
- `friendlyFilename(deliverable, format)` → human-meaningful download name (never the raw mission
  id as identity; FR-013). The **authoritative** filename is the server's `Content-Disposition`;
  this is the fallback.

**Rules**:
- Pure function of its inputs; same inputs → same output (testable offline).
- Never surfaces a mission id / MIME / path as a format's or deliverable's identity.

---

## API wrappers: `app/studio/src/api.ts` (additive)

Mirror the existing `fetchMissionPdf` (`api.ts:133–136`) — `fetch → Blob`, throw on non-`ok` so
501/404/500 are **catchable** (not a broken `<a href>` navigation):

```text
fetchMissionPdf(id, signal?)        // EXISTING — reused as-is for the document format
fetchMissionMediaZip(id, signal?)   // NEW → GET /api/mission/{id}/media.zip  → Blob
fetchMissionBundle(id, signal?)     // NEW → GET /api/mission/{id}/bundle.zip → Blob
```

Each throws `new Error(await errorText(res, …))` on non-`ok`, exactly like `fetchMissionPdf`, so
the screen maps status → state (501 → capability-absent; 404 → no-deliverable/no-media; 500 →
failed-retry).

## Download helper: `screens/export/download.ts`

`downloadBlob(blob, filename)` → object-URL + programmatic anchor click + revoke. Prefers the
server `Content-Disposition` filename; falls back to `friendlyFilename`. Shared by all three
formats. No new dependency (browser APIs only).

---

## i18n catalog-key contract (`i18n/catalog.ts` + `en.ts` + `fr.ts`)

New `export.*` typed keys, EN (source of truth) + FR, ~30–45 keys covering:
- format names + `contentsDescription` per format (document / media pack / full bundle);
- produce / download CTAs, in-progress + ready confirmation;
- capability-absent ("not available here — how to enable"), no-media-to-pack;
- empty (first-run), empty-for-client-context, connection-lost states;
- render/packaging-failure + retry.

**Rules** (umbrella): every key present in **both** locales (completeness check, SC-004); English
fallback; zero raw-key leaks; no machinery term, store id, MIME, or file path in any string
(FR-013, SC-004).

---

## Screen behavior contract (`Export.tsx` / `ExportPanel.tsx` / `FormatCard.tsx`)

- Lists **finished** deliverables (reusing S4's finished-mission listing), scoped by the shell
  client-context; running/failed not offered (FR-004).
- For a chosen deliverable: shows the three formats with plain-language contents (FR-005) and their
  availability; media pack disabled with "no media to pack" when `hasMedia` is false (FR-009).
- Produce → progress → download (friendly filename) with a plain "ready" confirmation (FR-011);
  501 → capability-absent state for that format only, others keep working (FR-012); 500 → plain
  retry (FR-011).
- Empty (first-run), empty-for-context, and connection-lost states are friendly and localized
  (FR-014). Fully keyboard-operable + screen-reader-labeled, AA contrast, visible focus (FR-017,
  SC-005). Language switch updates all chrome immediately; the deliverable's own content/filename
  is not translated.

---

## Test contract (offline, Vitest)

- `exportModel.test.ts` — availableFormats derivation; `hasMedia` gating (assets present/absent →
  `no-media-to-pack`); `contentsDescription`; `friendlyFilename`; single-deliverable scope.
- `Export.test.tsx` — load + list finished deliverables; empty / empty-for-context /
  connection-lost; only finished offered; a11y/keyboard.
- `ExportPanel.test.tsx` — choose each format, produce + download (mocked api wrappers), progress;
  media-pack disabled when no media; 501 → capability-absent; 500 → retry.
- `download.test.ts` — Blob → filename from `Content-Disposition`; 501/404/500 surfaced as
  catchable errors.
