# Feature Specification: Import — The Front Door for the Operator's Own Material (Brick 7 · Screen S5)

**Feature Branch**: `011-s5-import`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "lance le cycle S5 Import" — start the spec-kit cycle for screen S5 (Import) of the Brick 7 magic-box inventory: bring existing material (documents, images, briefs, videos) into the studio as **mission input** attached to a client or a brief, with supported material types, attach-to-brief / attach-to-client flows, and validation & feedback (per the authoritative screen inventory in `specs/007-magic-box/spec.md`).

## Scope

This spec covers the **Import screen (S5)** only: the operator-facing front door through
which a non-technical user brings **their own existing material** into the studio so it can
be used as **input to a production** — reference documents, briefs, brand material, images —
attached to a **client** (the Brick 6 taxonomy) or to a **brief** (S2 Guided Brief). It
replaces the current `import` coming-soon placeholder with a shipped experience: pick
material from the machine, see it validated and confirmed in plain language, associate it
with a client (or leave it unassigned), and have it ready to feed a mission as context — so
a production can build on what the operator already has rather than starting from a blank
page.

It builds on the Brick 7 umbrella foundation (shell, persistent navigation, the shell's
client-context selector, EN/FR i18n, design system, shared loading/empty/error states), on
the Brick 6 client/project/campaign taxonomy, on the S2 Guided Brief (which is where
imported material is attached to a specific production as its input), and on the studio's
**existing local ingestion paths** — the document-knowledge ingestion and the image/visual
ingestion that already accept a file, keep it on the machine, and make it available to a
mission through the mission's existing `knowledge` / `visual` opt-ins. S5 is the friendly,
non-technical surface that composes these existing building blocks into one place; it adds
**no new mission semantics** and changes **no mission-loop behavior** (umbrella FR-016;
Constitution Principles III, V, X).

S5 treats imported material as **source input**, strictly distinct from a produced
**deliverable**: importing a file never produces a deliverable, and imported material never
appears in the S4 Deliverable Library as one. Because imported items are the operator's own
inputs (not agency-produced work), S5 **may** remove them at the operator's request through
the existing delete-ingested-item path — a safe operation that never touches any produced
deliverable (this is the deliberate contrast with S4, which is non-destructive on
deliverables).

Out of scope here: capturing intent (S1) and building the brief itself (S2 — S5 only feeds
material into it); following a running production (S3); browsing finished deliverables (S4 —
S5 is the input side, not the output side); building shareable export bundles (S6); the
capability/model panel (S7 — S5 respects the machine's ingestion capabilities but does not
configure models); settings (S8); creating, editing, or renaming the underlying
clients/projects/campaigns (owned by the Brick 6 taxonomy surface, which S5 reuses as a
selector); **deep import of video and audio** (bringing in a moving-image or sound file as reusable
mission-input material) — the studio has no path that ingests a video or sound file *as
stored, mission-consumable import material* today (audio transcription exists only as a
transient live-session step, not as importable material), so v1 states this limitation
plainly rather than silently accepting material nothing can use (FR-012); and any change whatsoever to the mission loop, routing,
synthesis, asset rendering, the inspector veto loop, or the shape of a saved dossier
(umbrella FR-016; Constitution Principles III, V, X). The existing developer console and its
document/visual management surfaces remain untouched at their secondary location (umbrella
coexistence assumption); S5 is the operator-facing front door, not a replacement for the
console.

## Clarifications

### Session 2026-07-06

