# Phase 0 — Research: Delete a recent mission

No `NEEDS CLARIFICATION` markers remained in the spec; the scope decision (permanent delete vs
archive) was resolved by reasonable default. The research below records the design decisions
that ground the implementation, each derived from existing, shipped patterns in the codebase.

## D1 — Which store must the delete purge?

**Decision**: Delete the per-mission directory in the saved-mission store,
`~/.agency/missions/<mission_id>/`, via a new `agency_kit.store.delete(mission_id)`.

**Rationale**: `GET /api/missions` → `_handle_list_missions` reads `store.list_missions()`,
which enumerates `store.missions_dir()` (= `~/.agency/missions/`). Both the home Recent work
list and the Library "See all" view consume that endpoint. Removing the mission's directory
from that one store therefore makes it disappear from every listing surface (FR-005 / US3) with
no secondary index to keep in sync.

**Alternatives considered**: (a) A soft-delete/"hidden" flag — rejected: adds a filter to every
listing path and a persisted flag, more surface than a permanent delete the user asked for.
(b) Deleting the project-local `missions/<id>/` mirror and `studio_assets/missions/<id>/`
render cache too — treated as out of scope for correctness (they are derived artifacts, not the
listing source); may be swept later, noted as a non-blocking follow-up, not required for FR-005.

## D2 — Endpoint shape and safety

**Decision**: `DELETE /api/mission/{id}` → `_handle_delete_mission`, mirroring the shipped
`DELETE /api/checkpoints/{id}` (`_handle_delete_checkpoint`): validate/normalize the id, guard
the filesystem path with `path_inside(store.missions_dir(), id)`, return **204** on removal and
**404** on an unknown or unsafe id.

**Rationale**: Reuses a proven, reviewed pattern and its traversal defense. `path_inside` is the
constitution's required guard (Art. VI); a malformed/`../` id simply fails the guard and 404s,
never escaping the store. Additive: `do_DELETE` already exists (checkpoints branch), so this is
one more `path.startswith("/api/mission/")` branch.

**Alternatives considered**: `POST /api/mission/{id}/delete` — rejected: DELETE is the correct
verb, already used elsewhere (`/api/docs/{id}`, `/api/visual/{id}`, `/api/checkpoints/{id}`),
and the OPTIONS preflight already advertises DELETE.

## D3 — Idempotency

**Decision**: Deleting an id that is already absent resolves as **success** (the store function
is a best-effort `rmtree`; a missing directory is not an error). The endpoint returns 204 when
the mission existed and was removed, 404 only for an unsafe/never-valid id.

**Rationale**: FR-009 requires idempotent deletion; a stale client list or a double click must
not surface a confusing error. This matches `test_delete_document_is_idempotent`'s existing
contract. (Endpoint nuance: an *already-gone* valid id may 404 or 204 depending on
existence-check ordering; the client treats both `204` and `404` as "gone" — see D5.)

## D4 — Confirmation UX (front end)

**Decision**: The delete control opens an explicit inline confirmation (confirm / cancel)
before any request is sent; only "confirm" calls `deleteMission(id)`. On success the item is
removed from `ResumeSection`'s local state (optimistic-after-success) so it disappears without a
full reload (FR-004). On failure the item stays and an error message is shown (FR-006).

**Rationale**: Art. VIII simplicity + FR-002 anti-accident. An inline confirm (vs a modal) keeps
the home panel simple and keyboard-accessible; the pattern is consistent with the studio's
lightweight controls. The delete button is visually and semantically distinct from the
item-open button (FR-001), each with its own accessible label.

**Alternatives considered**: Native `window.confirm` — rejected: not styleable, not bilingual
through the i18n catalog, and harder to test in vitest. A full modal — rejected as heavier than
needed for a single destructive action.

## D5 — Client handling of the response

**Decision**: `deleteMission(id)` treats `204` and `404` as success (the mission is gone either
way) and throws only on other non-OK statuses. After success the client also clears the
follow/resume pointer if it referenced the deleted id (FR-007).

**Rationale**: Idempotency end-to-end (D3) — a mission already removed server-side should still
clear from the UI. Clearing a dangling follow pointer prevents offering "resume" for a mission
that no longer exists.

## D6 — Deletability gate (terminal only)

**Decision**: The delete control is offered only for saved missions in a terminal state
(delivered/failed/cancelled) as surfaced by the Recent work item's status; a mission still
running (the live-followed item) does not show delete (FR-008).

**Rationale**: A running mission is not yet a saved dossier and is managed via cancel/resume;
deleting it has no store target. `recentMissionsView` already distinguishes a live item (routes
to `#/missions`) from a saved one (routes to the Library), giving the front end the signal to
gate the control.

## Testing approach (Art. VII — fully offline)

- **store.delete**: unit tests with `store.missions_dir()` monkeypatched to `tmp_path` — deletes
  an existing mission dir, is idempotent for a missing id, and refuses a traversal id.
- **endpoint**: `tests/test_server.py` — 204 on delete, 404 on unknown/unsafe id, idempotent,
  path-traversal rejected; mirrors `test_list_and_delete_checkpoints_endpoints` + the `_delete`
  helper; store dir monkeypatched.
- **GUI**: `ResumeSection.test.tsx` — delete button present per item, confirm required (cancel
  leaves the item), confirm removes the item from the list, failure keeps it and shows an error,
  EN/FR labels; `deleteMission` fetch mocked.

All boundaries (filesystem store, `fetch`) are monkeypatched/mocked — no network, no CLI, no
Node beyond vitest, no GPU.
