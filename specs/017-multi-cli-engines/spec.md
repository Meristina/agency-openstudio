# Feature Specification: Real Multi-CLI — Validate codex, Replace gemini with antigravity, Add opencode, Publish Compatibility Matrix

**Feature Branch**: `017-multi-cli-engines`

**Created**: 2026-07-07

**Status**: Draft

**Input**: User description: "Brick 9 — Real multi-CLI: validate codex and gemini end-to-end against the Brick 1 Engine contract, add opencode, and publish an engines × capabilities compatibility matrix."

> **Scope correction (2026-07-07, from CLI verification)**: The original brief named `gemini` as the second engine to validate. Verification of the actual CLIs found that Google has transitioned **Gemini CLI → Antigravity CLI** (binary `agy`); the consumer `gemini` binary stopped serving requests on 2026-06-18 and is absent from the environment, while `agy` (Antigravity CLI 1.0.14) is installed. Per the owner's decision, the deprecated `gemini` slot is **replaced by a new `antigravity` engine** (binary `agy`). Codex — which exposes a real web-search flag (`--search` = live web search) — becomes the target second *validated* engine; `antigravity` and `opencode` are registered as candidates pending proof of guaranteed headless web search.

## Overview

Today only one engine — `claude-code` — is validated to drive a production mission; `codex` and `gemini` are registered but refused (`EngineNotValidated`). Brick 1 formalized the Engine contract (run/route invocation, a declared `web_search_headless` capability, kill-tree on cancel) so that adding or promoting an engine is a single registry change plus its contract tests, with no changes to the mission loop. Brick 9 makes a second engine genuinely usable and broadens the candidate roster: it validates `codex` end-to-end, replaces the deprecated `gemini` slot with a new `antigravity` engine (binary `agy`), registers `opencode` as a further candidate, and publishes a single engines × capabilities compatibility matrix so an operator can see at a glance what each engine can and cannot do — and which are cleared for production.

The load-bearing promise (Constitution Art. II & III) is preserved throughout: an engine may only be promoted to production once it genuinely satisfies the contract, **including guaranteed headless web search** — because a mission must research the live internet, never fabricate. Engines that have not passed that bar stay registered but refused.

## Clarifications

### Session 2026-07-07

- Q: What may `web_search_headless=True` mean when an engine's web search is config-/env-gated (opencode's Exa via `OPENCODE_ENABLE_EXA` or the OpenCode provider; Antigravity's tool-driven search) rather than guaranteed by our own invocation flag? → A: Permissive — an engine MAY declare `web_search_headless=True` when the required configuration is explicitly **documented** AND a **live-test proves real headless web search** under that configuration; absent that proof it declares `False`. The compatibility matrix must surface the config dependency rather than showing a plain affirmative.
- Q: What is the validation scope to close Brick 9? → A: The brick **attempts live validation of all three candidates** (codex, antigravity, opencode); each flips to `validated=True` only if its own live-test proves the full contract (including headless web search). The minimum completion bar stays `claude-code` + `codex` (two validated engines) — antigravity and opencode validate if they pass, but their failure does not block the brick.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the same mission on a second production engine (Priority: P1)

An agency operator who normally runs on `claude-code` selects `codex` for a mission and gets a comparable, source-verified deliverable — no longer a refusal. The operator is not locked to a single vendor: any engine that has passed validation drives the full route → execute → synthesize → inspect loop unchanged, and its dossier carries resolvable, cited sources just like the default engine's.

**Why this priority**: This is the core value and the brick's "Done when" — the same mission passing on two engines with comparable dossiers and verified sources per engine. Codex is the realistic second engine because it exposes a real headless web-search capability. Without this, engine-neutrality is a claim in the contract but not a reality for the operator.

