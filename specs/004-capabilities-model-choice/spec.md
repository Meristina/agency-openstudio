# Feature Specification: Capabilities & Model Choice (the end of env-only)

**Feature Branch**: `004-capabilities-model-choice`

**Created**: 2026-07-04

**Status**: Draft

**Input**: User description: "Brick 4 — Capabilities & model choice (the end of env-only). Today a user can only pick which models and tools the studio uses by setting environment variables and restarting — invisible, terminal-bound, and undiscoverable. Brick 4 makes capability and model selection a first-class, in-interface choice: the user sees every model and tool the studio can run, knows which are free vs paid and available vs unavailable on their machine, picks the ones they want, and that choice persists — all without touching a terminal. Environment variables remain a valid override for power users."

## Clarifications

### Session 2026-07-05

- Q: For PAID entries, what should AVAILABLE mean? (FR-005) → A: Presence-only — API key env var set + declared runtime support; no network or validity check ever.
- Q: Where and in what format should the persisted selection store live? (FR-007) → A: A dedicated JSON file (family → entry id) in the studio's server-side data directory, written atomically.
- Q: Is the production-tools (OpenMontage) family selectable like the model families, or inventory-only in this brick? → A: Inventory-only — tier, cost class, and availability are shown, but no default selection; pipelines keep choosing tools per task.
- Q: How should cost class be shown for HYBRID-tier production tools? → A: Dual badge, tier-derived — LOCAL/LOCAL_GPU → FREE, API → PAID, HYBRID → both (FREE via the local path, PAID via the API path).
- Q: What does "don't forget MCP" mean for this brick's scope? → A: Add MCP servers as a ninth inventory family, enumerated from the studio's MCP configuration with passive availability checks and cost class; inventory-only — no selection in this brick.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the honest capability inventory (Priority: P1)

A studio user (non-technical) opens the interface and sees a single, complete inventory
of everything the studio can run, grouped by capability: image generation, video
generation, visual analysis, embedding, knowledge-graph extraction, speech-to-text,
text-to-speech, the OpenMontage production tools, and the configured MCP servers. For every entry they can tell at
a glance: is it FREE or PAID (requires an API key / billed service), and is it
AVAILABLE right now on this machine or UNAVAILABLE — and if unavailable, exactly why
(missing optional install, missing key, unsupported runtime) and what concrete step
would enable it.

**Why this priority**: Discovery is the foundation of the whole brick. Without an
honest inventory there is nothing to select from, and today this information is
invisible outside the terminal. This story alone already delivers value: the user
finally *sees* what their studio can do.

**Independent Test**: Can be fully tested by opening the capabilities view on a machine
with a known mix of installed/missing extras and present/absent keys, and verifying
every capability family appears with correct cost class, availability, and
unavailability reasons — without setting any environment variable or opening a
terminal.

**Acceptance Scenarios**:

1. **Given** a fresh studio with no optional extras installed and no API keys set,
   **When** the user opens the capabilities view, **Then** every capability family
   (image, video, visual, embedding, knowledge-graph extraction, speech-to-text,
   text-to-speech, production tools, MCP servers) is listed, and every entry that needs a missing
   extra or key shows UNAVAILABLE with a human-readable reason and the concrete
   enablement step (install hint or key name).
2. **Given** a machine where one local model's optional dependency is installed,
   **When** the user opens the capabilities view, **Then** that entry shows AVAILABLE
   and FREE while its uninstalled siblings still show UNAVAILABLE with reasons.
3. **Given** a paid entry whose API key is present in the environment, **When** the
   user opens the capabilities view, **Then** the entry shows PAID and AVAILABLE, and
   the key's value is never displayed, transmitted, or logged — only its presence.
4. **Given** the production-tool catalog, **When** the user browses it, **Then** each
   tool shows its native runtime tier (LOCAL / LOCAL_GPU / API / HYBRID) alongside
   cost class and availability.

---

### User Story 2 - Pick a default model per capability, and have it stick (Priority: P2)

For each model family (production tools and MCP servers excluded — they are
inventory-only), the user selects which available model the studio should use as its
default. The choice takes effect without a restart, is remembered across
restarts, and is visible the next time the user opens the view. If the user tries to
select an unavailable entry, the interface surfaces the exact reason and the concrete
step to enable it, instead of failing silently.

**Why this priority**: Selection is the "choice" half of the brick and the direct end
of env-only configuration, but it requires the inventory (P1) to exist first.

**Independent Test**: Can be fully tested by selecting an available model for one
capability, restarting the studio, and confirming the selection is still active —
plus attempting to select an unavailable entry and confirming a clear, actionable
explanation appears.

**Acceptance Scenarios**:

1. **Given** a capability with at least two available entries, **When** the user
   selects a non-default entry as their default, **Then** the interface confirms the
   change and the inventory reflects the new active default immediately.
2. **Given** a persisted selection, **When** the studio is stopped and started again,
   **Then** the same selection is still active without any user action.
