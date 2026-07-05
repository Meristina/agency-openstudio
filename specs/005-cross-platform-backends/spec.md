# Feature Specification: Cross-Platform Backends ("any machine")

**Feature Branch**: `005-cross-platform-backends`

**Created**: 2026-07-05

**Status**: Draft

**Input**: User description: "Brick 5 — Cross-platform ("any machine"). Today the studio's multimedia layer (image, STT, TTS, embeddings) only runs on Apple Silicon / MLX: on a Linux or Windows machine without MLX these capabilities are dead, and a mission with assets fails. Brick 5 makes the studio genuinely cross-platform by adding non-Mac backends BEHIND the existing registries (IMAGE_MODELS, VIDEO/VISUAL, EMBED_MODELS, STT, TTS), following exactly the openmontage-remotion pattern — no new agency-kit surface, purely additive. Each family gains at least one portable, CPU-friendly backend: image = stable-diffusion.cpp (MIT) or a LocalAI (MIT) gateway; speech-to-text = whisper.cpp / faster-whisper; text-to-speech = Piper / Kokoro-onnx on CPU; embeddings = llama.cpp via its /v1/embedding endpoint. Every backend follows the probe → load → run contract and, when absent, returns a clean 501 with an install hint (never a crash). Backend selection flows through the registries and the Brick 4 capability-choice mechanism (environment variables remain the power-user override). The user never touches a terminal: on any machine they pick an available backend and their mission with assets runs. The offline test suite stays green everywhere (backends and network stubbed), with the live runs that need the real binaries deferred as they were for Wave 2. Done when: the same mission with assets runs on a Linux/Windows box without MLX, and the offline suite is green on every platform."

## Clarifications

### Session 2026-07-05

- Q: When a mission requires an asset family whose selected/default backend is unavailable on this machine, what should happen? → A: Preflight block — before the mission starts, every needed family is checked; if any is unavailable, the mission refuses to launch and lists each blocking family with its install hint.
- Q: How do gateway-style backends (locally-running model services reached over HTTP) coexist with the HTTPS-only outbound rule? → A: Loopback-only exception — plain HTTP is permitted strictly to loopback addresses (127.0.0.1 / ::1 / localhost); any non-loopback gateway address is rejected. HTTPS-only stays absolute for everything else.
- Q: With no env override and no persisted selection, what happens when the family's built-in default backend is unavailable on this platform but another backend is available? → A: Platform-aware default — the effective default becomes the first AVAILABLE entry in deterministic registry order; Mac defaults are unchanged.
- Q: How is "offline suite green on macOS, Linux, and Windows" verified? → A: This brick adds a minimal continuous-integration workflow running the offline suite on all three operating systems on every pull request.
- Q: How strictly must user-acquired backend programs and model files be pinned and verified? → A: Pinned + verified — install hints reference exact pinned versions/revisions, and the studio verifies model files (checksum or pinned revision) at probe/load time; a mismatch is reported as unavailable with a reason, never silently run.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A mission with assets runs on a machine without Apple Silicon (Priority: P1)

An agency operator installs the studio on a Linux or Windows machine (no Apple
Silicon, no Apple-specific runtime). They follow the install hints shown in the
capabilities view to enable one free, locally-running backend per capability family
they need (image generation, speech-to-text, text-to-speech, embeddings). They then
launch the same mission with assets that a Mac user would launch — and it completes:
every requested asset is produced by the portable backends, with no step requiring
Apple hardware.

**Why this priority**: This is the brick's "done when". Today that mission simply
fails on non-Mac hardware, which contradicts the product promise that the studio runs
on any machine. Everything else in this brick exists to make this journey possible.

**Independent Test**: On a Linux or Windows machine without any Apple-specific
runtime, install the portable backends for image, speech-to-text, text-to-speech, and
embeddings, run a mission that produces assets in each of those families, and verify
the mission completes with all assets present — identical in kind to what the same
mission produces on a Mac.

**Acceptance Scenarios**:

