# Contract: `DELETE /api/mission/{id}`

Delete a saved mission from the studio's mission store. Additive to the existing
`agency_studio` server; mirrors `DELETE /api/checkpoints/{id}`.

## Request

```
DELETE /api/mission/{id}
```

- `{id}` — a `mission_id` as returned by `GET /api/missions` (`mission_id` field).
- No request body. No auth (loopback-only server, single operator).

## Responses

| Status | When | Body |
|---|---|---|
| `204 No Content` | The mission existed and its stored record was removed. | *(empty)* |
| `404 Not Found` | The id is unknown, malformed, or fails the `path_inside` traversal guard. | `{"error": "mission not found"}` |
| `501 Not Implemented` | *(not applicable — no optional extra gates this route)* | — |

- **Idempotent**: deleting an id whose record is already absent does not error. Depending on the
  existence check it resolves as `204` (treated as removed) or `404` (already gone); **clients
  MUST treat both `204` and `404` as success** ("the mission is gone").
- **Traversal-safe**: the deleted path is resolved through `path_inside(store.missions_dir(),
  id)`; any id that would escape the store (`../`, absolute, malformed) fails the guard and
  returns `404` — it is never used to touch the filesystem.
- **CORS/headers**: same `_cors()` headers as sibling routes; `127.0.0.1` only; the `OPTIONS`
  preflight already advertises `DELETE`.

## Side effects

- Removes `~/.agency/missions/{id}/` (dossier + deliverable) recursively.
- Does **not** touch checkpoints, the project-local mission mirror, or the render cache.
- The mission thereafter is absent from `GET /api/missions` (Recent work + Library).

## Client contract (`deleteMission(id)` in `api.ts`)

```
deleteMission(id): Promise<void>
  → fetch(`/api/mission/${encodeURIComponent(id)}`, { method: "DELETE" })
  → resolves on res.ok OR res.status === 404 (both mean "gone")
  → throws on any other non-OK status (surfaced as a user-facing error)
```

On success the caller removes the item from the Recent work list and, if the follow/resume
pointer references `id`, clears it.