3. **Given** an unavailable entry, **When** the user attempts to select it, **Then**
   the interface refuses the selection and shows the machine-detected reason plus the
   concrete enablement step (install hint or required key name) — never a silent
   failure or a crash.
4. **Given** a previously selected entry that has since become unavailable (extra
   uninstalled, key removed), **When** the user opens the capabilities view, **Then**
   the stale selection is clearly flagged as no longer available, with its reason,
   and the studio behaves as if no selection were made for that capability (falls
   back to its documented default) rather than erroring.

---

### User Story 3 - Missions honor the persisted choice; env vars still win (Priority: P3)

A mission (or any studio operation that consumes a model) automatically uses the
user's persisted selection — no environment variable required. When a power user *has*
set the corresponding environment variable, the environment variable takes precedence
over the persisted selection, and this override order is documented.

**Why this priority**: This closes the loop — the selection must actually drive
behavior to mean anything — but it depends on both the inventory (P1) and the
selection store (P2) existing.

**Independent Test**: Can be fully tested by persisting a selection, running an
operation that consumes that capability with no environment variables set, and
verifying the selected model is the one used; then setting the corresponding
environment variable and verifying it wins.

**Acceptance Scenarios**:

1. **Given** a persisted selection for a capability and no corresponding environment
   variable, **When** an operation consuming that capability runs, **Then** the
   persisted selection is the model/tool actually used.
2. **Given** a persisted selection *and* a corresponding environment variable set to a
   different entry, **When** the operation runs, **Then** the environment variable's
   choice is used, and the interface indicates that an environment override is
   currently active for that capability.
3. **Given** no persisted selection and no environment variable, **When** the
   operation runs, **Then** today's built-in default behavior applies unchanged.

---

### Edge Cases

- What happens when a capability family has zero available entries (e.g. no extras
  installed at all)? The family still appears, all entries show UNAVAILABLE with
  reasons, and no selection is possible — the view must not hide the family or error.
- What happens when the production-tool catalog cannot be read (vendored catalog
  missing or unreadable)? The production-tools family shows an unavailable state with
  a reason; the rest of the inventory still renders.
- What happens when the MCP configuration is missing, empty, or unreadable? The MCP
  family shows an empty or unavailable state with a reason; the rest of the
  inventory still renders.
- What happens when the persisted selection store is missing, empty, or corrupted?
  The studio treats it as "no selections made", falls back to documented defaults,
  and the user can re-select; it never crashes or blocks startup.
- What happens when a selection references an entry id that no longer exists in any
  registry? It is treated like an unavailable stale selection (flagged, fallback to
  default), not an error.
- What happens when an API key is present but invalid/expired? The entry still shows
  AVAILABLE (availability is presence-only per FR-005); the error surfaces at actual
  use time. The system never validates a key by making a hidden paid call.
- What happens when two clients edit selections near-simultaneously? Last write wins;
  the view reflects the stored state on next load — no partial/merged state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose a single aggregated inventory covering every
  capability family the studio has: image, video, visual analysis, embedding,
  knowledge-graph extraction, speech-to-text, text-to-speech, the OpenMontage
  production tools, and the configured MCP servers.
- **FR-002**: Every inventory entry MUST carry: a stable identifier, a human-readable
  label, its capability family, a cost class (FREE, PAID, or — for HYBRID-tier
  production tools — both), an availability status
  (AVAILABLE or UNAVAILABLE), and — when unavailable — a machine-readable reason plus
  a human-actionable enablement step (install hint or required key name).
- **FR-003**: Production-tool entries MUST additionally carry their native runtime
  tier (LOCAL / LOCAL_GPU / API / HYBRID). Their cost class is derived from the
  tier: LOCAL and LOCAL_GPU are FREE, API is PAID, and HYBRID entries carry both
  badges (FREE via the local path, PAID via the API path).
- **FR-004**: Speech-to-text and text-to-speech MUST be promoted to first-class
  registries so they are enumerated, described, and selected exactly like the other
  model families (they are currently ad-hoc).
