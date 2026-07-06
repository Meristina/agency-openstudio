# Contract — Whole-Set Brief Attachment (S2 integration)

How FR-007 ("direct a brief to use my imported material") is realized **without** any
mission-loop or mission-bridge change — by flipping the mission's pre-existing
`knowledge`/`visual` opt-ins. Per spec Clarifications (2026-07-06): **whole-set**, no
per-item curation.

## 1. The existing consumption path (unchanged)

`runMission(goal, onEvent, opts)` already accepts `opts.knowledge` and `opts.visual`
(booleans, default false). When on, the mission draws on the **existing global** document /
image RAG stores through the sanctioned cited-RAG retrieval path. S5 adds **nothing** to
`runMission` or the server — it only decides when these booleans are set.

## 2. Brief-draft field (additive, default-off)

`briefDraft.ts` — the persisted `Brief` gains:

```
useImportedMaterial?: boolean   // default false
```

- **MUST** default to `false`/absent; a brief that never touches the affordance is
  byte-identical to today (Principle X).
- **MUST** persist with the existing brief draft (no new store).

## 3. Compose-time mapping (`composeMission.ts`)

`MissionDraft.opts` gains `knowledge?: boolean` and `visual?: boolean`. At compose time:

```
if (brief.useImportedMaterial && importedMaterialExists) {
  opts.knowledge = true;
  if (anyImportedImages) opts.visual = true;
}
```

- **MUST** set `knowledge` when the operator directed the brief to use imported material and
  at least one document is imported.
- **MUST** additionally set `visual` when at least one **image** is imported.
- **MUST** leave `opts` byte-identical to the current output when `useImportedMaterial` is
  false/absent (regression-guarded by the updated `composeMission.test.ts`).
- **MUST NOT** select or reference individual item ids — attachment is whole-set (no
  per-item payload reaches the mission).

## 4. Review-screen affordance (`Review.tsx`)

- **MUST** show a plain-language control ("Use the material you've imported") and, when on, a
  summary line ("This production will build on your imported material") — `import.brief.*`
  catalog keys, EN/FR.
- **MUST** be visible **only when imported material exists** (else the affordance is hidden —
  no dead control; ties to `listDocs`/`listVisual` being non-empty).
- **MUST NOT** expose store ids, MIME types, or file paths; it speaks only of "your imported
  material" (FR-013).
- Reachability parity (FR-007): the same intent is reachable from the Import screen (which can
  deep-link into the brief) and from within the brief flow.

## 5. Guarantees

- **No mission-bridge change**: the mission consumes material exactly as it does today when a
  user manually enables knowledge/visual; S5 only automates the intent from the brief.
- **Consistency with client scope**: whole-set attachment matches R4/R5 — the stores are
  shared and non-isolated, so a production uses the imported material as a whole (per-item /
  per-client filtering is a documented future refinement).
- **Offline-testable**: the mapping is a pure function of the brief + a boolean
  "material exists" input; `composeMission.test.ts` covers both on and off with no network.
