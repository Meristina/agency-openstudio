# Feature Specification: Deliverable Library — The Permanent Home for Everything the Agency Has Produced (Brick 7 · Screen S4)

**Feature Branch**: `010-s4-deliverable-library`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "lance le cycle S4 Deliverable Library" — start the spec-kit cycle for screen S4 (Deliverable Library) of the Brick 7 magic-box inventory: browse, search, and preview every finished deliverable, organized per client → project → campaign, with per-deliverable actions — the permanent destination that S3 Mission Timeline hands off to at completion (per the authoritative screen inventory in `specs/007-magic-box/spec.md`).

## Scope

This spec covers the **Deliverable Library screen (S4)** only: the shelf where a
non-technical operator finds everything the agency has ever produced for them, long
after the production that made it has finished. It turns the flat, technical list of
saved missions into a browsable, searchable library of **finished deliverables**,
organized the way an agency thinks — by **client → project → campaign** (the Brick 6
taxonomy) — with a work-with-no-client "unassigned" shelf, a quick **preview** of each
deliverable in place, and the everyday **per-deliverable actions** (open the full
dossier, download its PDF, attach or move it within the taxonomy). It replaces the
current `library` coming-soon placeholder with the shipped experience, and it becomes
the permanent home for the interim "open details / download PDF" hand-off that S3
Mission Timeline points at on a successful finish.

It builds on the Brick 7 umbrella foundation (shell, persistent navigation, the shell's
client-context selector, EN/FR i18n, design system, shared loading/empty/error states),
on the Brick 6 client/project/campaign taxonomy, and on the existing local mission store
and its saved dossiers — which S4 only **reads and organizes**, never alters (umbrella
FR-016; Constitution Principles III, V, X). The finished-deliverable listing, the
per-client/project/campaign grouping, the saved dossier detail view, its PDF, and the
attach/move-within-taxonomy capability all already exist as building blocks; S4 is the
operator-facing library surface that composes them into one place, not new production
machinery.

Out of scope here: capturing intent (S1) and building the brief (S2); following a
**running** production live (S3 Mission Timeline — S4 is where a run lands *after* it
finishes, not where it is watched); importing new material (S5); building shareable
**export bundles** — media zip, full dossier bundle — beyond the single existing
per-deliverable PDF (S6 Export owns bundle composition; S4 only exposes the already-
existing PDF as one per-deliverable action and hands off to S6 when it ships); the
capability/model panel (S7); settings (S8); creating, editing, or renaming the
underlying clients/projects/campaigns themselves (owned by the Brick 6 taxonomy surface,
which S4 reuses as a selector); and any change whatsoever to the mission loop, routing,
synthesis, asset rendering, the inspector veto loop, how or where dossiers are persisted,
or the shape of a saved dossier (umbrella FR-016; Constitution Principles III, V, X). The
existing developer console and its raw mission list remain untouched at their secondary
location (umbrella coexistence assumption); S4 is the operator-facing library, not a
replacement for the console.

## Clarifications

### Session 2026-07-06

- Q: Should the Library let an operator delete/remove a deliverable in v1? → A: No — v1 is strictly non-destructive (browse, open, download PDF, file/refile only); nothing produced can be removed from the Library. Deletion is deferred to a later, guarded capability so S4 keeps its "reads and organizes, never alters persistence" pledge intact (the sole sanctioned mutation remains taxonomy filing via the existing assign path).
- Q: What is the preview scope for v1 (the inventory names "previews" as an S4-owned concern)? → A: An in-place preview AND full open — a quick inline summary (headline/description, outcome, key sources & decisions, produced-media thumbnails) shown without navigating away, alongside the action to open the full dossier detail (FR-008 stands as written).
- Q: With S3's resume-from-checkpoint, how does the Library keep "each deliverable appears exactly once"? → A: Dedupe by logical mission identity — one deliverable per mission regardless of how many resume hops it took; a resumed run supersedes (updates/replaces) its prior entry rather than creating a second card, so an interrupted-then-resumed production never appears twice.
- Q: How does the Library handle list volume at real agency scale? → A: Load-all with client-side grouping/search/filter for v1 — no server-side pagination; local single-user agency mission counts are modest (tens to low hundreds), and the existing finished-mission listing is read once and organized in the browser. Pagination/virtualization can be added later without redesign if volumes grow.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find and open everything produced for a client (Priority: P1)