- **FR-005**: Availability determination MUST be safe and passive: presence checks for
  optional installs, presence-only checks for API keys (never the key's value), and
  declared runtime support — with no network calls and no paid calls. For PAID
  entries, AVAILABLE means exactly "required key present AND runtime supported";
  key validity is never probed — an invalid or expired key still reports AVAILABLE,
  and failure surfaces only when the user actually runs the paid operation.
- **FR-006**: Users MUST be able to select, per model family (image, video, visual
  analysis, embedding, knowledge-graph extraction, speech-to-text, text-to-speech),
  one entry as the persisted default, from the interface, without touching a
  terminal or restarting. The production-tools family is inventory-only in this
  brick: it is browsable with tier, cost class, and availability, but carries no
  default selection — pipelines continue choosing tools per task.
- **FR-007**: The persisted selection MUST survive studio restarts and be stored
  server-side as a dedicated JSON document (capability family → entry identifier)
  in the studio's data directory, written atomically. Precedence versus environment
  variables follows the resolution order in FR-009 (env var always wins).
- **FR-008**: Selecting an unavailable entry MUST be refused with the reason and
  enablement step surfaced to the user; it MUST never fail silently or crash.
- **FR-009**: Operations that consume a capability MUST resolve the active model/tool
  in this documented order: environment variable (if set) → persisted user selection
  (if present and available) → built-in default. With neither env var nor selection,
  behavior MUST be byte-identical to today.
- **FR-010**: When an environment override is active for a capability, the interface
  MUST indicate that the persisted selection is currently overridden.
- **FR-011**: A persisted selection whose entry has become unavailable MUST be flagged
  as stale in the interface and skipped at resolution time (fallback per FR-009),
  never causing an error.
- **FR-012**: An absent optional extra MUST always yield a clean
  unavailable-with-hint state — never a crash, a server error, or a hidden entry.
- **FR-013**: API key values MUST never be returned by any interface surface,
  persisted in the selection store, or written to logs; only boolean presence and the
  key's environment variable name may be exposed.
- **FR-014**: The entire inventory and selection surface MUST be fully exercisable in
  the offline test suite: no model installed, no key present, no network, all
  registries, the production-tool catalog, and the MCP configuration stubbed at
  their boundaries.
- **FR-015**: The inventory and selection surfaces MUST respect existing security
  invariants: local-only binding, no permissive cross-origin policy, path guards on
  any served file.
- **FR-016**: The inventory MUST NOT add new model backends or generation
  capabilities; it only describes and selects what already exists.
- **FR-017**: MCP servers MUST appear as their own inventory family, enumerated from
  the studio's MCP configuration. Each entry MUST carry cost class and passive
  availability (configuration entry present, launch command/executable present) with
  an enablement hint when unavailable. The family is inventory-only in this brick:
  no default selection, and mission MCP attachment behavior is unchanged.

### Key Entities

- **Capability Family**: One of the studio's model/tool domains (image, video,
  visual, embedding, knowledge-graph extraction, speech-to-text, text-to-speech,
  production tools, MCP servers). The unit at which a default is selected — except
  production tools and MCP servers, which are inventory-only (no default selection
  in this brick).
- **Capability Entry**: A single selectable model or tool within a family —
  identifier, label, family, cost class, availability (+ reason and enablement step
  when unavailable), and runtime tier where applicable.
- **Capability Inventory**: The aggregated, read-only view of all entries across all
  families, reflecting the current machine's real state at the time it is read.
- **Selection Store**: The server-side persisted mapping of capability family → chosen
  entry identifier, editable from the interface, surviving restarts. Persisted as a
  dedicated JSON document in the studio's data directory, written atomically.
- **Resolution Order**: The documented precedence chain (environment variable →
  persisted selection → built-in default) used whenever an operation needs a model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can enumerate every capability family and every entry's cost
  class and availability from the interface alone — zero terminal commands, zero
  environment variables — within 2 minutes of opening the studio.
- **SC-002**: 100% of unavailable entries display both a reason and a concrete
  enablement step; zero entries fail silently or render as an error state.
- **SC-003**: A selection made in the interface is still active after a full studio
  restart, with no user re-configuration, in 100% of restarts.
- **SC-004**: An operation consuming a capability uses the persisted selection with
  zero environment variables set; with the corresponding environment variable set, the
  environment variable wins in 100% of cases, and the override is visible in the
  interface.
- **SC-005**: On a machine with no optional extras and no keys, the full inventory
  and selection surface renders and remains navigable with zero crashes and zero
  server errors.
- **SC-006**: The complete inventory/selection behavior is verified by the offline
  test suite with no model, no key, and no network — suite stays green.
- **SC-007**: No interface response, stored file, or log line ever contains an API
  key value (verified by test assertion across the new surfaces).

## Assumptions

- The existing capability registries (image, video, visual, embedding,
  knowledge-graph extraction), the OpenMontage tool catalog, and the studio's MCP
  configuration are the single sources of truth for what exists; this feature
  aggregates them and adds none.
- "Selection takes effect without restart" applies to new operations started after
  the change; operations already in flight finish with the model they started with.
- Cost class is a static property declared by each entry (local = free; keyed/billed
  service = paid; HYBRID-tier production tools carry both badges); this brick does
  not meter or estimate actual spend.
- Key management remains environment-based; the interface reads key presence only.
  Helping the user *set* a key is out of scope for this brick.
- Per-mission model overrides in the interface are a later brick; this brick sets the
  persisted studio-wide default only.
- Cross-platform runtime expansion is Brick 5; entries unsupported on the current
  platform simply report UNAVAILABLE with an "unsupported runtime" reason.
- The inspector/veto contract and the verifiable-source postcondition (Brick 3) are
  untouched by this feature.
- Concurrent selection edits are resolved last-write-wins; the studio is a
  single-user local tool, so stronger coordination is unnecessary.
