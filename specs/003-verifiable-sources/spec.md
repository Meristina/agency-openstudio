# Feature Specification: Verifiable Internet (Enforced Source Postcondition)

**Feature Branch**: `003-verifiable-sources`

**Created**: 2026-07-04

**Status**: Draft

**Input**: User description: "Brick 3 — verifiable internet: turn the "no invented information" mandate from a prompt-only soft guarantee into an enforced postcondition. Today nothing checks that a deliverable's claims are backed by real, resolvable sources — the inspector (inspector-agency, veto loop in agencykit/agency_cli/engines/cli_engine.py) trusts the prompt. Harden it: (1) extract citations/URLs from each department deliverable and the synthesized dossier; (2) resolve each URL with a lightweight liveness check (HTTP HEAD), fully offline-stubbed in tests — no real network in the suite; (3) enforce a configurable minimum resolvable-source count per deployed department; (4) enrich the inspector verdict with a verification report (per-claim/source: resolved / unresolved / missing) and block delivery when the minimum isn't met. Surface the verified-source rate in the mission dossier (runner_bridge) and in the GUI (app/studio). Reference pattern: gpt-researcher (Apache-2.0), concepts only, no AGPL/GPL copy. Done when: a deliverable without resolvable sources is blocked by the inspector with an actionable report naming the offending claims, AND the verified-source rate is visible in both the dossier and the GUI. Invariants: offline suite stays green (network stubbed, no CLI/Node/GPU), zero core runtime deps, subprocess boundaries respected, per-mission network opt-in (URL resolution is itself opt-in / stubbed by default), security (127.0.0.1, no CORS *, path guards, env-only keys), and agency-kit's veto-loop decision logic is enriched but its PASS/PASS-WITH-FIXES/VETO contract and _short_verdict behavior are never altered."

## Overview

The agency's founding promise — **no invented information** (Constitution Principle III)
— is today a prompt-level mandate: every mission is *told* to research the live internet
and cite real sources, and the inspector is *told* to spot-check them. Nothing in the
runtime actually verifies that the sources in a deliverable exist, resolve, or cover the
claims made. A mission that fabricates a plausible-looking bibliography would pass
untouched.

This feature hardens the mandate into an **enforced runtime postcondition**. After the
departments and the synthesis produce their deliverables, the system extracts every
cited source, checks each one's liveness (when the mission has network permission to do
so), counts resolvable sources against a configurable per-department minimum, and
attaches a structured verification report to the inspection verdict. A deliverable whose
sources don't meet the bar is **blocked from delivery** through the existing quality
loop, with an actionable report naming the offending claims and departments. The
resulting verified-source rate becomes a first-class, visible quality signal in the
mission dossier and in the studio GUI — so an operator can see at a glance how much of
a deliverable is actually backed by the live internet.

The existing inspection loop's decision contract (PASS / PASS-WITH-FIXES / VETO, and how
the verdict token is read from inspector output) is **enriched, never altered**: source
verification adds evidence to the loop, it does not change how verdicts are parsed or
what they mean.

## Clarifications

### Session 2026-07-04

- Q: Out of the box (operator does nothing, no network opt-in), what does the
  verification gate do? → A: Gate ON by default, offline mode — extraction and
  minimum-count enforcement run on every mission (counting cited sources, no network);
  real URL resolution only with explicit opt-in. Principle X is honored through the
  explicit opt-out (minimum zero / gate disabled ⇒ byte-identical pre-feature
  behavior).
- Q: What minimum source count per deployed department does the gate ship with? →
  A: 3 — low enough that a genuinely researched department output clears it easily,
  high enough that an unsourced or token-effort deliverable is caught; overridable per
  mission, zero exempts/disables.
- Q: Where does the URL-resolution network opt-in live? → A: A dedicated per-mission
  switch — a "verify sources online" toggle at mission launch in the GUI and a matching
  CLI flag for headless runs — mirroring the Brick 2 configuration precedent
  (`--no-escalation` / `--escalation-budget`), scoped to this feature only.
