# Feature Specification: Deliverable Recipes (mission → production in one click)

**Feature Branch**: `016-deliverable-recipes`

**Created**: 2026-07-07

**Status**: Draft

**Input**: User description: "lance le cycle Brick 8 — Deliverable recipes : des recettes de production « mission → livrable en un clic » depuis le magic box. Une recette enchaîne mission (départements agency-kit) → assets (image / voix) → composition (vidéo) → export bundle, sans que l'utilisateur non-technique touche un terminal. Exposer les 13 pipelines OpenMontage plus des recettes d'agence composées : campagne complète, pitch client, event clé en main, pack de contenu social. L'utilisateur choisit une recette depuis l'écran Home/Brief, la lance, suit une timeline unifiée (réutiliser S3), et récupère le dossier stratégie ET les créatifs associés en un seul run. Contraintes non négociables : OpenMontage piloté uniquement en subprocess (jamais d'import in-process), local-first par défaut avec choix cloud explicite opt-in, la boucle de veto de l'inspecteur inchangée, EN/FR, extensions additives (registres/hooks default-None). Done when : « lance une campagne pour X » produit le dossier stratégie et les créatifs en un run."

## Clarifications

### Session 2026-07-07

- Q: How many recipe runs can be active at once? → A: Single active run — one recipe run executes at a time; launching another is blocked with a clear message until the current run finishes or is cancelled (matches S3, which renders only the live session).
- Q: When a stage fails or is vetoed mid-run, how does the user continue? → A: Resume from the failed stage — completed stages' outputs are reused and the run resumes at the failed stage, so the slow, internet-researching, inspector-gated mission stage is not re-run.
- Q: Where does recipe selection surface for the user? → A: Both Home and the Guided Brief — the catalog is reachable from Home (as a launch option) and inside the Guided Brief (as a deliverable type); both paths lead to a recipe run.
- Q: Do all four composed agency recipes run the identical mission→assets→composition→export chain, or may each declare its own stage set? → A: Per-recipe stage set — each composed recipe declares which stages it runs (e.g. a social content pack may skip long-form composition); the full mission→assets→composition→export chain is the canonical maximal shape, not a fixed mandate for every recipe.

### Session 2026-07-07 (analysis remediation)

- Resolved (C1 — production tiers vs local-first): a production recipe's pipeline-stage tier is **derived from that pipeline's manifest** — a pipeline that requires paid cloud media providers is surfaced as a **cloud** stage requiring explicit per-run opt-in (never a silent paid run), while a fully-local pipeline is a **local (free)** stage. Reasoning/orchestration still runs on the subscription CLI agent (no billed reasoning path); only paid media, where a pipeline needs it, is the opt-in.
- Resolved (I1 — the "assets" stage): image/voice **assets are produced within the mission stage** (via the studio's existing asset step). The orchestrated stages are therefore **mission → composition → export**; "assets" is the mission stage's creative output, not a separate orchestrated stage with its own driver.
- Resolved (U1 — production-recipe output): a production recipe (no mission stage, hence no full dossier) lands its single artifact in the **same** library/export via a **lightweight deliverable record**, so every recipe's output is retrievable through one path.

## User Scenarios & Testing *(mandatory)*

Brick 8 is the first brick after the "magic box" (Brick 7) shipped all its screens.
Until now, a non-technical user could run a **mission** (research → strategy dossier)
through the studio, and — separately — the studio carried OpenMontage's production
tooling (13 pipelines, image/voice/video). What was missing is the **bridge**: a way
to go from a spoken intent ("launch a campaign for X") to a finished package —
strategy **and** creatives — in a single, terminal-free run.

**Deliverable Recipes** are that bridge. A *recipe* is a named, plain-language
production template the user picks from the front door. Two families exist:

1. **Production recipes** — the 13 OpenMontage pipelines exposed one-to-one (e.g. a
   talking-head video, a cinematic clip, an animated explainer), for when the user
   already knows what single artifact they want.
2. **Composed agency recipes** — higher-level, end-to-end templates that chain a full
   agency **mission** (agency-kit departments) → **assets** (image / voice) →
   **composition** (video) → **export bundle** in one run: *full campaign*, *client
   pitch*, *turnkey event*, *social content pack*. These deliver the strategy dossier
   **and** the associated creatives together.

The user chooses a recipe from Home/Brief, launches it, follows a **single unified
timeline** (reusing the S3 Mission Timeline), and retrieves **everything the run
produced** — the strategy dossier and the creatives — from one place. All of it is
additive: with no recipe selected, the existing mission/brief flow behaves exactly as
before.

### User Story 1 - Launch a campaign for X and get dossier + creatives in one run (Priority: P1)

A non-technical user opens the studio, picks the **full campaign** recipe, says what
it is for ("a launch campaign for our new coffee subscription"), and starts it. From
there the studio does the whole chain by itself: it runs the agency mission (the
departments produce a sourced strategy dossier, and the inspector gates it exactly as
it always has), then generates the campaign's creatives (images, voice-over, composed
video), then bundles the result. When the run finishes, the user opens **one package**
containing both the strategy dossier **and** the finished creatives — having never
opened a terminal.