**Independent Test**: Run one representative mission on `claude-code` and again on `codex`; confirm both return a structurally comparable dossier (route, department outputs, synthesized deliverable, inspector verdict) and that each dossier meets the source-verification postcondition (minimum sources per department, URLs resolvable). The offline suite proves the engine is *accepted* for production and drives the loop against a fake binary; the real cross-engine parity run is captured in a live-test report.

**Acceptance Scenarios**:

1. **Given** `codex` has passed end-to-end validation and is marked validated, **When** the operator runs a mission selecting `codex`, **Then** the mission is not refused and completes the full route → execute → synthesize → inspect loop, returning a dossier of the same shape as a `claude-code` run.
2. **Given** `codex` is validated, **When** the operator runs the same mission on it, **Then** the deliverable cites resolvable internet sources meeting the per-department minimum (the Brick 3 verification postcondition), with no fabricated data.
3. **Given** a validated engine is selected, **When** the mission runs, **Then** the mission-loop logic (routing, department order, synthesis, and the inspector veto loop) behaves identically to a `claude-code` run — only the engine invocation differs.
4. **Given** the same mission is run on `claude-code` and on `codex`, **When** both complete, **Then** the two dossiers are comparable in structure and each independently satisfies the source-verification postcondition (evidenced in the live-test report).

---

### User Story 2 - Consult the engines × capabilities compatibility matrix (Priority: P2)

An operator (or contributor) opens the README and reads a single table showing every registered engine against its capabilities — run/route invocation, headless web search, MCP tool-config support, kill-tree on cancel — and its current validation status. They can decide which engine to run without reading source code, and see honestly which engines are cleared for production and which are not yet.

**Why this priority**: The matrix is an explicit brick deliverable and the operator-facing surface that makes engine-neutrality legible. It depends on the validation work (P1) and the roster changes (P3) being reflected accurately, so it ranks below P1 but is required for the brick to be done.

**Independent Test**: Read the README matrix and confirm it lists every registered engine with a row per engine and a column per capability, that each engine's validation status matches the actual registry state, and that no validated engine is shown without headless web search.

**Acceptance Scenarios**:

1. **Given** the compatibility matrix is published in the README, **When** a reader views it, **Then** it contains one row per registered engine (`claude-code`, `codex`, `antigravity`, `opencode`) and columns for run/route, headless web search, MCP tool-config support, kill-tree on cancel, and validation status.
2. **Given** the matrix, **When** compared against the actual engine registry, **Then** each engine's stated validation status and capabilities match reality (the matrix reflects the registry, not aspiration) — including honestly marking any engine whose headless web search is config-gated rather than guaranteed.
3. **Given** the matrix, **When** any engine is marked validated, **Then** that engine's headless-web-search column is affirmative (the two can never disagree).

---

### User Story 3 - Register the new candidate engines (antigravity, opencode) (Priority: P3)

