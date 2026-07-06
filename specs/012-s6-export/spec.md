# Feature Specification: Export — Turn Finished Work into Shareable Bundles (Brick 7 · Screen S6)

**Feature Branch**: `012-s6-export`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "lance le cycle S6 Export" — start the spec-kit cycle for screen S6 (Export) of the Brick 7 magic-box inventory: produce shareable bundles from finished work — a PDF document, a media zip, or a full dossier — through per-client / per-mission export flows, owning bundle composition and formats (per the authoritative screen inventory in `specs/007-magic-box/spec.md`, row S6).

## Scope

This spec covers the **Export screen (S6)** only: the operator-facing surface through which
a non-technical user turns a **finished deliverable** into a **shareable bundle** they can
hand to a client or teammate — a **PDF document**, a **media zip** of the produced
images/videos/audio, or a **full dossier bundle** that packages the deliverable, its media,
and its sources into one self-contained artifact. It replaces the current `export`
coming-soon placeholder with a shipped experience: pick a finished deliverable (or a whole
client's/campaign's finished work), choose a format in plain language, see what the bundle
will contain, and download it — with clear progress, an unambiguous confirmation, and a
friendly failure message when a format is not available on this machine.

It builds on the Brick 7 umbrella foundation (shell, persistent navigation, the shell's
client-context selector, EN/FR i18n, design system, shared loading/empty/error states), on
the Brick 6 client/project/campaign taxonomy, and on **S4 Deliverable Library** — S6 is the
"turn it into something shareable" side of the same finished work S4 browses. S4 already
exposes the **single existing per-deliverable PDF** as one per-deliverable action and hands
off to S6 for anything richer; S6 owns **bundle composition and formats**.

Unlike S4 and S5 — which mostly compose paths that already exist — S6 introduces **new
composition**: only the single-deliverable **PDF** path exists today (agency-kit's
`exporter.export_pdf`, the `[pdf]` extra). The **media zip** and **full dossier bundle** are
new, but they are strictly **read-only packaging** operations: they read a finished
deliverable's saved dossier and the media already on disk under that mission and assemble
them into a downloadable archive. They **re-render nothing**, mutate no dossier, add no new
persistence store, introduce **no new mission semantics**, and change **no mission-loop
behavior** (umbrella FR-016; Constitution Principles III, V, X). Exporting is
**non-destructive** — the deliverable and how/where it is persisted are untouched (the same
read-only pledge S4 makes).

S6 is **fully on-machine**: producing a bundle triggers **no outbound network of its own** —
the archive is built locally and streamed to the operator's browser as a download; whether to
then share that file is the operator's own action, off the studio. This is a stronger
invariant than S5's (Import's optional cloud image-understanding opt-in has no equivalent
here — nothing about exporting ever leaves the machine).

Out of scope here: capturing intent (S1) and building the brief (S2); following a **running**
production (S3 — S6 exports only a **finished** deliverable); browsing/previewing finished
deliverables (S4 — S6 is the bundle-and-download side, and reuses S4's finished-deliverable
listing and taxonomy as its picker rather than rebuilding it); bringing **in** existing
material (S5 — S6 is the output side, not the input side); the capability/model panel (S7 —
S6 respects whether the `[pdf]` render capability is installed but configures no models);
settings (S8); creating, editing, or renaming the underlying clients/projects/campaigns
(owned by the Brick 6 taxonomy surface, which S6 reuses as a selector); **per-client /
per-campaign bulk export** (deferred post-v1 — v1 exports one finished deliverable at a
time; bulk reuses the same read-only composition and can be added later without redesign);
**editing a deliverable's content before export** (S6 packages what was produced, exactly as saved — it
is not an editor); **cloud delivery / send-to-client / email / upload integrations** (S6
produces a downloadable file; delivering it anywhere off the machine is the operator's own
action and a possible future refinement); and any change whatsoever to the mission loop,
routing, synthesis, asset rendering, the inspector veto loop, how or where dossiers are
persisted, or the shape of a saved dossier (umbrella FR-016; Constitution Principles III, V,
X). The existing developer console and the raw `GET /api/mission/{id}/pdf` endpoint remain
untouched at their secondary location (umbrella coexistence assumption); S6 is the
operator-facing front door, not a replacement for the console.

