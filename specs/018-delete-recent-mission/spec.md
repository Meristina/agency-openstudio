# Feature Specification: Delete a recent mission from the home list

**Feature Branch**: `018-delete-recent-mission`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "Reprendre le travail / Travaux récents … [list of recent delivered missions] … ajoute supprimer si je veux" — from the studio home screen, add a way to delete a recent mission the user no longer wants.

## User Scenarios & Testing *(mandatory)*

The studio home shows a **Recent work** ("Travaux récents") list of the user's recent
missions, each with its goal text and a status ("Livré"/delivered). Today an item can only
be opened — there is no way to remove one. Over time the list fills with test runs, throwaway
goals ("goal", "goal"), and finished work the user no longer cares about. This feature lets a
user remove an item they no longer want.

### User Story 1 - Remove an unwanted item from Recent work (Priority: P1)

From the Recent work list, the user removes a mission they no longer want, and it disappears
from the list.

**Why this priority**: This is the whole request. Without it there is no feature; with just
this, the user can already declutter their home screen — a viable MVP.

**Independent Test**: Open the home screen with several recent items, delete one, and confirm
it is gone from the list and does not return after reloading the home screen.

**Acceptance Scenarios**:

1. **Given** the Recent work list has several delivered missions, **When** the user activates
   delete on one item and confirms, **Then** that item is removed from the list and the
   others remain, with no manual page refresh needed.
2. **Given** a mission was just deleted, **When** the user reloads the home screen, **Then**
   the deleted mission does not reappear.
3. **Given** the user deletes the only remaining item, **When** the deletion completes,
   **Then** the list shows the normal empty state.

---

### User Story 2 - Guard against accidental deletion (Priority: P2)

Deletion is permanent, so the user must confirm before anything is removed, and can back out.

**Why this priority**: Deletion destroys the user's own work; a single misclick must not lose
a mission. Safety is required for the feature to be trustworthy, but it layers on top of the
P1 removal rather than being independently valuable on its own.

**Independent Test**: Activate delete on an item, then cancel — confirm nothing is removed;
activate delete again and confirm — confirm the item is removed.

**Acceptance Scenarios**:

1. **Given** the user activates delete on an item, **When** they cancel the confirmation,
   **Then** the item is left untouched and still opens normally.
2. **Given** the user activates delete on an item, **When** they confirm, **Then** — and only
   then — the item is removed.

---

### User Story 3 - Deletion is consistent everywhere the mission appears (Priority: P3)

A mission deleted from Recent work also disappears from the Library (the "See all" view) and
any other listing of saved missions.

**Why this priority**: Consistency prevents the confusing state where a "deleted" mission
still shows elsewhere. Valuable, but the core decluttering benefit (P1) already lands on the
home screen without it.

**Independent Test**: Delete a mission from Recent work, then open the Library — confirm the
same mission is absent there too.

**Acceptance Scenarios**:

1. **Given** a mission is deleted from Recent work, **When** the user opens the Library,
   **Then** that mission is not listed.
2. **Given** a mission is deleted, **When** any saved-missions listing is requested, **Then**
   the deleted mission is not included.

---

### Edge Cases

- **Deleting the followed/resumable mission**: if the deleted mission is the one the home
  "resume" affordance currently points to, that pointer is cleared so no stale resume or
  "reprendre" is offered for a mission that no longer exists.
- **A running (non-terminal) mission**: an in-progress mission is not deletable; delete is
  offered only for saved, terminal (delivered/failed/cancelled) missions.
- **Already gone / double delete**: deleting a mission that was already removed (e.g. a stale
  list, a repeated click) resolves as success — the end state (mission absent) is the same;
  the user is never shown a confusing error for a mission that is already gone.
- **Deletion failure** (storage/permission error): the item is left intact and the user sees
  a clear, understandable error rather than a silent no-op or a falsely-removed item.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each item in the Recent work list MUST present a clearly-labelled delete
  control, distinct from the control that opens the item.
- **FR-002**: Activating delete MUST require an explicit confirmation step before anything is
  removed; the user MUST be able to cancel and leave the item untouched.
- **FR-003**: On confirmation, the system MUST permanently remove the selected mission's saved
  record.
- **FR-004**: After a successful deletion, the item MUST disappear from the Recent work list
  without requiring the user to manually reload the page.
- **FR-005**: A deleted mission MUST NOT appear in any other listing of saved missions
  (including the Library "See all" view).
- **FR-006**: If deletion fails, the system MUST leave the mission intact and surface a clear
  error message; it MUST NOT show the item as removed when it was not.
- **FR-007**: Deleting a mission that the home resume/follow pointer currently references MUST
  clear that pointer, so no stale resume is offered afterwards.
- **FR-008**: The delete control MUST be offered only for saved missions in a terminal state;
  a mission still running MUST NOT be deletable.
- **FR-009**: Deleting a mission that is already absent MUST resolve as success (idempotent),
  leaving the list in the same "mission absent" state without an error.
- **FR-010**: The delete control and its confirmation MUST be available in both supported
  interface languages (English and French).
- **FR-011**: The delete flow MUST be operable by a non-technical user — a single obvious
  control plus a plain-language confirmation — and keyboard/assistive-technology accessible,
  consistent with the studio's "simple for the end user" principle.

### Key Entities *(include if feature involves data)*

- **Saved mission (deliverable)**: the stored record of a completed mission — its goal,
  terminal status, and identifier — surfaced both in Recent work and in the Library. This is
  the unit a delete removes.
- **Resume/follow pointer**: the client-side reference to the most-recently-followed mission,
  used to offer "resume". It must be invalidated when its target mission is deleted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can remove an unwanted recent item in at most two deliberate steps
  (activate delete, then confirm) without leaving the home screen.
- **SC-002**: 100% of confirmed deletions remove the mission from every listing surface
  (Recent work and Library) within one refresh cycle — no stale entries remain.
- **SC-003**: No mission is ever removed without an explicit confirmation (zero single-action
  deletions).
- **SC-004**: A deletion failure never removes the mission and always presents an
  understandable error — 0% of failures result in a falsely-removed or silently-lost item.
- **SC-005**: The delete flow behaves identically and is fully labelled in both English and
  French.

## Assumptions

- **Permanent delete, not archive**: "supprimer" is taken to mean permanent removal of the
  mission's saved record. Because the studio is local-first and single-operator, there is no
  trash/undo; the required confirmation (FR-002) is the safety net. (Revisit only if the user
  later asks for an archive/trash instead.)
- **Only saved, terminal missions are deletable** (FR-008); a live/in-flight mission is
  managed through its own cancel/resume controls, not deleted here.
- **Existing storage and listing are reused**: deletion removes the same saved-mission record
  that the current Recent work and Library listings read, so all surfaces stay consistent
  without a separate index.
- **Security carries over from existing mission access**: deletion is confined to the mission
  store and keyed by mission identifier with the same path-safety guarantees as today's saved
  mission reads (no traversal outside the store, loopback-only server) — deletion adds no new
  external surface.
- **Scope is the studio GUI home surface** the user pointed at (Recent work), plus the
  consistency guarantee into the Library; a bulk "clear all" is out of scope for this feature.
