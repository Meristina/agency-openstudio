# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0). Mark each PASS /
FAIL / N/A with a one-line justification; any FAIL requires a Complexity Tracking
entry or a redesign.

- [ ] **I. Brain = subscription CLI agents**: No reasoning path calls a
  token-billed API; all heavy reasoning goes through a CLI engine subprocess.
- [ ] **II. Engine neutrality**: Engine-specific behavior stays behind the Engine
  contract; nothing assumes an engine lacking guaranteed headless web search;
  unvalidated engines cannot run production missions.
- [ ] **III. No invented information**: Mission-facing features preserve
  internet research, source citation (URL + date), and the inspector's veto.
- [ ] **IV. Local-first & offline-by-default**: Local/free is the default; cloud
  is explicit, opt-in, env-keyed; no network access without per-mission opt-in;
  non-Mac platforms are not regressed.
- [ ] **V. Subprocess boundaries**: No in-process import of `openmontage/`;
  engines driven via subprocess only; vendored subtrees untouched except via
  `git subtree pull` (`agencykit/` remains the only imported library).
- [ ] **VI. Security**: `127.0.0.1` bind only, no CORS `*`, `path_inside()` on
  served paths, https-only outbound, API keys env-only (never persisted/logged).
- [ ] **VII. Offline tests**: New behavior is covered by tests that run with no
  network, no CLI, no Node, no GPU (boundaries monkeypatched).
- [ ] **VIII. End-user simplicity**: Any user-facing surface is operable by a
  non-technical user (single entry point, guided defaults, no terminal required).
- [ ] **IX. License**: New/reused components are AGPL-3.0-compatible and recorded
  in `docs/LICENSES.md`.
- [ ] **X. Additive over invasive**: Changes land as default-`None` hooks /
  registry entries; behavior is byte-identical with the option off; the
  inspector veto loop is untouched.
- [ ] **XI. English everywhere**: All code, docs, and commits in English.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