1. **Given** a Linux machine without any Apple-specific runtime where the portable
   backends are installed and selected, **When** the user runs a mission with image
   and speech assets, **Then** the mission completes and every asset is produced by
   the portable backends.
2. **Given** a Windows machine in the same state, **When** the user runs the same
   mission, **Then** the outcome is the same as on Linux.
3. **Given** a Mac where nothing new was installed and no selection was changed,
   **When** the user runs the same mission, **Then** behavior is exactly what it was
   before this feature existed (the Apple-Silicon backends still serve it unchanged).

---

### User Story 2 - Pick a portable backend without touching a terminal (Priority: P2)

On any machine, the user opens the capabilities view (Brick 4) and sees the new
portable backends listed inside their existing capability families — each marked FREE,
and AVAILABLE or UNAVAILABLE for *this* machine, with a concrete, platform-aware
enablement step when unavailable. The user picks an available portable backend for a
family in the interface, the choice persists, and subsequent asset production uses it.
Power users can still override any choice with an environment variable, exactly as
before.

**Why this priority**: Portable backends that only a terminal user can activate would
violate the product's simplicity principle and leave the brick unusable by its target
audience. Selection must ride the existing capability-choice mechanism — no new
surface, no new concept for the user to learn.

**Independent Test**: On a machine with one portable backend installed and its
siblings absent, open the capabilities view, verify the installed backend shows
AVAILABLE/FREE while absent ones show UNAVAILABLE with an install hint, select the
available one through the interface alone, and verify the next asset request in that
family uses it.

**Acceptance Scenarios**:

1. **Given** a machine where a portable speech-to-text backend is installed, **When**
   the user opens the capabilities view, **Then** that backend appears inside the
   speech-to-text family as AVAILABLE and FREE, and the user can select it without
   using a terminal.
2. **Given** an Apple-Silicon-only backend viewed on a Linux or Windows machine,
   **When** the user opens the capabilities view, **Then** that backend shows
   UNAVAILABLE with a reason that says it is not supported on this platform — not a
   generic or misleading error.
3. **Given** a persisted in-interface selection of a portable backend and an
   environment variable naming a different backend for the same family, **When** an
   asset is produced, **Then** the environment variable wins (existing precedence:
   environment > selection > default).
4. **Given** a family where the user selected a portable backend, **When** the studio
   restarts, **Then** the selection is still in effect.

---

### User Story 3 - Absent backends fail cleanly everywhere (Priority: P3)

A user on any platform requests an asset from a family whose selected or default
backend is not installed on that machine. Instead of a crash or a cryptic stack
trace, they receive a clear "this capability is not available here" response naming
the missing component and the exact step that would enable it. The studio process
stays healthy, and everything else keeps working.

**Why this priority**: Graceful absence is what makes cross-platform honest: on any
given machine most backends will be absent, and every absence must be a guidance
moment, not a failure. It also protects the mission pipeline — one missing backend
must never take down the studio.

**Independent Test**: On a machine with zero optional backends installed, request an
asset from each capability family and verify every response is a clean
"not available + install hint" answer, the process survives, and unrelated
capabilities keep responding.

**Acceptance Scenarios**:

1. **Given** a machine where no portable backend is installed, **When** the user
   requests an image, **Then** the response clearly states the capability is
   unavailable, names the missing component, and gives the concrete install step —
   and the studio keeps serving other requests.
2. **Given** a backend whose program is installed but whose model files are missing,
   **When** the user requests an asset from it, **Then** the response pinpoints the
   missing model files and how to obtain them, rather than reporting the backend as
   generally broken.
3. **Given** the automated test suite running on macOS, Linux, or Windows with no
   backend installed, no network, and no external tools, **When** the suite runs,
   **Then** it passes everywhere (all backend and network boundaries are stubbed).

---

### Edge Cases

- A machine has some families covered and others not (e.g., speech-to-text installed,
  text-to-speech absent): the preflight check refuses to launch the mission and lists
  every blocking family with its install hint (see FR-012); nothing is produced
  partially.
