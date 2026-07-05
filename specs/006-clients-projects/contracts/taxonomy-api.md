# API Contract: Taxonomy endpoints (Brick 6)

All endpoints ride the existing loopback-only stdlib server (`127.0.0.1`), same
security posture as every existing route: no CORS `*`, no new static serving,
no outbound requests. All are workspace-scoped exactly like the existing
history routes (missions outside the server's `project_root` are invisible;
scoping uses the same rules as `_load_scoped_dossier` / `mission_in_project`).

## 1. POST /api/mission — additive payload fields

Existing endpoint; body gains three optional string fields:

```json
{
  "goal": "…", "engine": "…", "web_search": false,
  "client":   "Acme",
  "project":  "Rebrand",
  "campaign": "Spring Launch"
}
```

- All three optional, independently (FR-001). Absent/empty-after-trim ⇒ that
  level resolves by default. Non-string ⇒ treated as absent.
- Validation: >120 chars or control characters ⇒ HTTP 400 before the mission
  starts.
- Behavior with none supplied: **byte-identical to today** (FR-008).
- On mission completion the tags are merged into the new mission's own dossier
  and re-saved; the checkpoint envelope carries them across a crash/resume.
- The `done` SSE frame additionally reports the resolved attribution:
  `"attribution": {"client": "Acme", "project": "Rebrand", "campaign": "Spring Launch"}`.

## 2. GET /api/taxonomy

Workspace-scoped tree with counts. `200 application/json`:

```json
{
  "clients": [
    {
      "name": "Acme",
      "missions": 7,
      "projects": [
        {
          "name": "Rebrand",
          "missions": 7,
          "campaigns": [
            { "name": "Spring Launch", "missions": 3 }
          ]
        }
      ]
    },
    {
      "name": "Studio",
      "missions": 12,
      "projects": [
        { "name": "agency-openstudio", "missions": 11, "campaigns": [] },
        { "name": "Unassigned", "missions": 1, "campaigns": [] }
      ]
    }
  ]
}
```

- `name` is the display form (first-typed casing preserved, FR-006).
- Counts: a project's count = missions resolving to it (campaign-less included);
  a client's count = sum over its projects. Every readable mission in the
  workspace appears in exactly one project (SC-002).
- Empty store ⇒ `{"clients": []}` (200, never an error).
- Read-only: serving this endpoint MUST NOT write anything (byte-identity,
  FR-007).

## 3. GET /api/missions — additive query filters

Existing endpoint; gains optional `client`, `project`, `campaign` query params
(display-or-any-casing names, matched via normalization).

- **No params ⇒ exact existing behavior and row shape, unchanged** (FR-008).
- With params: rows are the existing summary shape **plus** the resolved
  attribution:

```json
{
  "missions": [
    {
      "mission_id": "…", "goal": "…", "route": ["…"], "iteration": 1,
      "verdict": "PASS", "delivered": true,
      "client": "Acme", "project": "Rebrand", "campaign": "Spring Launch"
    }
  ]
}
```

- Filters compose (AND). Unknown names ⇒ `{"missions": []}` (200, spec
  acceptance scenario — empty, not error). Invalid values (>120 chars, control
  chars) ⇒ 400.

## 4. POST /api/mission/{id}/assign

Set or clear the side-band override for one mission (FR-013).

Request — set (any subset; the triple stored is the resolved result of applying
the given levels over the mission's current attribution):

```json
{ "client": "Acme", "project": "Rebrand", "campaign": null }
```

Request — clear:

```json
{ "clear": true }
```

Responses:

- `200` — `{ "ok": true, "attribution": { "client": "…", "project": "…", "campaign": null } }`
  (the post-change resolved attribution).
- `404` — mission unknown, corrupt, or outside this workspace (same opaque 404
  as `GET /api/mission/{id}` — no cross-project disclosure).
- `400` — invalid values (length/control chars) or a body that is neither a
  set nor a clear.

Guarantee: this endpoint writes ONLY `~/.agency/taxonomy.json` (atomic
replace); the mission's stored dossier is never touched (FR-007 holds through
re-assignment).

## Compatibility matrix

| Surface | Without Brick 6 input | With Brick 6 input |
|---|---|---|
| `POST /api/mission` | byte-identical | tags merged into own dossier post-run |
| `GET /api/missions` | byte-identical | filtered + attribution columns |
| `GET /api/mission/{id}` | unchanged | unchanged (raw dossier as stored) |
| `GET /api/taxonomy` | n/a (new) | tree + counts, read-only |
| `POST /api/mission/{id}/assign` | n/a (new) | registry-only write |