- Q: When imported material is attached to a brief, what granularity does v1 support (which items feed a production)? → A: **Whole-set (global on/off)** — directing a brief to use imported material enables the production's existing knowledge/visual capability so the mission draws on the imported material of the relevant kinds; selecting *which specific* items feed one production (per-item curation) is deferred beyond v1, consistent with the shared-store client scope below.
- Q: Should v1 support importing video/audio, given the studio has no path to ingest them as mission-consumable material? → A: **No — defer.** v1 supports documents and images only; the video/audio limitation is stated plainly (FR-012). No new ingestion capability is built.
- Q: Does attaching material to a client isolate a mission's context to that client's material, or is it organizational metadata? → A: **Organizational metadata** over the studio's shared local stores; it does not isolate a mission's context to only that client's material in v1. True per-client context isolation is a future refinement (no mission-loop change in v1).
- Q: Can the operator remove imported source material in v1? → A: **Yes — removable** through the existing delete-ingested-item path; removal affects only the imported source material and never any produced deliverable (FR-009).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bring my own material in and see it ready to use (Priority: P1)

An agency operator has material they already own — a client's existing brand guide, a prior
strategy PDF, a brief they wrote in another tool, reference images — and wants the studio to
build on it. They open Import, choose one or more files from their machine, and each is
checked and brought in with clear, plain-language feedback: what it is, that it was accepted
(or, if not, exactly why — unsupported kind, too large, unreadable), and a confirmation that
it is now available to use as input for a production. If the shell's client-context selector
is set to a client, imported material is associated with that client automatically; if not,
it lands on a clearly labeled **unassigned** shelf it can be attached from later. At no point
does the operator see a file path, a store ID, a MIME type, or a raw error.

**Why this priority**: This is the screen's founding purpose and the reason S5 is on the
inventory — a non-technical user cannot get their existing material into a production without
a simple, forgiving way to bring it in and be told it worked. Bringing-in-and-confirming is
the minimum that makes Import a real, usable screen on its own, independent of the brief or
library.

**Independent Test**: With the app running on a machine whose document and image ingestion
are available, open Import, bring in a supported document and a supported image, and verify
each is accepted with a plain-language confirmation and shown in the imported list; bring in
an unsupported or oversized file and verify it is rejected with a clear, localized reason and
no crash or silent drop; verify that with a client context set the items are associated with
that client, and with none they land on the unassigned shelf.

**Acceptance Scenarios**:

1. **Given** the machine can ingest documents and images, **When** the operator brings in a supported document or image, **Then** it is accepted, shown clear progress, and confirmed in plain language as available to use as production input — with no file path, store ID, or MIME type shown as its identity.
2. **Given** the operator brings in an unsupported kind, an oversized file, or an unreadable file, **When** validation runs, **Then** the item is rejected with a plain-language reason (unsupported kind / too large / unreadable) and a way to try again — never a crash, a silent drop, or a raw technical error.
3. **Given** the shell's client-context selector is set to a client, **When** the operator imports material, **Then** the material is associated with that client automatically; **Given** no client context is set, **When** they import, **Then** the material lands on a clearly labeled unassigned shelf and can be attached to a client later.
4. **Given** a machine where the required ingestion capability is not installed, **When** the operator opens Import or tries to bring in that kind of material, **Then** they see a friendly, localized "not available on this machine — here's how to enable it" message, never a broken control or raw error.
5. **Given** nothing has been imported yet, **When** the operator opens Import, **Then** they see a friendly empty state explaining what Import is for and offering a way to bring material in — never a blank screen or a technical error.

---

### User Story 2 - Feed my material into a production as its input (Priority: P2)

The point of importing is to actually use the material. From the Import screen (or from within
the S2 Guided Brief), the operator directs a **brief** to build on their imported material as
the production's input. They launch the production and it draws on the imported material
through the studio's existing local knowledge/visual capability — no manual wiring, no
terminal, no understanding of how the material is stored underneath. The screen explains in
plain terms that the production will use the operator's imported material. (Choosing *which
specific* items feed one production — per-item curation — is a later refinement; v1 attaches
the imported material as a whole, consistent with the shared-store client scope.)

**Why this priority**: Bringing material in is only half the promise; "as mission input
attached to a brief" is the value that makes Import worth having — the operator's own
material demonstrably shapes the production. It ranks second because it layers onto — and
requires — the bring-in foundation from US1, and because a working Import screen (US1)
already delivers standalone value.

