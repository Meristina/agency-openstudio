# Feature Specification: Capability & Model Panel — See What This Machine Can Produce and Choose Models (Brick 7 · Screen S7)

**Feature Branch**: `013-s7-capability-panel`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "lance le cycle S7 Capability Panel" — start the spec-kit cycle for screen S7 (Capability & Model Panel) of the Brick 7 magic-box inventory: surface the Brick 4 capability/model panel as a first-class, non-technical, localized screen inside the app shell — see what this machine can produce, and choose which model each capability uses, with local/free by default and cloud/paid explicit opt-in (per the authoritative screen inventory in `specs/007-magic-box/spec.md`, row S7).

## Scope

This spec covers the **Capability & Model Panel screen (S7)** only: the operator-facing surface through which a
non-technical user (a) **sees, in plain language, what this machine can produce** — images, video, voice/narration,
transcription, understanding, search/memory — and whether each is ready to use right now, and (b) **chooses which model
each capability uses**, or keeps the sensible built-in default, with **local/free options on by default** and **cloud/paid
options clearly marked as a deliberate opt-in**. It turns the Brick 4 capability inventory and selection mechanism into a
front-door screen a non-technical operator can read and operate — no terminal, no environment variables, no internal model
identifiers.

The **backend already exists** (Brick 4, done `6e71879` / #6): the studio already aggregates every registry into a passive
capability inventory (families, entries, availability, cost, active resolution) and already persists a **server-side model
selection** per capability family with an env-var override precedence (env > selection > built-in default). S7 adds **no new
backend, no new persistence store, and no new capability** — it is a **read-through-plus-select** operator surface over the
existing local capability interfaces, in the same spirit as S4/S6 (which mostly compose paths that already exist).

Today the magic box already routes `models` to a screen, but that screen embeds the **raw developer capability component
verbatim** — the same one shown in the developer Console: English-only hardcoded strings, raw internal family names
(`image`, `stt`, `tts`, `visual`), raw model identifiers shown as code, raw badges (`FREE/PAID`, `API`, `UNAVAILABLE`), and
raw machine reasons (`missing_binary`, `gateway_down`). It is a developer panel under a localized title, not an
operator-facing screen. S7's job is to **replace that thin raw embed with a real, non-technical, EN/FR-localized screen**:
plain-language capability names and descriptions, plain-language availability and cost, plain-language "how to enable it"
guidance when something isn't ready, and a simple "choose a model / keep the default / go back to the default" control — with
**zero internal identifiers or secrets** on the operator surface.

S7 is **machine-level, not per-client**: the models a machine can run are a property of the machine, not of a client,
project, or campaign — so this screen is **not** taxonomy-scoped (unlike S3/S4/S5/S6). It respects the shell, the persistent
navigation, the EN/FR language switch, the design system, and the shared loading/empty/error patterns established by the
Brick 7 umbrella.

S7 is **local-first and secret-free by construction**: reading the inventory and choosing a model triggers **no outbound
network of its own** beyond the studio's own local capability probing, which is existing Brick 4 behavior — S7 changes none
of it. Choosing a paid cloud provider records a **preference** only; it never sends anything to that provider and never
asks for, accepts, displays, persists, or transmits an API key. Keys remain **environment-only** (Constitution security
invariant; umbrella FR-015): the screen shows *whether* a paid entry's key is configured in the environment and *which*
environment variable enables it, but never a field to enter one.

Out of scope here: capturing intent (S1) and building the brief (S2); following a running production (S3); browsing,
previewing, or exporting finished deliverables (S4/S6); bringing in existing material (S5); general application settings —
language default, theme, data location, retention, and other non-capability configuration (S8, a separate screen); **adding,
installing, or downloading** a model, backend, binary, or extra (S7 *reports* what is installed and *how* to enable what is
not, mirroring the studio's 501-plus-install-hint contract — it is not an installer); **entering, storing, or managing API
keys or any secret** (keys stay environment-only, never a UI field); changing the **resolution precedence** or any Brick 4
selection semantics (env > selection > default is inherited unchanged); per-mission model overrides at brief time (a
possible future refinement — S7 sets the machine's standing default per capability, not a one-off per-mission choice); and
any change whatsoever to the mission loop, routing, synthesis, asset rendering, the inspector veto loop, the capability
probing/aggregation logic, the selection store's shape, or the shape of a saved dossier (umbrella FR-016; Constitution
Principles III, V, X, and agency-kit's veto-loop invariant). The existing developer Console capability panel remains
available at its secondary location (umbrella coexistence assumption); S7 is the operator-facing front door, not a
replacement for the console.

## Clarifications

### Session 2026-07-06

- Q: Which of the Brick 4 inventory families does S7 surface — only the user-selectable model families, or also the non-selectable ones (OpenMontage production tools, MCP integrations)? → A: **All families, read-through.** S7 shows every inventoried family so the operator sees the full picture of what this machine can produce; the model **chooser** is rendered only on the **selectable model families** (images, video, visual understanding, search/memory, knowledge extraction, transcription, narration). The **non-selectable** families (production tools, integrations/connectors) appear as **read-only** availability status with plain-language "how to enable it" guidance and no chooser — never a misleading selection control on something that offers no choice.
- Q: When the operator picks a model, what does the screen promise about when it takes effect (the backend applies a selection on **next use**, not by hot-swapping a warm model mid-flight)? → A: **Standing default, applies to the next production.** The screen confirms the choice is **saved and will be used the next time that capability runs** — it does not claim an immediate live hot-swap of an already-warm model. Acceptance wording is "becomes the standing default and persists," not "instantly active"; this mirrors the honest env-override framing (FR-007).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See what this machine can produce, in plain language (Priority: P1)

A non-technical agency operator wants to know what the studio on this machine can actually make — can it produce images? a
voiceover? transcribe an interview? understand a photo? — before they start a brief. They open the Capability & Model
Panel from the persistent navigation and see each capability named in plain production language, with a plain-language
status: **ready to use** (works right now, for free, locally), **ready with a cloud provider** (a paid option is configured),
or **not available yet — here's how to enable it**. At no point do they see a raw model identifier, an internal family code,
a MIME type, an environment-variable dump, or a raw machine error.

**Why this priority**: Knowing what the machine can produce is the screen's founding purpose and the reason S7 is on the
inventory — a non-technical user who can't tell whether "make a video" will work is flying blind. A readable, honest
capability overview is the minimum that makes this a real, usable screen on its own, independent of choosing models.

**Independent Test**: On a machine with a mix of available and unavailable capabilities, open the screen and verify every
capability is named and described in plain language with an accurate plain-language status; verify an unavailable capability
shows a friendly "not available yet — here's how to enable it" explanation (not a raw reason code); verify a paid cloud
option is clearly marked as paid/cloud and shows whether its key is configured — without any field to enter a key; verify
no raw model identifier, family code, MIME type, or stack trace appears anywhere.

**Acceptance Scenarios**:

1. **Given** the operator opens the screen, **When** it loads, **Then** each capability is presented in plain production
   language (e.g., images, video, voice/narration, transcription, understanding, search/memory) with a plain-language status
   — never a raw internal family code or model identifier as its name.
2. **Given** a capability that is available locally for free, **When** the operator views it, **Then** it is clearly shown as
   **ready to use, free, on this machine** — the local-first default made visible.
3. **Given** a capability whose only options need something that isn't installed, **When** the operator views it, **Then**
   they see a friendly "not available yet — here's how to enable it" explanation in plain language (mirroring the studio's
   501-plus-install-hint contract), never a raw reason like `missing_binary` or `gateway_down`.
4. **Given** a paid cloud option, **When** the operator views it, **Then** it is clearly marked as **paid / cloud** and shows
   whether it is configured (its key is present in the environment) or not — with a plain-language note of what to set to
   enable it, and **never a field to type a key into**.
5. **Given** the screen is open, **When** the operator switches the app language EN↔FR, **Then** every label, status,
   description, and enablement hint follows the switch immediately — the panel is fully localized, not English-only.

---

### User Story 2 - Choose which model each capability uses (Priority: P2)

Beyond seeing what's possible, the operator wants to choose — for a capability that offers more than one option — which
model it uses, or to keep the sensible built-in default. On the same screen, for each capability that supports a choice, they
pick an available option in plain language, see their choice **saved as the standing default** (used the next time that
capability runs) and persist, and can **go back to the built-in default** at any time. Unavailable options can't be chosen (they're clearly shown as not-yet-available with how to enable
them), and choosing a paid cloud option is a deliberate, clearly-marked opt-in that records only a preference — it sends
nothing and asks for no key.

**Why this priority**: Seeing capabilities is the core promise (US1); letting the operator *choose* the model fulfills the
Brick 4 done-when ("the user picks their models/tools from the interface without touching a terminal") and the inventory's
"choose models" mandate. It ranks second because it layers onto the read-only overview from US1, which already delivers
standalone value with sensible defaults in force.

**Independent Test**: On a machine where at least one capability offers more than one available option, choose a non-default
available option and verify the choice is reflected as the standing default and persists across a reload; revert to the built-in default
and verify that persists too; verify an unavailable option cannot be selected; verify choosing a paid cloud option records
the preference without prompting for or transmitting any key; verify that when an environment variable overrides the choice,
the screen honestly shows the override is in force rather than pretending the operator's pick won.

**Acceptance Scenarios**:

1. **Given** a capability with more than one available option, **When** the operator picks a different available option,
   **Then** that option becomes the **standing default** for the capability — the screen confirms it is saved and will be
   used the next time that capability runs (not a claim of an immediate live hot-swap) — and the choice persists (survives a
   reload), expressed in plain language, never requiring a raw model identifier to be typed.
2. **Given** the operator has chosen a non-default model, **When** they choose to go back to the built-in default, **Then**
   the capability returns to its default and that reversion persists.
3. **Given** an option that is not available on this machine, **When** the operator views the chooser, **Then** that option
   is clearly shown as not selectable with a plain-language reason and how to enable it — it cannot be picked into an active
   state.
4. **Given** a paid cloud option, **When** the operator selects it, **Then** the selection is recorded as a preference only
   — nothing is sent to the provider, no key is requested or stored, and the screen still reflects whether the key is
   configured in the environment.
5. **Given** an environment variable is overriding a capability's model, **When** the operator views that capability, **Then**
   the screen plainly states the machine's environment is currently deciding this one (the operator's selection is retained
   but not in force), rather than silently showing a selection that isn't actually active.
6. **Given** a previously-selected model is no longer available (it was removed/uninstalled since it was chosen), **When** the
   operator views that capability, **Then** the screen plainly notes the prior choice is no longer available and what is in
   force instead — never a crash, a blank chooser, or a silently broken selection.

---

### Edge Cases

- **Everything local-only (offline machine, no cloud keys)**: the screen is fully usable — every capability shows its
  local/free status honestly and paid options appear as clearly-marked, not-yet-configured opt-ins; no capability requires
  the network to be *displayed*.
- **A whole capability has no available option** (nothing installed for it yet): it shows a friendly "not available yet —
  here's how to enable it" state rather than an empty control or a crash, and it is not silently omitted.
- **Environment override in force**: the screen honestly shows the environment is deciding a capability and does not present
  the operator's stored selection as active (US2-AC5).
- **Stale selection** (the chosen model was uninstalled since it was picked): the screen notes the choice is no longer
  available and what is in force instead, and lets the operator pick again or return to default (US2-AC6).
- **Capability probing is slow**: the screen shows the shared loading state (not a frozen or blank panel) and, if the
  operator asks to re-check, gives honest progress rather than appearing to hang.
- **Re-check / refresh**: the operator can ask the screen to re-check what the machine can do (re-probe), and the view
  updates to the current truth — availability that changed since the screen opened is reflected.
- **A paid cloud option with its key configured vs. not configured**: both render cleanly — "ready with your configured
  cloud provider" vs. "paid/cloud, not configured — set `<VAR>` to enable" — and neither ever shows a key value or a field
  to enter one.
- **Language switch while viewing**: all panel chrome (capability names, statuses, descriptions, enablement hints, chooser
  labels) follows the EN/FR switch immediately; model *product* names that are proper nouns are shown as-is, not translated.
- **Read failure** (the capability inventory can't be read): a clean, plain-language error with a way to retry — never a raw
  stack trace or a blank screen.
- **Selection failure** (the choice couldn't be saved): a clean, plain-language failure that leaves the prior state intact
  and offers a retry — never a silently dropped selection presented as success.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Capability & Model Panel MUST replace the current raw developer-capability embed on the `models` screen
  with a shipped, operator-facing surface — reachable from the persistent navigation under its plain-language label and fully
  localized in EN/FR.
- **FR-002**: The screen MUST present **every** capability family the studio inventories — both the **selectable model
  families** (images, video, visual understanding, search/memory, knowledge extraction, transcription, narration) and the
  **non-selectable** ones (production tools, integrations/connectors) — in **plain production language**, each with a
  plain-language description of what it does, so the operator sees the full picture of what this machine can produce. It MUST
  never surface an internal family code (`image`, `stt`, `tts`, `visual`, …) or a raw model identifier as the capability's
  name.
- **FR-003**: The screen MUST show, for each capability, a plain-language **availability status** — ready to use (local/free),
  ready with a configured cloud provider, or not available yet — reflecting the studio's existing capability probing, without
  the operator needing to interpret raw reason codes.
- **FR-004**: The screen MUST make the **local-first, free-by-default** posture visible — capabilities available locally for
  free are clearly shown as such, and cloud/paid options are clearly marked as a **deliberate opt-in**, never the presented
  default.
- **FR-005**: For a **selectable model family**, the screen MUST let the operator **choose which model it uses** among its
  **available** options, or keep the **built-in default**, and MUST let the operator **return to the built-in default** at any
  time — expressed in plain language, never requiring a raw model identifier to be typed. For a **non-selectable** family
  (production tools, integrations/connectors), the screen MUST show its availability status **read-only** and MUST NOT render
  a chooser — never a selection control on a capability that offers no choice.
- **FR-006**: A chosen model (or a reversion to default) MUST **persist** as the capability's **standing default** via the
  studio's existing server-side selection mechanism and be reflected as in force on reload (subject to the FR-007 env
  override) — used the next time that capability runs, not by hot-swapping an already-warm model; S7 MUST introduce **no new
  persistence store** and MUST NOT change the selection store's shape or the Brick 4 resolution precedence
  (env > selection > default).
- **FR-007**: When an environment variable is **overriding** a capability's model, the screen MUST honestly show that the
  environment is currently in force (the operator's stored selection is retained but not active) — never presenting a stored
  selection as active when it is not.
- **FR-008**: An **unavailable** option MUST NOT be selectable into an active state; it MUST be clearly shown as not-yet-available
  with a plain-language reason and **how to enable it** (mirroring the studio's 501-plus-install-hint contract), rather than
  a raw reason code.
- **FR-009**: The screen MUST treat a **paid/cloud** option as an explicit opt-in: selecting it records a **preference only**
  — it MUST trigger no outbound network to the provider, and it MUST show whether the provider's key is configured in the
  **environment** and which environment variable enables it.
- **FR-010**: The screen MUST **never** accept, display, persist, or transmit any API key or secret, and MUST render no field
  for entering one; keys remain environment-only (Constitution security invariant; umbrella FR-015).
- **FR-011**: The screen MUST let the operator **re-check** what the machine can do (re-probe the inventory) and reflect the
  current truth, with the shared loading state while checking and honest progress rather than a frozen or blank panel.
- **FR-012**: The screen MUST handle a **stale selection** (a chosen model no longer available) gracefully — plainly noting
  the prior choice is unavailable and what is in force instead, and letting the operator choose again or return to default —
  never a crash, a blank chooser, or a silently broken selection.
- **FR-013**: The screen MUST NOT surface internal identifiers — raw model IDs, internal family codes, MIME types,
  environment-variable *values*, engine/kit names as machinery, or file-system paths — as operator-facing content; the one
  permitted technical token is the **name** of an environment variable to set to enable a capability (shown as guidance, with
  no value).
- **FR-014**: The screen MUST provide friendly, localized **empty and error states** — a capability with no available option
  ("not available yet — here's how to enable it"), an inventory that can't be read (retryable error), and a selection that
  couldn't be saved (retryable, prior state intact) — never a blank screen or a raw stack trace.
- **FR-015**: The screen MUST be **machine-level, not taxonomy-scoped** — it reflects what this machine can produce
  independent of the active client/project/campaign context, and does not filter by or depend on the shell's client-context
  selector.
- **FR-016**: The screen MUST inherit the umbrella **design-system accessibility baseline** (WCAG 2.1 AA — full keyboard
  operability including reading each capability's status and choosing/reverting a model; screen-reader labels; AA contrast;
  visible focus) and the shared loading/empty/error state patterns.
- **FR-017**: The screen MUST preserve all **security invariants** (served only from 127.0.0.1, no wildcard cross-origin
  access, HTTPS-only for any outbound step — of which S7 has none beyond the studio's existing local probing) and MUST NOT
  accept, persist, or display any API key or secret.
- **FR-018**: The screen MUST be **additive** — it MUST NOT change the mission loop, routing, synthesis, asset rendering, the
  inspector veto loop, the capability probing/aggregation logic, the selection store's shape, the env > selection > default
  precedence, or the shape of a saved dossier (umbrella FR-016; Constitution Principles III, V, X, and agency-kit's veto-loop
  invariant). The existing developer Console capability panel MUST remain available at its secondary location.

### Key Entities *(include if feature involves data)*

- **Capability**: an operator-facing area of what the machine can produce — images, video, voice/narration, transcription,
  understanding, search/memory, production tools, integrations/connectors — named and described in plain language, with a
  plain-language availability status and a **selectable** flag: selectable model families expose a chooser, non-selectable
  families (production tools, integrations/connectors) are read-only status only. Backed read-only by the existing Brick 4
  capability inventory; S7 defines no new persisted entity.
- **Model option**: one concrete choice within a capability — its plain-language label, whether it is **free/local** or
  **paid/cloud**, its availability (available / not-yet-available with how to enable), whether it is the built-in default,
  and, for paid/cloud options, whether its key is configured in the environment (never the key itself).
- **Model selection**: the operator's **standing default** choice of model for a capability (or "built-in default"),
  persisted via the existing server-side selection mechanism and used the next time that capability runs (not a live hot-swap
  of a warm model); subject to the inherited env > selection > default precedence, so an environment override can supersede it
  (shown honestly).
- **Availability status**: the plain-language state of a capability or option — ready (local/free), ready with a configured
  cloud provider, or not available yet (with plain-language enablement guidance) — derived from the studio's existing probing,
  never a raw reason code on the operator surface.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A non-technical operator can open the panel and correctly tell, for every capability, whether the machine can
  produce it right now and at what cost (free/local vs. paid/cloud), without seeing any raw model identifier, family code, or
  MIME type — verified by every capability showing a plain-language name, status, and cost.
- **SC-002**: An operator can change the model for a capability that offers a choice and revert to the built-in default
  entirely from the screen (no terminal, no environment editing), and both the change and the reversion persist across a
  reload — fulfilling the Brick 4 done-when.
- **SC-003**: 100% of unavailable capabilities/options show a plain-language "not available yet — here's how to enable it"
  explanation (mirroring the 501-plus-install-hint contract) and cannot be selected into an active state — zero raw reason
  codes (`missing_binary`, `gateway_down`, …) shown to the operator.
- **SC-004**: Every operator-facing string on the screen is available in both EN and FR and follows a language switch
  immediately, with zero internal family codes, raw model IDs, MIME types, or file paths shown as operator-facing content —
  the only permitted technical token being the *name* of an environment variable to set (no value).
- **SC-005**: The screen never accepts, displays, persists, or transmits an API key — verified by the absence of any
  key/secret input on the screen and by no outbound network to any provider when a paid option is selected (selection records
  a preference only).
- **SC-006**: When an environment variable is overriding a capability's model, 100% of the time the screen shows the override
  is in force rather than presenting a stored selection as active — verified with an override set.
- **SC-007**: The panel is machine-level — its content does not change with the active client/project/campaign context —
  verified by switching client context and observing identical capability content.
- **SC-008**: The screen meets WCAG 2.1 AA — reading each capability's status and choosing/reverting a model are fully
  operable by keyboard and labeled for screen readers, with AA contrast and visible focus.
- **SC-009**: S7 introduces zero changes to the mission loop, capability probing/aggregation, selection-store shape, or the
  env > selection > default precedence — verified by the offline suite staying green and by capability resolution behaving
  byte-identically to Brick 4 before and after.

## Assumptions

- **Backend already exists (Brick 4) — S7 is frontend-only over existing paths**: the studio already inventories every
  registry into families/entries with availability, cost, and active resolution, and already persists a server-side model
  selection per family with env > selection > default precedence (done `6e71879` / #6). S7 adds **no new backend, no new
  endpoint semantics, and no new persistence** — it is a read-through-plus-select operator surface, in the same additive
  spirit as S4/S6.
- **Replaces a thin raw embed, not a coming-soon placeholder**: unlike S4/S5/S6 (which replaced coming-soon placeholders),
  the `models` route already renders a screen — but it embeds the **raw developer capability component verbatim**
  (English-only, raw family names, raw model IDs as code, raw badges, raw reason codes). S7 replaces that embed with a real,
  non-technical, EN/FR-localized operator screen; the underlying inventory/selection interfaces are reused unchanged.
- **Plain-language mapping of capabilities**: internal family codes map to operator-facing names (e.g., images, video,
  voice/narration, transcription, understanding, search/memory); the exact wording is finalized during design, but the
  invariant is that **no internal family code or raw model identifier is the operator-facing name** (FR-002, FR-013).
- **Selection is in scope; precedence is inherited unchanged**: the operator can choose a model and revert to default via the
  existing selection mechanism; S7 does **not** change the env > selection > default precedence — an environment override
  still wins and is shown honestly (FR-007). Per-mission model overrides at brief time are a possible future refinement, not
  v1.
- **Keys stay environment-only; paid = preference-only opt-in**: choosing a paid cloud provider records a preference and
  never sends anything to the provider or handles a key; the screen shows *whether* a key is configured and *which* env var
  enables it, never a value or an input field (Constitution security invariant; umbrella FR-015; consistent with the existing
  Models.test no-secret assertion).
- **Machine-level, not taxonomy-scoped**: the models a machine can run are a property of the machine, so the screen is not
  filtered by client/project/campaign; it does not consume the shell's client-context selector (route already
  `taxonomyScoped: false`).
- **Reports, does not install**: S7 surfaces what is installed and, for what is not, the plain-language enablement hint
  (mirroring the studio's 501-plus-install-hint contract); installing/downloading a model, binary, or extra is out of scope —
  S7 is not an installer.
- **General settings live in S8, not here**: language default, theme, data location, retention, and other non-capability
  configuration belong to the separate Settings screen (S8); S7 is strictly the capability/model surface.
- **Coexistence with the developer console**: the existing developer Console capability panel remains at its secondary
  location; S7 is the operator-facing front door, not a replacement, and the two read the same inventory.
- **Local-first, no new network, no secrets**: reading the inventory and choosing a model add no outbound network beyond the
  studio's existing local capability probing (unchanged Brick 4 behavior); security invariants (127.0.0.1 bind, no CORS `*`,
  keys env-only) are inherited unchanged.
