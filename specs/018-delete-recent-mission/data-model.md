# Phase 1 — Data Model: Delete a recent mission

This feature removes records; it introduces no new persisted entity. Two existing entities are
involved.

## Saved mission (deliverable)

The stored record of a completed mission — the unit a delete removes.

| Attribute | Meaning | Source |
|---|---|---|
| `mission_id` | Stable identifier; also the directory name in the store and the delete key | `store.new_mission_id()` |
| `goal` | The mission goal shown as the item label | dossier |
| verdict / status | Terminal state (delivered / failed / cancelled) shown as the item's status badge | dossier `verdicts` / residual |
| dossier + deliverable | The persisted content under `~/.agency/missions/<mission_id>/` | `store.save` |

**Storage location**: `~/.agency/missions/<mission_id>/` (`store.missions_dir()`).

**Read paths**: `store.list_missions()` → `GET /api/missions` → Recent work list AND Library.

**Delete rule**: remove `path_inside(store.missions_dir(), mission_id)` recursively.
- Guard: the resolved path MUST stay inside `store.missions_dir()`; an id failing the guard is
  rejected (→ 404), never deleted.
- Idempotent: a missing directory is a no-op success (FR-009).
- Deletable only when terminal (FR-008); an in-flight mission is not a delete target.

**State transition**: `saved` → `deleted (absent)`. Terminal and irreversible (no trash/undo);
the confirmation step is the only safeguard.

## Follow / resume pointer (client-side)

The browser-persisted reference to the most-recently-followed mission, used to offer "resume".

| Attribute | Meaning |
|---|---|
| `runId` / `missionId` | Which mission this pointer references |
| `status` / `resumable` / `checkpoint` / `resumeKind` | Resume affordance state |

**Relationship to delete**: if the pointer references the deleted `mission_id`, it MUST be
cleared on successful delete (FR-007) so no stale "resume" is offered for a mission that no
longer exists. No server state — cleared client-side via the existing follow-pointer `clear()`.

## Non-entities (explicitly not touched)

- **Checkpoints** (`~/.agency/checkpoints/`, `<docs_root>/checkpoints/`): separate crash-recovery
  store with its own `DELETE /api/checkpoints/{id}`; unaffected by mission delete.
- **Project-local `missions/<id>/` mirror** and **`studio_assets/missions/<id>/` render cache**:
  derived artifacts, not the listing source; out of scope for FR-005 correctness (optional
  future sweep).
