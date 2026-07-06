# Phase 0 Research — Deliverable Library (S4)

All unknowns are resolved against the **existing** studio frontend, the local HTTP server,
and the agency-kit store. No new technology is introduced; the research below records the
decisions that let S4 be a pure presentation + organization layer with zero server change.

---

## R1 — What is a "deliverable", and where does the list come from?

**Decision**: A deliverable is one **durable saved mission dossier**. The Library reads the
existing `GET /api/missions` via `api.ts::listMissions({client?, project?, campaign?})`,
which returns `MissionSummary[]` (`mission_id`, `goal`, `route`, `verdict`, `delivered`, …);
the full dossier for the open/preview surfaces comes from `getMission(id)` (`GET
/api/mission/{id}`), and the PDF from `fetchMissionPdf(id)`.

**Rationale**: These endpoints already exist and already back the developer console's
`TaxonomyBrowser`. Reusing them means no new store, no new persisted field, and no server
change — S4 is a second, operator-facing *view* of the same durable data.

**Alternatives considered**: A dedicated "deliverables" store/index — rejected: it would
duplicate the mission store, add a persistence path, and violate "additive over invasive".

---

## R2 — How are deliverables grouped by client → project → campaign, and what is the unassigned shelf?

**Decision**: `listMissions()` (no filter) returns every saved mission; each carries its
taxonomy attribution. The Library groups them **client-side** into a `client → project →
campaign` tree, with a dedicated **unassigned** shelf for missions with no client. The
taxonomy tree itself (for filing choices and shelf labels) comes from the shell's already-
loaded `useClientContext().taxonomy` (`fetchTaxonomy` → `TaxonomyTree`). When the shell's
client-context selector is set, the Library scopes to that client (optionally passing the
filter to `listMissions` and/or narrowing client-side).

**Rationale**: The grouping is a pure fold over data already fetched; the shell already
owns and validates the active client context (`ClientContext.tsx`), so S4 consumes it
rather than re-implementing a picker (Assumptions §"single client context").

**Alternatives considered**: A separate in-screen client picker — rejected for v1
(duplicates the shell selector). Server-side grouping — rejected (the flat list + client
fold is trivial at local volume, and the server stays untouched).

---

## R3 — FR-014a "appears exactly once": how are resumed runs keyed? (the one real unknown)

**Decision**: Deduplicate by the durable **`mission_id`** returned by `listMissions()`. The
Library renders **one card per `mission_id`**, applying a defensive client-side dedup.

