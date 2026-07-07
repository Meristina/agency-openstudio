# Feature Specification: S1 Home

**Feature Branch**: `015-s1-home`

**Created**: 2026-07-07

**Status**: Draft

**Input**: User description: "lance le cycle S1 Home"

## Clarifications

### Session 2026-07-07

- Q: Should Home's recent-missions list be scoped to the active default working context, or show recent work across all contexts? → A: All contexts (global) — most-recent-first regardless of context, nothing hidden when the user switches context.
- Q: When the user selects a completed mission from Home, where should it open? → A: By state, reusing existing surfaces — an in-progress mission (the live/last run) opens the mission timeline; a completed mission opens its delivered work in the Library. (Planning reconciliation: no per-mission dossier-by-id view exists — the timeline shows only the live run and completed work lives in the Library — so a single shared destination would require an out-of-scope new route; this keeps S1 additive.)
- Q: How many recent missions should Home show at a glance? → A: Up to 5 most-recent, with a link to the Library (the full browsable list of work) for more. (Planning note: `#/missions` shows only the live/last run, not a browsable list, so "see more" points to the Library.)
- Q: Should Home display the active default working context as a read-only orientation label? → A: Yes — a small non-editable indicator of the active context (editing stays in S8 Settings).

## User Scenarios & Testing *(mandatory)*

S1 is a child spec of Brick 7 ("the magic box"). Its siblings — the Guided Brief
(S2), Mission Timeline (S3), Deliverable Library (S4), Import (S5), Export (S6),
Capability & Model panel (S7), and Settings (S8) — have all shipped. Home is the
**one entry point** every non-technical user lands on first, and today it is the
thinnest screen in the studio: a single question and a text box that starts a brief.

S1 **enriches the Home screen** so that the entry point does three jobs instead of
one: it invites the user to **start** new work, lets them **resume** work already in
progress, and helps them **orient** toward the rest of the studio — all without
touching a terminal, and all *additive* to the existing question → brief flow, which
stays the primary action and keeps working exactly as before.

### User Story 1 - Start new work from a calm, welcoming entry point (Priority: P1)

A non-technical user opens the studio and lands on Home. They read a single plain
question ("What do you want to produce?"), type what they want in their own words,
and start a guided brief. The entry point feels like a deliberate front door — not a
bare form — but starting work is still one obvious action away.

**Why this priority**: This is the reason Home exists and the load-bearing flow of
the entire magic box — every mission begins here. It must keep working byte-for-byte
in behavior (intent text carries into the brief) while reading as a finished,
inviting screen. It is the minimum viable Home and delivers value entirely on its
own, even if no other story ships.

**Independent Test**: Open Home, type an intent, start the brief, and confirm the
guided brief opens pre-filled with exactly the typed intent — identical to today's
behavior — from a screen that now presents itself as a real home rather than a stub.

**Acceptance Scenarios**:

1. **Given** the Home screen is open, **When** the user types an intent and starts,
   **Then** the guided brief opens carrying that intent unchanged (the existing
   `#/brief?intent=…` flow is preserved).
2. **Given** the Home screen is open with an empty intent, **When** the user starts,
   **Then** the guided brief still opens (an intent is optional, matching today).
3. **Given** the interface language is switched (English ↔ French), **When** Home is
   shown, **Then** every element on Home — question, labels, actions, and any new
   copy — appears in the selected language with no missing or hard-coded strings.

---

### User Story 2 - Resume work already in progress (Priority: P2)

The same user rarely starts from zero. When they return, Home shows what they were
last doing so they can pick it back up in one click: an **unfinished brief** they
started but did not submit, and their **recent missions** (in-progress or recently
completed). Selecting one takes them straight back to it — the brief they were
filling, or the mission's timeline / its delivered work.

**Why this priority**: Resumption is what turns Home from a launcher into a workspace.
A non-technical user should never have to remember a mission name, hunt through the
Missions or Library screens, or re-type a half-finished brief. This is high value but
still secondary to the core start flow, and it degrades gracefully to Story 1 when
there is nothing to resume.

