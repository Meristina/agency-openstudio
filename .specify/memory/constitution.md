<!--
Sync Impact Report
==================
Version change: (template, unversioned) → 1.0.0 (initial ratification)
Modified principles: n/a — initial adoption; all 11 principles created from user input:
  I. Brain = Subscription CLI Agents
  II. Engine Neutrality (Headless Web Search Precondition)
  III. No Invented Information (NON-NEGOTIABLE)
  IV. Local-First, Cross-Platform, Explicit Free/Paid Choice
  V. Subprocess Boundaries
  VI. Non-Negotiable Security
  VII. Mandatory Offline Tests
  VIII. End-User Simplicity
  IX. License: AGPL-3.0-only
  X. Additive Over Invasive
  XI. English Everywhere
Added sections: Core Principles (I–XI), Additional Constraints & Technology Stack,
  Development Workflow & Quality Gates, Governance
Removed sections: none (all template placeholder slots filled)
Templates:
  ✅ .specify/templates/plan-template.md — Constitution Check gate list populated (I–XI)
  ✅ .specify/templates/tasks-template.md — tests made mandatory for code changes (Principle VII)
  ✅ .specify/templates/spec-template.md — no change required (no constitution-specific sections)
  ✅ AGENTS.md / CLAUDE.md — already aligned (principles were derived from it); it defers to
     this constitution by design
  ➖ .specify/templates/commands/*.md — directory does not exist in this repo (N/A)
Follow-up TODOs: none — no deferred placeholders.
-->

# Agency OpenStudio ("Agency 360") Constitution

Agency OpenStudio is the ultimate 360 agency: a multimedia, B2B 360, and event agency
driven end-to-end by CLI coding agents on monthly subscriptions. This constitution is
the supreme governance document for the repository. Every spec, plan, task list, and
implementation MUST comply with it; `AGENTS.md` and all other guidance documents are
subordinate to it and must never contradict it.

## Core Principles

### I. Brain = Subscription CLI Agents

All heavy reasoning — routing, department execution, synthesis, inspection, and
extraction — MUST run through a CLI agent subprocess (claude, codex, gemini, …)
operating on a monthly subscription. A token-billed API MUST NOT be used for any
reasoning path. The marginal cost of a mission MUST remain zero.

**Rationale**: The entire business model rests on zero marginal cost per mission;
one token-billed call reintroduces per-mission economics and breaks the product.

### II. Engine Neutrality (Headless Web Search Precondition)

Any engine satisfying the Engine contract (headless `run(prompt)` / `route(prompt)`,
declared capabilities, kill-tree on cancel) MAY drive the agency. The absolute
precondition is **guaranteed headless web search** (`web_search_headless: true`).
The validated v1 engine is `claude`. An engine that has not passed end-to-end
validation MUST NOT run a production mission; unvalidated engines stay registered
but explicitly marked unvalidated.

**Rationale**: Engine neutrality prevents vendor lock-in, but Principle III is
impossible on an engine that cannot search the web headlessly — so that capability
gates admission, and validation gates production use.

### III. No Invented Information (NON-NEGOTIABLE)

Every mission MUST research on the live internet. Every factual claim in a
deliverable MUST cite a real, verifiable source (URL + access date). The inspector
spot-checks sources and holds veto power over every deliverable; its verdict is
final until fixes are applied and re-inspected. This guarantee MUST be hardened from
a prompt-level mandate into a runtime-verified postcondition (citation extraction,
URL resolution, minimum source count per department — PLAN.md Brick 3): a
deliverable without resolvable sources MUST be blocked.

**Rationale**: An agency that invents facts is worthless and dangerous to its
clients; trust is the product.

### IV. Local-First, Cross-Platform, Explicit Free/Paid Choice

Local models are the default and MUST be free to run. Cloud providers are explicit,
opt-in, env-keyed choices (paid) — never silent defaults. The product MUST run on
any machine (macOS, Linux, Windows): platform-specific engines (e.g. MLX) MUST get
cross-platform siblings behind the same registries. A mission MUST NOT touch the
network except through an explicit per-mission opt-in flag; absent opt-in, the
mission is fully offline apart from the engine's own research (Principle III).

**Rationale**: Local-first keeps the free tier genuinely free and private;
explicitness keeps every euro spent a deliberate user decision.

### V. Subprocess Boundaries

`openmontage/` and the CLI engines MUST be driven only across subprocess
boundaries. `openmontage/` MUST NOT be imported in-process (its
`tools/base_tool.py` autoloads `.env` at import). `agencykit/` is the single
permitted imported library — the orchestration brain (`agency_cli` /
`agency_kit`), installed editable from the subtree. Vendored subtrees
(`openmontage/` pinned @ `0c202b5`, `agencykit/` pinned @ `fc8ac76`) MUST be
updated only via `git subtree pull`; local edits to `openmontage/` MUST be avoided.

**Rationale**: Subprocess isolation contains side effects, keeps the core
dependency-free, and preserves clean subtree merges with upstreams.

### VI. Non-Negotiable Security

The server MUST bind `127.0.0.1` only — never `0.0.0.0`. The server MUST NOT emit
`Access-Control-Allow-Origin: *`. Every served file path MUST pass a
path-traversal guard (`path_inside()`). All outbound requests MUST be HTTPS-only.
API keys MUST live in environment variables only: never accepted in request
fields, never persisted, never logged. See `docs/SECURITY.md`.

**Rationale**: The studio runs on the user's own machine next to their client
data and paid credentials; any one of these failures is a direct compromise.

### VII. Mandatory Offline Tests

The full test suite MUST run with no network, no CLI agent installed, no Node, and
no GPU — every subprocess and network boundary monkeypatched. No merge to `main`
without a green suite. `pytest` at the repo root collects `tests/` only;
`openmontage/` and `agencykit/` carry their own suites, run from their directories.

**Rationale**: Offline tests are the only tests every contributor and CI runner
can execute identically; anything requiring live engines or network is untestable
at the boundary and flaky at the core.

### VIII. End-User Simplicity

Every user-facing surface MUST be operable by a non-technical user: a single entry
point ("what do you want to produce?"), guided briefs, sensible defaults, and
import/export. Complexity lives behind the interface, never in front of it. A
feature that requires the user to open a terminal is not done (env vars remain a
power-user override, never a requirement).

**Rationale**: The target user is an agency operator, not a developer; the "magic
box" promise (PLAN.md Brick 7) fails the moment a screen assumes technical skill.

### IX. License: AGPL-3.0-only

The combined work is licensed AGPL-3.0-only (since the OpenMontage fusion;
pre-fusion studio code remains MIT-available in `LICENSE.MIT`). Reusing
open-source code is welcome and encouraged; every reused component MUST be
recorded in `docs/LICENSES.md` with its license, and MUST be AGPL-compatible.

**Rationale**: AGPL keeps the network-served studio and its derivatives open;
the licenses ledger keeps the combination legally auditable.

### X. Additive Over Invasive

Extensions MUST land as default-`None` hooks and registry entries
(`IMAGE_MODELS` / `VIDEO_MODELS` / `VISUAL_MODELS` / `make_extractor` pattern):
with the option off, existing behavior stays byte-identical. agency-kit's
inspector veto-loop logic MUST never change behavior. Invasive rewrites of
working paths require explicit justification in the feature's Complexity
Tracking table.

**Rationale**: Byte-identical defaults make every brick independently mergeable
and revertible; the veto loop is the trust anchor and must stay provably intact.

### XI. English Everywhere

All documentation, code, comments, identifiers, commit messages, specs, and plans
MUST be written in English. End-user-facing product surfaces MAY be localized
(EN/FR i18n is planned — PLAN.md Brick 7); the repository itself is English-only.

**Rationale**: One repository language keeps every engine, contributor, and
vendored upstream working from the same text.

## Additional Constraints & Technology Stack

- **Core**: Python stdlib only — zero runtime dependencies. Everything else is a
  lazily-imported optional extra; when absent, the server returns a clean HTTP 501
  with an install hint.
- **Frontend**: React + Vite under `app/studio/`.
- **Typing**: Python code carries type hints.
- **Roadmap**: `PLAN.md` (bricks 0–9) is the canonical roadmap; work proceeds
  brick by brick, in order, each brick independently mergeable.
- **Agent context**: `AGENTS.md` is canonical (`CLAUDE.md` is a symlink to it) and
  MUST NOT contradict this constitution.
- **Vendored suites**: `openmontage/` and `agencykit/` internal agent
  configuration (`CLAUDE.md`, `.claude/`) governs those subtrees only.

## Development Workflow & Quality Gates

- **Spec-kit cycle**: Every PLAN.md brick goes through the full spec-kit cycle —
  `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks` →
  `/speckit.implement` — before merge. No brick skips a stage.
- **Constitution Check**: Every implementation plan MUST pass the Constitution
  Check gates (plan template) before Phase 0 research and again after Phase 1
  design. Violations require a justified entry in Complexity Tracking or a
  redesign.
- **Commits & PRs**: Conventional Commits; branch before non-trivial work; PRs
  squash-merge to `main`.
- **Merge gate**: Offline suite green on every merge (Principle VII); security
  invariants (Principle VI) verified on any change touching the server surface.
- **Inspector gate**: Mission deliverables pass the inspector (Principle III);
  its veto blocks shipment until fixes are applied and re-inspected.

## Governance

- **Supremacy**: This constitution supersedes all other practices, guidance files,
  and habits in this repository. Where any document conflicts with it, the
  constitution wins and the other document MUST be corrected.
- **Amendment procedure**: Any change to this constitution requires an explicit
  human decision — the repository owner approves the amendment before it is
  committed. Agents MUST NOT amend the constitution autonomously. Each amendment
  updates the version, the Sync Impact Report, and propagates to dependent
  templates in the same change.
- **Versioning policy**: Semantic versioning — MAJOR for backward-incompatible
  principle removals or redefinitions; MINOR for new principles or materially
  expanded guidance; PATCH for clarifications and wording.
- **Compliance review**: Every spec, plan, and PR review MUST verify compliance
  with the applicable principles; the plan template's Constitution Check is the
  enforcement point during design, and the offline suite plus code review enforce
  it at merge. Complexity MUST always be justified against a simpler rejected
  alternative.

**Version**: 1.0.0 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-07-03