**Why this priority**: This is the reason Brick 8 exists and its literal done-when:
*"launch a campaign for X produces the strategy dossier AND the associated creatives
in a single run."* It is the load-bearing vertical slice — one composed recipe,
end-to-end — and delivers the core promise entirely on its own, even if no other
recipe or refinement ships.

**Independent Test**: Pick the full-campaign recipe, give it a subject, launch it, and
confirm that a single run produces (a) a sourced strategy dossier that passed the
unchanged inspector gate and (b) the associated creatives, both retrievable together
from one place — with no terminal touched at any point.

**Acceptance Scenarios**:

1. **Given** the recipe entry point is open, **When** the user selects the full-campaign
   recipe, gives a subject, and launches, **Then** a single recipe run starts that
   chains mission → assets → composition → export without further manual steps.
2. **Given** the recipe run reaches the mission stage, **When** the departments produce
   the dossier, **Then** the inspector veto loop runs with **byte-identical behavior**
   to a standalone mission (a veto holds the run exactly as it would today; recipe
   orchestration never alters the verdict or the loop).
3. **Given** the recipe run completes, **When** the user opens the result, **Then** they
   find the strategy dossier **and** the creatives collected together as one deliverable
   package, retrievable in a single place.
4. **Given** the mission stage's dossier makes factual claims, **When** the run
   completes, **Then** those claims still cite verifiable sources exactly as a normal
   mission (the recipe never bypasses the no-invented-information guarantee).

---

### User Story 2 - Choose the right recipe from a plain-language catalog (Priority: P2)

The user browses a catalog of recipes from Home/Brief. Each recipe is described in
plain, non-technical language: what it produces, what it needs from the user, and
roughly how much it will do. The catalog offers both the **13 OpenMontage production
pipelines** (for a single artifact) and the **4 composed agency recipes** (for a full
package). The user picks the one that matches their need and launches it the same way
regardless of which family it belongs to.

**Why this priority**: A single hardcoded recipe proves the chain, but the brick's
value is the *menu* — exposing all 13 pipelines plus the composed recipes so the user
can produce the specific deliverable they need. It broadens P1 from one path to the
whole surface, and is independently testable by launching any catalog entry.

**Independent Test**: Open the catalog, confirm all 13 production pipelines and all 4
composed recipes appear with plain-language descriptions of output and required inputs,
then launch at least one of each family and confirm each starts a valid run.

**Acceptance Scenarios**:

1. **Given** the recipe catalog is open, **When** the user reads it, **Then** all 13
   OpenMontage production pipelines and all 4 composed agency recipes are listed, each
   with a plain-language name, a description of what it produces, and what it needs.
2. **Given** a recipe requires input the user has not given, **When** the user tries to
   launch, **Then** the studio asks for the missing input in plain language rather than
   launching with silent placeholder values or failing obscurely.
3. **Given** a recipe's production capability is not available on this machine, **When**
   the user views or launches it, **Then** the studio shows an honest message with an
   install hint (never a crash), and every other recipe remains launchable.
4. **Given** the interface language is switched (English ↔ French), **When** the catalog
   is shown, **Then** every recipe name, description, input prompt, and status appears in
   the selected language with no hard-coded or missing strings.