- Both an Apple-Silicon backend and a portable backend are installed on a Mac: the
  pre-existing default stays the default; the portable backend is offered as an
  additional choice, never a silent replacement.
- A portable backend is installed but too slow for a large request on weak hardware:
  the request either completes or fails with a clear timeout message — never a hang
  that blocks the mission indefinitely.
- The user copies their studio data (including a persisted backend selection) to a
  machine where that backend is absent: the studio reports the selected backend as
  unavailable with an install hint and lets the user re-select, instead of failing
  opaquely.
- A backend's availability changes while the studio is running (user installs it
  mid-session): a refresh of the capabilities view reflects the new availability
  without a restart.
- A gateway-style backend that reaches a locally-running service finds the service
  stopped: the response distinguishes "installed but not running" (with a start hint)
  from "not installed" (with an install hint).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each of the four capability families — image generation,
  speech-to-text, text-to-speech, and embeddings — MUST offer at least one backend
  that runs on macOS, Linux, and Windows using only the CPU, free of charge, with no
  paid service involved.
- **FR-002**: Portable backends MUST appear as additional entries inside the existing
  capability families of the Brick 4 inventory — same families, same availability and
  cost-class semantics — never as a new parallel surface.
- **FR-003**: Every portable backend MUST be availability-checked before use with a
  passive, side-effect-free check, and its inventory entry MUST reflect the result
  for the current machine and platform.
- **FR-004**: When a requested backend is absent, the studio MUST return a clean
  "capability not available" response carrying a human-readable reason and a concrete
  enablement step (install hint), and MUST NOT crash, hang, or degrade unrelated
  capabilities.
- **FR-005**: Unavailability reasons MUST be platform-aware: a backend that cannot
  run on the current platform states so explicitly, and is distinguished from one
  that is merely not yet installed, and from one that is installed but not currently
  runnable (e.g., missing model files, companion service not running).
- **FR-006**: Backend selection MUST flow through the existing Brick 4 capability
  choice mechanism — visible, selectable, and persistent in the interface — with the
  existing precedence preserved: environment variable override first, then persisted
  in-interface selection, then the default. The default is platform-aware: when the
  built-in default backend is unavailable on the current platform, the family's
  effective default is the first AVAILABLE entry in deterministic registry order (on
  a Mac with the built-in default available, nothing changes). No terminal is ever
  required.
- **FR-007**: The feature MUST be purely additive: on a machine with no portable
  backend installed and no selection changed, every existing behavior — including all
  Apple-Silicon flows — remains byte-identical.
- **FR-008**: The same mission with assets that succeeds on a Mac MUST succeed on a
  Linux or Windows machine without any Apple-specific runtime, once the user has
  installed and selected portable backends for the families the mission uses.
- **FR-009**: The automated test suite MUST pass on macOS, Linux, and Windows with no
  backend installed, no network access, and no external tools — every backend and
  network boundary stubbed. Verification requiring real binaries is deferred to
  explicitly separate live runs, as established practice.
- **FR-010**: Backends MUST NOT reach the network during asset production; any
  gateway-style backend MUST only address a loopback address (127.0.0.1 / ::1 /
  localhost) — plain HTTP is permitted strictly there, any non-loopback gateway
  address is rejected, and the HTTPS-only rule stays absolute for all other outbound
  traffic. Acquiring a backend's program or model files is an explicit user-driven
  setup step guided by install hints — never a silent download by the studio.
- **FR-011**: Every third-party component adopted for a portable backend MUST have a
  license compatible with the project's license and MUST be recorded in the project's
  license ledger.
- **FR-012**: Before a mission with assets starts, the studio MUST preflight-check
  availability of every asset family the mission needs; if any family is unavailable,
  the mission MUST refuse to launch, listing each blocking family with its
  unavailability reason and install hint. A mission never starts producing assets it
  cannot finish.
- **FR-013**: Install hints MUST reference exact pinned versions / model revisions,
  and the studio MUST verify the identity of the model files it loads (checksum or
  pinned revision) at availability-check or load time; a mismatch is reported as
  UNAVAILABLE with an "unexpected model files" reason — never silently run.

