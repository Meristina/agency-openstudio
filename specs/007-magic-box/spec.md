# Feature Specification: The Magic Box — App Shell, Navigation, i18n & Screen Inventory (Brick 7 umbrella)

**Feature Branch**: `007-magic-box`

**Created**: 2026-07-05

**Status**: Draft

**Input**: User description: "Brick 7 — The magic box (full custom UI redesign). The current GUI is a developer-facing console; a non-technical agency user can't drive it end to end. Brick 7 is a new front-end application built around one promise: a single entry point — 'what do you want to produce?' — that guides an ordinary user from intent to a finished, exported deliverable without touching a terminal or understanding the department machinery underneath. This umbrella spec establishes the app-level foundation and the screen inventory; each screen then gets its own spec-kit cycle. In scope for the whole application: (1) a single-entry 'magic box' home; (2) a guided brief flow parameterized by sector / domain / deliverable type; (3) a live mission timeline in human terms; (4) a per-client deliverable library; (5) import of existing material as mission input; (6) export bundles (PDF / media zip / full dossier); (7) EN/FR internationalization across every screen; (8) the Brick 4 capability & model panel embedded in the app. Builds on the Brick 6 client/project/campaign taxonomy and Brick 4 capability selection. Additive and local-first: no change to agency-kit's mission loop, security invariants preserved, offline suite green. UX references: AnythingLLM (workspace = project) and Jan (local-first). This spec defines the app shell, navigation, the shared design system / i18n scaffolding, and the enumerated list of screens each needing its own downstream spec — it does NOT fully specify each screen's internals."

## Scope of this umbrella spec

This spec covers the **application foundation only**: the app shell (frame, navigation,
global states), the shared design system and internationalization scaffolding, and the
**authoritative screen inventory** — the enumerated list of screens that each receive
their own downstream spec-kit cycle. The internals of each screen (brief questions,
timeline visuals, library layouts, export options…) are explicitly **out of scope
here** and deferred to the child specs listed in the Screen Inventory section.

The brick's overall exit criterion — a non-technical user produces a complete
deliverable (research → strategy → video → export) unassisted — is owned by Brick 7 as
a whole and is met only once the child screen specs ship. It is recorded here as a
brick-level success criterion (SC-010) so it is never lost, but it is not a merge gate
for this umbrella feature.

## Clarifications

### Session 2026-07-05

