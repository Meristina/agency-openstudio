# Tasks: Verifiable Internet (Enforced Source Postcondition)

**Input**: Design documents from `/specs/003-verifiable-sources/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: MANDATORY (Constitution VII) — every code change ships offline tests (no
network, no CLI, no Node, no GPU; the liveness probe is a module seam monkeypatched
exactly like `cli_engine._call`). Tests are written FIRST and must FAIL before the
implementation task that makes them pass.

**Organization**: Grouped by user story so each story is independently implementable
and testable. US1 = runtime enforcement (library), US2 = visibility (dossier + GUI),
US3 = operator control (flags / request field / toggle).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (user story phases only)

## Path Conventions

Three-surface layout from plan.md: brain in `agencykit/agency_cli/` (+ its own
`agencykit/tests/`, run from `agencykit/`), server in `agency_studio/` (+ repo-root
`tests/`), GUI in `app/studio/src/` (vitest).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the green starting state — no scaffolding or dependencies are
needed (stdlib-only feature on an existing tree).

- [X] T001 Record the pre-feature baseline: run `pytest tests/ -q` in `agencykit/`, `pytest tests/ -q` at repo root, and `npx vitest run` in `app/studio/` — all green, zero network (this baseline is the SC-004 byte-identical reference)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The verification engine module itself — pure, loop-independent logic
every story consumes (config, extraction, probe, gate, report).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Write failing unit tests in `agencykit/tests/test_verification.py`: VerificationConfig defaults/validation (min_sources ≥ 0) and dict coercion; URL extraction + per-department attribution + dedup; the full D3 classification table (probe seam monkeypatched per row); policy refusals (non-https, literal private/loopback IP, `localhost`) asserting the probe seam is NEVER called; per-dept gate math incl. `min_sources=0` exemption (D7 unified counted formula); rate math (`resolved/checkable`, `null` when resolve off); total-network-outage degradation (all probes fail at connection level ⇒ statuses `unverified`, `rate=null`, gate falls back to extracted count — D3); cap/clamp-skipped URLs ⇒ `unverified` + `truncated` accounting; per-mission probe cache
- [X] T003 Create `agencykit/agency_cli/verification.py` with `VerificationConfig` (frozen dataclass: `min_sources=3`, `resolve=False`, fail-fast validation) and the `{"min_sources", "resolve"}` dict-coercion helper (data-model.md)
- [X] T004 Implement URL extraction, per-department attribution (`dept_outputs` + synthesis pool), and first-seen dedup in `agencykit/agency_cli/verification.py` (reuse the `_SOURCE_URL_RE` extraction shape from `cli_engine.py`)
- [X] T005 Implement the probe seam and pre-fetch policy guards in `agencykit/agency_cli/verification.py`: HTTPS-only scheme check, literal-IP private/loopback/link-local + `localhost` refusal (never fetched), HEAD probe (5 s timeout, redirects followed, no body read, no credentials), and the D3 outcome→status classification (resolved / ambiguous / unresolved / unverified / unverifiable)
- [X] T006 Implement the bounded resolution runner in `agencykit/agency_cli/verification.py`: dedup-then-cap at `MAX_URLS_PER_CYCLE=50` with `truncated` count, `concurrent.futures.ThreadPoolExecutor(max_workers=8)`, 60 s wall clamp per cycle, per-mission URL→(status, detail) cache (depends on T005)
- [X] T007 Implement gate math + rate + report assembly in `agencykit/agency_cli/verification.py`: per-dept `counted` via the D7 unified formula (`extracted − unresolved − unverifiable`), gate `ok` iff every deployed dept meets `min_sources`, `rate = resolved/checkable` (`None` when resolve off or cycle degraded), assemble the `CycleVerification` dict per data-model.md (depends on T004, T006)
- [X] T008 Run `pytest tests/test_verification.py -q` from `agencykit/` — the T002 suite now passes, fully offline

**Checkpoint**: The verification engine is a tested, standalone module — story phases can begin.

---

## Phase 3: User Story 1 — An unsourced deliverable is blocked with an actionable report (Priority: P1) 🎯 MVP

**Goal**: The synth→inspect loop enforces the source minimum as a runtime
postcondition: unmet minimum ⇒ re-enter the veto loop with actionable fixes;
verdict contract untouched; two independent recorded signals (clarify Q5).

**Independent Test**: Offline engine test (`_call` + probe seam faked): a mission
whose department output cites nothing is blocked — the loop re-enters with the
verification failure naming the offending department/claims — while a well-sourced
mission passes untouched; `--min-sources 0`-equivalent (hook `None`) is byte-identical
to the T001 baseline.

### Tests for User Story 1 (write first, ensure they FAIL) ⚠️

- [X] T009 [US1] Write failing loop-integration tests in `agencykit/tests/test_engine.py`: (a) `verification=None` ⇒ dossier/prompts/events byte-identical to pre-feature; (b) under-sourced dept ⇒ `verifications[i].ok is False`, fixes injected, synthesis re-run; (c) inspector PASS + verification FAIL ⇒ retried, verdict entry still `PASS` (Q5 two-signal); (d) cap reached ⇒ `residual_risk` names the verification failure; (e) dict-shaped `verification` coerced; (f) cancellation mid-verify ⇒ `MissionCancelled`, no dossier; (g) checkpoint carries `verifications`, resume tolerates absent key and recomputes the re-entered cycle; (h) the cycle report's `missing` list carries inspector-named unsourced claims when present, `[]` when indeterminate

### Implementation for User Story 1

- [X] T010 [US1] Add `verification: Optional[VerificationConfig] = None` to `run_mission_cli` in `agencykit/agency_cli/engines/cli_engine.py`: dict coercion (mirror the escalation coercion), per-cycle verification after the verdict is parsed, separate `verifications` list, loop break `token not in _RETRY_VERDICTS and verification_ok`, verification failure block appended to `fixes` — `_short_verdict`, verdict tokens, `verdicts` schema, `MAX_ITERS` untouched
- [X] T011 [US1] Enrich the inspector input (only when the hook is active) in `agencykit/agency_cli/engines/cli_engine.py`: append the deterministic report to `_inspect_prompt`'s deliverable context with the name-unsourced-claims instruction; parse named claims into the cycle report's `missing` list (D9 — inspector output *parsing* for the verdict unchanged)
- [X] T012 [US1] Assemble `dossier["verification"]` (`min_sources`, `resolve`, `cycles`, `final`) and extend the `residual_risk` text to cover a failing verification at the cap, in `agencykit/agency_cli/engines/cli_engine.py` (key present ONLY when the hook is active)
- [X] T013 [US1] Emit `{"phase": "verify", ...}` `on_event` frames (start / done with `ok`, `rate`, `checked`) per cycle in `agencykit/agency_cli/engines/cli_engine.py` (contracts/http-api-gui.md)
- [X] T014 [US1] Carry `verifications` through `_checkpoint` snapshots and extend `_validate_resume_state` (absent ⇒ valid; present ⇒ list with `len == len(verdicts)`); resumed cycle recomputes verification, in `agencykit/agency_cli/engines/cli_engine.py`
- [X] T015 [US1] Run `pytest tests/ -q` from `agencykit/` — T009 suite passes, all pre-existing tests still green (byte-identical guarantee holds)

**Checkpoint**: The enforced postcondition works end-to-end at the library level — SC-001 provable offline.

---

## Phase 4: User Story 2 — The operator sees the verified-source rate in the dossier and the GUI (Priority: P1)

**Goal**: The verification record flows from the engine into the persisted dossier
(structured + rendered) and the studio GUI (timeline + mission detail), with the
`null`-rate "unverified (resolution not enabled)" distinction.

**Independent Test**: Offline: run a faked mission with a known resolved/unresolved
mix through `runner_bridge.run(verification=...)`; assert `dossier.md` contains the
Source verification section with the rate, and vitest renders the rate (and the
"unverified" label for `rate: null`) in MissionDetail from a fixture dossier.

### Tests for User Story 2 (write first, ensure they FAIL) ⚠️

- [X] T016 [P] [US2] Write failing tests in `agencykit/tests/test_runner_bridge.py` (extend existing runner-bridge coverage or create): `run()`/`resume()` accept and pass through `verification`; `_resolve_verification` coercion (dict → config; `min_sources=0` + `resolve=False` → `None`; `min_sources=0` + `resolve=True` → report-only config; junk → defaults); `_dossier_md` renders the Source verification section (rate %, per-dept table, unresolved list, missing claims, truncation note; offline mode renders "unverified (resolution not enabled)"; absent key ⇒ byte-identical rendering)
- [X] T017 [P] [US2] Write failing GUI tests: `app/studio/src/components/MissionDetail.test.tsx` (rate headline, per-dept table, `null` rate → "unverified" label, absent `verification` ⇒ no section) and `app/studio/src/components/Timeline.test.tsx` (verify phase frames render per iteration)

### Implementation for User Story 2

- [X] T018 [US2] Implement `_resolve_verification` and the `verification` kwarg on `run()`/`resume()` in `agencykit/agency_cli/runner_bridge.py` (mirror `_resolve_escalation`; `min_sources=0` without resolve ⇒ pass `None` to the engine — byte-identical path; `min_sources=0` with resolve ⇒ report-only config)
- [X] T019 [US2] Render the conditional `## Source verification` section in `_dossier_md` in `agencykit/agency_cli/runner_bridge.py` (contracts/dossier-verification.md; same conditional pattern as `residual_risk`)
- [X] T020 [P] [US2] Add `VerifyEvent`, `MissionVerification`, `CycleVerification`, `SourceRecord` types in `app/studio/src/types.ts` (optional-field style matching existing event interfaces)
- [X] T021 [US2] Render the verify phase in `app/studio/src/components/Timeline.tsx`: spinner on start; "✓ sources verified (NN%)" / "✗ sources below minimum" / "sources counted (unverified)" on done (depends on T020)
- [X] T022 [US2] Render the verification section in `app/studio/src/components/MissionDetail.tsx`: rate headline (or "unverified — resolution not enabled"), per-department table, per-source status list, missing-claims list, truncation note; no section when the key is absent (depends on T020)
- [X] T023 [US2] Verify SSE passthrough of `verify` frames in `agency_studio/server.py` (the existing on_event→SSE bridge should forward them unchanged — add a passthrough test in `tests/test_server_verification.py`, new file)
- [X] T024 [US2] Run `pytest tests/ -q` from `agencykit/`, `pytest tests/ -q` at repo root, and `npx vitest run` in `app/studio/` — T016/T017/T023 suites pass