### Key Entities

- **Capability family**: A kind of asset work the studio performs (image generation,
  speech-to-text, text-to-speech, embeddings). Families are fixed; this feature adds
  members, not families.
- **Backend (registry entry)**: One concrete way to perform a family's work on some
  set of platforms. Attributes: family, display name, supported platforms, cost class
  (all new backends: FREE), availability on this machine, unavailability reason and
  enablement step when absent.
- **Availability check (probe)**: The passive verification that a backend is usable
  here and now; produces AVAILABLE, or UNAVAILABLE plus a categorized reason
  (unsupported platform / not installed / installed but missing models / unexpected
  model files / companion service not running).
- **Selection**: The user's persisted per-family choice of backend, shared with
  Brick 4; subject to the environment > selection > default precedence.
- **Install hint**: The human-readable enablement step attached to every UNAVAILABLE
  state; references exact pinned versions / model revisions, and is specific enough
  that following it changes the state to AVAILABLE.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A mission with image and speech assets that completes on a Mac also
  completes on a Linux machine and on a Windows machine without any Apple-specific
  runtime, producing 100% of its requested assets via free, locally-running backends.
- **SC-002**: Every one of the four capability families offers at least one backend
  that can be made AVAILABLE on each of the three platforms using only free
  components and the displayed install hints.
- **SC-003**: 100% of asset requests against an absent backend return an explanatory
  "not available" response with a concrete enablement step; zero crashes and zero
  hung requests across all such cases.
- **SC-004**: The automated test suite passes on macOS, Linux, and Windows with zero
  optional backends installed and no network access, verified continuously by an
  automated check on every proposed change (not by hand).
- **SC-005**: A non-technical user can discover, enable (following displayed hints),
  and select a portable backend, then produce an asset with it, without ever opening
  a terminal for selection — selection and use are 100% in-interface.
- **SC-006**: On an unchanged Mac setup (nothing new installed, nothing re-selected),
  observed studio behavior before and after this feature is identical.

## Assumptions

- The four families covered are image generation, speech-to-text, text-to-speech,
  and embeddings. Three of them (image, speech-to-text, embeddings) are
  Apple-Silicon-only today; text-to-speech already runs on a portable CPU engine but
  has only ever been validated on Apple Silicon — for that family this brick's work
  is confirming (and where needed fixing) genuine Linux/Windows availability rather
  than adding a first portable backend. Video generation and visual analysis already
  reach non-Mac machines through their existing platform-neutral paths
  (externally-billed services and the vendored production pipeline) and gain no new
  backend in this brick.
- The roadmap names candidate components per family (image: stable-diffusion.cpp or a
  LocalAI gateway; speech-to-text: whisper.cpp or faster-whisper; text-to-speech:
  Piper or Kokoro-onnx; embeddings: llama.cpp's embedding endpoint). The spec requires
  one portable backend per family meeting FR-001; choosing among these candidates is
  a planning-phase decision, and adding more than one per family is welcome but not
  required.
- "Windows" means native Windows. If a chosen component cannot meet that natively,
  planning must pick a candidate that can, or fall back to the gateway pattern with a
  natively-runnable local service.
- Installing a backend (its program and model files) is a user-performed setup step
  guided by the displayed install hints, consistent with how optional extras are
  enabled today. In-interface one-click installation is out of scope for this brick
  (it belongs to the magic-box redesign).
- The Brick 4 capability inventory and selection mechanism is in place and is the
  single point where the new backends surface; this brick adds entries behind it and
  changes none of its semantics.
- Performance on CPU-only machines will be materially slower than on Apple Silicon;
  this brick's bar is correct completion with honest progress/failure reporting, not
  performance parity.
- This brick adds a minimal continuous-integration workflow running the offline
  suite on macOS, Linux, and Windows on every pull request — the mechanism by which
  SC-004 is continuously verified. Live runs with real binaries remain deferred,
  matching the established Wave 2 practice.