**Independent Test**: With supported material already imported, direct a brief to use it (from
Import or from the S2 brief flow), confirm the brief clearly indicates in plain language that
the production will build on the operator's imported material, launch the production, and
verify it proceeds using that material via the existing knowledge/visual capability — with
clear confirmation that the imported material will be used.

**Acceptance Scenarios**:

1. **Given** supported material has been imported, **When** the operator directs a brief to use it, **Then** the brief clearly indicates in plain language that the production will build on the operator's imported material as its input.
2. **Given** a brief set to use imported material, **When** the operator launches the production, **Then** the mission draws on the imported material through the studio's existing local knowledge/visual capability, with no new mission semantics introduced by S5.
3. **Given** the operator is in the S2 Guided Brief, **When** they choose to use existing material, **Then** they can reach their imported items (or import a new one inline) without leaving the brief flow, and return with the production set to build on the imported material.
4. **Given** attached material would be processed off-machine (e.g., optional cloud image understanding), **When** the operator attaches or imports it, **Then** any off-machine step is explicit, per-item opt-in, and off by default — the operator is told plainly when an item would leave the machine.

---

### User Story 3 - See, organize, and clean up what I've imported (Priority: P3)

Over time the operator accumulates imported material and needs to keep it tidy. Import shows
everything they have brought in, organized by client with an unassigned shelf, each item in
plain language (what it is, when it was imported). They can re-associate a mis-filed item to
the right client (or return it to unassigned), and remove material they no longer need — with
confirmation and clear feedback. Removing imported source material never affects any
deliverable already produced from it.

**Why this priority**: Housekeeping keeps Import usable as volume grows, but it layers onto
the bring-in and use foundations (US1–US2) and is not required for the screen to deliver its
core value, so it ranks third.

**Independent Test**: With several items imported across clients and the unassigned shelf,
verify the imported list is grouped by client with an unassigned shelf and shown in plain
language; re-associate an item to a different client and verify it moves shelves immediately;
remove an item and verify it disappears with clear feedback and that a deliverable previously
produced from it (if any) is unaffected.

**Acceptance Scenarios**:

1. **Given** several items have been imported, **When** the operator opens Import, **Then** the items are listed grouped by client with a clearly labeled unassigned shelf, each in plain language (what it is, when imported) — never as a file path, store ID, or MIME type.
2. **Given** a mis-filed item, **When** the operator re-associates it to a different client (or returns it to unassigned), **Then** the change takes effect immediately and is reversible by re-associating again.
3. **Given** an imported item the operator no longer needs, **When** they remove it and confirm, **Then** it is removed with clear feedback, and any deliverable already produced from it is unaffected.
4. **Given** any organize or remove action, **When** it succeeds or fails, **Then** the operator gets plain-language feedback — never a silent no-op and never a raw technical error.

---

### Edge Cases

