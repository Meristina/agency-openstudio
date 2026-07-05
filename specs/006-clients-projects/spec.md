# Feature Specification: Clients & Projects (Brick 6)

**Feature Branch**: `006-clients-projects`

**Created**: 2026-07-05

**Status**: Draft

**Input**: User description: "Brick 6 — Clients & projects. Today every mission is a flat, standalone entry in the store; the only organizing hook is the existing `project_root` stamp, and history is one undifferentiated list. A real agency works for clients, on projects, under campaigns — and Brick 6 introduces that taxonomy ABOVE the store without rewriting it. Add a client / project / campaign hierarchy layered on top of the existing store (the `project_root` stamp is the anchor point): new dossier fields that tag each mission and its deliverables with their client, project, and campaign; grouping/listing endpoints so history can be queried and browsed by client and by campaign rather than as a flat feed; and a soft, non-destructive migration that folds every existing mission into the new taxonomy (a sensible default project) without losing or rewriting any historical dossier. This is additive and store-compatible — no change to agency-kit's mission loop, no new required fields that would break older missions, existing endpoints keep working. The offline suite stays green everywhere, including a migration test over a fixture of pre-Brick-6 missions. Done when: history is browsable by client and by campaign, and every deliverable belongs to a project."

## Clarifications

### Session 2026-07-05

- Q: Does Brick 6 include user-facing GUI changes in the web studio, or server endpoints only (GUI deferred to Brick 7)? → A: Minimal GUI included — the mission-start form gains client / project / campaign fields and the history view gains grouped browsing (by client, by campaign); the full visual redesign remains Brick 7.
- Q: How is the taxonomy persisted — for new missions and for pre-Brick-6 missions? → A: Hybrid — new missions carry optional client/project/campaign fields in their own dossier; a side-band override registry (kept outside the historical records) can re-assign any mission and takes precedence; anything else resolves by derivation from the existing `project_root` stamp. Resolution order: override > dossier fields > derived default.
- Q: What default names does the operator see for a workspace's default project and for stamp-less missions? → A: The default project is named after the workspace directory (e.g. "agency-openstudio"), under the implicit client "Studio"; missions with no workspace stamp group under "Unassigned".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tag a mission with its client, project, and campaign (Priority: P1)

An agency operator launching a mission states who the work is for: they pick (or type)
a client, a project under that client, and optionally a campaign under that project.
The finished mission and every deliverable it produces carry those tags, so from that
moment the work is attributable — "this video belongs to the Spring Launch campaign of
Acme's Rebrand project" — instead of being one more anonymous entry in a flat feed.
If the operator states nothing, the mission still runs exactly as today and lands in a
sensible default project for the current workspace.

**Why this priority**: Tagging is the foundation — browsing (Story 2) and migration
(Story 3) only have meaning once missions can carry taxonomy. It is also the only part
that touches the mission-creation path, so proving it is additive and non-breaking
first de-risks everything else.

**Independent Test**: Can be fully tested by starting one mission with client /
project / campaign values and one without, then loading both saved missions and
confirming the first carries the exact tags on the mission and its deliverables, and
the second landed in the default project with behavior otherwise identical to today.

**Acceptance Scenarios**:

1. **Given** a new mission brief, **When** the operator supplies a client, a project,
   and a campaign, **Then** the saved mission record and its deliverables carry those
   three tags exactly as given.
2. **Given** a new mission brief, **When** the operator supplies no taxonomy values,
   **Then** the mission runs and saves exactly as before this feature, and it is
   attributed to the default project of the current workspace.
3. **Given** a new mission brief, **When** the operator supplies only a client (no
   project, no campaign), **Then** the mission is attributed to that client's default
   project and no campaign, without error.
4. **Given** a mission tagged with taxonomy values, **When** the mission completes and
   its deliverables are produced, **Then** every deliverable is attributable to the
   same client, project, and campaign as its mission.

---

### User Story 2 - Browse history by client and by campaign (Priority: P2)

An agency operator opens mission history and, instead of one undifferentiated list,
can browse it grouped: all clients with their projects and campaigns, and within each,
the missions and deliverables that belong to it. They can ask "show me everything we
did for Acme" or "show me the Spring Launch campaign" and get exactly that slice of
history — while the plain flat history they know keeps working unchanged.

**Why this priority**: This is the visible payoff of the taxonomy — the "browsable by
client and by campaign" half of the done-when. It depends on Story 1's tags existing
but delivers standalone value the moment any mission is tagged.

**Independent Test**: Can be fully tested by seeding a history containing missions
tagged with two different clients (one with a campaign) plus one untagged mission,
then querying the grouped views and confirming each mission appears exactly once,
under the right client/project/campaign, and the untagged one under the default
project.

