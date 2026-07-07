# Feature Specification: S8 Settings

**Feature Branch**: `014-s8-settings`

**Created**: 2026-07-07

**Status**: Draft

**Input**: User description: "lance le cycle S8 Settings"

## User Scenarios & Testing *(mandatory)*

S8 is the final child spec of Brick 7 ("the magic box"). It replaces the current
**Settings "coming soon" placeholder** with a real Settings screen: a single,
calm place where a non-technical user manages their studio preferences, confirms
the studio is healthy and local-first, and jumps to model selection — without ever
touching a terminal or a config file.

### User Story 1 - Manage core studio preferences in one place (Priority: P1)

A non-technical user opens **Settings** to set how the studio behaves for them:
the **interface language** (English / French) and the **default working context**
(client / project / campaign) that new missions and briefs start from. They change
a preference, see it confirmed immediately, and find it still applied the next time
they open the studio.

**Why this priority**: This is the reason Settings exists — one predictable home
for the preferences that shape every other screen. Without it, preferences stay
scattered (language in the top bar, context selected ad hoc) and the "one entry
point, sensible defaults" promise is incomplete. It is the minimum viable Settings
screen and delivers value on its own.

**Independent Test**: Open Settings, change the language and the default working
context, reload the studio, and confirm both choices persisted and are reflected
everywhere they apply (top-bar language control, context used by brief/missions).

**Acceptance Scenarios**:

1. **Given** the Settings screen is open, **When** the user switches the interface
   language, **Then** the whole interface updates immediately and the top-bar
   language control shows the same choice (the two never disagree).
2. **Given** the Settings screen is open, **When** the user sets a default working
   context (client/project/campaign), **Then** the choice persists across sessions
   and a newly started brief/mission opens pre-scoped to that context.
3. **Given** a preference was just changed, **When** the change is applied, **Then**
   the screen gives an honest visual confirmation of the new state and never shows a
   false "saved" if persistence did not actually happen.

---

### User Story 2 - See the studio is healthy and local-first (Priority: P2)

The same user wants reassurance that the studio is working and that their data stays
on their machine. Settings shows a **read-only status/about panel**: connection state
to the local studio server, the application version, where their data lives (local),
and a short summary of the currently selected models — with a direct link to the
Model & Capability panel for changes.

**Why this priority**: Trust and orientation. A non-technical user needs to see, in
plain language, that the studio is connected, local-first, and which models are in
play — without reading logs. It builds on P1 but is not required for the MVP.

**Independent Test**: Open Settings with the server running and confirm the status
panel shows a connected state, the version, the local data location, and a model
summary whose link opens the Model & Capability panel; stop the server and confirm
the panel honestly shows an offline/unknown state instead of breaking the screen.

**Acceptance Scenarios**:

1. **Given** the studio server is reachable, **When** the user opens Settings,
   **Then** the status panel shows a connected state, the application version, and
   the local location/scope where their data is stored.
2. **Given** the user wants to change models, **When** they use the model summary's
   link, **Then** they land on the Model & Capability panel (S7) — Settings does not
   duplicate that management UI.
3. **Given** the studio server is unreachable, **When** the user opens Settings,
   **Then** server-dependent status shows an honest offline/unknown state while
   local preference controls still work.

---

### User Story 3 - Reset preferences and recover (Priority: P3)

The user wants a clean slate — return language and context to defaults (for example
before handing the machine to a colleague) — without losing any of their real work.
Settings offers a guarded **reset local preferences** action.

**Why this priority**: A safety net and a courtesy, not core to daily use. It matters
for shared machines and recovering from a confusing state, but the studio is fully
usable without it.

**Independent Test**: With deliverables, missions, and a saved model selection
present, reset local preferences from Settings, confirm language and context return
to defaults, and confirm every server-side deliverable, mission, and model selection
is still intact.

**Acceptance Scenarios**:

1. **Given** custom preferences are set, **When** the user resets local preferences
   and confirms, **Then** language and default context return to their defaults.
2. **Given** the reset action is offered, **When** the user resets, **Then**
   server-side deliverables, missions, and persisted model selections are NOT
   deleted.
3. **Given** the reset confirmation is shown, **When** the user dismisses it,
   **Then** nothing changes.

---

### Edge Cases

- **Server unreachable on open**: the status/about panel shows an honest
  offline/unknown state; purely local preference controls (language) remain usable.
- **Local preference storage unavailable/disabled**: preferences fall back to
  session defaults, the screen still works, and it tells the user honestly that
  changes will not persist.
- **Stale default context**: the saved default client/project/campaign points to
  something that no longer exists (deleted since) — Settings shows it as stale and
  lets the user clear or reselect it, rather than silently applying a dead value.