**Rationale (grounded in the store)**: `agencykit/agency_cli/runner_bridge.py` (lines
~281–307) documents two distinct resume concepts, and neither produces a duplicate library
entry:
- **`resume_state` (checkpoint / crash-recovery)** continues an *interrupted* mission. The
  checkpoint is *transient* and **never web-served** (server.py: checkpoints live under
  `docs_root/checkpoints`, are not in `list_missions`). The interrupted run therefore
  **never appears** in the Library at all. When it completes on resume, it "persists under a
  FRESH mission_id … exactly like a first run" (`dossier["mission_id"] =
  store.new_mission_id(goal)`), yielding **exactly one** durable dossier.
- **`resume(mission_id)` (re-run a *completed* mission)** deliberately produces a *new*
  result under a fresh id — that is a genuinely distinct second deliverable (the operator
  chose to run it again), not a duplicate to hide.

So "each finished deliverable appears exactly once" is **already guaranteed at the data
layer**: the Library lists durable `mission_id`s (each unique), an interrupted-then-resumed
production surfaces as a single completed dossier, and a deliberate re-run is correctly its
own card. FR-014a is satisfied by "one card per durable `mission_id`" with a defensive
dedup — **no parent-link, no superseding index, no server change** is required. The spec's
"supersede its prior entry" wording is honored *in effect*: the interrupted entry was never
durable, so there is nothing stale to show.

**Alternatives considered**: A `parent_mission_id`/lineage field to explicitly link and
hide superseded runs — rejected: the store does not record lineage, the interrupted run has
no durable entry to link, and inventing one would mean a server + store change (violates
X). Showing whatever the store returns with no dedup — rejected: loses the cheap defensive
guard that protects SC-002 if the list ever returns a repeat.

---

## R4 — Outcome classification (successful vs needs-attention)

**Decision**: Classify each deliverable into **successful** vs **needs-attention** from the
mission's **already-stored** signals — its `verdict`/`delivered` fields on `MissionSummary`
(and the dossier's `verdicts[]` / `delivered` when the full dossier is loaded). A run that
delivered with a passing/soft-pass inspector verdict is *successful*; a run that ended in
error, cancellation, or veto (no clean delivery) is *needs-attention*. Reuse the existing
`summaryVerdictClass` / `lastVerdict` / `verdictClass` helpers in `types.ts` that the
console already uses, mapped to plain-language, localized labels.

**Rationale**: No new computation or stored state — S4 reads verdict/delivery signals the
mission loop already writes, and reuses the console's existing verdict helpers, re-phrased
for a non-technical operator (no raw verdict codes, per FR-003/SC-004).

**Alternatives considered**: Recomputing an outcome from event history — rejected (S4 has
no event stream; that is S3's domain, and the durable dossier already carries the verdict).

---

## R5 — Preview vs. open full detail (FR-008)

**Decision**: The **in-place preview** is a lightweight summary panel assembled from the
loaded dossier (`getMission`): headline/description (`goal`), outcome badge, the top few
`sources` and `decisions`, and media thumbnails via the existing `AssetGallery` over the
dossier `assets[]`. **Opening the full detail** renders the existing
`components/MissionDetail` (full dossier Markdown + sources + AssetGallery + PDF button).

**Rationale**: Preview and full-detail are both named S4 concerns (inventory + clarify). The
full-detail surface already exists (`MissionDetail`), so "open" reuses it verbatim; preview
is a strict subset assembled from the same dossier — no new data, no navigation, matching
FR-008.

**Alternatives considered**: Preview = a hover tooltip — rejected (insufficient for
sources/decisions/thumbnails, and not keyboard/AA-friendly). Drop preview, open-only —
rejected in clarify (the inventory names "previews").

---

## R6 — Filing (attach / move / return-to-unassigned) and the non-destructive guarantee

**Decision**: Filing reuses `api.ts::assignMission(id, {client?, project?, campaign?} | {
clear: true })` (`POST /api/mission/{id}/assign`) — the exact path the console's
`TaxonomyBrowser` uses. Attaching an unassigned deliverable, moving a mis-filed one, and
returning one to unassigned (`{clear:true}`) are all the *same* endpoint; the Library
re-reads/optimistically updates the grouped model so the new shelf shows immediately, and
filing again reverses it. **No delete** action exists in v1 (clarify): filing is the *only*
mutation S4 performs.

**Rationale**: The assign endpoint is the sanctioned, already-secured taxonomy mutation;
reusing it keeps S4 additive and its single mutation on a validated server path. Excluding
delete keeps S4 within the "reads and organizes, never alters persistence (beyond filing)"
pledge (FR-009/FR-015).

**Alternatives considered**: A client-side file operation or a new delete endpoint —
rejected (delete is deferred as a later guarded capability; a client-side FS op is
impossible and unsafe).

---

## R7 — Scale / volume handling (load-all, client-side)

**Decision**: Load the full finished-mission list once (`listMissions`) and do grouping,
search, and outcome-filtering **client-side**; **no server-side pagination** in v1.
Rendering stays responsive at the expected local single-user volume (tens–low hundreds of
missions).

**Rationale**: A local single-user agency's mission count is modest; the flat list is cheap
to fold and filter in the browser, and the server's `list_missions` has no paging surface.
Pagination or list virtualization can be layered in later without redesign if volumes grow
(clarify).

**Alternatives considered**: Server-side pagination — rejected for v1 (needs new endpoint
params; premature for the volume). Virtualized rendering now — deferred (unneeded at v1
volume; noted as the first lever if profiling shows jank).

---

## R8 — S3 completion hand-off (S4 as the permanent home)

**Decision**: S4 becomes the destination the S3 Mission Timeline "view your deliverable"
action lands on. Today S3 points at the interim `MissionDetail`/PDF surface (S3 clarify);
once S4 ships, a finished run is reachable in the Library, and its card opens the same
`MissionDetail`. The S3→S4 wiring itself (route target on completion) is a small S3-side
follow-up recorded as an integration note; S4's obligation is to present the finished run
correctly and openably (FR-017, SC-007).

**Rationale**: Keeps the S3/S4 boundary clean — S4 owns the library surface; the hand-off
target flip is minimal and additive. A finished run already becomes a durable dossier, so
it appears in the Library with no extra plumbing.

**Alternatives considered**: Embedding library logic into S3 — rejected (violates the
inventory's screen separation).

---

## Summary of decisions

| # | Topic | Decision |
|---|-------|----------|
| R1 | Deliverable source | Durable dossiers via existing `listMissions` / `getMission` / `fetchMissionPdf` — no new store |
| R2 | Grouping | Client-side fold into client→project→campaign + unassigned; taxonomy from shell context |
| R3 | Dedup (FR-014a) | One card per durable `mission_id`; guaranteed unique at data layer (checkpoints never durable) |
| R4 | Outcome | successful vs needs-attention from stored verdict/delivered signals; reuse `types.ts` helpers |
| R5 | Preview / open | In-place preview subset + reuse `MissionDetail` for full open |
| R6 | Filing | Reuse `assignMission` (attach/move/clear); **no delete** in v1 |
| R7 | Scale | Load-all, client-side group/search/filter; no pagination |
| R8 | S3 hand-off | S4 is the permanent home; S3 completion-target flip is a minimal integration note |

**No NEEDS CLARIFICATION remain.** Zero server changes, zero new dependencies.