**Checkpoint**: SC-002 provable — the rate is visible in both the rendered dossier and the GUI. US1+US2 together satisfy the brick's headline done-condition.

---

## Phase 5: User Story 3 — The operator controls verification strictness and network use (Priority: P2)

**Goal**: The configuration surface — CLI flags, studio request field with tolerant
coercion and resume-envelope precedence, GUI launch toggle — with gate-ON-offline as
the product default (Q1) and `--min-sources 0` as the byte-identical opt-out.

**Independent Test**: Offline: same faked mission blocked under `--min-sources 5` and
not blocked under `--min-sources 0`; `POST /api/mission` with junk `verification`
runs with defaults (no 500); a default mission makes zero probe calls (seam spy).

### Tests for User Story 3 (write first, ensure they FAIL) ⚠️

- [X] T025 [P] [US3] Write failing CLI tests in `agencykit/tests/test_cli.py`: `--min-sources N` / `--resolve-sources` parsed on `run`, `resume`, `batch run` and forwarded to `runner_bridge` (monkeypatched); defaults ⇒ `min_sources=3, resolve=False`; `--min-sources 0` alone ⇒ verification `None` reaches the bridge; `--min-sources 0 --resolve-sources` ⇒ report-only config reaches the bridge; negative ⇒ argparse error
- [X] T026 [P] [US3] Write failing server tests in `tests/test_server_verification.py`: `verification` request field parsed (valid / absent ⇒ server default gate-ON-offline / junk ⇒ field-by-field coercion, never a 500); on `resume_from` the pinned envelope's verification wins over the body; default mission never touches the probe seam
- [X] T027 [P] [US3] Write failing GUI test in `app/studio/src/App.test.tsx` (existing file): "Verify sources online" toggle default unchecked; checked ⇒ request body carries `verification: {"resolve": true}`; unchecked ⇒ field omitted