- Q: Does an ambiguous liveness result (probe refused, bot wall, timeout) count toward
  the resolvable minimum? → A: Benefit of the doubt — only a definitive not-found/dead
  result fails; ambiguous results count toward the minimum and are reported distinctly
  as "ambiguous" (the gate catches fabricated sources, not bot-hostile live sites).
- Q: When a cycle's inspector verdict is PASS but the source minimum is unmet, what
  does the recorded audit trail show? → A: Two independent recorded signals — the
  inspector verdict stays exactly as issued, and a distinct verification result
  (pass/fail + report) is recorded alongside it for the cycle; delivery requires both.
  The trail reads "inspector PASS + verification FAIL → retried"; the verdict is never
  rewritten.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An unsourced deliverable is blocked with an actionable report (Priority: P1)

An agency operator runs a mission. One department's output (or the synthesized
deliverable) makes claims without citing sources, cites fewer resolvable sources than
the configured minimum, or cites sources that do not resolve. Instead of shipping, the
mission's quality gate blocks the deliverable and produces an actionable verification
report: which departments fell short, which claims lack sources, and which cited sources
failed to resolve. The deliverable re-enters the existing fix-and-re-inspect loop with
that report as required fixes.

**Why this priority**: This is the brick's headline done-condition — the moment the
"no invented information" guarantee stops depending on the model's goodwill. Without
enforcement, everything else in this feature is cosmetic.

**Independent Test**: Run one mission offline (engine and liveness boundaries faked)
whose faked deliverable cites no resolvable sources. Assert the delivery is blocked
(the quality loop re-enters with verification findings as required fixes), and the
verification report names the offending department(s) and claim(s).

**Acceptance Scenarios**:

1. **Given** a completed synthesis whose sources fall below the configured minimum for a
   deployed department, **When** the quality gate runs, **Then** the deliverable is not
   accepted as final and the loop re-enters with the verification failures injected as
   required fixes.
2. **Given** a blocked deliverable, **When** the operator reads the verification report,
   **Then** it identifies each offending department, each claim or section lacking a
   source, and each cited source that failed to resolve — specific enough to act on.
3. **Given** a deliverable whose sources meet or exceed every deployed department's
   minimum, **When** the quality gate runs, **Then** verification does not block it and
   the existing inspection behavior proceeds unchanged.
4. **Given** repeated failed fix cycles reaching the existing iteration cap, **When**
   the mission closes out, **Then** the unresolved verification failure is recorded
   explicitly as residual risk in the dossier — never silently dropped or marked
   verified.

---

### User Story 2 - The operator sees the verified-source rate in the dossier and the GUI (Priority: P1)

After any mission completes, the operator can see — in the mission dossier and in the
studio's mission view — what fraction of the deliverable's cited sources actually
resolved: per deployed department and for the mission overall, alongside the
per-source detail (resolved / unresolved / missing).

**Why this priority**: Visibility is the second half of the brick's done-condition.
Enforcement without a visible signal leaves the operator unable to judge deliverable
trustworthiness or explain a block; the rate is the trust dial of the whole product.

**Independent Test**: Run one mission offline with a faked deliverable containing a
known mix of resolvable and unresolvable sources. Assert the serialized dossier carries
the verified-source rate (per department and overall) plus per-source statuses, and
that the mission view in the GUI renders the rate for that mission.

**Acceptance Scenarios**:

1. **Given** a completed mission, **When** the operator opens the mission dossier,
   **Then** it shows the verified-source rate overall and per deployed department, and
   the per-source verification detail.
2. **Given** the same mission, **When** the operator opens it in the studio GUI,
   **Then** the verified-source rate is visible on the mission's detail view without
   requiring any technical steps.
3. **Given** a mission run without network permission for source resolution, **When**
   the operator views the rate, **Then** the display distinguishes "unverified
   (resolution not enabled)" from "checked and failed" — the two are never conflated.

---

### User Story 3 - The operator controls verification strictness and network use (Priority: P2)