## Clarifications

### Session 2026-07-06

- Q: Which export formats ship in S6 v1 (only the single-deliverable PDF exists today; media pack and full dossier bundle are new packaging)? → A: **All three** — document (PDF, via the existing exporter), media pack (zip of produced media), and full dossier bundle. The umbrella names all three as S6-owned; the two new formats are strictly read-only assembly of existing on-disk artifacts, adding no mission semantics.
- Q: Should per-client / per-campaign bulk export ship in v1, or is v1 single-deliverable only? → A: **Single-deliverable only in v1.** v1 exports one finished deliverable at a time; per-client / per-campaign **bulk** export is **deferred** to a later cut. It reuses the same read-only composition, so it can be added later without redesign.
- Q: What goes into the "full dossier bundle" — client-facing only, or also archival/re-importable? → A: **Client-facing only** — the readable deliverable (document), its produced media, and a **human-readable** sources list; no raw machine-readable dossier snapshot in v1 (keeps internal structure out of the operator/client's face, FR-013). A machine-readable / re-importable archival snapshot is a future refinement.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Turn a finished deliverable into a shareable file (Priority: P1)

An agency operator has a finished deliverable — a strategy the agency produced, a campaign
with rendered images and a video — and needs to hand it to a client. They open Export (or
reach it from the deliverable in S4), pick the deliverable, choose a format in plain language
— **a polished document (PDF)**, **a media pack (zip of the produced images/videos/audio)**,
or **the whole thing as one bundle** — see in plain terms what the file will contain, and
download it. They get clear progress and an unambiguous confirmation that the file is ready,
or a plain-language reason if a format is not available on this machine. At no point do they
see a mission ID, a store path, a MIME type, or a raw error.

**Why this priority**: This is the screen's founding purpose and the reason S6 is on the
inventory — a finished deliverable that can't leave the studio as a shareable file is a
dead end for a non-technical user. Exporting one deliverable into one downloadable file is
the minimum that makes Export a real, usable screen on its own, independent of bulk flows.

**Independent Test**: With at least one finished deliverable present (produced with and
without media), open Export, choose a deliverable, and for each available format produce and
download a file; verify each downloads with a friendly filename and opens correctly off the
studio; verify a deliverable with no produced media still offers the document and full-bundle
formats and explains there is no media to pack; verify that when the PDF render capability is
absent the operator sees a localized "not available here — how to enable it" state for that
format while other formats keep working — never a crash, a silent failure, or a raw error.

**Acceptance Scenarios**:

1. **Given** a finished deliverable, **When** the operator chooses a format and exports, **Then** a shareable file is produced and downloaded with clear progress and a plain-language confirmation that it is ready — with no mission ID, store path, or MIME type shown as its identity.
2. **Given** a finished deliverable that produced no media, **When** the operator opens Export for it, **Then** the document (PDF) and full-dossier-bundle formats are offered and the media-pack option explains in plain language that there is no media to pack — never a broken control or an empty zip presented as a success.
3. **Given** a machine where the PDF render capability is not installed, **When** the operator tries to export a document, **Then** they see a friendly, localized "not available on this machine — here's how to enable it" state for that format, while any still-available format (media pack) keeps working — never a raw error.
4. **Given** a deliverable that is still running or failed (not finished), **When** the operator looks for it in Export, **Then** it is clearly not offered for export with a plain-language reason (only finished work can be exported), rather than producing a broken or partial bundle.
5. **Given** nothing has been produced yet, **When** the operator opens Export, **Then** they see a friendly empty state explaining what Export is for and pointing to where work is produced — never a blank screen or a technical error.

---

### User Story 2 - Choose what goes in the bundle (Priority: P2)

Before downloading, the operator wants to know — and control — what the shareable file
contains. Export shows, in plain language, what each format includes: the **document** is the
written deliverable laid out for reading and printing; the **media pack** is the produced
images, videos, and audio; the **full bundle** is everything together — the document, the
media, and the sources the work is built on — as one self-contained package a client can open
without the studio. The operator picks the format that fits, sees a plain-language summary of
the contents, and produces exactly that. Nothing is re-generated or altered; the bundle is a
faithful package of what was already produced.

**Why this priority**: Producing a file is the core promise (US1); letting the operator
choose and understand what's inside it is what makes the file trustworthy to hand to a
client. It ranks second because it layers onto — and requires — the produce-and-download
foundation from US1, which already delivers standalone value with sensible default contents.

**Independent Test**: With a finished deliverable that has both written content and produced
media, open Export, review the plain-language description of each format's contents, produce
the full dossier bundle, and verify the downloaded package is self-contained — the document,
the media, and a readable list of sources open correctly off the studio without the studio
running — and that the deliverable in S4 is byte-for-byte unchanged after export (packaging
is read-only).

**Acceptance Scenarios**:

1. **Given** a finished deliverable, **When** the operator views the export options, **Then** each format's contents are described in plain language (document = the written deliverable; media pack = the produced images/videos/audio; full bundle = document + media + sources) — never in internal machinery terms.
2. **Given** the operator chooses the full dossier bundle, **When** it is produced, **Then** the downloaded package is self-contained — it opens off the studio and contains the readable deliverable, its produced media, and a plain list of the sources the work cites.
3. **Given** any export, **When** the bundle is produced, **Then** the deliverable's saved content and media are read-only — S6 re-renders nothing and alters nothing, and the deliverable is unchanged in S4 afterward.
4. **Given** a deliverable whose produced media was pruned from disk since it was made, **When** the operator exports it, **Then** the bundle is produced gracefully from what is present, with a plain-language note about what is no longer available — never a crash or a silently corrupt file.

---

> **Deferred (post-v1)** — *Export a whole client's or campaign's finished work in one go.*
> Per-client / per-campaign **bulk** export is out of v1 scope: v1 exports one finished
> deliverable at a time. Bulk hand-off reuses the same read-only composition applied to each
> finished deliverable in a taxonomy scope (excluding unfinished missions), so it can be added
> later without redesign. It is recorded here to preserve intent, not as a v1 requirement.

---

### Edge Cases

- **Nothing produced yet (first run)**: Export shows the friendly empty state (US1-AC5), not a blank grid or a spinner-forever.
- **Client context set to a client with no finished deliverables**: the scoped view shows an empty-for-this-client state that still lets the operator clear the context or go to where work is produced.
- **Deliverable with no produced media**: the media-pack format is disabled with a plain-language "no media to pack" note; document and full-bundle formats still work (US1-AC2).
- **PDF render capability absent** (the `[pdf]` extra is not installed on the machine): the document format shows a clean, localized "not available here — how to enable" state (mirroring the studio's 501-plus-install-hint contract), while the media pack keeps working — never a broken control.
- **Media pruned since production** (retention removed a mission's `/media` assets after it was produced): re-export is graceful — the document drops a missing embed to its caption and the media pack includes what is present, each with a plain-language note about what is no longer available (US2-AC4); never a crash or a corrupt archive.
- **Deliverable still running or failed**: not offered for export, with a plain-language reason that only finished work can be exported (US1-AC4).
- **Very large media bundle**: the screen stays responsive and gives honest progress while a large archive is assembled, rather than freezing or appearing to hang.
- **Render or packaging failure** (e.g., WeasyPrint fails on a document): a clean, plain-language failure with a way to retry or pick another format — never a dropped download or a raw stack trace.
- **Duplicate export** (the same deliverable exported twice): produces a fresh file each time; S6 keeps no export store, so there is nothing stale to reconcile.
- **Language switch while composing/browsing**: all Export chrome (labels, actions, contents descriptions, states) follows the EN/FR switch immediately; the operator's own deliverable content and filenames are not translated.
- **Confinement**: an export request for a deliverable outside the operator's current project scope is refused with the same confinement as viewing it, and a bundle never packages a file from outside its own mission's media/dossier.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Export MUST replace the current `export` coming-soon placeholder as the shipped operator-facing surface for turning finished work into shareable bundles, reachable from the persistent navigation under its plain-language label and localized in EN/FR.
- **FR-002**: Export MUST let the operator export a **finished deliverable** in a chosen format, presented in plain, non-technical language, covering at minimum the v1 formats — **a document (PDF)**, **a media pack (zip of the produced images/videos/audio)**, and **a full dossier bundle** (the document, its media, and its sources as one self-contained package) — never requiring the operator to understand file formats, MIME types, or archive internals to succeed.
- **FR-003**: Export MUST produce every format by **read-only packaging** of the finished deliverable's saved dossier and the media already on disk under that mission — the PDF via the studio's **existing** exporter, the media pack and dossier bundle by assembling existing on-disk artifacts. Export MUST re-render nothing, MUST NOT mutate any dossier, and MUST introduce no new mission semantics or mission-loop change (umbrella FR-016; Constitution Principles III, V, X).
- **FR-004**: Export MUST offer only **finished** deliverables for export; a still-running or failed mission MUST be clearly not offered, with a plain-language reason (only finished work can be exported), rather than producing a broken or partial bundle.
- **FR-005**: Export MUST describe, in plain language, what each format's bundle will contain before it is produced (document = the written deliverable; media pack = the produced media; full bundle = document + media + sources) — never surfacing internal machinery terms as the description.
- **FR-006**: Export MUST stream every produced bundle to the operator's machine as a **download**; S6 MUST persist no new export store — the produced bundle is a transient artifact, and re-exporting simply produces a fresh file.
- **FR-007**: Export MUST support **single-deliverable** export — exporting one finished deliverable at a time — reachable both from the Export screen (scoped by the shell client-context) and from a deliverable in S4. Per-client / per-campaign **bulk** export is **out of v1 scope** (deferred): v1 exports one deliverable per action; bulk hand-off reuses the same read-only composition and can be added later without redesign.
- **FR-008**: Export MUST be **fully on-machine**: producing any bundle MUST trigger no outbound network of its own — the archive is built locally and delivered as a browser download; whether to share the resulting file off the machine is the operator's own action, outside S6.
- **FR-009**: When a deliverable produced **no media**, Export MUST still offer the document and full-dossier-bundle formats and MUST present the media-pack option as unavailable with a plain-language "no media to pack" explanation — never an empty archive presented as a successful media export.
- **FR-010**: The **full dossier bundle** MUST be self-contained and **client-facing** — it MUST open off the studio (without the studio running) and contain the readable deliverable, its produced media, and a plain, **human-readable** list of the sources the work cites. v1 MUST NOT include a raw machine-readable dossier snapshot in the bundle (an archival / re-importable snapshot is a future refinement); the bundle presents no internal identifiers as content (FR-013).
- **FR-011**: Export MUST show clear progress while a bundle is being assembled and an unambiguous, localized confirmation when the file is ready to download, and a plain-language failure message (with a way to retry or choose another format) otherwise — never a dropped download or a raw technical error.
- **FR-012**: When a format's underlying capability is absent on the machine (e.g., the `[pdf]` render extra is not installed), Export MUST show a clean, localized "not available here — how to enable it" state (mirroring the studio's 501-plus-install-hint contract) for that format, while keeping any still-available format working — never a broken control or a raw error.
- **FR-013**: Export MUST NOT surface internal identifiers — mission IDs, store IDs, chunk IDs, MIME types, engine or kit names, or file-system paths — as the primary operator-facing identity of a deliverable or a produced bundle; downloaded files MUST carry friendly, human-meaningful names.
- **FR-014**: Export MUST provide friendly, localized empty states — nothing produced yet (first run), and nothing finished for the active client context — each offering a way forward (go to where work is produced / clear context) rather than a blank screen or an error.
- **FR-015**: Export MUST re-export from the deliverable's **current** on-disk state and handle media pruned since production gracefully — the document drops a missing embed to its caption and the media pack includes what is present, each with a plain-language note about what is no longer available — never a crash or a silently corrupt archive.
- **FR-016**: Export MUST be **non-destructive** — it MUST treat the deliverable's saved content and media as strictly read-only, MUST NOT alter or remove any deliverable, and MUST NOT change how or where dossiers are persisted or their shape; a deliverable MUST be unchanged in the S4 Library after any export.
- **FR-017**: Export MUST inherit the umbrella design-system accessibility baseline (WCAG 2.1 AA — full keyboard operability including choosing a deliverable, choosing a format, and downloading; screen-reader labels; AA contrast; visible focus) and the shared loading/empty/error state patterns.
- **FR-018**: Export MUST preserve all security invariants (served only from 127.0.0.1, no wildcard cross-origin access, path-traversal guards on every packaged and served file so a bundle can never include a file from outside its own mission's media/dossier, same project-scope confinement as viewing the deliverable, HTTPS-only for any outbound step — of which S6 has none) and MUST NOT accept, persist, or display any API key or secret.
- **FR-019**: Export MUST only add an operator-facing front door over existing local read paths plus read-only packaging; it MUST NOT change the mission loop, routing, synthesis, asset rendering, the inspector veto loop, how or where produced dossiers are persisted, or the shape of a saved dossier (umbrella FR-016; Constitution Principles III, V, X).

### Key Entities *(include if feature involves data)*

- **Exportable deliverable**: the operator-facing representation of one **finished** production available to export — its plain-language name / what-it-is, its client/project/campaign placement (from S4/Brick 6), whether it has produced media, and which export formats are available for it. Backed read-only by the existing saved dossier and its on-disk media; S6 defines no new persisted entity.
- **Export format**: the shareable form the operator chooses — **document (PDF)**, **media pack (zip of produced media)**, or **full dossier bundle (document + media + sources)** — each with a plain-language contents description and an availability state (available / unavailable-here / no-media-to-pack).
- **Export bundle**: the produced downloadable artifact — a document, a media archive, or a self-contained dossier package — assembled on demand by read-only packaging and streamed to the machine; transient (not persisted by S6).
- **Export scope**: what the operator is exporting — in v1, a **single finished deliverable**, resolved from S4's finished-deliverable listing and the Brick 6 taxonomy. Per-client / per-campaign bulk scope is deferred post-v1.
- **Bundle composition**: the plain-language statement of what a chosen format will include, shown before the bundle is produced, so the operator knows what they are about to hand over.
- **Export result**: the per-request outcome — ready-to-download (with a friendly filename), failed-with-reason (render/packaging failure, retryable), or format-unavailable (capability absent / no media) — carrying a plain-language message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A non-technical operator can turn a finished deliverable into a shareable file in a chosen format and download it in under 30 seconds, without knowing any mission ID, store path, or MIME type.
- **SC-002**: All three v1 formats (document, media pack, full dossier bundle) produce a file that opens correctly off the studio, and 100% of export failures show a plain-language reason with a way to retry or choose another format — with zero silent or dropped downloads.
- **SC-003**: Exporting a deliverable never alters or removes it — verified by exporting and confirming the deliverable is byte-for-byte intact in the S4 Library afterward.
- **SC-004**: Every operator-facing string in Export is available in both EN and FR and follows a language switch immediately, with zero mission IDs, store IDs, MIME types, kit/engine names, or file paths shown as the identity of a deliverable or a produced bundle anywhere in the screen.
- **SC-005**: Export meets WCAG 2.1 AA — choosing a deliverable, choosing a format, and downloading are fully operable by keyboard and labeled for screen readers, with AA contrast and visible focus.
- **SC-006**: Export introduces zero changes to the mission loop, saved-dossier shape, or deliverable persistence — verified by the offline suite staying green and by exported content faithfully matching the saved deliverable with no re-render.
- **SC-007**: With default settings, 100% of exports stay entirely on the machine — no bundle assembly ever triggers an outbound network — verified by no outbound network on any export.
- **SC-008**: When a format's capability is absent (e.g., the PDF render extra), 100% of the time the operator sees a localized "not available — how to enable" state for that format while other formats keep working, rather than a broken control or a raw error.
- **SC-009**: The full dossier bundle opens as a self-contained artifact — the readable deliverable, its produced media, and a plain sources list — without the studio running, verified on a machine with the studio stopped.

## Assumptions

- **Builds on S4 and finished deliverables only**: Export operates on the same finished deliverables S4 lists, reusing S4's finished-deliverable listing and the Brick 6 taxonomy as its picker; only successfully-finished deliverables are exportable (a running or failed mission has nothing complete to package). S4 continues to expose the single per-deliverable PDF as a quick action and hands off to S6 for richer bundles.
- **v1 formats = document (PDF), media pack (zip), full dossier bundle**: the umbrella names all three as S6-owned; v1 delivers all three. The **PDF** reuses agency-kit's existing `exporter.export_pdf` (`[pdf]` extra). The **media pack** and **full dossier bundle** are **new but read-only packaging** — they assemble the saved dossier and the media already on disk under the mission; they re-render nothing and add no new mission capability.
- **New composition, still additive**: S6 is the first Brick 7 screen to add composition beyond existing paths, but the composition is strictly read-only assembly of existing artifacts into a downloadable archive — no mission-loop change, no dossier mutation, no new persistence store, security invariants inherited unchanged.
- **Exports are transient downloads**: a produced bundle is streamed to the operator's machine as a download; S6 keeps no server-side export store or history, so re-exporting simply produces a fresh file and there is nothing stale to reconcile or prune.
- **Fully on-machine, no off-machine step**: producing any bundle triggers no outbound network of its own; unlike S5's optional cloud image-understanding, S6 has **no** off-machine path — sharing a produced file off the machine is the operator's own action, outside S6's scope.
- **Media pack = existing on-disk media, nothing re-rendered**: the media pack contains the produced images/videos/audio already saved under the mission's media directory; a deliverable with no media offers the document and full-bundle formats and explains there is nothing to pack.
- **Full dossier bundle is self-contained and client-facing**: it packages the readable deliverable, its media, and a **human-readable** sources list so a client can open it without the studio; it is a point-in-time package, not a live or editable copy, and v1 does **not** include a raw machine-readable dossier snapshot (an archival / re-importable snapshot is a future refinement).
- **Graceful under retention pruning**: because retention may prune a mission's `/media` after it was produced, re-export reads current on-disk state — the document drops missing embeds to their captions and the media pack includes what is present, each with a plain-language note — consistent with the existing exporter's behavior.
- **Bulk export deferred (post-v1)**: v1 exports one finished deliverable per action. Per-client / per-campaign bulk export would apply the same read-only packaging to each finished deliverable in a taxonomy scope (excluding unfinished missions) and organize the combined package by the taxonomy — recorded as intent, added later without redesign, not a v1 requirement.
- **Capability-gated formats**: a format whose capability is absent (e.g., the `[pdf]` render extra not installed) shows the localized "not available — how to enable" state for that format only, while still-available formats keep working (mirroring the studio's 501-plus-install-hint contract).
- **Single client context from the shell**: Export respects the shell's existing client-context selector to scope which finished deliverables are offered; a separate in-screen client picker is not required for v1.
- **Coexistence**: the existing developer console and the raw `GET /api/mission/{id}/pdf` endpoint remain available at their secondary location; S6 is the operator-facing front door, not a replacement.
- **Local-first, no new network, no secrets**: Export builds every bundle from local, already-produced artifacts and triggers no network access of its own; security invariants (127.0.0.1 bind, no CORS `*`, path-traversal guards on every packaged/served file, same project-scope confinement as viewing, keys env-only) are inherited unchanged.