An agency operator opens the Library and sees every finished deliverable the agency has
produced, arranged the way they think about their work: grouped by client, then by that
client's projects and campaigns, with an obvious **unassigned** shelf for anything not
yet attached to a client. Each deliverable is shown as a plain-language card — what it
was ("a go-to-market strategy for the spring launch"), when it was produced, and its
outcome at a glance — never as a mission ID, a route of department kits, a verdict code,
or a file path. Picking one opens its full deliverable (the saved dossier detail, with
its sources, decisions, and any produced assets) so the operator can read, reuse, or
download it. When the shell's client-context selector is set to a client, the Library
narrows to that client's shelf automatically.

**Why this priority**: This is the screen's founding purpose and the reason S4 is on the
inventory — a non-technical user cannot benefit from what the agency produced if they
cannot find it again. It is also the permanent landing place S3 hands a finished
production to, so without it the end-to-end "produce → find it later" loop is broken.
Browsing-and-opening is the minimum that makes the Library a real, usable screen on its
own.

**Independent Test**: With at least one finished mission saved (some attached to a
client/project/campaign, some not), open the Library and verify the deliverables appear
grouped by client → project → campaign with an unassigned shelf, each shown in plain
language, and that opening one reaches its full saved deliverable detail — with no
mission IDs, kit names, phase codes, or file paths exposed anywhere.

**Acceptance Scenarios**:

1. **Given** finished deliverables exist across several clients, projects, and campaigns, **When** the operator opens the Library, **Then** the deliverables are presented grouped by client → project → campaign, each as a plain-language card showing what it is, when it was produced, and its outcome — with no internal identifiers, kit names, or paths shown.
2. **Given** a deliverable was produced with no client attached, **When** the operator browses the Library, **Then** that deliverable appears on a clearly labeled "unassigned" shelf from which it remains fully openable.
3. **Given** the shell's client-context selector is set to a specific client, **When** the operator is in the Library, **Then** the Library is scoped to that client's deliverables (grouped by its projects and campaigns), and clearing the selector returns the full library view.
4. **Given** the operator picks a deliverable card, **When** they open it, **Then** they reach its full saved deliverable detail (dossier with sources, decisions, and any produced assets) presented in plain language.
5. **Given** no finished deliverables exist yet (first run), **When** the operator opens the Library, **Then** they see a friendly empty state that explains the Library will fill as productions finish and offers a way to start producing — never a blank screen or a technical error.

---

### User Story 2 - Search and filter to the one deliverable I need (Priority: P2)

An operator who has produced dozens of deliverables needs a specific one — "the pitch
deck we made for Acme last month" — without scrolling every shelf. They type a few words
and the Library narrows to matching deliverables as they type, matching on what the
deliverable is about (its plain-language description/goal) and its taxonomy placement
(client, project, campaign). They can also narrow by outcome (finished successfully vs.
needs-attention) to separate the ready-to-use work from runs that ended in trouble. When
a search finds nothing, the Library says so plainly and lets them clear the search in one
step.

**Why this priority**: Browse-only works for a handful of deliverables; the moment an
agency has real volume, find-by-search is what keeps the Library usable. It is the second
half of the "find it again" promise but sits below browse because browse already delivers
a working screen on its own.

**Independent Test**: With many finished deliverables saved, type a query that matches a
subset and verify the Library narrows to matching deliverables (by description and by
client/project/campaign), that an outcome filter further narrows them, that a
no-match query shows a clear "nothing found" state, and that clearing search restores the
full grouped view.

**Acceptance Scenarios**:

1. **Given** many finished deliverables exist, **When** the operator types a query, **Then** the Library narrows to deliverables whose plain-language description or taxonomy placement (client / project / campaign) matches, updating as they type.
2. **Given** a mix of successful and troubled outcomes exists, **When** the operator applies an outcome filter, **Then** only deliverables with that outcome are shown, combinable with the text query and the active client context.
3. **Given** a query matches nothing, **When** the results resolve, **Then** the operator sees a clear, friendly "nothing found" state with a one-step way to clear the search — never a blank screen or an error.
4. **Given** an active search or filter, **When** the operator clears it, **Then** the Library returns to the full grouped browse view (respecting any active client context).