**Acceptance Scenarios**:

1. **Given** a history with missions tagged for two different clients, **When** the
   operator requests history grouped by client, **Then** each client appears with
   exactly its own missions, and no mission appears under the wrong client.
2. **Given** a history with missions tagged with campaigns, **When** the operator
   requests a single campaign's history, **Then** only the missions and deliverables
   of that campaign are returned.
3. **Given** any history, **When** the operator requests the pre-existing flat history
   view, **Then** it returns the same missions it returned before this feature, with
   no missions hidden or duplicated by the taxonomy.
4. **Given** a query for a client or campaign that does not exist, **When** the
   operator requests its history, **Then** they receive an empty result, not an error.
5. **Given** the taxonomy exists, **When** the operator asks for the list of known
   clients (or of one client's projects and campaigns), **Then** they receive the
   list with a count of missions in each group.

---

### User Story 3 - Existing history folds into the taxonomy untouched (Priority: P3)

An operator who has been using the studio since before this feature upgrades and opens
the new grouped history. Every one of their old missions is already there — folded
into a sensible default project anchored on the workspace each mission was recorded
in — and not a single historical mission record has been lost, modified, or rewritten.
Old missions remain loadable, exportable, and listable exactly as before.

**Why this priority**: Migration is what makes the taxonomy total ("every deliverable
belongs to a project") rather than only-for-new-work. It is P3 because it protects
existing users rather than creating new capability, and it presupposes Stories 1–2.

**Independent Test**: Can be fully tested against a fixture of pre-Brick-6 mission
records (with and without a workspace stamp): after the upgrade, every fixture mission
appears in the grouped views under a default project, and every fixture file on disk
is byte-identical to before.

**Acceptance Scenarios**:

1. **Given** a store of pre-Brick-6 missions, **When** the operator browses the new
   grouped history, **Then** every old mission appears under a sensible default
   project derived from its workspace stamp.
2. **Given** a pre-Brick-6 mission with no workspace stamp at all (legacy global
   missions), **When** the grouped history is browsed, **Then** that mission still
   appears, in the "Unassigned" group, and is not dropped.
3. **Given** a store of pre-Brick-6 missions, **When** the upgrade and any number of
   grouped-history browses have occurred, **Then** every historical mission record on
   disk is unchanged byte-for-byte.
4. **Given** a pre-Brick-6 mission folded into the default project, **When** the
   operator opens it, exports it, or lists it through the pre-existing views,
   **Then** every pre-existing operation behaves exactly as it did before the upgrade.

---

### Edge Cases

- A mission tagged with a campaign but no client or project: the campaign is kept and
  the missing levels fall back to their defaults, so the mission is never rejected.
- Two different clients each have a project with the same name: the projects are
  distinct groups; missions never leak across clients on a name collision.
- The same client typed with different casing or stray whitespace ("Acme " / "acme"):
  treated as one client, so history does not silently split into near-duplicate groups.
- A mission record that is corrupt or unreadable: grouped views skip it exactly as the
  flat history already does, without failing the whole listing.
- A mission whose generated media files were pruned for disk space: the mission still
  appears in its group; taxonomy browsing never depends on media files existing.
- Concurrent histories from multiple workspaces on one machine: grouped views are
  scoped to the current workspace the same way flat history already is.
- An empty store (fresh install): grouped views return an empty taxonomy, not an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Operators MUST be able to attach a client, a project, and a campaign to
  a mission when creating it; each of the three is individually optional.
- **FR-002**: Every mission and every deliverable MUST resolve to exactly one project:
  when no project is stated, the system MUST attribute the mission to a default
  project anchored on the mission's existing workspace stamp (`project_root`) and
  named after the workspace directory, under the implicit client "Studio"; missions
  with no workspace stamp MUST resolve to an "Unassigned" group rather than being
  dropped.
- **FR-003**: Deliverables MUST be attributable to the same client, project, and
  campaign as the mission that produced them.
- **FR-004**: The system MUST provide history views grouped by client and by campaign,
  and MUST allow listing the missions of a single client, a single project, and a
  single campaign.
- **FR-005**: The system MUST provide a listing of known clients, of a client's
  projects, and of a project's campaigns, each with the number of missions it contains.
- **FR-006**: Taxonomy names MUST be matched case-insensitively and
  whitespace-trimmed so one real-world client, project, or campaign never splits into
  near-duplicate groups; the display form MUST preserve what the operator first typed.
- **FR-007**: Every mission saved before this feature MUST appear in the grouped views
  (folded into its default project) without any historical mission record being
  modified, rewritten, or deleted — historical files MUST remain byte-identical.
- **FR-008**: The taxonomy MUST be additive: missions without taxonomy fields MUST
  remain fully loadable, listable, and exportable; no new field is required for a
  mission to run or save; all pre-existing history views and operations MUST keep
  returning what they returned before this feature.
- **FR-009**: The mission execution loop (routing, departments, synthesis, inspection
  and its veto) MUST be entirely unaffected by the presence or absence of taxonomy
  tags.
- **FR-010**: Grouped views MUST be scoped to the current workspace in the same way
  the existing flat history is scoped, and MUST tolerate corrupt or unreadable
  mission records by skipping them, exactly as the flat history does.
- **FR-011**: The offline test suite MUST cover the taxonomy end-to-end with no
  network, CLI agent, Node, or GPU, and MUST include a migration test over a fixture
  of pre-Brick-6 missions asserting both their appearance in the grouped views and
  the byte-identity of their stored records.
- **FR-012**: The studio's mission-start surface MUST offer client, project, and
  campaign inputs, and the studio's history surface MUST offer the grouped views
  (browse by client and by campaign) — both operable by a non-technical user. The
  full visual redesign of these surfaces remains out of scope (Brick 7).
- **FR-013**: A mission's attribution MUST resolve in a fixed order: side-band
  override (if any) > taxonomy fields carried by the mission's own record (new
  missions) > default derived from the mission's workspace stamp. Operators MUST be
  able to re-assign any mission (old or new) to a different client, project, or
  campaign via the override registry — without the mission's historical record being
  modified (FR-007's byte-identity guarantee holds through re-assignment).

### Key Entities

- **Client**: The organization the agency works for. Identified by its name (matched
  case-insensitively, display form preserved). Owns projects. Unattributed work falls
  under the implicit client "Studio".
- **Project**: A body of work for one client; the mandatory attribution level — every
  mission and deliverable belongs to exactly one project. Each workspace has a default
  project (anchored on the existing workspace stamp, named after the workspace
  directory) that absorbs untagged and pre-existing missions; stamp-less missions
  fall into the "Unassigned" group.
- **Attribution override** *(side-band)*: A record outside the mission's stored
  dossier that re-assigns one mission to a client / project / campaign. Takes
  precedence over the mission's own taxonomy fields and over derived defaults;
  never modifies historical records.
- **Campaign**: An optional grouping under a project (e.g. a launch, an event, a
  season). A mission belongs to at most one campaign.
- **Mission** *(existing)*: A single agency run, already persisted with its dossier
  and workspace stamp; gains optional client / project / campaign attribution.
- **Deliverable** *(existing)*: The output of a mission (report, media assets);
  attributable through its mission's taxonomy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can retrieve everything done for one client, or within one
  campaign, in a single query/browse action — no scanning of the flat feed required.
- **SC-002**: 100% of missions — pre-existing and new, tagged and untagged — resolve
  to a project in the grouped views; zero missions are dropped or duplicated.
- **SC-003**: After upgrade and arbitrary browsing, 100% of pre-existing mission
  records on disk are byte-identical to their pre-upgrade state.
- **SC-004**: All pre-existing history operations (flat list, open one mission,
  export) return the same results after the feature as before it, for the same store.
- **SC-005**: The full offline test suite passes on every supported platform with the
  feature present, including the pre-Brick-6 migration fixture test.
- **SC-006**: A non-technical operator can attribute a mission to a client, project,
  and campaign from the normal mission-start surface without touching a terminal or
  editing any file.

## Assumptions

- The taxonomy is lightweight and implicit: clients, projects, and campaigns come into
  existence the first time a mission is tagged with them. No separate CRM-style
  management (create/rename/archive screens, client contact records, budgets) is in
  scope for this brick.
- The existing workspace stamp (`project_root`) is the anchor for defaults: one
  workspace ⇒ one default project, named after the workspace directory, under the
  implicit client "Studio". Missions with no stamp fold into the "Unassigned" group.
- "Non-destructive migration" means historical dossier files are never rewritten:
  pre-existing missions are attributed by derivation from their workspace stamp,
  re-assignments live in a side-band override registry outside the historical
  records, and only new missions carry taxonomy directly in their own records
  (new writes). Resolution order: override > record fields > derived default.
- Hierarchy discipline is client → project → campaign, with client and project
  defaulted when absent and campaign optional; a mission belongs to exactly one node
  at each level it uses.
- Attribution is set at mission creation, and any mission can later be re-assigned
  through the side-band override registry (clarified 2026-07-05); overrides never
  touch the mission's stored record.
- The vendored orchestration library's persistence format and mission loop are not
  modified; the taxonomy layers above the store from the studio side, consistent with
  the "additive over invasive" principle.
- Multi-user access control per client is out of scope: the studio remains a local,
  single-operator tool; taxonomy is organization, not authorization.