An operator can configure how strict verification is: the minimum resolvable-source
count required per deployed department (including zero, to exempt a department or
disable the gate), and whether the mission is allowed to touch the network to resolve
URLs at all. By default a mission performs **no** real network calls for verification —
resolution is an explicit per-mission opt-in, consistent with how the product treats all
network access.

**Why this priority**: Different missions warrant different strictness (a creative
brief vs. a market analysis), and the local-first/no-implicit-network promise is a
constitutional invariant. It builds on US1/US2, which prove the mechanism works.

**Independent Test**: Run the same faked mission twice offline — once with a minimum of
zero and once with a high minimum — and assert the first is not blocked while the second
is. Run a default mission (no opt-in) and assert zero real network activity occurs.

**Acceptance Scenarios**:

1. **Given** a configured minimum resolvable-source count, **When** a department's
   resolvable sources meet it, **Then** verification passes for that department; when
   they fall short, it fails for that department.
2. **Given** a minimum of zero (or verification explicitly disabled) and no online-
   resolution opt-in, **When** the mission runs, **Then** behavior is identical to the
   pre-feature baseline — no blocking, no behavioral drift. (A zero minimum combined
   with an explicit resolution opt-in is report-only mode: the report and rate are
   produced, the gate never blocks.)
3. **Given** no per-mission network opt-in, **When** verification runs, **Then** no
   real network call is made: sources are extracted and counted, liveness is reported
   as "unverified", and the minimum-count gate operates on extracted (cited) sources
   instead of resolved ones.
4. **Given** the per-mission network opt-in is granted, **When** verification runs,
   **Then** each extracted source is liveness-checked and classified resolved or
   unresolved.

---

### Edge Cases

- **Liveness check not permitted by the target site**: A live site may reject the
  lightweight check method while still being real. Such a result is classified
  **ambiguous** — it counts toward the minimum (benefit of the doubt) and is reported
  distinctly; only a definitive "does not exist" is unresolved and fails the gate.
- **Duplicate sources**: The same URL cited by multiple departments or repeated in the
  synthesis is checked once and counted per the department(s) citing it; duplicates
  never inflate a department's count.
- **Non-URL citations**: A citation without a checkable address (book, print report,
  interview) cannot be liveness-verified; it is reported as unverifiable rather than
  resolved, and does not count toward the resolvable minimum.
- **Source flood**: A deliverable citing hundreds of URLs must not trigger unbounded
  checking; verification work is bounded and any truncation is explicit in the report.
- **Total network failure with opt-in granted**: If resolution is enabled but the
  network is entirely unavailable, verification must degrade to the "unverified" path
  with the outage noted — not classify every real source as fabricated.
- **Insecure or local addresses**: Cited addresses that are not secure public web URLs
  (plain-HTTP, localhost/private ranges) are never fetched; they are classified
  unresolved-by-policy with the reason stated.
- **Cancellation during verification**: A mission cancelled mid-verification honors the
  existing cancellation contract — no dossier, no verdict, no partial report.
- **Inspector says PASS but verification fails**: The runtime postcondition holds
  independently of the inspector's prose: an under-sourced deliverable is blocked even
  if the inspector's own text was favorable. Both signals are recorded independently —
  the trail shows "inspector PASS + verification FAIL → retried".
- **Malformed deliverable**: Extraction from an empty or malformed deliverable yields
  an empty source set (zero resolvable sources), which the gate evaluates like any
  other count — no crash.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST extract the cited sources (checkable URLs) from each
  deployed department's deliverable and from the synthesized deliverable,
  de-duplicated, attributing each source to the department(s) whose output cites it.
- **FR-002**: When the mission's per-mission network opt-in is granted, the system MUST
  check each extracted source's liveness with a lightweight, bounded check and classify
  it **resolved** (confirmed reachable), **unresolved** (definitively dead/not-found,
  or disallowed by policy), or **ambiguous** (probe refused or inconclusive). Only
  unresolved sources fail the gate: resolved and ambiguous sources both count toward
  the minimum, with ambiguous reported distinctly — an ambiguous response is never
  treated as fabricated.