### Implementation for User Story 3

- [X] T028 [US3] Add `--min-sources N` (default 3, 0 disables) and `--resolve-sources` flags to `run`, `resume`, and `batch run` in `agencykit/agency_cli/cli.py`, wired to `runner_bridge` (mirror the `--no-escalation` / `--escalation-budget` wiring, incl. batch pass-through in `agencykit/agency_cli/batch_runner.py` if the escalation precedent touches it)
- [X] T029 [US3] Parse the `verification` request field in `agency_studio/server.py` `_parse_mission_request`: tolerant field-by-field coercion to the gate-ON-offline default, resume-envelope precedence (mirror the escalation resume rule), pass through to `runner_bridge.run`
- [X] T030 [US3] Add the "Verify sources online" launch toggle in `app/studio/src/App.tsx` (default unchecked ⇒ omit the field; checked ⇒ `verification: {"resolve": true}`)
- [X] T031 [US3] Run all three suites (agencykit pytest, repo pytest, vitest) — T025/T026/T027 pass, everything else still green

**Checkpoint**: All three stories independently functional; every clarify decision (Q1–Q5) is enforced by a test.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, invariant audits, and the brick's live done-condition demo.

- [X] T032 [P] Update `agencykit/CLAUDE.md`: dossier schema (`verification` key), new CLI flags, `verification.py` row in Key files, mission-loop description (verify step)
- [X] T033 [P] Update `docs/SECURITY.md`: probe security posture (per-mission opt-in, HTTPS-only, private/loopback refusal before any socket work, no credentials, bounded count/time; accepted residual: no DNS-rebinding pinning per research.md D4)
- [X] T034 Audit SC-004/SC-005 and FR-012 invariants explicitly: confirm the byte-identical (hook-off) and verdict-contract (same tokens on same inspector text, aborted mission ⇒ no dossier) assertions exist in the suites and pass; diff behavior against the T001 baseline; confirm zero new runtime dependencies (`agencykit/pyproject.toml`, root `pyproject.toml`, `app/studio/package.json` dependency sections unchanged)
- [X] T035 Confirm no gpt-researcher (or any external) code was copied — concepts only (research.md D13); `docs/LICENSES.md` needs no new entry (or add one if anything was reused)
- [X] T036 Execute `specs/003-verifiable-sources/quickstart.md` offline sections end-to-end: all three suites green with zero network / CLI / Node-server / GPU
- [X] T037 Live validation on the validated engine (manual, outside the offline suite): `agency run "<research goal>" --resolve-sources` — confirm a real mission produces the Source verification dossier section, and the GUI mission view shows the rate (SC-001/SC-002 demonstrated for real)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none — start immediately
- **Foundational (Phase 2)**: after T001 — BLOCKS all user stories
- **US1 (Phase 3)**: after Phase 2 — no dependency on US2/US3
- **US2 (Phase 4)**: after Phase 2; consumes US1's dossier key for end-to-end flows, but its own tests run on fixture dossiers, so it is independently testable (T016–T017 can start right after Phase 2; T023's full-flow assertion is cleanest after T012)
- **US3 (Phase 5)**: after Phase 2; wires configs into surfaces built in US1/US2 (T028 needs T018's bridge kwarg; T029 needs T018; T030 is independent)
- **Polish (Phase 6)**: after US1–US3

### Within Each Story

- Test tasks FIRST — confirm they fail before the implementation tasks
- Same-file tasks are sequential (all `cli_engine.py` tasks T010→T014 in order; both `runner_bridge.py` tasks T018→T019)
- Suite-green checkpoint task closes each phase

### Parallel Opportunities

- Phase 2: T003→T007 are sequential (all edit `verification.py` — same file, no [P]); only T002 (tests) precedes them independently
- Phase 4: T016, T017, T020 in parallel (three different surfaces)
- Phase 5: T025, T026, T027 in parallel (three different test files)
- Phase 6: T032, T033 in parallel
- Cross-story (if staffed): after Phase 2 + T018, US2's GUI work (T020–T022) and US3's flag work (T025/T028) can proceed in parallel with US1's loop work — different files throughout

## Parallel Example: User Story 2

```bash
# After Phase 2, launch the three US2 test tasks together:
Task: "Failing runner-bridge tests in agencykit/tests/test_runner_bridge.py"    # T016
Task: "Failing GUI tests in MissionDetail.test.tsx + Timeline.test.tsx"         # T017
Task: "Types in app/studio/src/types.ts"                                        # T020
```

## Implementation Strategy

### MVP First (US1)

1. Phase 1 → Phase 2 (the verification engine)
2. Phase 3 (US1): the enforced postcondition, provable offline — **stop and validate**
3. US1 alone already delivers the constitutional hardening (an unsourced deliverable cannot ship)

### Incremental Delivery

- US1 → the guarantee exists (library-level MVP)
- +US2 → the guarantee is *visible* (dossier + GUI) — headline done-condition complete
- +US3 → the guarantee is *operable* (flags, toggle, defaults) — product-default gate-ON lands here
- Polish → docs, invariant audits, live demo

### Notes

- Commit after each task or logical group (Conventional Commits)
- Every clarify decision maps to a test: Q1→T026, Q2→T025, Q3→T025/T027, Q4→T002 (classification), Q5→T009(c)
- Avoid touching: `_short_verdict`, verdict tokens, `verdicts` schema, `MAX_ITERS`, `openmontage/` — enforced by T034
