# Feature Specification: Guided Brief — From Intent to a Launch-Ready Production (Brick 7 · Screen S2)

**Feature Branch**: `008-s2-guided-brief`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "lance le cycle S2 Guided Brief" — start the spec-kit cycle for screen S2 (Guided Brief) of the Brick 7 magic-box inventory: turn intent into a complete mission brief through guided questions parameterized by sector / domain / deliverable type; owns the question flow, sector/domain/deliverable parameterization, deliverable language choice, and brief review & launch (per the authoritative screen inventory in `specs/007-magic-box/spec.md`).

## Scope

This spec covers the **Guided Brief screen (S2)** only: the guided question flow that
turns a user's stated intent into a complete, reviewed, launch-ready production brief,
and the act of launching that brief as a mission. It builds on the Brick 7 umbrella
foundation (shell, navigation, EN/FR i18n scaffolding, design system, client-context
selector) and the Brick 6 client/project/campaign taxonomy.

Out of scope here: following the running mission (S3 Mission Timeline), browsing
finished work (S4 Deliverable Library), importing existing material (S5 Import — the
brief may reference imported material once S5 ships, but the import flows themselves
are S5's), export (S6), the capability/model panel internals (S7), settings (S8), and
any change to the mission loop, routing, or inspection semantics (Constitution
Principle X / umbrella FR-016).

## Clarifications

### Session 2026-07-06

- Q: Is the mission's internet research (the engine researching and citing sources, free via the CLI subscription) enabled by default in a brief launched from the Guided Brief? → A: Yes, enabled by default — sourced research is the agency's honesty guarantee (Constitution III), free, and exempt from the network opt-in rule (Principle IV); the brief presents it in plain language with the ability to turn it off.
- Q: Which deliverable types must the Guided Brief support at v1? → A: Research-type, strategy-type, and video deliverables — the trio the brick's exit criterion requires (confirmed as decided, not assumed); further types (e.g. Brick 8 recipe packs) are added as question sets without redesign.
- Q: Are expert mission settings (specialist-army escalation budget, source-verification thresholds) exposed in the Guided Brief at v1? → A: No — v1 applies sensible defaults with no extra step; the effective values remain visible on the review (FR-015). A fine-tune step may be added later without restructuring the flow.
- Q: Are the brief's question sequences curated deterministic question sets, or generated dynamically by a CLI agent? → A: Curated and deterministic — fixed question sets per deliverable type, parameterized by sector/domain; fully offline-testable (Constitution VII) and 100% catalog-translatable. Agent-assisted enrichment may layer on later without changing the screen's contract.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Answer a few plain questions, get a complete brief (Priority: P1)

A non-technical agency operator arrives on the Guided Brief — usually carrying the
intent they typed into the magic box home ("a launch video for my bakery client", "a
market study on padel in Morocco") — and is walked, one step at a time, through a
short sequence of plain-language questions. The questions adapt to what they are
producing: the flow first establishes the **deliverable type** (e.g. research dossier,
strategy dossier, marketing video), then the **sector / domain** context, then the
type-specific essentials (audience, objective, key messages, constraints, the
**language the deliverable should be written in**). At every step the operator sees
where they are, can go back without losing answers, and is never asked for anything
technical. At the end, their answers form one complete production brief.

**Why this priority**: This is the screen's founding purpose and the reason S2 blocks
the brick's exit criterion — without a guided path from intent to a complete brief, a
non-technical user cannot start a production at all. Everything else on this screen
(review, launch, attachment, drafts) presupposes the question flow exists.

**Independent Test**: Starting from a stated intent, a test user can complete the
question sequence for each supported deliverable type using only plain-language
choices and short text answers, and the result is a single brief containing every
answer — testable without launching anything.

**Acceptance Scenarios**:

1. **Given** the operator answered "What do you want to produce?" on the home screen, **When** they arrive on the Guided Brief, **Then** their stated intent is already present as the brief's starting point (visible and editable) — they never retype it.
2. **Given** the operator opens the Guided Brief directly from navigation with no prior intent, **When** the flow starts, **Then** the first step asks for their intent in plain language and the flow proceeds identically from there.
3. **Given** the flow has established the deliverable type, **When** the operator advances, **Then** the subsequent questions are those relevant to that deliverable type and sector/domain — no question irrelevant to the chosen production is asked.
4. **Given** any step of the flow, **When** the operator looks at the screen, **Then** they can tell how far along they are, what is asked of them, and how to go back — and going back preserves every answer already given.
5. **Given** a question the operator is unsure about, **When** a sensible default or "skip" exists for it, **Then** the operator can accept the default or skip and still reach a complete brief; only the minimal essential set (intent, deliverable type, deliverable language) is required.
6. **Given** the whole flow, **When** its wording is reviewed, **Then** every question, choice, and helper text is phrased in plain production language (no department, engine, pipeline, or flag terminology) and rendered in the interface language (EN/FR).

---

### User Story 2 - Review everything, then launch with one action (Priority: P2)

Having answered the questions, the operator lands on a **brief review**: a single
human-readable summary of every choice they made — what will be produced, for whom,
in which language, under which client, with which options. Any line can be edited in
place (jumping back to the matching question and returning to the review). One clearly
labeled action launches the production; the operator is then handed off to the
mission-following surface to watch it run.

**Why this priority**: The review-and-launch step is what turns the question flow's
output into an actual mission — the handoff from "brief" to "production". It is second
only to the flow itself: without it US1 produces a brief that goes nowhere.

**Independent Test**: Complete a brief, verify the review lists 100% of the given
answers, edit one answer from the review, verify the change is reflected, launch, and
verify a production starts and the operator is routed to the mission-following area.

**Acceptance Scenarios**:

1. **Given** a completed question flow, **When** the review is shown, **Then** every answer and every effective option (including defaulted ones that affect the production, such as deliverable language and client attachment) is visible in plain language — nothing the production will use is hidden.
2. **Given** the review, **When** the operator chooses to change one answer, **Then** they are taken to that question with its current value, and after changing it they return to the review with all other answers intact.
3. **Given** the operator launches the brief, **When** the production starts successfully, **Then** the operator is routed to the mission-following surface for that production, and the brief they launched remains consultable.
4. **Given** the operator launches the brief, **When** the studio service rejects it or is unreachable, **Then** a plain-language, localized explanation is shown, no answer is lost, and the operator can retry or keep editing — the brief is never destroyed by a failed launch.
5. **Given** a launched production, **When** the underlying request is inspected (in tests), **Then** it contains exactly what the operator chose — their goal and answers verbatim, their explicit options, and nothing fabricated on their behalf.

---

### User Story 3 - File it under the right client, or not yet (Priority: P3)

During the brief, the operator can attach the production to a **client** (and
optionally a project/campaign) from the Brick 6 taxonomy — picking an existing one or
creating a new client on the spot with just a name. If the shell already has an active
client context, it is proposed as the default. The operator can equally skip the step
entirely: the work then lands in the "unassigned" bucket and can be attached later
from the library, exactly as the umbrella promises.

**Why this priority**: Client attachment is how the brief connects to the agency's
organizational spine (Brick 6) — valuable from day one, but the umbrella already
guarantees production works without it, so it must never gate US1/US2.

**Independent Test**: With taxonomy data present, complete a brief attaching an
existing client/project/campaign and verify the launched production carries that
attachment; repeat while skipping attachment and verify the work is unassigned; repeat
creating a new client inline and verify it exists in the taxonomy afterwards.

**Acceptance Scenarios**:

1. **Given** clients exist in the taxonomy, **When** the operator reaches the attachment step, **Then** they can browse and pick a client (and drill into its projects/campaigns) without leaving the flow.
2. **Given** the shell has an active client context, **When** the attachment step is shown, **Then** that client is pre-selected as the default, and the operator can change or clear it.
3. **Given** no client is chosen, **When** the production launches, **Then** it lands in the "unassigned" bucket and nothing in the flow ever forced a choice.
4. **Given** the operator's client does not exist yet, **When** they choose to create one at the attachment step, **Then** providing just a name is enough to create it, attach the production to it, and continue — deeper taxonomy management stays outside the brief.

---

### User Story 4 - Nothing paid, nothing off-machine, without saying so (Priority: P4)

Where the brief offers choices that cost money or leave the operator's machine —
cloud-rendered video versus local rendering, optional paid providers — each such
choice is presented in plain language with the **free/local option as the default**
and the paid/cloud option explicitly marked as such. If the operator's machine cannot
produce what they asked for (a missing local capability), the brief says so **before
launch**, in plain words, with a way forward — never a technical error after the fact,
and never a field to type a secret into.

**Why this priority**: Constitution Principle IV (explicit free/paid choice) and VI
(no secrets in the interface) are non-negotiable; the brief is the exact surface where
a silent paid default would betray them. It ranks below US1–US3 only because it
qualifies choices those stories introduce.

**Independent Test**: Drive a brief toward a video deliverable and verify the
local/cloud choice is explicit with local as default; simulate a machine missing the
needed capability and verify a plain-language blocker appears before launch with
guidance; verify no surface of the flow accepts a credential.

**Acceptance Scenarios**:

1. **Given** a deliverable type with a local/free and a cloud/paid production option, **When** the choice is presented, **Then** the local/free option is the default and the paid/cloud option is explicitly labeled as paid and off-machine, in plain language.
2. **Given** the operator changes nothing, **When** the production launches, **Then** zero paid or off-machine options are enabled — every such option requires an explicit act of the operator during the brief.
3. **Given** the chosen deliverable needs a capability the machine cannot provide, **When** the operator reaches the point where it matters (at the latest, the review), **Then** the brief explains what is missing in plain language and points to where it can be resolved (the models area), instead of failing at launch.
4. **Given** any step of the flow, **When** a provider credential would be relevant, **Then** the interface never offers a way to enter or view a secret — it states that keys are configured outside the app, consistent with the umbrella.

---

### User Story 5 - Life interrupts: the draft survives (Priority: P5)

An operator who leaves mid-brief — navigating elsewhere, closing the app, or losing
the studio service — finds their in-progress brief waiting when they come back: the
Guided Brief offers to **resume the draft** (with every answer restored) or to discard
it and start fresh. Drafts live on the operator's machine only.

**Why this priority**: Draft resilience turns the brief from a form you must finish in
one sitting into a workspace — important for real agency life, but the flow is fully
usable without it, so it ships last.

**Independent Test**: Answer several questions, restart the application, reopen the
Guided Brief, and verify the resume offer restores every answer; discard and verify a
clean start.

**Acceptance Scenarios**:

1. **Given** a brief in progress, **When** the operator navigates away or the application closes, **Then** the answers given so far are kept on the local machine without any explicit "save" action.
2. **Given** a stored draft exists, **When** the operator returns to the Guided Brief, **Then** they are offered the choice to resume it (all answers restored, at the step they left) or discard it — never silently overwritten, never forced to resume.
3. **Given** the operator discards the draft, **When** the flow restarts, **Then** no trace of the previous answers appears.
4. **Given** a draft is stored, **When** its content is examined, **Then** it contains only the operator's own answers and choices — no secrets, nothing sent off the machine.

---

### Edge Cases

- **Empty or unusable intent from home**: arriving with a blank or whitespace-only intent behaves like arriving with none — the flow simply asks for it (US1, scenario 2).
- **Deliverable type changed mid-flow**: answers still relevant to the new type are preserved; answers that no longer apply are set aside (not silently reused), and the operator is told which questions are newly relevant.
- **Very long free-text answers**: long intents/messages are accepted up to a generous, stated limit; over-limit input is flagged in plain language, never truncated silently.
- **Interface language switched mid-brief**: the flow re-renders in the new language with every answer intact (umbrella guarantee); the *deliverable* language choice is untouched by the switch.
- **Deliverable language vs interface language**: an operator using the FR interface can order an EN deliverable and vice versa; the two settings never overwrite each other (umbrella FR-009a).
- **Taxonomy empty on first run**: the attachment step still renders — offering "no client (unassigned)" and inline creation — and never blocks progress.
- **Client deleted between draft and resume**: a resumed draft whose attached client no longer exists surfaces the attachment step again instead of launching with a dangling reference.
- **Studio service unreachable during the flow**: the operator can keep answering (the flow itself is local); reachability matters only at taxonomy lookups and launch, where the shell's plain-language connection state applies and nothing is lost.
- **Double launch**: the launch action is protected against double activation — one completed brief yields one production.
- **Concurrent drafts**: only one in-progress brief draft exists at a time; starting a new brief while a draft exists always goes through the resume-or-discard choice (US5, scenario 2).

## Requirements *(mandatory)*

### Functional Requirements

**Intent & question flow**

- **FR-001**: The Guided Brief MUST accept the intent stated on the magic box home as its starting point, shown editable at the start of the flow; entering the screen without prior intent MUST lead to an identical flow that first asks for the intent.
- **FR-002**: The screen MUST guide the operator through an ordered sequence of plain-language questions that adapts to the chosen deliverable type and sector/domain — only questions relevant to the chosen production are asked.
- **FR-003**: The flow MUST support, at minimum, the deliverable types required by the brick's exit criterion — a research-type deliverable, a strategy-type deliverable, and a video deliverable — and MUST be structured so that adding a deliverable type means adding a question set, not redesigning the flow.
- **FR-004**: The flow MUST establish the sector/domain context via a guided choice (curated list of common sectors with a free-text "other"), and that context MUST parameterize the wording and defaults of later questions.
- **FR-005**: Every question beyond the essential minimum (intent, deliverable type, deliverable language) MUST offer a sensible default or an explicit skip; accepting all defaults MUST still yield a complete, launchable brief.
- **FR-006**: The flow MUST show progress (where the operator is, how much remains) and allow moving backward and forward between steps without any loss of already-given answers.
- **FR-007**: All flow text — questions, choices, helper text, validation messages — MUST be phrased in plain production language (tone-of-voice rules of the umbrella design system; no internal machinery terms) and MUST come from the umbrella's EN/FR locale catalogs (no hardcoded strings, complete in both languages).

**Deliverable language**

- **FR-008**: The brief MUST include an explicit choice of the language the deliverable is to be produced in; it MUST default to the current interface language but remain freely changeable, and MUST remain independent of the interface language thereafter (umbrella FR-009a).

**Client attachment (Brick 6)**

- **FR-009**: The flow MUST offer an optional attachment step where the operator can pick an existing client (and optionally drill into project/campaign) from the Brick 6 taxonomy, pre-selecting the shell's active client context when one is set.
- **FR-010**: The operator MUST be able to create a new client inline by providing just a name; richer taxonomy management stays outside the brief.
- **FR-011**: Skipping attachment MUST always be possible; the launched production then lands in the "unassigned" bucket, attachable later from the library (umbrella FR-013a). An empty taxonomy MUST never block the flow.

**Cost, network & capability transparency**

- **FR-012**: Every brief choice that enables a paid or off-machine production option MUST present the local/free option as the default and label the paid/cloud alternative explicitly as such, in plain language; a brief launched with no explicit operator action on these choices MUST enable zero paid or off-machine options.
- **FR-012a**: The mission's internet research (the engine researching and citing sources — free, subscription-covered, and exempt from the network opt-in rule per Constitution Principles III and IV) MUST be enabled by default in every brief, presented in plain language, and remain switchable off by the operator; it does not count as a paid or off-machine option under FR-012.
- **FR-013**: When the chosen deliverable requires a capability the operator's machine cannot currently provide, the brief MUST surface this in plain language before launch — at the latest on the review — with guidance toward resolution (the models area), instead of letting the launch fail technically.
- **FR-014**: No surface of the Guided Brief may accept, display, or persist API keys or other secrets (umbrella FR-015); where credentials are relevant, the flow states that they are configured outside the application.

**Review & launch**

- **FR-015**: Completing the flow MUST lead to a single review presenting every answer and every effective option of the brief in plain language — including defaulted values that affect the production — with nothing the production will use left invisible.
- **FR-016**: From the review, the operator MUST be able to edit any answer and return to the review with all other answers intact.
- **FR-017**: A single, clearly labeled action MUST launch the brief as a production through the studio's existing local mission interface, carrying the operator's goal and answers verbatim, their explicit options, and the client attachment — adding nothing the operator did not choose and changing no mission semantics (umbrella FR-016; Constitution Principles III and X).
- **FR-018**: On successful launch, the operator MUST be routed to the mission-following surface for that production (or, until S3 ships, its localized placeholder), and the launched brief MUST remain consultable.
- **FR-019**: On a rejected launch or unreachable service, the screen MUST show a plain-language, localized explanation, preserve the full brief, and allow retry or further editing; a failed launch MUST never lose answers. The launch action MUST be protected against double activation.

**Draft persistence**

- **FR-020**: An in-progress brief MUST be kept automatically on the operator's machine (local, non-secret, never synced or sent anywhere) across navigation and application restarts.
- **FR-021**: Returning to the Guided Brief with a stored draft MUST offer an explicit resume-or-discard choice; resume restores every answer at the step the operator left, discard leaves no trace. At most one in-progress draft exists at a time.

**Foundation compliance**

- **FR-022**: The screen MUST be built on the umbrella foundations — shell navigation, i18n mechanism, design system components and shared states (loading/empty/error), and WCAG 2.1 AA accessibility rules (full keyboard operability, screen-reader labels, AA contrast, visible focus) — re-inventing none of them.
- **FR-023**: All Guided Brief behavior — flow logic, parameterization, review, launch handoff, draft persistence, blockers — MUST be covered by automated tests that run fully offline (no network, no CLI agents, no live services), with the launch boundary exercised against a simulated service.

### Key Entities

- **Brief**: The complete, structured result of the flow — intent, deliverable type, sector/domain, type-specific answers, deliverable language, client attachment, and explicitly chosen production options. Exists as a draft during the flow, becomes launch-ready at review, and remains consultable after launch.
- **Question Flow**: The ordered, adaptive sequence of steps for one deliverable type × sector/domain combination; each step carries a question, its answer choices or input, its default/skip behavior, and its localized wording.
- **Deliverable Type**: A named kind of production the agency can deliver (research dossier, strategy dossier, video, …); determines which question set the flow uses and which capabilities matter at preflight.
- **Sector / Domain**: The business context of the production (e.g. food & beverage, sport, events), chosen from a curated list or free text; parameterizes question wording and defaults.
- **Production Option**: A brief-level choice affecting how the mission runs (e.g. cloud vs local video rendering); carries a plain-language label, a free/local default, and an explicit paid/off-machine marker where applicable.
- **Brief Draft**: The locally persisted in-progress brief — answers given so far plus the operator's position in the flow; at most one at a time; resumable or discardable.
- **Client Attachment**: The optional link from a brief to a Brick 6 client (and optionally project/campaign); absent ⇒ the production is "unassigned".

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A non-technical test user goes from stated intent to a launched production in under 5 minutes, unassisted, for each supported deliverable type.
- **SC-002**: At least 90% of first-time test users complete the brief on their first attempt without external help, and 100% of them can correctly say, at the review, what will be produced, in which language, and for which client.
- **SC-003**: 100% of the answers and effective options of a brief are visible on the review, and 100% of them are editable from it without losing any other answer.
- **SC-004**: Briefs launched with all defaults enable zero paid or off-machine options — verified by automated inspection of every launch request in the test suite.
- **SC-005**: The full flow is operable with the keyboard alone and passes the umbrella's WCAG 2.1 AA checks on every step; 100% of flow strings resolve from the EN and FR catalogs with zero missing keys.
- **SC-006**: An interrupted brief (navigation away, application restart) restores 100% of its answers on resume, and a failed launch preserves 100% of the brief.
- **SC-007**: The wording audit finds zero internal machinery terms (departments, engines, pipelines, flags, environment variables) in any flow surface, in both languages.
- **SC-008**: The offline test suite — existing plus new Guided Brief coverage — passes with no network, no CLI agents, and no live services.
- **SC-009**: With S2 shipped, an operator can perform the first half of the brick's exit journey (intent → brief → launched mission) end-to-end through the application, unassisted.

## Assumptions

- **Curated question sets, not generated ones**: v1 question flows are deterministic, curated per deliverable type (parameterized by sector/domain) — simple, predictable, and fully offline-testable (Constitution VII); confirmed by clarification 2026-07-06. Agent-assisted brief enrichment can layer on later without changing this screen's contract.
- **Three deliverable types at v1**: research-type, strategy-type, and video deliverables — the minimum the brick's exit criterion (research → strategy → video → export) requires. The flow's structure treats deliverable types as data (question sets), so Brick 8 recipes can extend the list without redesign.
- **Advanced production tuning stays out of the flow entirely (v1)**: expert-level mission knobs (e.g. specialist-army escalation budget, source-verification thresholds) receive sensible defaults and are not exposed anywhere in the v1 flow (clarified 2026-07-06); the effective defaults that affect the production remain visible on the review (FR-015), and a fine-tune step can be added later without restructuring the flow.
- **The mission's research honesty is upstream**: the brief transmits the operator's answers verbatim; sourcing, citation, and inspection guarantees (Constitution III) are enforced by the mission loop and Brick 3, not by this screen.
- **Existing local interfaces suffice**: launching uses the studio's existing local mission interface, including its taxonomy fields, option flags, and capability preflight; S2 adds no new service semantics and no new outbound network behavior.
- **Imported material comes later**: referencing imported documents/images as brief inputs is S5's scope; S2's flow is designed so an "attach material" step can be inserted without restructuring.
- **Drafts are single and local**: one in-progress draft at a time, stored on the operator's machine alongside the umbrella's other local, non-secret preferences; multi-draft management is not a v1 need.
- **Desktop-first, EN/FR only**: as set by the umbrella — desktop/laptop browser, two interface locales, deliverable language freely choosable beyond those two if the mission supports it (the choice field is not limited to EN/FR).