---

### User Story 3 - Stay local-first, with explicit opt-in for anything paid (Priority: P3)

Before launching, the user sees which stages of the recipe run for **free on this
machine** (local-first, the default) and which — if any — would use a **paid cloud**
provider. Nothing paid or online happens silently: cloud steps are an explicit, per-run
opt-in the user must turn on, and the studio never asks for or stores a key in the run
itself. A user who does nothing gets an entirely local, free run.

**Why this priority**: Cost and privacy control is a non-negotiable of the whole
product, and recipes — which fan out into many production steps — are exactly where a
silent paid call would hurt most. It is lower priority than getting the chain and the
catalog working, but it protects trust and is independently testable.

**Independent Test**: Open any recipe, confirm each stage is labeled local (free) by
default, launch without opting into anything, and confirm the run stays fully local and
offline (apart from the mission's own sanctioned research); then explicitly opt a stage
into cloud and confirm that choice is required, visible, and reversible before launch.

**Acceptance Scenarios**:

1. **Given** a recipe is selected, **When** the user reviews it before launch, **Then**
   each stage clearly shows whether it runs locally (free) or would use a paid cloud
   provider, defaulting to local.
2. **Given** the user launches without changing anything, **When** the run executes,
   **Then** no stage uses a paid cloud provider and the run makes no network calls beyond
   the mission's own sanctioned research (per-mission opt-in).
3. **Given** the user explicitly opts a stage into a paid cloud provider, **When** they
   launch, **Then** that choice is required (never a silent default) and visible, and the
   run honors the studio's rule that provider keys live in the environment only — never
   requested in, or persisted by, the run.

---

### User Story 4 - Follow the whole run on one timeline (Priority: P3)

Once launched, the recipe run shows up as a **single unified timeline** — the same
mission timeline surface from S3 — where the user watches the whole chain progress: the
mission stage, then assets, then composition, then export, each with an honest live
status. The user can cancel the run at any point; cancelling stops the **entire** chain
cleanly, leaving no runaway background work.

**Why this priority**: "One run, one timeline" is what makes the multi-stage chain feel
like a single deliverable rather than a pile of disconnected jobs. It reuses S3 rather
than inventing a new surface, so it is additive and lower risk, but it is essential to
the experience and independently testable.

**Independent Test**: Launch any composed recipe and confirm all its stages appear as
one continuous timeline with live status; then cancel mid-run and confirm the whole
chain — including any background production work — stops with no orphaned processes and
an honest final state.

**Acceptance Scenarios**:

1. **Given** a recipe run is in progress, **When** the user views its timeline, **Then**
   all stages (mission → assets → composition → export) appear on one unified timeline
   with honest, live per-stage status, reusing the existing mission timeline surface.
2. **Given** a stage fails or is vetoed mid-run, **When** the run stops, **Then** the
   timeline shows exactly which stages completed and which did not, preserves the outputs
   already produced, offers to **resume from the failed stage** (reusing completed stages),
   and never reports overall success falsely.
3. **Given** a run is in progress, **When** the user cancels it, **Then** the entire
   chain stops — including any subprocess production work — leaving no orphaned background
   jobs and an honest cancelled state.

---

### Edge Cases

- **Production capability missing (no GPU / tool not installed)**: a recipe whose pipeline
  needs an absent capability shows an honest, plain-language message with an install hint
  and does not crash; other recipes stay usable and the mission stage still runs.
- **Stage fails midway**: if assets or composition fail after the mission succeeded, the
  run preserves the completed strategy dossier, marks the failed stage honestly, and offers
  the user their partial result **plus the option to resume from the failed stage** (reusing
  the completed mission) rather than discarding everything, re-running the mission, or
  claiming success.
- **Launch while a run is active**: attempting to start a second recipe while one is running
  is blocked with a plain-language message pointing to the in-progress run — never a silent
  drop and never a second parallel run.
- **Inspector veto during the mission stage**: the recipe holds exactly as a standalone
  mission would — the run does not "push past" a veto to keep producing creatives on top
  of unapproved strategy.
- **Missing required input**: launching a recipe without a needed subject/brief prompts
  the user for it in plain language instead of running on empty placeholders.
- **Cloud opt-in without a configured key**: if the user opts a stage into a paid cloud
  provider whose key is not present in the environment, the studio explains what is
  missing (env-only keys) rather than prompting for the secret in the run or failing
  silently.
- **Cancellation**: cancelling a running recipe stops the whole chain and its subprocess
  children (no orphaned renders), leaving a clean cancelled state.
- **Long-running composition**: a slow video composition shows continuous honest progress
  on the unified timeline, never a frozen or falsely-complete state.
- **Recipe produces nothing usable**: if every production stage yields no artifact, the run
  says so honestly and still surfaces whatever the mission produced — never a fake
  "delivered" package.
- **Language switch mid-run**: recipe names, stage labels, and statuses update live with
  the interface language.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The studio MUST expose a **recipe catalog** containing the 13 OpenMontage
  production pipelines (one-to-one) and the 4 composed agency recipes (full campaign,
  client pitch, turnkey event, social content pack), each described in plain,
  non-technical language stating what it produces and what it needs from the user.
- **FR-002**: A non-technical user MUST be able to select and launch any recipe from **both
  the Home screen** (as a launch option) **and the Guided Brief** (as a deliverable type),
  using pointer or keyboard alone, without opening a terminal, editing a config file, or
  typing a technical identifier.
- **FR-003**: A **composed agency recipe** MUST chain its declared stages in a single run,
  carrying context from each stage into the next automatically. The canonical maximal chain
  is mission (agency-kit departments) → assets (image / voice) → composition (video) →
  export bundle; each composed recipe **declares its own stage set** and MAY omit stages
  that do not fit its deliverable (e.g. a social content pack may skip long-form
  composition). A composed recipe MUST include the mission stage and MUST end by collecting
  its outputs. In orchestration terms, image/voice **assets are produced within the mission
  stage** (via the studio's existing asset step), so the orchestrated stages are
  **mission → composition → export** — "assets" is the mission stage's creative output, not a
  separate orchestrated step.
- **FR-004**: A composed recipe run MUST deliver **both** the strategy dossier (mission
  output) **and** the associated creatives (produced media) from that single run,
  collected together so the user retrieves everything from one place.
- **FR-005**: Recipe orchestration MUST drive OpenMontage's production tooling **only
  across the established subprocess boundary** and MUST NOT import OpenMontage in-process.
- **FR-006**: The mission stage's **inspector veto loop MUST behave byte-identically** to a
  standalone mission — recipe orchestration MUST NOT change the inspector's verdict, the
  veto loop, or when it runs. A veto MUST hold the run as it would today.
- **FR-007**: The mission stage MUST preserve the no-invented-information guarantee:
  factual claims in the strategy dossier MUST cite verifiable sources exactly as in a
  standalone mission; a recipe MUST NOT be a path around sourcing or the inspector.
- **FR-008**: Every recipe stage MUST default to **local, free** execution. Any stage that
  would use a paid cloud provider MUST be an **explicit per-run opt-in**, never a silent
  default, and MUST be clearly indicated before launch.
- **FR-009**: A recipe run MUST NOT touch the network except through the mission's own
  sanctioned research and any stage the user explicitly opted into cloud for; absent
  opt-in, production stages run offline.
- **FR-010**: The studio MUST honor env-only provider keys for any cloud stage — keys MUST
  NOT be requested in, persisted by, or logged from a recipe run.
- **FR-011**: A recipe run MUST appear as a **single unified timeline** reusing the existing
  S3 mission timeline surface, showing every stage with honest, live status; the feature
  MUST NOT introduce a competing progress surface.
- **FR-012**: The user MUST be able to **cancel** a running recipe; cancellation MUST stop
  the entire chain including subprocess production children (kill-tree), leaving no
  orphaned background work and an honest cancelled state.
- **FR-013**: On a stage failure or veto, the run MUST stop honestly, **preserve outputs
  already produced** (e.g. a completed dossier), clearly mark which stages completed and
  which did not, and MUST NOT report overall success falsely.
- **FR-013a**: After a stage failure, the user MUST be able to **resume the run from the
  failed stage**, reusing the outputs of already-completed stages rather than re-running
  them — so a run that failed at composition does not re-run the mission (with its internet
  research and inspector gate). Resume MUST re-apply the same local/cloud choices unless the
  user changes them.
- **FR-014**: When a recipe's required production capability is unavailable on this machine,
  the studio MUST surface a clean, honest message with an install hint (the studio's
  standard "capability absent" behavior) rather than crashing, and every other recipe MUST
  remain usable.
- **FR-015**: Before launch, a recipe MUST state what inputs it requires and what it will
  produce; a launch missing a required input MUST prompt for it in plain language rather
  than run on silent placeholders.
- **FR-016**: All recipe-facing copy — names, descriptions, input prompts, stage labels,
  statuses, and messages — MUST be fully internationalized in English and French, with no
  hard-coded or missing strings, updating live when the interface language changes.
- **FR-017**: The feature MUST be **additive**: recipes land as registry entries and
  default-`None` hooks so that, with no recipe selected, the existing mission/brief flow and
  all prior screens behave byte-identically. Recipes MUST NOT modify agency-kit's veto-loop
  behavior.
- **FR-018**: The strategy dossier and creatives produced by a run MUST land in the studio's
  existing deliverable surfaces (the per-client library and export bundle) so the user can
  browse and export them with the tools they already know; the feature MUST NOT introduce a
  separate parallel store. A **production recipe** — which has no mission stage and thus no
  full dossier — MUST still land its single artifact in the same library/export via a
  **lightweight deliverable record** (the recipe subject as its label, the produced media
  attached), so every recipe's output is retrievable through one path.
- **FR-019**: The single-artifact **production recipes** (the 13 pipelines exposed
  one-to-one) MUST be launchable and observable through the same catalog, launch, and
  unified-timeline experience as the composed recipes, differing only in that they produce a
  single artifact rather than a full package. Each production recipe's `pipeline` stage tier
  MUST be **derived from that pipeline's declared provider needs**: a pipeline that can run
  fully local is a **local (free)** stage, while a pipeline that requires paid cloud
  providers MUST be surfaced as a **cloud** stage requiring explicit per-run opt-in (FR-008) —
  never a silent paid run. Only paid **media** providers are the opt-in; the pipeline's
  reasoning/orchestration still runs on the subscription CLI agent (no billed reasoning path).
- **FR-020**: The studio MUST allow only **one active recipe run at a time**. While a run is
  in progress, an attempt to launch another MUST be blocked with a clear, plain-language
  message (never silently dropped or silently started), and MUST become available again once
  the active run finishes or is cancelled.

### Key Entities *(include if feature involves data)*

- **Recipe**: a named, plain-language production template the user can launch. Declares what
  it produces, what inputs it needs, its stages, and each stage's local/cloud tier. Two
  kinds: a *production recipe* (one OpenMontage pipeline) or a *composed agency recipe*.
  Defined via additive registry entries; selecting none leaves existing behavior unchanged.
- **Composed agency recipe**: the four end-to-end templates (full campaign, client pitch,
  turnkey event, social content pack) that deliver dossier + creatives together. Each
  declares its own stage set drawn from the canonical mission → assets → composition → export
  chain and MAY omit stages that do not fit its deliverable (always including the mission and
  a final output-collection step).
- **Recipe run**: one execution instance of a recipe; only one may be active at a time. Has a
  subject/brief, an ordered set of stages, a single unified timeline, an honest overall
  status, and one collected output. Can be cancelled as a whole, and — after a stage failure —
  resumed from the failed stage (reusing completed stages' outputs).
- **Stage**: one step of a recipe run (mission, asset generation, composition, export). Has
  its own status, its own local/cloud tier, and an output that feeds the next stage.
- **Strategy dossier**: the mission stage's sourced research-and-strategy output, gated by
  the unchanged inspector, delivered alongside the creatives.
- **Creatives**: the media artifacts a run produces (images, voice, video) plus the export
  bundle that packages them.
- **Working context (read-only here)**: the active client / project / campaign (owned by S8
  Settings) that a run is scoped to; recipes read it to scope and file outputs, they do not
  edit it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can complete "launch a campaign for X" and, from that **single run**,
  retrieve both a sourced strategy dossier and the associated creatives together — the
  literal done-when of the brick — with no terminal touched.
- **SC-002**: All 13 OpenMontage production pipelines and all 4 composed agency recipes are
  selectable and launchable from the Home/Brief entry point.
- **SC-003**: 100% of default recipe runs stay local and free — no run reaches a paid cloud
  provider without an explicit per-run opt-in, verified by launching with defaults and
  observing no paid/network activity beyond sanctioned mission research.
- **SC-004**: The inspector veto behaves identically inside a recipe run and in a standalone
  mission — a vetoed dossier holds the run in both cases — with zero observable difference in
  veto behavior.
- **SC-005**: 100% of recipe-facing text renders correctly in both English and French with
  zero hard-coded or missing strings, verified by switching languages on the catalog and a
  live run.
- **SC-006**: When a recipe's production capability is missing, the user gets an honest
  install hint and the rest of the studio keeps working 100% of the time — no crash, no dead
  screen.
- **SC-007**: A user follows an entire multi-stage run on one unified timeline without
  leaving for another screen, and can cancel it such that no orphaned background work
  remains.
- **SC-008**: On any stage failure or veto, completed outputs are preserved and the user is
  told exactly which stages completed — a run never reports success falsely.
- **SC-009**: With no recipe used, the existing mission/brief flow and all prior screens
  behave byte-identically to before this feature (additivity verified).
- **SC-010**: Only one recipe run is active at any time — a second launch attempt during a
  run is blocked with a clear message 100% of the time — and after a stage failure the user
  can resume from the failed stage without the mission stage re-running.

## Assumptions

- **Reuses the magic box, does not replace it**: recipe selection surfaces from **both** the
  existing Home screen and the Guided Brief, the unified progress view reuses the S3 mission
  timeline (which shows one live run at a time), and outputs land in the existing S4
  deliverable library and S6 export bundle. Brick 8 adds the recipe layer on top; it does not
  redesign these screens.
- **The guided brief gathers a recipe's inputs**: a composed recipe collects its subject /
  brief through the existing guided-brief flow rather than a new bespoke input screen,
  keeping one consistent way to describe work.
- **Composed-recipe internals are a planning decision**: each composed recipe declares its
  own stage set (stages may be skipped where they do not fit the deliverable), but exactly
  which OpenMontage pipeline(s) and asset steps each composed recipe (full campaign, client
  pitch, turnkey event, social content pack) chains, and their default parameters, are decided
  at plan time; the spec requires only that each produces a coherent dossier + creatives
  package.
- **Local-first is the ground truth**: every stage runs free and local by default; cloud is
  always an explicit, per-run, env-keyed opt-in, consistent with the rest of the studio.
- **Production-recipe tiers & output**: each of the 13 production recipes maps to one
  OpenMontage pipeline; its stage tier is read from the pipeline's manifest (a paid-provider
  need ⇒ cloud/opt-in, otherwise local), and its single artifact lands in the library/export
  via a lightweight deliverable record — so production and composed recipes share one
  retrieval path.
- **Offline-testable by design**: the feature must be exercisable with no GPU, no Node, no
  network, and no CLI engine installed — the production and mission boundaries are the
  monkeypatch points — so "capability absent" and "stage failed" are first-class, tested
  paths, not afterthoughts.
- **OpenMontage stays a pinned subprocess subtree**: recipes drive it only across the
  subprocess boundary; no in-process import and no local edits to the `openmontage/` subtree
  are introduced by this feature.
- **The inspector is untouched**: Brick 8 wires the mission stage into a chain but changes
  nothing about the inspector, its veto, or when it runs.
- **Two languages**: English and French only, matching the rest of the magic box; no
  additional locales in this cycle.
- **Out of scope for this cycle**: authoring brand-new pipelines, deep per-stage manual
  editing of intermediate artifacts, scheduling/recurring runs, and the multi-CLI validation
  work (Brick 9). Recipes launch, chain, and collect; fine-grained creative editing remains
  the province of the underlying tools.