**Independent Test**: Start a brief without submitting it and run at least one
mission, then reopen Home; confirm the unfinished brief and the recent mission both
appear, and that selecting each navigates to the correct place (the in-progress
brief, and the mission's timeline or delivered output).

**Acceptance Scenarios**:

1. **Given** an unfinished brief draft exists, **When** Home loads, **Then** a
   "resume your brief" affordance appears, and selecting it reopens the guided brief
   at the point the user left off (not a blank brief).
2. **Given** one or more recent missions exist, **When** Home loads, **Then** Home
   lists up to the 5 most recent (across all contexts, most-recent-first) with a
   plain-language label and status, and selecting one opens the right existing surface
   for its state — the live mission timeline if it is in progress, its Library
   deliverable if it is complete.
3. **Given** no unfinished brief and no missions exist yet, **When** Home loads,
   **Then** the resume area shows a calm empty state that points back to starting new
   work — never an error, a spinner that never resolves, or a broken panel.
4. **Given** the local studio server cannot return recent work, **When** Home loads,
   **Then** Home still renders the start flow fully and shows an honest, non-alarming
   note that recent work could not be loaded (Story 1 is never blocked by Story 2).

---

### User Story 3 - Orient toward the rest of the studio (Priority: P3)

A newer user wants to understand what the studio can do and move around it. Home
offers a small set of **clearly labeled shortcuts** to the main areas — see finished
deliverables (Library), bring in existing material (Import), and check which models
this machine will use (Models) — so the whole studio is reachable from the front door
without relying only on the navigation chrome.

**Why this priority**: Orientation lowers the first-run cliff and makes Home feel like
a hub, but the studio is already fully navigable without it, so it is the lowest
priority and purely additive.

**Independent Test**: From Home, use each shortcut and confirm it lands on the correct
screen (Library, Import, Models), and that removing this story would leave Stories 1–2
fully functional.

**Acceptance Scenarios**:

1. **Given** the Home screen is open, **When** the user selects a shortcut, **Then**
   the corresponding screen opens (Library / Import / Models).
2. **Given** the shortcuts are shown, **When** the user reads them, **Then** each is
   labeled in plain, non-technical language in the active interface language.

---

### Edge Cases

- **No history at all (first run)**: Home shows the start flow and a welcoming empty
  state for resume — never a blank or broken region.
- **Stale or invalid brief draft**: if the saved draft cannot be reopened cleanly,
  Home offers to start fresh instead of trapping the user in a broken resume.
- **Long or empty mission goals**: a recent mission with a very long goal is shown
  truncated but readable; one with no goal still shows a sensible label and status.
- **Recent-work list is large**: Home shows only a small, most-recent subset (a
  "recent" glance, not the full list) and lets the user go to the Library — the full
  browsable list of work — for more.
- **Server offline / slow**: the start flow renders immediately; recent work loads
  independently and fails soft with an honest message, never a false "empty".
- **Language switch while on Home**: all copy, including newly added sections, updates
  live with the rest of the interface.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Home MUST remain the single default entry point of the studio (the empty
  route resolves to Home) and MUST present a single, plain-language prompt inviting the
  user to describe what they want to produce.
- **FR-002**: Home MUST preserve the existing start flow exactly: an optional free-text
  intent that, on start, opens the guided brief carrying that intent unchanged.
- **FR-003**: Home MUST surface an unfinished brief, when one exists, and allow the user
  to resume it at the step they left off rather than starting a blank brief.
- **FR-004**: Home MUST surface a short, most-recent-first list of the user's recent
  missions (up to 5, with a link to the Library for the full browsable list) with a
  plain-language label and an honest status (e.g. in progress / delivered), and MUST let
  the user open any of them. The list MUST span all working contexts (global
  most-recent-first) — it is NOT scoped to the active default context, so a mission run
  under any context still appears.
- **FR-005**: Selecting a recent mission MUST navigate to the right existing surface for
  its state — an **in-progress** mission (the live/last run) MUST open the mission
  timeline; a **completed** mission MUST open its delivered work in the Library (focused
  on that mission). S1 MUST reuse these existing destinations and MUST NOT introduce a
  new per-mission view.
- **FR-006**: Home MUST provide clearly labeled shortcuts to the studio's main areas
  (at minimum Library, Import, and Models) that navigate to those screens.
- **FR-007**: Home MUST degrade gracefully: when there is no unfinished brief and no
  recent missions, it MUST show a calm empty state that guides the user back to starting
  new work, and MUST never block the start flow on the availability of recent work.
- **FR-008**: When recent work cannot be loaded (e.g. the local server is unreachable),
  Home MUST render the start flow fully and show an honest, non-alarming message instead
  of a false "no work" state or an unresolved loading state.
- **FR-009**: All Home copy — existing and newly added — MUST be fully internationalized
  (English and French) with no hard-coded or missing strings, and MUST update live when
  the interface language changes.
- **FR-010**: Home MUST honor the studio's local-first, honest-labeling principle: it
  MUST NOT invent recent work, MUST NOT claim work is delivered when it is not, and MUST
  reflect only the actual state reported by the local studio.
- **FR-011**: Home MUST be fully operable by a non-technical user with pointer or
  keyboard alone — no terminal, config file, or technical identifier (raw mission IDs,
  paths) required to start, resume, or navigate.
- **FR-012**: Home MUST display the active default working context (client / project /
  campaign) as a read-only orientation label so the user can see what new work will be
  scoped to; editing the context stays in S8 Settings (Home never edits it). When no
  default context is set, the label MUST show a plain "no context / all work" state
  rather than appearing broken or empty.

### Key Entities *(include if feature involves data)*

- **Intent**: the free-text description of what the user wants to produce; optional;
  carried into the guided brief unchanged. Not persisted by Home beyond the current
  entry action.
- **Unfinished brief (draft)**: the most recent guided-brief-in-progress the user has
  not yet submitted; has enough state to reopen the brief where it was left. Home reads
  and offers it; it is owned/persisted by the brief flow, not created by Home.
- **Recent mission (summary)**: a lightweight view of a past or in-progress mission —
  a human-readable goal/label and a status — sufficient to display and to open it. Home
  reads these from the local studio (up to 5, global most-recent-first); it does not
  create or modify missions.
- **Active working context (read-only)**: the current default client / project /
  campaign that new work is scoped to, owned and edited by S8 Settings. Home only reads
  and displays it as an orientation label; it never changes it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a cold open, a first-time user can start a guided brief from Home in
  a single deliberate action (type intent → start), with no regression versus today's
  intent → brief behavior.
- **SC-002**: A returning user with work in progress can resume either their unfinished
  brief or a recent mission in **one selection** from Home, without visiting the Missions
  or Library screens first.
- **SC-003**: 100% of Home's visible text renders correctly in both English and French,
  with zero hard-coded or missing strings, verified by switching languages on Home.
- **SC-004**: When the local studio cannot provide recent work, Home still lets the user
  start a new brief 100% of the time, and never displays a false "no recent work" or a
  perpetual loading state.
- **SC-005**: A user who has never run a mission sees a welcoming, non-broken Home (start
  flow + guided empty state), with no error, blank panel, or dead control.
- **SC-006**: Every shortcut and every resume affordance on Home navigates to the correct
  screen/state on the first attempt.
- **SC-007**: Home correctly reflects the active default working context as a read-only
  label 100% of the time — matching what S8 Settings holds — and shows a clear "no
  context" state when none is set, never a blank or stale value.

## Assumptions

- **Redesign, not net-new**: Home is an existing shipped screen; S1 enriches it
  additively and MUST NOT regress the current question → brief entry flow.
- **Reuses existing surfaces**: recent missions come from the studio's existing mission
  list, and the unfinished brief comes from the brief flow's existing saved draft; S1
  does not introduce a new persistence store of its own.
- **"Recent" is a glance, not the full list**: Home shows only a small, most-recent
  subset of missions; the Library remains the place to browse the full list of work
  (`#/missions` shows only the live/last run, not a browsable list).
- **Scope is the Home screen only**: S1 does not change the guided brief, the mission
  timeline, the library, or the navigation chrome beyond linking to them; it changes
  what the entry point presents.
- **Two languages**: English and French, matching the rest of the magic box; no
  additional locales in scope for this cycle.
- **Local-first**: all data shown originates from the local studio server; Home makes no
  network calls of its own and reflects only real, local state.
- **Default working context** (client/project/campaign, from S8 Settings) continues to
  apply to work started from Home; S1 *displays* it read-only for orientation and
  surfaces entry and resumption, but never edits it — context editing stays in S8.