---

### User Story 3 - Preview and act on a deliverable without ceremony (Priority: P3)

From the Library, an operator can glance at what a deliverable actually contains — a quick
in-place **preview** (its headline, outcome, key sources/decisions, and any produced
media thumbnails) — before committing to open the full detail. Right there on each
deliverable they can take the everyday actions: **open** the full dossier, **download its
PDF**, and **file it** — attach an unassigned deliverable to a client/project/campaign, or
move a mis-filed one — so the Library stays tidy over time. Each action gives clear
feedback, and the ones that could surprise (moving where a deliverable lives) are
understandable and reversible by simply filing it again.

**Why this priority**: Preview and per-deliverable actions are the concerns the inventory
assigns to S4, and they turn the Library from a read-only index into a place the operator
actually works from. They rank third because they layer onto — and require — the browse
and find foundations from US1–US2.

**Independent Test**: On a finished deliverable, open the in-place preview and verify it
summarizes the deliverable without leaving the Library; then exercise each per-deliverable
action — open full detail, download the PDF, and file/refile it into the taxonomy — and
verify each completes with clear feedback and that refiling moves the deliverable to the
expected shelf.

**Acceptance Scenarios**:

1. **Given** a finished deliverable in the Library, **When** the operator triggers its preview, **Then** a quick in-place summary appears (headline/description, outcome, key sources and decisions, and thumbnails of any produced media) without navigating away.
2. **Given** a deliverable with a saved dossier, **When** the operator chooses "download PDF", **Then** the existing per-deliverable PDF is produced and offered for download, with clear progress and a clear message if it is unavailable.
3. **Given** an unassigned deliverable, **When** the operator files it under a client/project/campaign, **Then** it moves to that shelf and the Library reflects the new placement immediately.
4. **Given** a mis-filed deliverable, **When** the operator moves it to a different client/project/campaign (or back to unassigned), **Then** the change takes effect immediately and can be undone by filing it again.
5. **Given** any per-deliverable action, **When** it succeeds or fails, **Then** the operator gets plain-language feedback — never a silent no-op and never a raw technical error.

---

### Edge Cases