- **FR-003**: Without the per-mission network opt-in, the system MUST make no real
  network call: sources are extracted and counted, each is classified **unverified**,
  and the minimum-count gate operates on extracted (cited) sources instead of resolved
  ones. The opt-in is a dedicated per-mission switch — a "verify sources online" toggle
  at mission launch in the GUI and a matching CLI flag for headless runs. Its default
  is off; the offline behavior is the default behavior.
- **FR-004**: The system MUST enforce a configurable minimum resolvable-source count
  per deployed department, defaulting to 3; a value of zero exempts that department
  (and zero everywhere disables the gate entirely). Requesting online resolution with
  a zero minimum yields report-only mode — visibility without blocking.
- **FR-005**: The system MUST produce a structured verification report per inspection
  cycle: per-source status (resolved / ambiguous / unresolved / unverified /
  unverifiable), claims
  or sections lacking any source (**missing**), per-department counts against their
  minimums, and the resulting verified-source rate per department and mission-wide.
- **FR-006**: When any deployed department falls below its minimum, the system MUST
  block delivery by re-entering the existing fix-and-re-inspect loop with the
  verification failures injected as required fixes — actionable, naming the offending
  departments, claims, and failed sources. The verification result (pass/fail plus
  report) is recorded per inspection cycle as its own signal alongside the inspector's
  verdict — the verdict is never rewritten — and final delivery requires both signals
  to pass.
- **FR-007**: The blocking mechanism MUST NOT alter the existing verdict contract: the
  PASS / PASS-WITH-FIXES / VETO token set, how the verdict token is read from inspector
  output, the iteration cap, and the aborted-mission (no dossier, no verdict) invariant
  all behave identically with verification on or off.
- **FR-008**: If the iteration cap is reached with verification still failing, the
  mission MUST close out with the failure recorded explicitly as residual risk in the
  dossier — never silently marked verified.
- **FR-009**: The mission dossier MUST carry the verification report and the
  verified-source rate (per department and overall), both in the structured dossier
  record and in the human-readable rendered dossier.
- **FR-010**: The studio GUI MUST display the verified-source rate on the mission
  detail view, distinguishing "unverified (resolution not enabled)" from "checked and
  failed", operable by a non-technical user.
- **FR-011**: Verification MUST be fully exercisable by the offline test suite — the
  liveness boundary faked, no real network, no CLI agent, no Node, no GPU — and the
  suite MUST stay green.
- **FR-012**: The feature MUST introduce zero new runtime dependencies in the core;
  liveness checking uses only what the platform already provides.
- **FR-013**: Real liveness checks (opt-in path only) MUST be secure-web-only: no
  plain-HTTP fetches, no requests to local or private addresses, no credentials or API
  keys attached, bounded time and count per mission. All existing server security
  invariants are untouched.
- **FR-014**: With verification disabled (minimum zero everywhere / explicit opt-out),
  mission behavior and outputs MUST be byte-identical to the pre-feature baseline.
- **FR-015**: The reference pattern (gpt-researcher, Apache-2.0) MAY inform concepts
  only; no code copy from it or any AGPL/GPL-incompatible source. Any reused component
  MUST be recorded in the licenses ledger with its license.

### Key Entities

- **Cited source**: A checkable address extracted from a deliverable, attributed to the
  department(s) citing it; carries a verification status.
- **Verification status**: One of **resolved** (confirmed live), **ambiguous** (probe
  refused or inconclusive — counts toward the minimum, benefit of the doubt),
  **unresolved** (definitively dead or disallowed by policy — fails the gate),
  **unverified** (resolution not enabled or network unavailable), **unverifiable**
  (no checkable address).
- **Missing-source finding**: A claim or section of a deliverable identified as lacking
  any cited source.
- **Verification report**: The structured record of one inspection cycle's source
  audit — per-source statuses, missing-source findings, per-department counts vs.
  minimums, and the verified-source rates. Recorded per cycle as its own signal
  alongside (never merged into or rewriting) the inspector's verdict.