- **Nothing imported yet (first run)**: Import shows the friendly empty state (US1-AC5), not a blank grid or spinner-forever.
- **Client context set to a client with no imported material**: the scoped view shows an empty-for-this-client state that still lets the operator clear the context or bring material in.
- **Required ingestion capability absent** (the optional document or image ingestion extra is not installed on the machine): the relevant import path shows a clean, localized "not available here — how to enable" state (mirroring the studio's 501-plus-install-hint contract), never a broken control; other still-available import kinds keep working.
- **Unsupported material kind** (e.g., an executable, or a video/audio file while deep AV import is out of v1 scope): rejected with a plain-language reason that names what *is* supported, never a silent accept of material nothing can use.
- **File too large**: rejected with the size limit stated in plain terms, before any long upload stalls the screen.
- **Corrupt, empty, or unreadable file**: rejected gracefully with a plain-language explanation; the rest of the screen stays usable.
- **Duplicate import** (the same material brought in twice): de-duplicated or clearly marked as already imported, so the imported list stays clean.
- **Off-machine processing opt-in** (the existing optional cloud image understanding): off by default; if the operator opts in, they are told explicitly that the item would leave the machine, per item.
- **Import with no client selected**: the material lands unassigned and is attachable to a client/project/campaign later — never a forced precondition to importing (mirrors umbrella FR-013a).
- **Removing material currently attached to a brief or referenced by a past production**: handled gracefully — the operator is warned if it is attached to a pending brief, and removal never corrupts or alters any already-produced deliverable.
- **Very large imported list**: the screen stays responsive and navigable at real agency volume without forcing an unbounded flat scroll.
- **Language switch while importing/browsing**: all Import chrome (labels, actions, validation messages, states) follows the EN/FR switch immediately; the operator's own material (filenames, content) is not translated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Import MUST replace the current `import` coming-soon placeholder as the shipped operator-facing surface for bringing in existing material, reachable from the persistent navigation under its plain-language label and localized in EN/FR.
- **FR-002**: Import MUST let the operator bring in existing material from their own machine, presented in plain, non-technical language ("bring in a document", "bring in an image"), covering at minimum the v1 supported kinds — **documents (including text and PDF briefs) and images** — never requiring the operator to understand MIME types or technical formats to succeed.
- **FR-003**: Import MUST validate each item before accepting it — supported kind, size within the machine's limit, readable — and on rejection MUST give a plain-language reason (unsupported kind / too large / unreadable) with a way to try again, never a crash, a silent drop, or a raw technical error.
- **FR-004**: Import MUST show clear progress while an item is being brought in and an unambiguous, localized confirmation when it is in and available to use as production input, and a plain-language failure message otherwise.
- **FR-005**: Imported material MUST be made available as **input/context for a production** through the studio's **existing** local ingestion and the mission's existing knowledge/visual opt-ins; S5 MUST NOT introduce a new mission input channel, new mission semantics, or any change to mission-loop behavior (umbrella FR-016; Constitution Principles III, V, X).
- **FR-006**: Import MUST let the operator associate imported material with a client (Brick 6 taxonomy) — defaulting to the shell's active client context when one is set — or leave it on a clearly labeled **unassigned** shelf, and MUST NOT make client association a forced precondition to importing (umbrella FR-013a). This association is **organizational metadata** over the studio's shared local stores: v1 does NOT isolate a mission's context to only that client's material (true per-client context isolation is a future refinement, out of v1 scope).
- **FR-007**: Import MUST let the operator direct a **brief** (S2 Guided Brief) to use their imported material as the production's input — reachable both from the Import screen and from within the S2 brief flow — by enabling the production's existing knowledge/visual capability so the mission draws on the imported material of the relevant kinds, with the brief stating in plain language that the production will build on the operator's imported material. Selecting *which specific* imported items feed a single production (per-item curation) is **out of v1 scope**: v1 attaches the imported material as a whole, consistent with the shared-store client scope of FR-006.
- **FR-008**: Import MUST list everything the operator has imported, organized by client with an unassigned shelf, each item in plain language (what it is, when imported), and MUST let the operator re-associate a mis-filed item to a different client or return it to unassigned, taking effect immediately and reversibly.
- **FR-009**: Import MUST let the operator remove imported material they no longer need, through the existing delete-ingested-item path, with confirmation and clear feedback; removal MUST affect only the imported source material and MUST NOT alter or remove any produced deliverable.
- **FR-010**: Import MUST remain local-first: it MUST read only local files the operator explicitly chooses and MUST trigger no outbound network of its own; any off-machine processing (e.g., the existing optional cloud image understanding) MUST stay explicit, per-item opt-in, and OFF by default, with a plain statement that the item would leave the machine.
- **FR-011**: When a required ingestion capability is absent on the machine (an optional extra is not installed), Import MUST show a clean, localized "not available here — how to enable it" state (mirroring the studio's 501-plus-install-hint contract) for that kind, while keeping any still-available import kinds working — never a broken control or a raw error.
- **FR-012**: Import MUST clearly communicate, in localized plain language, the v1 supported material set and that **deep import of video and audio is not yet available**, rather than silently accepting material that nothing on the machine can use; unsupported kinds MUST be rejected with a message that names what *is* supported.
- **FR-013**: Import MUST NOT surface internal identifiers — store IDs, chunk IDs, MIME types, engine or kit names, or file-system paths — as the primary operator-facing identity of imported material anywhere in the screen.
- **FR-014**: Import MUST provide friendly, localized empty states — nothing imported yet (first run), and nothing imported for the active client context — each offering a way forward (bring material in / clear context) rather than a blank screen or an error.
- **FR-015**: Import MUST de-duplicate re-imports of the same material (or clearly mark it as already imported) so the imported list stays clean and an item is not brought in twice by accident.
- **FR-016**: Import MUST treat imported material as **source input** strictly distinct from a produced deliverable — it MUST NOT appear in the S4 Deliverable Library as a deliverable, and removing imported material MUST NOT affect any deliverable already produced from it.
- **FR-017**: Import MUST inherit the umbrella design-system accessibility baseline (WCAG 2.1 AA — full keyboard operability including bring-in, associate, attach-to-brief, organize, and remove; screen-reader labels; AA contrast; visible focus) and the shared loading/empty/error state patterns.
- **FR-018**: Import MUST preserve all security invariants (served only from 127.0.0.1, no wildcard cross-origin access, path-traversal guards on every stored/served file, HTTPS-only for any explicitly opted-in outbound step) and MUST NOT accept, persist, or display any API key or secret.
- **FR-019**: Import MUST only add an operator-facing front door over existing local service interfaces; it MUST NOT change the mission loop, routing, synthesis, asset rendering, the inspector veto loop, how or where produced dossiers are persisted, or the shape of a saved dossier (umbrella FR-016; Constitution Principles III, V, X).

### Key Entities *(include if feature involves data)*

- **Imported material item**: the operator-facing representation of one brought-in file — its plain-language name / what-it-is, its kind (document / image), when it was imported, its client association (or unassigned), its readiness (available as input, or failed with a reason), and the handle to attach or remove it. Backed by an existing local ingestion-store record; S5 defines no new produced-deliverable entity.
- **Material kind**: the supported category of imported material (v1: document — including text and PDF briefs — and image) that determines how it is ingested locally and which existing mission capability consumes it (knowledge for documents, visual for images). Video and audio are explicitly outside the v1 kind set.
- **Client association**: the Brick 6 client (optionally project / campaign) an imported item is attached to, or "unassigned" — organizational metadata that reuses the taxonomy and the shell client-context, is mutable, and is never a precondition to importing.
- **Brief attachment**: the operator's decision that a brief's production should build on their imported material as input — realized by enabling the production's existing knowledge/visual capability so the mission draws on the imported material. v1 attaches the imported material **as a whole** (per-item curation of which items feed one production is deferred).
- **Import validation result**: the per-item accept/reject outcome of bringing material in — accepted (ready to use) vs. rejected (unsupported kind / too large / unreadable / capability absent) — carrying a plain-language reason.
- **Import view state**: the operator's current lens onto their imported material — active client context (from the shell) and any filter — that determines which items are shown and how they are grouped. Ephemeral; not persisted by S5.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A non-technical operator can bring in a document or image and see it confirmed as ready to use as production input in under 30 seconds, without knowing any file path, store ID, or MIME type.
- **SC-002**: 100% of accepted imported items are available as input to a subsequent production (through the machine's existing knowledge/visual capability), and 100% of rejected items show a plain-language reason — with zero silent drops.
- **SC-003**: An operator can direct a brief to use their imported material and launch a production that builds on it as input in a single guided flow (from Import or from the S2 brief), with clear confirmation that the imported material will be used.
- **SC-004**: Every operator-facing string in Import is available in both EN and FR and follows a language switch immediately, with zero store IDs, MIME types, kit/engine names, or file paths shown as an item's identity anywhere in the screen.
- **SC-005**: Import meets WCAG 2.1 AA — bring-in, associate, attach-to-brief, organize, and remove are fully operable by keyboard and labeled for screen readers, with AA contrast and visible focus.
- **SC-006**: Import introduces zero changes to the mission loop, saved-dossier shape, or deliverable persistence — verified by the offline suite staying green and by productions launched with imported material behaving identically to those launched via the equivalent existing opt-ins.
- **SC-007**: With default settings, 100% of imports stay entirely on the machine — no material is ever sent off-machine without an explicit, per-item opt-in — verified by no outbound network on a default import.
- **SC-008**: When a required ingestion capability is absent, 100% of the time the operator sees a localized "not available — how to enable" state rather than a broken control or a raw error.
- **SC-009**: Removing imported source material never alters or removes any already-produced deliverable — verified by removing material after a deliverable was produced from it and confirming the deliverable is intact in the S4 Library.

## Assumptions

- **Reuses existing local ingestion**: documents are brought in through the studio's existing document-knowledge ingestion path and images through the existing image/visual ingestion path; S5 introduces no new persistence store and no new server ingestion capability — it is the operator-facing front door over what already exists.
- **Missions consume imported material via existing opt-ins**: a production uses imported documents/images through the already-existing mission `knowledge` / `visual` capability toggles (which the S2 brief already exposes); S5 adds no new mission input channel or semantics.
- **v1 supported kinds = documents and images**: these have existing local ingestion and are directly usable by a mission. **Deep import of video and audio is deferred** — the studio has no path that ingests a moving-image or sound file *as stored, mission-consumable import material* today (audio transcription exists only as a transient live-session step, not as importable material), and adding deep AV import would be a new capability; v1 states this limitation plainly (FR-012) rather than silently accepting unusable material. (Text and PDF briefs are handled as documents.)
- **Client association is organizational metadata**: attaching imported material to a client reuses the Brick 6 taxonomy and the shell client-context for organization and brief-attachment; true per-client isolation of a mission's context (filtering a production to only one client's material) is a future refinement and not a v1 requirement.
- **Brief attachment is whole-set in v1**: directing a production to use imported material enables the existing knowledge/visual capability so the mission draws on the imported material; selecting which *specific* imported items feed one production (per-item curation) is a future refinement, consistent with the shared-store client scope above. This keeps S5 a presentation-layer front door with no change to the mission bridge.
- **Removal is safe for source material**: imported items are the operator's own inputs (not agency-produced deliverables), so v1 allows removing them via the existing delete-ingested-item path; this is the deliberate contrast with S4 (non-destructive on deliverables) and never touches any produced deliverable.
- **Local-first, explicit opt-in for any off-machine step**: a default import stays entirely on the machine; the existing optional cloud image-understanding step remains off by default and per-item opt-in, and is the only path by which an imported item could leave the machine.
- **Load-all at v1 scale**: the imported-item counts for a local single-user agency are modest; the imported list is read once and grouped/filtered client-side, with no server-side pagination — pagination or virtualization can be added later without redesign if volumes grow.
- **Single client context from the shell**: Import respects the shell's existing client-context selector; a separate in-screen client picker is not required for v1.
- **Coexistence**: the existing developer-console document/visual management surfaces remain available at their secondary location; S5 is the operator-facing front door, not a replacement.
- **Local-first, no new network**: apart from the explicitly opted-in cloud image-understanding step, Import reads only local, operator-chosen files and triggers no network access of its own; security invariants (127.0.0.1 bind, no CORS `*`, path guards, keys env-only) are inherited unchanged.