- **No deliverables at all (first run)**: the Library shows the friendly empty state (US1-AC5), not a blank grid or spinner-forever.
- **Client context set to a client with no deliverables**: the scoped view shows an empty-for-this-client state that still lets the operator clear the context or start producing.
- **A finished run that ended in error / was cancelled / was vetoed**: it still appears (so nothing produced is silently lost) but is clearly marked as needs-attention rather than presented as a ready deliverable; the outcome filter can separate these out.
- **A deliverable whose PDF cannot be produced** (missing extra, render failure): the download action fails gracefully with a plain-language explanation and an install/enable hint where relevant — the rest of the deliverable stays fully usable.
- **A deliverable with no produced media (research/strategy only)**: preview shows the textual summary with no broken media placeholders.
- **A deliverable attached to a client/project/campaign that no longer exists in the taxonomy**: it is shown on the unassigned shelf (or a clearly labeled "orphaned" state) and can be refiled — it is never hidden or dropped.
- **Very long lists**: the Library remains responsive and navigable at real agency volume without forcing the operator to scroll an unbounded flat list.
- **Language switch while browsing**: all Library chrome (shelf labels, actions, states) follows the EN/FR switch immediately; the operator's own produced content is not translated.
- **A production still running (S3's domain)**: it is not presented as a finished deliverable in the Library; the Library is the after-completion home, and following live runs stays in S3.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Library MUST replace the current `library` coming-soon placeholder as the shipped operator-facing surface for finished deliverables, reachable from the persistent navigation under its plain-language label and localized in EN/FR.
- **FR-002**: The Library MUST present finished deliverables organized by the Brick 6 taxonomy — grouped by client → project → campaign — with a clearly labeled "unassigned" shelf for deliverables not attached to a client.
- **FR-003**: The Library MUST represent each deliverable in plain, non-technical language (what it is, when it was produced, its outcome at a glance) and MUST NOT surface mission IDs, department/kit names, engine names, phase or verdict codes, or file paths anywhere in the operator-facing view.
- **FR-004**: The Library MUST scope its contents to the shell's active client-context selector when one is set (showing that client's deliverables grouped by its projects and campaigns) and MUST show the full library across all clients when no context is set.
- **FR-005**: Opening a deliverable MUST reach its full saved deliverable detail (the existing dossier view — sources, decisions, produced assets), presented in plain language, without altering the saved dossier.
- **FR-006**: The Library MUST let the operator search deliverables by a text query that matches the deliverable's plain-language description/goal and its taxonomy placement (client, project, campaign), narrowing results as the operator types.
- **FR-007**: The Library MUST let the operator filter deliverables by outcome (at minimum: finished successfully vs. needs-attention), combinable with the text query and the active client context.
- **FR-008**: The Library MUST provide an in-place preview of a deliverable (headline/description, outcome, key sources and decisions, and thumbnails of any produced media) that summarizes it without navigating away from the Library.
- **FR-009**: The Library MUST offer, per deliverable, the everyday actions: open the full detail, download the existing per-deliverable PDF, and file/refile the deliverable within the taxonomy (attach an unassigned deliverable, move a mis-filed one, or return it to unassigned). The Library MUST NOT offer deletion or removal of a deliverable in v1 — it is strictly non-destructive, and taxonomy filing (via the existing assign path) is the only mutation it performs; removal is deferred to a later, guarded capability.
- **FR-010**: Filing or moving a deliverable within the taxonomy MUST take effect immediately in the Library view, MUST reuse the existing attach/assign capability (never a new persistence path), and MUST be reversible by filing it again.
- **FR-011**: Every Library action MUST give plain-language feedback on success and failure — never a silent no-op, never a raw technical error — and PDF download in particular MUST show progress and a clear message (with an enable/install hint where relevant) when the PDF cannot be produced.
- **FR-012**: The Library MUST provide friendly, localized empty states — no deliverables at all (first run), and no deliverables for the active client context — each offering a way forward (start producing / clear context) rather than a blank screen or error.
- **FR-013**: The Library MUST show finished runs that ended in error, cancellation, or veto (so nothing produced is lost) marked clearly as needs-attention rather than presented as ready deliverables, and MUST keep deliverables whose taxonomy attachment no longer resolves visible and refilable (never hidden or dropped).
- **FR-014**: The Library MUST NOT present in-progress (still-running) productions as finished deliverables; following live runs remains owned by S3 Mission Timeline, and the Library is the after-completion home a finished run lands in.
- **FR-014a**: The Library MUST present one deliverable per logical mission identity — a production resumed from a checkpoint (S3 resume path) MUST supersede its prior entry rather than appear as a second deliverable, so an interrupted-then-resumed run is never shown twice.
- **FR-015**: The Library MUST only read and organize the existing mission store, saved dossiers, PDF, and taxonomy; it MUST NOT change the mission loop, routing, synthesis, asset rendering, the inspector veto loop, how or where dossiers are persisted, or the shape of a saved dossier (Constitution Principles III, V, X; umbrella FR-016).
- **FR-016**: The Library MUST inherit the umbrella design-system accessibility baseline (WCAG 2.1 AA — full keyboard operability including grouping/preview/actions, screen-reader labels, AA contrast, visible focus) and the shared loading/empty/error state patterns.
- **FR-017**: The Library MUST serve as the permanent destination for the S3 Mission Timeline completion hand-off, replacing the interim mission-detail/PDF hand-off S3 points at, so a finished production reaches its library home from the moment S4 ships.
- **FR-018**: The Library MUST NOT itself build multi-file export bundles (media zip, full dossier bundle) — it exposes only the already-existing single per-deliverable PDF and hands off bundle composition to S6 Export when it ships — and MUST NOT create, rename, or delete the underlying clients/projects/campaigns (it reuses the Brick 6 taxonomy as a selector).

### Key Entities *(include if feature involves data)*