- **Language changed in two places**: changing language in Settings and via the
  top-bar control keep a single source of truth and never drift apart.
- **Reset dismissed**: dismissing the reset confirmation leaves every preference
  untouched.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Settings screen MUST replace the existing "coming soon"
  placeholder and be reachable from the studio's primary navigation.
- **FR-002**: Users MUST be able to view and change the interface language
  (English / French) from Settings; the choice MUST take effect immediately, persist
  across sessions, and stay in sync with the existing top-bar language control as a
  single source of truth (the two controls never disagree).
- **FR-003**: Users MUST be able to view and set the default working context
  (client / project / campaign) that seeds new missions and briefs; the selection
  MUST persist and reflect the same context used elsewhere in the studio.
- **FR-004**: Settings MUST present a read-only system/status panel showing at least:
  the connection state to the local studio server, the **studio version**, and the
  studio's **primary local data folder** (where documents, settings, knowledge, and
  model-selection preferences are kept). This folder MUST be labeled for what it is;
  the panel MUST NOT imply it contains every produced deliverable — missions and
  produced media may reside in separate working/output folders.
- **FR-005**: Settings MUST summarize the current model/capability selection and link
  directly to the Model & Capability panel (S7) rather than duplicating that
  management interface.
- **FR-006**: Users MUST be able to reset locally stored preferences to defaults from
  Settings, guarded by an explicit confirmation, WITHOUT deleting server-side
  deliverables, missions, or persisted model selections.
- **FR-007**: Settings MUST NOT introduce any global control that bypasses or weakens
  the per-mission network/research opt-in; any network-related preference is a
  suggested default only and is still confirmed per mission.
- **FR-008**: Every Settings surface MUST be fully available in English and French,
  keyboard-operable, and screen-reader accessible (WCAG-AA), consistent with the
  other shipped studio screens.
- **FR-009**: Settings MUST degrade gracefully when the studio server is unreachable:
  purely local preference controls keep working, and server-dependent status shows an
  honest offline/unknown state instead of failing the whole screen.
- **FR-010**: Any preference change MUST give immediate, honest visual confirmation
  of the resulting state — no silent no-op, and no false "saved" when persistence did
  not succeed.

### Key Entities

- **Studio Preference**: a user-scoped, locally persisted setting the user controls
  from Settings — e.g. interface language, default working context. Has a stable
  identity, a current value, and a known default value to reset to.
- **System Status (read-only view)**: an at-a-glance, non-persisted summary assembled
  from existing studio signals — server connection state, application version, local
  data location/scope, and current model-selection summary. Settings displays it; it
  does not own or store it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A non-technical user can find and change their language and default
  working context from Settings in under 60 seconds, without touching a terminal or
  editing any config file.
- **SC-002**: 100% of Settings controls, labels, and status text render in both
  English and French with no missing or fallback-only strings.
- **SC-003**: After setting a default working context in Settings, a newly started
  brief or mission opens pre-scoped to that context on the first attempt.
- **SC-004**: Resetting preferences returns language and context to defaults while
  100% of server-side deliverables, missions, and model selections remain intact
  (verified before and after).
- **SC-005**: With the studio server unreachable, the Settings screen still renders
  and lets the user change local preferences — no crash and no blank screen.
- **SC-006**: The Settings screen passes the same accessibility bar as the shipped
  screens: fully keyboard reachable with no critical accessibility violations.

## Assumptions

- **Presentation/consolidation layer.** Following the established Brick 7 child-spec
  pattern (S2–S7), S8 is a front-end presentation and consolidation layer over
  existing endpoints and the studio's existing client-side preference storage. It
  introduces no new server-side settings store of its own.
- **Model selection is owned by S7.** The Model & Capability panel (S7) remains the
  place to change models; Settings summarizes and links to it rather than
  re-implementing it.
- **Appearance/theme is out of scope for S8.** There is no existing theme system; the
  studio follows the operating-system appearance. A light/dark toggle is deferred.
- **Per-mission network opt-in is unchanged.** The security invariant (network only
  via explicit per-mission opt-in) is preserved; Settings never adds a global network
  bypass.
- **Existing sources of truth are reused.** The current language control, client-context
  selection, and system/health signals are the single sources of truth that Settings
  surfaces — it does not fork them.
- **Local persistence uses the studio's existing preference storage** already used for
  language and client context; where that storage is unavailable, the screen degrades
  to session-only behavior and says so.
- **"Where your data lives" is the primary data folder, honestly labeled.** The studio
  uses more than one local folder (a primary data directory for
  documents/settings/knowledge, plus working/output folders for missions and produced
  media). S8's System panel shows the primary data directory the server can
  authoritatively report, labeled as such — it does not enumerate every deliverable
  path (deferrable to a later iteration).