- Q: When the Brick 7 shell lands, is the magic box the default surface immediately, or opt-in until child screens ship? → A: Magic box is the default landing surface as soon as the shell merges; the existing developer console stays fully functional at a secondary location until parity.
- Q: What accessibility baseline must the Brick 7 design system (and every child screen) meet? → A: WCAG 2.1 AA — full keyboard operability, screen-reader labels, AA contrast, visible focus — enforced as design-system rules all child screens inherit.
- Q: Must the user choose (or create) a client before starting a production? → A: Optional — the user can produce immediately; work lands in an "unassigned" bucket and can be attached to a client/project/campaign during the brief or later from the library.
- Q: Does EN/FR internationalization cover the interface only, or also the language of produced deliverables? → A: Interface only — EN/FR governs all UI text; deliverable language is chosen per production in the guided brief (owned by S2's downstream spec), independent of the UI language.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single entry point: "What do you want to produce?" (Priority: P1)

A non-technical agency operator opens the studio and lands directly on the magic box
home: one welcoming question — "What do you want to produce?" — with no terminal, no
developer console, and no department machinery visible. From that single entry point
they can start a new production (which routes them into the guided brief) or reach any
other area of the application (their library, a running mission, imports, exports,
settings, the model panel) through one persistent, plainly-worded navigation.

**Why this priority**: The single entry point is the brick's founding promise
(Constitution Principle VIII) and the frame every other screen hangs from. Without the
shell and navigation, no child screen has a home; with them, even placeholder screens
already deliver a coherent, navigable application.

**Independent Test**: Launch the application as a first-time user and verify the
landing surface is the magic box question, that every inventoried area is reachable
from the persistent navigation, and that no step requires a terminal or exposes
developer tooling.

**Acceptance Scenarios**:

1. **Given** a fresh launch of the studio application, **When** the user opens it, **Then** the first surface shown is the magic box home asking "What do you want to produce?" with a visible way to answer it.
2. **Given** the user is on any screen of the application, **When** they look at the persistent navigation, **Then** every top-level area of the screen inventory is reachable, labeled in plain production language (produce, library, missions, import, export, models, settings) — never in internal machinery terms.
3. **Given** the user answers the home question or picks "start producing", **When** they proceed, **Then** they are routed into the guided brief entry (the child screen), carrying their stated intent with them.
4. **Given** any navigation action in the application, **When** the user performs it, **Then** at no point are they required to open a terminal, edit a file, or set an environment variable.

---

### User Story 2 - The whole application speaks my language (EN/FR) (Priority: P2)

A French-speaking (or English-speaking) agency operator switches the application
language once and the entire visible interface — navigation, screen titles, buttons,
empty states, errors — follows immediately, on every screen, and stays that way the
next time they open the studio.

**Why this priority**: EN/FR i18n is declared in scope "across every screen"; if the
scaffolding is not laid at shell level first, every child screen would hardcode text
and retrofitting would be invasive. It is the second foundation the child specs build
on.

**Independent Test**: Toggle the language switcher on each existing shell surface and
verify every visible string changes locale immediately and the choice survives an
application restart.

**Acceptance Scenarios**:

1. **Given** the application is displayed in English, **When** the user switches the language to French, **Then** all visible shell text (navigation, titles, actions, states) renders in French without losing the user's current place in the application.
2. **Given** a language was chosen in a previous session, **When** the user reopens the application, **Then** it opens in that language without being asked again.
3. **Given** a first-ever launch with no stored choice, **When** the application starts, **Then** it picks EN or FR from the user's system/browser preference, defaulting to English when neither matches.
4. **Given** a translation is missing for a given string in the active language, **When** that string is displayed, **Then** the English text is shown (never a raw internal key or blank).

---

### User Story 3 - My work is organized by client (Priority: P3)

An agency operator navigating the application always sees their work through the
client → project → campaign lens established by Brick 6: the navigation exposes a way
to pick the active client context, and the library and mission areas present work
grouped by that taxonomy rather than as one flat technical list.

**Why this priority**: The library and history are declared "organized by" the Brick 6
taxonomy; anchoring that context in the shell (rather than per-screen) keeps every
child screen consistent and lets the operator think in agency terms (clients, not
mission IDs).

**Independent Test**: With at least one client/project/campaign registered, verify the
shell offers a client context selector, and that entering the library area shows work
scoped and grouped by the selected client.

**Acceptance Scenarios**:

1. **Given** clients exist in the taxonomy, **When** the user opens the client selector in the shell, **Then** they can browse and choose among their clients (and drill into projects/campaigns).
2. **Given** a client context is selected, **When** the user navigates to the library or missions area, **Then** the content presented is scoped to that client and grouped by its projects and campaigns.
3. **Given** no client exists yet (first run), **When** the user opens the application, **Then** the shell presents a friendly starting state that lets them begin producing anyway — the absence of taxonomy never blocks the magic box.
4. **Given** work was produced with no client selected, **When** the user browses the library, **Then** that work appears in a visible "unassigned" bucket from which it can be attached to a client/project/campaign at any time.

---

### User Story 4 - Models and capabilities without leaving the app (Priority: P4)

An agency operator who wants to check what their machine can produce locally — or
deliberately opt into a paid cloud provider — reaches the capability & model panel
(Brick 4) from the application's navigation as a first-class screen, phrased in the
same plain language and localized like everything else.

**Why this priority**: The model panel already exists (Brick 4); embedding it is
integration work, not invention — valuable but not blocking the shell, i18n, or
taxonomy foundations.

**Independent Test**: Navigate to the models area from the shell and verify the Brick
4 capability/model information is displayed inside the application shell, localized,
with free/local versus paid/cloud choices explicit.

**Acceptance Scenarios**:

1. **Given** the user is anywhere in the application, **When** they choose the models area in the navigation, **Then** the Brick 4 capability & model panel is presented inside the app shell (same navigation, same language setting).
2. **Given** the panel presents model choices, **When** a choice involves a paid cloud provider, **Then** it is explicitly marked as paid/opt-in, and local free options remain the default (no silent paid selection).
3. **Given** the panel needs a provider credential, **When** the user looks for where to enter it, **Then** the application never offers a field to type an API key — it explains that keys are configured in the environment (power-user override), consistent with the security invariants.

---

### User Story 5 - Not-yet-built areas fail gracefully (Priority: P5)

An agency operator who navigates to an area whose dedicated screen has not shipped yet
(because its child spec is still downstream) sees a friendly, localized "coming soon"
surface inside the shell — never a broken page, a developer console, or a dead end —
and can always get back to the magic box home.

**Why this priority**: The umbrella ships before the child screens by design; the
shell must make that intermediate state presentable so the application is releasable
at every point of the brick's life.

**Independent Test**: Navigate to each inventoried area before its child spec ships
and verify a localized placeholder renders within the shell with a working way home.

**Acceptance Scenarios**:

1. **Given** an inventoried screen whose child spec has not shipped, **When** the user navigates to it, **Then** a localized placeholder explains the area is coming and offers a way back to the home.
2. **Given** the user enters an address/route that does not exist at all, **When** the application resolves it, **Then** a localized not-found state is shown inside the shell with a way back to the home (never a blank or developer error page).
3. **Given** the local studio service is unreachable, **When** the user opens or uses the application, **Then** a localized, plain-language connection message is shown (never raw technical errors), and the application recovers once the service is back.

---

### Edge Cases

- **Missing translation key**: the English string is displayed as fallback; a missing-key situation is detectable in tests so catalogs stay complete (see FR-007).
- **Unknown route / deep link to a removed screen**: localized not-found state inside the shell, one action back to home.
- **Local service down or restarting**: shell renders with a plain-language connection state; no loss of the user's language/context choices, automatic recovery on reconnect.
- **First run, empty taxonomy, empty library**: every area presents a guided empty state pointing back to "produce something"; nothing assumes existing data.
- **Language switched mid-task**: the current screen re-renders in the new language without losing state (no forced navigation reset).
- **Two areas open in sequence with different client contexts**: the active client context is a single, shell-owned selection; changing it updates all scoped areas consistently.
- **Small window / laptop half-screen**: the shell navigation remains usable at common laptop widths; no horizontal dead zones that hide navigation items.

## Requirements *(mandatory)*

### Functional Requirements

**App shell & navigation**

- **FR-001**: The application MUST present, as its default landing surface, a single-entry magic box home whose primary interaction is the question "What do you want to produce?" routing the user toward the guided brief.
- **FR-002**: The application MUST provide a persistent navigation from which every top-level area in the Screen Inventory is reachable, labeled in plain, non-technical production language and localized.
- **FR-003**: No shell interaction (navigation, language change, client-context change, reaching any inventoried area) may require a terminal, file editing, or environment configuration; environment variables remain a power-user override only.
- **FR-004**: The shell MUST render a localized placeholder state for every inventoried screen whose dedicated spec has not shipped, and a localized not-found state for unknown routes, each with a working path back to home.
- **FR-005**: The shell MUST surface the reachability of the local studio service in plain language (connected / not reachable) and recover automatically when the service returns, without losing user context.

**Internationalization (EN/FR)**

- **FR-006**: Every user-visible string in the shell and its screens MUST come from a locale message catalog; hardcoded user-facing strings are not permitted in any Brick 7 surface.
- **FR-007**: The application MUST ship complete EN and FR catalogs for all shell surfaces, fall back to English for any missing key, and make catalog completeness verifiable by automated test.
- **FR-008**: The user MUST be able to switch language from anywhere in the application; the choice takes effect immediately without losing the current screen state, persists across sessions, and the initial default follows the system/browser preference (English otherwise).
- **FR-009**: The i18n scaffolding MUST be the single mechanism child screens use for their own text (one catalog structure, one switching mechanism), so no child spec re-invents localization.
- **FR-009a**: EN/FR internationalization governs interface text only; the language of produced deliverables is a per-production choice made in the guided brief (owned by S2's downstream spec) and MUST NOT be coupled to the interface language.

**Design system**

- **FR-010**: Brick 7 MUST establish a shared design system — visual tokens (color, type, spacing), core interactive components (navigation elements, buttons, forms, lists, empty/error/loading states), and tone-of-voice rules (plain production language, no internal machinery terms) — that all child screens consume.
- **FR-011**: The design system MUST include the localized shared states (loading, empty, error, coming-soon, not-found) so every screen presents failure and absence consistently.
- **FR-011a**: The design system MUST meet WCAG 2.1 AA as its accessibility baseline — full keyboard operability, screen-reader labels on interactive elements, AA color contrast, and visible focus indicators — expressed as reusable design-system rules that every child screen inherits rather than re-implements.

**Taxonomy context (Brick 6)**

- **FR-012**: The shell MUST expose an active client context selector backed by the Brick 6 client/project/campaign taxonomy; taxonomy-scoped areas (library, missions) MUST present their content organized by that taxonomy.
- **FR-013**: The absence of any taxonomy data MUST never block use of the application; empty states guide the user toward producing their first deliverable.
- **FR-013a**: Client assignment MUST be optional at production time: the user can start producing with no client selected, the resulting work lands in a visible "unassigned" bucket, and it can be attached to a client/project/campaign during the brief or later from the library — never as a forced precondition.

**Embedded capability & model panel (Brick 4)**

- **FR-014**: The Brick 4 capability & model panel MUST be embedded as a first-class inventoried screen of the application — inside the shell, localized, with local/free defaults and paid/cloud choices explicitly marked opt-in.
- **FR-015**: No surface of the application may accept, persist, or display API keys or other secrets; provider credentials remain environment-only, and the interface states this where relevant.

**Foundation invariants**

- **FR-016**: Brick 7 MUST NOT change the mission loop, veto-loop behavior, or any agency-kit orchestration logic; it is a presentation layer over existing local service interfaces.
- **FR-017**: All existing security invariants MUST hold across the new application: served only from the local machine (127.0.0.1), no wildcard cross-origin access, path-traversal guards on every served file, HTTPS-only outbound, keys env-only.
- **FR-018**: The redesign MUST land additively: the magic box becomes the default landing surface as soon as the shell ships, while the existing developer console remains fully functional at a secondary location until the child screens reach parity, and the offline test suite stays green throughout.
- **FR-019**: The shell, navigation, i18n mechanism, shared states, and placeholder/not-found behavior MUST be covered by automated tests that run fully offline (no network, no CLI agents, no live services).

**Screen inventory governance**

- **FR-020**: This spec MUST enumerate the authoritative screen inventory (below); every inventoried screen MUST receive its own downstream spec-kit cycle (specify → clarify → plan → tasks → implement) before it is considered shipped, and no screen outside the inventory may ship under Brick 7 without first being added here.

### Screen Inventory *(authoritative — each entry gets its own downstream spec)*

| # | Screen | Purpose (one line) | Builds on | Downstream spec owns |
|----|--------|--------------------|-----------|----------------------|
| S1 | **Magic Box Home** | The single entry point: "What do you want to produce?" — intent capture, recent work, shortcuts into everything else. | Shell (this spec) | Intent capture design, suggestions, recent-work surface |
| S2 | **Guided Brief** | Turn intent into a complete mission brief through guided questions parameterized by sector / domain / deliverable type. | S1, Brick 6 taxonomy | Question flow, sector/domain/deliverable parameterization, deliverable language choice, brief review & launch |
| S3 | **Mission Timeline** | Follow a running mission live, in human terms: research → departments at work → synthesis → quality inspection, including fix loops, with cancel. | Existing mission events | Human-language event mapping, live progress presentation, cancel/error handling |
| S4 | **Deliverable Library** | Browse, search, and preview every finished deliverable, organized per client → project → campaign. | Brick 6 taxonomy | Library organization, previews, search/filter, per-deliverable actions |
| S5 | **Import** | Bring existing material (documents, images, briefs, videos) into the studio as mission input attached to a client or brief. | S2, S4, Brick 6 | Supported material types, attach-to-brief/client flows, validation & feedback |
| S6 | **Export** | Produce shareable bundles from work: PDF document, media zip, or full dossier. | S4 | Bundle composition, formats, per-client/per-mission export flows |
| S7 | **Capability & Model Panel** | See what this machine can produce and choose models — local/free by default, cloud/paid explicit — embedded from Brick 4. | Brick 4 panel | Embedding, localization, non-technical phrasing of capabilities |
| S8 | **Settings & Preferences** | Language, sensible defaults, and plain-language explanations of power-user options (never secret entry). | Shell i18n | Preference set, defaults management, environment-override explanations |

Cross-cutting concerns owned by this umbrella (not by child specs): navigation between
screens, EN/FR mechanism and catalogs, design system and shared states, client-context
selection, security invariants, placeholder behavior.

### Key Entities

- **App Shell**: The persistent frame of the application — navigation, language switcher, client-context selector, connection state, and the surface each screen renders into.
- **Screen (inventoried area)**: A named top-level destination with a route, a localized title, a lifecycle status (placeholder → specified → shipped), and an owning downstream spec.
- **Locale Catalog**: The complete set of user-visible strings for one language (EN, FR), keyed identically across languages, with English as the fallback source of truth.
- **Design System**: The shared visual tokens, components, tone-of-voice rules, and shared states all Brick 7 screens consume.
- **Client Context**: The shell-owned selection of active client (optionally project/campaign) drawn from the Brick 6 taxonomy, scoping taxonomy-aware screens.
- **User Preferences**: Locally persisted, non-secret choices — language, last client context, defaults — surviving restarts on the user's machine.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a cold start, a first-time user reaches the "What do you want to produce?" prompt without performing any technical action (no terminal, no configuration) — one launch, zero intermediate technical steps.
- **SC-002**: Every area in the screen inventory is reachable from anywhere in the application in at most 2 interactions.
- **SC-003**: Switching language updates 100% of visible interface text on every shell surface with no page reload and no loss of the user's place, and the choice persists across application restarts.
- **SC-004**: EN and FR catalogs are 100% complete for all shipped Brick 7 surfaces, verified by an automated completeness check (zero missing keys, zero raw-key leaks in rendered output).
- **SC-005**: 100% of inventoried screens either render their shipped experience or a localized coming-soon placeholder — zero broken pages, developer consoles, or dead ends across the inventory.
- **SC-006**: All 8 inventoried screens are enumerated with purpose, dependencies, and downstream ownership, such that each child spec-kit cycle can start from this document without re-deriving scope.
- **SC-007**: A non-technical test user, given only the running application, can correctly describe where to go to (a) start producing, (b) find past work for a client, and (c) change the language — 3 out of 3 — within their first 5 minutes, without assistance.
- **SC-008**: The full offline test suite (existing plus new shell/i18n/navigation tests) passes with no network, no CLI agents, and no live local services.
- **SC-009**: All pre-existing studio functionality remains available and behaviorally unchanged after the shell lands (additive delivery — zero regressions attributable to Brick 7 foundation work).
- **SC-010** *(brick-level exit criterion — met once all child screen specs ship, not a merge gate for this umbrella)*: A non-technical user produces a complete deliverable — research → strategy → video → export — entirely unassisted through the application.
- **SC-011**: Every shipped Brick 7 shell surface passes a WCAG 2.1 AA check: 100% of interactive elements operable by keyboard alone and exposing accessible labels, all text meeting AA contrast, and focus visibly indicated throughout.

## Assumptions

- **Coexistence over big-bang**: the redesigned application is the default landing surface from the moment the shell ships, while the existing developer-facing console remains available at a secondary location until the child screens reach parity; nothing in Brick 7's foundation removes existing surfaces (Constitution Principle X).
- **Two locales for v1**: EN and FR are the only languages in scope; the scaffolding is built so adding a locale later means adding a catalog, not touching screens (Constitution Principle XI keeps the repository itself English-only).
- **Desktop-first**: the primary target is a desktop/laptop browser window on the operator's own machine (local-first); tablet/phone layouts are out of scope for this brick.
- **Existing local interfaces suffice**: the shell consumes the studio's existing local service interfaces (missions, taxonomy, capabilities, media); Brick 7's foundation adds no new outbound network behavior and no new mission semantics.
- **Preferences are local and non-secret**: language and context choices persist on the user's machine only; no accounts, no sync, no server-side profiles.
- **Child spec numbering**: each inventoried screen enters its own spec-kit cycle as a subsequent numbered feature; this umbrella is the single source that orders and scopes them.
- **UX references are inspiration, not contracts**: AnythingLLM (workspace = project mental model) and Jan (local-first presentation) inform design choices in child specs; no compatibility with either product is implied.
