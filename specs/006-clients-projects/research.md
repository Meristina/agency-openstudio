# Phase 0 Research: Clients & Projects (Brick 6)

All Technical Context unknowns resolved. Decisions below are grounded in the
current code (read this session): `agency_studio/server.py` (mission POST
payload parsing at `_read_json_body`/`_str_field`, SSE `done` frame built from
`result.dossier`, history scoping at `/api/missions`), and
`agencykit/agency_kit/store.py` (`project_root` stamp, `_matches_project`,
`list_missions` corrupt-dossier skip, public `save()`/`load()`).

## D1 — How new missions get their taxonomy fields (no agencykit change)

**Decision**: The server captures optional `client` / `project` / `campaign`
strings from the mission POST payload, threads them through the worker, and
**after the mission completes** merges them into `result.dossier` and re-saves
via the public `agency_kit.store.save(dossier)`. The tags are also carried in
the crash-recovery checkpoint envelope (beside `goal`/`engine`/`flags`) so a
resumed mission keeps them.

**Rationale**: The kit's mission loop stays untouched (spec: "no change to
agency-kit's mission loop"; Constitution V and X). `store.save()` is public and
already the canonical dossier writer; re-saving the mission's **own, just
created** record is a new write — the byte-identity guarantee only covers
pre-existing missions. The server already holds `result.dossier` at the exact
point it emits the `done` SSE frame.

**Alternatives considered**:
- *Additive `dossier_extra` hook in `runner_bridge.run()`* — cleaner data flow,
  but requires an agency-kit-studio fork change + subtree sync; the local
  checkout is already known to drift from the CI subtree (Brick 5 lesson), and
  the spec explicitly forbids mission-loop changes. Rejected.
- *Sidecar-only for new missions too* — violates the Session 2026-07-05
  clarification (hybrid: new missions carry fields in their own dossier).
  Rejected.

## D2 — Side-band override registry: location & format

**Decision**: One global JSON file `~/.agency/taxonomy.json` (path derived from
the store's own `agency_dir()`), written atomically (write tmp file in the same
directory, then `os.replace`). Shape:

```json
{
  "version": 1,
  "overrides": { "<mission_id>": {"client": "...", "project": "...", "campaign": "..."} },
  "names":     { "client:acme": "Acme", "project:acme/rebrand": "Rebrand", "...": "..." }
}
```

`overrides` re-assigns single missions (FR-013); `names` maps normalized keys to
the first-typed display form (FR-006). Corrupt/missing file ⇒ empty registry
(same tolerance as `list_missions`).

**Rationale**: Missions live in the **global** store (`~/.agency/missions/`)
keyed by mission_id; the registry that describes them belongs beside them, so a
re-assignment is visible from every workspace. JSON matches the store's own
format and the zero-dependency core. Atomic replace prevents a torn file from a
crashed write.

**Alternatives considered**:
- *Per-workspace registry under `docs_root` (`.agency-studio/`)* — would
  fragment overrides across workspaces for globally-stored missions and break
  "re-assign once, true everywhere". Rejected.
- *SQLite* — stdlib-available but overkill for a small map, diverges from the
  store's JSON-file convention, and complicates the byte-level test story.
  Rejected.

## D3 — Endpoint shape

**Decision**: Three surface changes on the existing loopback server:
1. `GET /api/taxonomy` — workspace-scoped tree: clients → projects → campaigns,
   each node with display name and mission count.
2. `GET /api/missions?client=&project=&campaign=` — the existing listing gains
   optional filters; **without params the handler delegates to the existing
   `store.list_missions` call unchanged** (byte-identical, FR-008). With params,
   rows additionally carry the resolved `client`/`project`/`campaign`.
3. `POST /api/mission/{id}/assign` — set or clear the override for one mission
   (body `{client?, project?, campaign?}` or `{"clear": true}`); 404 for a
   mission outside the current workspace (same confinement as
   `_load_scoped_dossier`).

**Rationale**: Tree + filterable flat list compose into every browse the GUI
needs (SC-001) without duplicating listing logic in a bespoke "grouped feed"
endpoint. Filters as optional params keep one history endpoint, one scoping
rule.

**Alternatives considered**: a single `GET /api/missions/grouped` returning the
fully nested tree with embedded mission rows — heavier payloads, duplicated
listing/scoping logic, harder to keep byte-identical. Rejected.

## D4 — Attribution resolution & the store scan

**Decision**: `agency_studio/taxonomy.py` owns a pure function
`resolve(dossier, registry) -> {client, project, campaign}` implementing the
clarified order: override > dossier fields > derived default (project =
`Path(project_root_stamp).name`, client `"Studio"`, no stamp ⇒ group
`"Unassigned"`). For tree/filter queries the module performs its own read-only
scan of `store.missions_path()` (full dossiers are needed for resolution;
summary rows don't carry the stamp), reusing `store.mission_in_project` for
workspace scoping and skipping corrupt files exactly like `list_missions`.

**Rationale**: Keeps resolution testable as a pure function; avoids changing
`store.list_missions`'s row shape (agencykit untouched). The duplicate
directory walk is the store's own documented pattern ("scans every dossier …
fine for a local tool").

**Alternatives considered**: extending `store.list_missions` to return stamps/
fields — an agencykit change. Rejected.

## D5 — Name normalization

**Decision**: Normalization key = `value.strip()` then `str.casefold()`;
project keys are namespaced under their client (`project:<client>/<project>`),
campaigns under both (`campaign:<client>/<project>/<campaign>`), so same-named
projects under different clients never merge (spec edge case). Display form =
first-typed, persisted in the registry `names` map; empty-after-trim values are
treated as absent; values are capped at 120 chars and stripped of control
characters (reject with HTTP 400 on the API, not silently altered).

**Rationale**: `str.casefold()` is the stdlib's Unicode-correct fold (FR-006);
namespacing implements the hierarchy discipline from the spec's Key Entities.

**Alternatives considered**: slug-based IDs exposed in the API — extra concept
with no user value at this scale; names + namespacing suffice. Rejected.

## D6 — Migration = derivation, verified by fixture

**Decision**: No write-time migration step exists at all. "Folding" pre-Brick-6
missions into the taxonomy IS the derived default of D4. The offline test
builds a fixture store of pre-Brick-6 dossiers (with stamp, without stamp,
corrupt) in a tmp dir, snapshots SHA-256 of every file, exercises
`/api/taxonomy`, filtered listings, and an override round-trip, then asserts
every fixture file's hash is unchanged (FR-007, SC-003) and every mission
appears exactly once in the tree (SC-002).

**Rationale**: A migration that writes nothing cannot lose anything — the
strongest possible form of "soft, non-destructive".

**Alternatives considered**: one-shot stamping migration writing taxonomy into
old dossiers — violates byte-identity and FR-007. Rejected.

## D7 — GUI surfaces

**Decision**: Mission-start form (`App.tsx`) gains three optional text inputs
backed by `<datalist>` suggestions from `GET /api/taxonomy` (typing a new name
creates it implicitly — no management screens, per spec assumptions). History
gains a `TaxonomyBrowser` component: group-by-client (default) and
group-by-campaign toggles, drilling into the existing mission list/detail;
re-assign action calls the assign endpoint. Full redesign stays in Brick 7
(FR-012).

**Rationale**: Matches the Session 2026-07-05 GUI-scope clarification and
Constitution VIII with the smallest surface change to the existing form.
