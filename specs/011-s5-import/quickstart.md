# Quickstart — S5 Import

How to build, run, and verify the Import screen. S5 is a **frontend-only** feature over the
existing local server — no server run/build changes.

## Prerequisites

- The studio installed editable (`pip install -e ./agencykit && pip install -e .`).
- The frontend toolchain in `app/studio/` (Node + the existing Vite/Vitest setup).
- For a full bring-in demo: the optional extras that back ingestion — `[studio]` (document
  conversion/embedding) and `[visual]` (image captioning). **Absent extras are expected to
  produce the localized "not available here — how to enable" state**, not an error (FR-011) —
  that path is itself part of the acceptance surface.

## Build & test (offline — the gate that must stay green)

```bash
# from app/studio/
npm run test        # Vitest — all new screens/import/* + updated composeMission.test.ts
npm run build       # type-check + production build (the served dist)

# from repo root
pytest              # server suite — MUST stay green (S5 changes no Python)
```

The offline suite mocks `ingestDoc`/`listDocs`/`deleteDoc`/`uploadVisual`/`listVisual`/
`deleteVisual` and `localStorage`; no network, no CLI, no live server, no GPU.

## Run the app

```bash
python -m agency_studio serve      # existing local server at 127.0.0.1
# open the studio, navigate to  #/import
```

## Manual verification (maps to acceptance scenarios)

1. **Bring in & confirm (US1)** — On `#/import`, bring in a supported document and a
   supported image. Each shows progress then a plain-language confirmation and appears on a
   shelf. With a client selected in the shell selector, items land on that client's shelf;
   with none, on **unassigned**. (US1-AC1, AC3)
2. **Validation & feedback (US1)** — Try an unsupported kind (e.g. a `.zip` or a video), an
   oversized file, and an unreadable file → each rejected with a plain reason that names what
   *is* supported; no crash, no silent drop. (US1-AC2)
3. **Capability absent (US1)** — Run without the `[visual]` extra installed and try an image
   → the localized "not available here — how to enable" state, documents still importable.
   (US1-AC4, FR-011)
4. **Empty state (US1)** — Fresh machine, open `#/import` → friendly empty state with a way to
   bring material in. (US1-AC5)
5. **Use in a production (US2)** — With material imported, open the Guided Brief, turn on
   "use the material you've imported", review shows "this production will build on your
   imported material", launch → the mission runs with `knowledge`/`visual` on and draws on
   the material. With the affordance off, the launch is byte-identical to today. (US2-AC1–AC2)
6. **Organize & remove (US3)** — Re-associate a mis-filed item to another client (moves
   shelves immediately, reversible); remove an item (confirmation + feedback). If a
   deliverable was produced from it earlier, confirm that deliverable is intact in the S4
   Library. (US3-AC2–AC3, SC-009)
7. **Local-first (SC-007)** — A default bring-in performs no off-machine call; only an
   explicit per-item cloud-captioning opt-in sends an image off-machine, and it is OFF by
   default with a plain warning. (FR-010)
8. **i18n & a11y (SC-004/SC-005)** — Switch EN/FR: all Import chrome follows immediately with
   zero raw keys and zero store ids/MIME/paths as identity; drive bring-in, associate, and
   remove by keyboard only, with visible focus and screen-reader labels.

## What must NOT change (guardrails)

- **No server file** is edited — `git status` shows changes only under `app/studio/src/` and
  `specs/011-s5-import/` (+ the AGENTS.md SPECKIT marker).
- **No new dependency** in `package.json`.
- The developer console's docs/visual surfaces render byte-identically.
- With no material imported and the brief affordance untouched, the whole app behaves exactly
  as pre-S5 (additive delivery, Principle X).