- **Verification policy**: The operator-facing configuration — per-department minimum
  resolvable-source count (zero = exempt/disabled) and the per-mission network opt-in
  governing whether real liveness checks run.
- **Verified-source rate**: The fraction of a deliverable's cited sources confirmed
  live — computed per department and mission-wide; the operator-visible trust signal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A mission whose deliverable cites no resolvable sources is blocked before
  delivery, and the verification report names the offending department(s), claim(s),
  and failed source(s). *(the brick's headline done-condition, part 1)*
- **SC-002**: For every completed mission, the verified-source rate is visible in both
  the mission dossier and the studio GUI mission view. *(headline done-condition,
  part 2)*
- **SC-003**: A default mission (no network opt-in) performs zero real network calls
  for verification, and the full offline test suite passes with no network, no CLI
  agent, no Node, and no GPU.
- **SC-004**: With verification disabled, mission behavior and outputs are identical to
  the pre-feature baseline — verifiable as identical output on the same input.
- **SC-005**: The inspection verdict contract is unchanged: identical inspector text
  yields identical verdict tokens with verification on and off, and an aborted mission
  still yields no dossier and no verdict.
- **SC-006**: Every source extracted from a mixed test deliverable is classified into
  exactly one verification status, and claims without sources are surfaced as
  missing-source findings.
- **SC-007**: The configurable minimum demonstrably gates: the same deliverable is
  blocked under a minimum above its resolvable-source count and passes under a minimum
  at or below it.
- **SC-008**: Verification work is bounded: a deliverable citing an arbitrarily large
  number of sources completes verification within the configured bounds, with any
  truncation stated in the report.

## Assumptions

- **Liveness check shape**: The "lightweight liveness check" is assumed to be a
  minimal reachability probe (e.g. an HTTP HEAD-style request with a short timeout and
  a tolerant fallback for sites that refuse the method). The exact probe, timeout, and
  retry/fallback rules are planning details; the spec-level guarantee is bounded,
  secure, tolerant classification.
- **Gate semantics without network**: Since URL resolution is itself opt-in and the
  suite is offline, the minimum-count gate falls back to counting extracted (cited)
  sources when resolution is not enabled. Only an opted-in mission can distinguish
  resolved from unresolved; an offline mission can still be blocked for citing too few
  sources at all.
- **Default minimum (clarified 2026-07-04)**: The gate ships with a default minimum of
  3 sources per deployed department, overridable per mission and settable to zero to
  exempt or disable — mirroring the existing escalation-budget configuration pattern.
- **Claim-level granularity**: "Per-claim" reporting is satisfied by identifying the
  claims/sections that lack sources (missing-source findings) and mapping cited sources
  to the departments citing them; a full claim-to-source alignment for every sentence
  is not required by this brick.
- **Missing-source detection is engine-assisted**: Identifying *claims lacking sources*
  is reasoning work and therefore runs through the existing CLI-agent inspection path
  (enriched inspector input), while source extraction and URL liveness are deterministic
  runtime checks. Both feed the same verification report.
- **Network opt-in (clarified 2026-07-04)**: The per-mission opt-in governing liveness
  checks is a dedicated, feature-scoped switch (GUI toggle at mission launch + CLI flag
  for headless runs), following the product's explicit per-mission opt-in pattern — no
  new implicit network path is introduced, and no broader general-purpose network
  permission is created by this brick.
- **Dossier and GUI are the existing surfaces**: The verification report and rate live
  in the existing mission dossier (structured record + rendered form) and the existing
  studio mission view; no new reporting artifact or page is introduced.
- **Additive wiring**: The feature lands as additive hooks/config following the
  repository's default-off/byte-identical extension pattern (Principle X); the
  inspector's veto-loop decision logic is enriched with verification evidence but its
  contract is untouched.
- **Reference pattern**: gpt-researcher (Apache-2.0) informs the extract→verify→report
  concept only; no code is copied from it.
- **Engine**: `claude` is the validated engine used to demonstrate the done-conditions;
  engine neutrality is preserved but end-to-end proof is on the validated engine.