A maintainer replaces the deprecated `gemini` slot with a new `antigravity` engine (using the Antigravity CLI's headless print invocation) and registers `opencode` (using its `run` invocation) — both as new candidates. They appear everywhere engines are listed — CLI choices, health check, the matrix — but start unvalidated and are refused for production missions until they pass the same end-to-end bar as codex, including proof of guaranteed headless web search.

**Why this priority**: Adding these candidates broadens engine coverage and proves the "adding an engine = one registry entry + contract tests" property, but neither delivers production capability on its own (both stay refused), so this is the lowest priority of the three.

**Independent Test**: Confirm `antigravity` and `opencode` are present in the registry and every derived listing, that the deprecated `gemini` slot is gone, that selecting either candidate for a production mission is refused with the standard not-validated error naming the validated alternative(s), and that the change leaves all other engines' behavior byte-identical.

**Acceptance Scenarios**:

1. **Given** `antigravity` and `opencode` are registered as engines, **When** the operator lists available engines (CLI, health check, matrix), **Then** both appear with an unvalidated status and the deprecated `gemini` slot is no longer offered.
2. **Given** a candidate engine is unvalidated, **When** the operator selects it for a production mission, **Then** the mission is refused with the standard not-validated error that names the reason and the validated alternative(s), and no engine is silently substituted.
3. **Given** the roster is changed, **When** the existing engines (`claude-code`, `codex`) are exercised, **Then** their invocation, refusal, and mission behavior are unchanged.
4. **Given** an engine whose headless web search is not guaranteed (config-/provider-gated), **When** it is registered, **Then** it is not promoted to validated on capability alone — validation still requires live proof that it genuinely searches the web headlessly.

---

### Edge Cases

- **Declared-but-unproven web search**: An engine's registry entry could claim headless web search that its real CLI does not actually perform (e.g. an engine whose search is provider- or env-gated). Promotion to validated MUST be backed by a live-test report demonstrating real searched sources; an engine that cannot genuinely search headlessly MUST NOT be promoted, regardless of its declared capability.
- **Inconsistent capability + validation**: An attempt to register a validated engine that does not declare headless web search MUST be rejected at registration (the existing invariant), so the two can never disagree.
- **Deprecated/absent binary**: Removing the deprecated `gemini` slot MUST NOT be a silent fallback — selecting `gemini` after removal is an unknown-engine error listing the current registered engines, not a substitution.
- **Missing engine binary**: Selecting a validated engine whose CLI is not installed/authenticated MUST fail fast with a clear, actionable message (install + authenticate), not a silent fallback or a mid-mission crash.
- **Cancel / timeout on a candidate or newly-validated engine**: Cancelling or timing out a mission on codex, antigravity, or opencode MUST terminate the engine's whole process group (kill-tree), leaving no orphaned child processes — the same guarantee `claude-code` gives.
- **Distinct run vs route invocation**: An engine whose non-interactive invocation requires a subcommand or specific flag placement (e.g. a subcommand-first CLI) MUST have both its run and route invocations independently correct — a route invocation that silently falls back to interactive mode (hanging headless) is a defect the contract tests MUST catch.
- **MCP tool-config on engines that don't support it**: The studio's MCP tool-config hook applies only to engines that speak that flag; for every other engine the invocation MUST be unchanged (no spurious flags), and the matrix MUST report which engines support it.
- **Unvalidated-but-declared-capable engine**: An engine that declares headless web search but has not passed validation MUST still be refused for production (validation gates production use, not merely capability).
- **Offline suite with no real CLI**: The full offline test suite MUST pass with no real engine CLI, no network, and no Node — each engine exercised via a fake binary on a temporary PATH with the subprocess boundary monkeypatched.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST promote `codex` to a validated production engine only after it has genuinely satisfied the Engine contract end-to-end — including guaranteed headless web search — evidenced by a live-test report; until then `codex` stays refused.
- **FR-002**: The system MUST replace the deprecated `gemini` registry slot with a new `antigravity` engine (Antigravity CLI, binary `agy`, headless print invocation), registered `validated=False` and therefore refused for production missions until it passes the same end-to-end bar (including proof of headless web search per FR-006). The brick MUST attempt this end-to-end validation for `antigravity`, flipping it to validated only if its own live-test proves the contract. The `gemini` engine slot MUST be removed.
- **FR-003**: Each engine MUST retain its own run/route invocation in the engine registry, with both invocations independently correct for non-interactive use; validating or adding an engine MUST be achievable as a single registry-entry change plus its contract tests, with zero changes to the mission loop.
- **FR-004**: The system MUST register `opencode` as a new engine (using its `run` invocation), starting `validated=False` and therefore refused for production missions until it passes the same end-to-end bar. The brick MUST attempt this end-to-end validation for `opencode` (with its Exa web search enabled via the documented configuration), flipping it to validated only if its own live-test proves the contract.
- **FR-005**: The system MUST refuse any registered-but-unvalidated engine selected for a production mission with the standard not-validated error, naming the reason and the validated alternative(s), and MUST NOT silently substitute a different engine. Selecting a removed engine name (e.g. `gemini`) MUST raise the unknown-engine error, never a silent substitution.
- **FR-006**: The system MUST reject registration of any engine marked validated that does not declare headless web search (preserve the existing construction-time invariant), so validation status and web-search capability can never disagree. An engine whose web search is config-/env-gated (e.g. opencode's Exa via `OPENCODE_ENABLE_EXA`/provider, or Antigravity's tool-driven search) MAY declare `web_search_headless=True` **only** when the required configuration is explicitly documented AND a live-test has proven real headless web search under that configuration; absent that proof it MUST declare `web_search_headless=False`.
- **FR-007**: A validated engine MUST drive the full route → execute → synthesize → inspect mission loop with behavior identical to `claude-code` — routing, department order, synthesis, and the inspector veto loop MUST stay byte-identical; only the engine invocation differs.
- **FR-008**: A mission run on any validated engine MUST satisfy the source-verification postcondition (minimum cited sources per department, URLs resolvable — the Brick 3 gate), producing a deliverable with no fabricated data.
- **FR-009**: Cancelling or timing out a mission on any engine MUST terminate the engine's whole process group (kill-tree), leaving no orphaned processes.
- **FR-010**: The README MUST publish an engines × capabilities compatibility matrix with one row per registered engine and columns for run/route invocation, headless web search, MCP tool-config support, kill-tree on cancel, and validation status.
- **FR-011**: The compatibility matrix MUST reflect the actual registry state — every engine's stated capabilities and validation status MUST match reality at publication time, and MUST honestly distinguish guaranteed headless web search from config-/provider-gated search.
- **FR-012**: Adding, replacing, or validating an engine MUST leave all *other* engines' invocation, refusal behavior, and mission behavior byte-identical, and the inspector veto loop MUST NOT change behavior. (Removing the deprecated `gemini` slot is a deliberate roster change justified by its consumer-tier deprecation and absent binary — see Assumptions — and is the one non-additive edit, scoped to that slot alone.)
- **FR-013**: Engines MUST be driven only across the subprocess boundary; no engine may be imported in-process.
- **FR-014**: Engine authentication and API keys MUST remain environment-/session-only — never accepted in request fields, never persisted, never logged.
- **FR-015**: The full test suite MUST remain green with no real engine CLI, no network, and no Node — each engine (including codex, antigravity, opencode) exercised via a fake binary on a temporary PATH with the subprocess boundary monkeypatched. End-to-end validation against the real CLIs is captured in a separate live-test report and MUST NOT be a requirement for the offline suite to pass.
- **FR-016**: The end-to-end validation attempts for codex, antigravity, and opencode MUST be recorded in a live-test report (in the style of the archived live-test reports) that documents, per engine, the outcome — a completed mission with resolvable, verified sources for any engine that passed (the artifact that justifies flipping it to validated), and the specific failure/limitation for any engine that did not.

### Key Entities

- **Engine**: A CLI agent that can drive a mission. Attributes: name, run invocation, route invocation, declared headless-web-search capability, kill-tree-on-cancel guarantee, per-call timeouts, and validation status (may / may-not drive a production mission). Registered engines after this brick: `claude-code` (validated), `codex` (target of validation), `antigravity` (candidate, binary `agy`), `opencode` (candidate). The deprecated `gemini` slot is removed.
- **Compatibility Matrix**: The README-published table mapping each registered engine to its capabilities (run/route, headless web search, MCP tool-config support, kill-tree) and its validation status. Derived from — and required to match — the registry.
- **Live-Test Report**: A per-engine end-to-end validation record demonstrating a real mission completing with resolvable, verified sources; the evidence that authorizes promoting an engine to validated.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The same representative mission completes on `claude-code` and on `codex`, each producing a structurally comparable dossier — a measurable jump from 1 validated production engine to at least 2.
- **SC-002**: For each validated engine, the mission's deliverable meets the source-verification postcondition — every routed department has at least the minimum number of cited sources and 100% of the sampled cited URLs resolve — with zero fabricated sources.
- **SC-003**: An operator can determine, from the README matrix alone (without reading source code), which engines are cleared for production and what each engine supports, for 100% of registered engines.
- **SC-004**: Selecting any unvalidated engine (`antigravity`, `opencode`) for a production mission is refused 100% of the time with an actionable message naming the validated alternative(s), and never silently substituted; selecting the removed `gemini` name yields an unknown-engine error.
- **SC-005**: The offline test suite passes with no real CLI, no network, and no Node installed, covering every registered engine via a fake binary.
- **SC-006**: Replacing the `gemini` slot, adding `antigravity`/`opencode`, and validating codex change zero behavior for any other engine and leave the inspector veto loop byte-identical (verified by the existing suite staying green).
- **SC-007**: 100% of validated engines shown in the matrix also show affirmative headless web search (the two never disagree).

## Assumptions

- **Validation is evidence-gated**: An engine is flipped to validated in the committed registry only after a live-test report demonstrates it genuinely satisfies the contract (including real headless web search). The offline suite then proves the *now-validated* engine is accepted and drives the loop against a fake binary; it does not itself perform live validation.
- **"Done when" threshold**: The minimum completion bar is the same mission passing on two engines total (`claude-code` plus `codex`) — `codex` is the realistic second *validated* engine because it exposes a guaranteed headless web-search flag (`--search` = live web search). Beyond that minimum, the brick **actively attempts** live validation of all three candidates (codex, antigravity, opencode); each flips to validated only if its own live-test proves the full contract (including headless web search per FR-006). Any candidate that does not pass stays registered-but-refused — none is promoted on partial evidence, and a candidate's failure does not block the brick from closing once the minimum bar is met.
- **gemini → antigravity replacement**: Google transitioned Gemini CLI to Antigravity CLI (binary `agy`); the consumer `gemini` binary stopped serving requests on 2026-06-18 and is absent from the environment. Per the owner's decision, the deprecated `gemini` slot is removed and replaced by an `antigravity` engine invoked headlessly via `agy --print`. Removing a registered engine is the single deliberate non-additive edit in this brick, justified by the upstream deprecation.
- **antigravity / opencode web-search caveat**: Neither Antigravity CLI nor opencode exposes a dedicated web-search flag the way codex does — Antigravity's search is tool/plugin-driven (likely requiring auto-approval of tool calls in headless mode) and opencode's is Exa-based and only enabled via the OpenCode provider or an `OPENCODE_ENABLE_EXA` environment flag. Both therefore start as candidates. Per the Session 2026-07-07 clarification, either MAY declare `web_search_headless=True` once its required configuration is explicitly documented AND a live-test proves real headless web search under that configuration (the permissive rule of FR-006); the presence of a config path alone is never sufficient, and the matrix must name the configuration dependency rather than showing a plain affirmative.
- **codex invocation correctness**: The engine's non-interactive invocation for codex uses the `exec` subcommand with correct flag placement (global `--search` before the subcommand; `exec` options after it) for *both* run and route paths — the pre-existing registry entry's route invocation is corrected as part of validating codex, since an interactive-fallback route path would hang headless.
- **Reuse of Brick 3**: The source-verification postcondition (minimum sources per department, URL resolution) is the existing Brick 3 gate, reused unchanged as the per-engine parity criterion — this brick adds no new verification mechanism.
- **`claude-code` stays the default**: The default engine and v1 validated engine remains `claude-code`; nothing in this brick changes the default or the mission loop.
- **MCP tool-config scope**: The studio's MCP tool-config hook remains applicable only to the engine family that speaks that flag today (`claude-code`); the matrix documents per-engine support rather than extending the hook to every engine.
- **Offline discipline mirrors the existing contract suite**: New per-engine contract tests mirror the existing engine-contract test approach — one fake binary per engine on a temporary PATH, subprocess boundary monkeypatched — so the suite needs no CLI, network, or Node.