- **Deliverable (library view of a finished mission)**: the operator-facing representation of one saved mission — its plain-language description (goal), the moment it was produced, its outcome (successful / needs-attention), its taxonomy placement (client / project / campaign, or unassigned), a preview summary (key sources, decisions, produced-media thumbnails), and the handle to its full saved detail and PDF. A read-only projection of an existing saved dossier — S4 defines no new stored fields.
- **Taxonomy placement**: the client → project → campaign attachment of a deliverable (or "unassigned"), read from the Brick 6 taxonomy and mutable only through the existing attach/assign capability that S4 reuses.
- **Library view state**: the operator's current lens onto the library — active client context (from the shell), text query, and outcome filter — that determines which deliverables are shown and how they are grouped. Ephemeral; not persisted by S4.
- **Deliverable outcome**: the plain-language status a finished run resolved to — successful (a ready deliverable) vs. needs-attention (ended in error, cancellation, or veto) — derived from the saved dossier's existing verdict/delivery signals, not newly computed.
- **Mission identity**: the logical key by which the Library deduplicates deliverables so a resumed-from-checkpoint run supersedes its prior entry rather than doubling it (FR-014a); read from the existing mission store, not newly assigned by S4.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A non-technical operator can locate a specific previously-produced deliverable and open its full detail in under 30 seconds, using only browse or search — without knowing any mission ID, kit name, or file path.
- **SC-002**: 100% of finished deliverables appear in the Library exactly once, filed under their correct client → project → campaign shelf (or the unassigned shelf), with none silently missing — including runs that ended in error, cancellation, or veto (shown as needs-attention), and including interrupted-then-resumed runs (which appear once, not doubled — FR-014a).
- **SC-003**: From the Library, an operator can complete each everyday action — open the full detail, download the PDF, and file/refile a deliverable into the taxonomy — each in a single, obvious step with clear success/failure feedback.
- **SC-004**: Every operator-facing string in the Library is available in both EN and FR and follows a language switch immediately, with zero mission IDs, department/kit names, engine names, phase/verdict codes, or file paths visible anywhere in the screen.
- **SC-005**: The Library meets WCAG 2.1 AA — browse, search, preview, and every per-deliverable action are fully operable by keyboard and labeled for screen readers, with AA contrast and visible focus.
- **SC-006**: The Library introduces zero changes to the mission loop, saved-dossier shape, or persistence — verified by the offline suite staying green and by finished deliverables produced before S4 shipping appearing correctly in the Library with no migration.
- **SC-007**: A finished production launched from the Guided Brief and followed in S3 Mission Timeline reaches its permanent home in the Library on completion, and is openable there, with no dead-end hand-off.

## Assumptions

- **A finished "deliverable" is a saved mission**: S4 treats each persisted mission dossier as one deliverable; the Library reads the existing finished-mission listing (filterable by client/project/campaign) and the existing per-mission dossier and PDF. No new deliverable entity or store is introduced.
- **Preview reads existing dossier content**: the in-place preview is assembled from fields already present in a saved dossier (description/goal, outcome/verdict, sources, decisions, produced-asset manifest); S4 computes and stores nothing new.
- **Filing reuses the existing attach/assign capability**: attaching/moving a deliverable within the taxonomy goes through the existing mission-assignment path (including "clear → unassigned"); S4 adds no new persistence route.
- **Taxonomy is reused, not managed here**: clients/projects/campaigns come from the Brick 6 taxonomy surface; S4 offers them as a selector for filing and does not create, rename, or delete them.
- **PDF is the only bundle S4 exposes**: the single existing per-deliverable PDF is surfaced as an action; richer export bundles (media zip, full dossier bundle) are S6 Export's responsibility and are out of scope here.
- **Single client context from the shell**: the Library respects the shell's existing client-context selector; a separate in-screen client picker is not required for v1.
- **Load-all at v1 scale**: the Library reads the existing finished-mission listing once and does grouping, search, and filtering client-side, with no server-side pagination — appropriate for a local single-user agency's modest mission counts (tens to low hundreds). Pagination or list virtualization can be introduced later without redesign if volumes grow.
- **Non-destructive v1**: the Library never deletes or removes a deliverable; the only mutation it performs is taxonomy filing through the existing assign path. A guarded deletion capability is deferred to a later iteration.
- **In-progress runs stay in S3**: the Library is the after-completion surface; live-run following, cancel, and error handling remain owned by S3 Mission Timeline.
- **Local-first, no new network**: the Library reads only local, already-persisted data and triggers no network access of its own; security invariants (127.0.0.1 bind, no CORS `*`, path guards) are inherited unchanged.
- **Coexistence**: the existing developer console and its raw mission list remain available at their secondary location; S4 is the operator-facing library, not a replacement for the console.
