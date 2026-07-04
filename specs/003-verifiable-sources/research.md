# Phase 0 Research: Verifiable Internet (Enforced Source Postcondition)

**Feature**: `003-verifiable-sources` | **Date**: 2026-07-04

No `NEEDS CLARIFICATION` markers remained in the Technical Context; this document
consolidates the design decisions that resolve every open planning question flagged in
the spec's Assumptions and the clarify session's "deferred to planning" list.

## D1 — Where the verification logic lives

- **Decision**: New module `agencykit/agency_cli/verification.py` in the agencykit
  fork, hooked into `run_mission_cli` via a default-`None` parameter.
- **Rationale**: The gate must wrap the veto loop, which lives in
  `agency_cli/engines/cli_engine.py`. Brick 2 established the exact precedent
  (`escalation.py`: module + frozen dataclass config + default-`None` engine hook +
  `_resolve_*` in `runner_bridge`). agencykit is the one import-permitted library
  (Constitution V) and is stdlib-only, matching zero-deps.
- **Alternatives considered**: (a) studio-side post-processing in `agency_studio` —
  rejected: the block must happen *inside* the loop to feed fixes into re-synthesis,
  and standalone `agency run` (headless CLI) must get the same guarantee; (b) a
  separate pip package — rejected: violates zero-deps and fractures the fork.

## D2 — Default-on product vs. byte-identical library (reconciling Q1 with Principle X)

- **Decision**: Two layers. Library: `run_mission_cli(verification=None)` — `None` ⇒
  byte-identical pre-feature behavior (Principle X). Product: `cli.py` and
  `agency_studio/server.py` construct `VerificationConfig(min_sources=3, resolve=False)`
  by default, so every real mission gets the offline gate (clarified Q1).
- **Rationale**: Identical to how Brick 2 shipped default-on escalation
  (`_resolve_escalation` builds the default config; the engine hook stays
  default-`None`). Byte-identical opt-out = `--min-sources 0`.
- **Alternatives considered**: default-on at the library layer — rejected: breaks
  Principle X's byte-identical-hook rule and every existing engine test.

## D3 — Probe mechanics and classification table

- **Decision**: `urllib.request` with `method="HEAD"`, per-URL timeout 5 s, redirects
  followed (default opener), a stable descriptive User-Agent, **no body read**, **no
  GET fallback**. Classification:

  | Probe outcome | Status |
  |---|---|
  | HTTP 2xx / 3xx (post-redirect) | `resolved` |
  | HTTP 404 / 410, DNS name-not-found | `unresolved` |
  | HTTP 401 / 403 / 405 / 429 / 5xx, timeout, TLS/connection error | `ambiguous` |
  | non-`https` scheme, literal-IP private/loopback/link-local host, `localhost` | `unresolved` (by policy — **never fetched**) |
  | resolution not enabled / network globally unavailable | `unverified` |
  | citation with no checkable URL | `unverifiable` |

  **Total-outage rule**: if *every* probe in a cycle fails at the connection level
  (no HTTP response received at all), the cycle is **degraded** — all probed sources
  are classified `unverified` (detail: `"network unavailable"`), `rate = null`, and
  the gate falls back to extracted-count semantics (as if resolution were off). This
  implements the spec's total-network-failure edge case and keeps "unchecked" and
  "checked and failed" distinct (US2 scenario 3).

- **Rationale**: Q4 chose benefit-of-the-doubt, which removes any need for an
  escalating GET retry (clarify option C was explicitly not chosen): ambiguous already
  counts toward the minimum, so a heavier probe buys nothing. 404/410 and NXDOMAIN are
  the only *definitive* "does not exist" signals. Policy rejections are `unresolved`
  because a private/plain-http address can never be a *verifiable public source*
  (Principle III requires verifiable), and not fetching them is the SSRF guard.
- **Alternatives considered**: HEAD→GET fallback on 405 (rejected above); status-code
  allowlists per site (rejected: unbounded maintenance); `robots.txt` respect
  (rejected: single HEAD probe per cited URL is not crawling).

## D4 — Network security posture of the probe

- **Decision**: HTTPS-only; scheme and host validated *before* any socket work
  (literal IPs checked against `ipaddress` private/loopback/link-local/reserved
  ranges; `localhost`-style names refused); no credentials, cookies, or env keys ever
  attached; probes run only when `resolve=True` (the per-mission opt-in).
- **Rationale**: Constitution VI (https-only outbound, env-only keys) + spec FR-013.
  The deliverable text is model-produced from web research, so cited URLs are
  low-trust input — the private-address refusal closes the "cite
  `https://192.168.1.1/admin`" hole without DNS-resolution pinning complexity.
- **Alternatives considered**: full DNS-rebinding defense (resolve host, pin IP) —
  rejected as over-engineering for a HEAD probe that sends no secrets and reads no
  body; documented as a known accepted residual.

## D5 — Bounds

- **Decision**: URLs de-duplicated mission-wide, then capped at
  `MAX_URLS_PER_CYCLE = 50` (first-seen order; the report records
  `truncated: N_dropped` when the cap bites). Probes run on a stdlib
  `concurrent.futures.ThreadPoolExecutor(max_workers=8)`; 5 s per-probe timeout and a
  60 s wall clamp per cycle. Cycle 2+ re-verifies (the deliverable changed) but reuses
  a per-mission URL→status cache so unchanged URLs are not re-probed (clamp-skips are
  never cached). *(Amended at review, 2026-07-04)*: the probe budget is allocated
  **round-robin across first-citing departments** (synthesis-only URLs form their own
  pool), so one department's URL flood cannot starve another department out of the
  cap; wall-clamp-skipped URLs are classified `unverified` (detail:
  `"not probed — cap/time limit"`) and cap-dropped URLs are reported via the
  `truncated` count — neither is silently ignored, and neither counts toward a
  minimum when probes ran (D7).
- **Rationale**: Spec SC-008 (bounded, truncation stated). 50 × 5 s / 8 workers ≈ 32 s
  worst case — tolerable against multi-minute engine calls. The cache keeps the
  3-iteration worst case flat.
- **Alternatives considered**: async `asyncio` probing — rejected: threads + blocking
  urllib is simpler and equally bounded at n=50.

## D6 — Verified-source rate definition

- **Decision**: `rate = resolved / checkable`, where
  `checkable = resolved + ambiguous + unresolved`. `unverified` / `unverifiable`
  sources are excluded from the denominator. With resolution off — or the cycle
  degraded by a total network outage (D3) — `rate = null` and surfaces display
  **"unverified (resolution not enabled)"** (or the outage note) — never `0%`.
- **Rationale**: The Key Entity definition says "fraction confirmed live", so
  `ambiguous` stays out of the numerator (honest) while still counting toward the
  *gate minimum* (Q4 — forgiving). Distinct rate-vs-gate semantics are deliberate:
  the rate informs, the gate enforces. `null`-when-off implements the spec's US2
  scenario 3 (never conflate "unchecked" with "failed").
- **Alternatives considered**: counting ambiguous in the numerator — rejected: inflates
  the trust dial with unconfirmed sources; rate 0 when off — rejected by spec.

## D7 — Gate semantics

- **Decision** *(amended at review, 2026-07-04 — closes a padding hole)*: two modes.
  **Probes ran** (resolve on, cycle not degraded): `counted = resolved + ambiguous`
  among the sources actually checked this cycle — an unchecked citation never counts,
  so padding a deliverable with URLs beyond the probe cap cannot buy a pass (the
  round-robin fair cap in D5 prevents the converse false-block from starvation).
  **Nothing checkable** (resolve off, or cycle degraded by total outage):
  `counted = extracted (cited) − known-bad` — nothing was checked, so every citation
  keeps the benefit of the doubt (clarified Q1). Gate
  fails iff any deployed department's `counted < min_sources`. Department attribution:
  URLs extracted from that department's `dept_outputs[dept]` text; the synthesized
  deliverable's URLs attribute to the mission-level pool (counted for the rate, not
  against any single department's minimum).
- **Rationale**: FR-004 is per-department; department outputs are the auditable
  citation trail each department owns (Art. IV sovereignty). The synthesis re-cites a
  subset, so gating departments on the synthesis text would punish faithful
  condensation.
- **Alternatives considered**: gating on the synthesis text only — rejected: a
  department could invent everything as long as the synthesis cites elsewhere.

## D8 — Loop integration and recording (implements Q5)

- **Decision**: In each synth→inspect cycle, after the inspector verdict is parsed:
  run verification on `delivered` + `dept_outputs`, append
  `{"iteration": N, "ok": bool, "report": {...}}` to a **separate**
  `verifications` list (never into the `verdicts` entries), and change the loop break
  to `if token not in _RETRY_VERDICTS and verification_ok: break` (verification `ok`
  is hard-`True` when the hook is `None` — byte-identical). When verification fails,
  its actionable failure block (offending departments, missing counts, dead URLs) is
  appended to `fixes` alongside any inspector findings for the next synthesis. At the
  cap, `residual_risk` text covers the unresolved verification failure too. The final
  dossier carries `dossier["verification"]` (summary + per-cycle results) only when
  the hook is active.
- **Rationale**: Q5 (two independent signals; verdict never rewritten), FR-006/007/008.
  `_short_verdict`, verdict tokens, `verdicts` schema, `MAX_ITERS`, and cancellation
  semantics are all untouched; `_last_verdict`-based consumers (`batch_runner`,
  `render_assets` PASS gate) keep their exact meaning.
- **Alternatives considered**: rewriting PASS → PASS-WITH-FIXES on failure (clarify
  option B) — rejected by the user; recording inside `verdicts` entries — rejected:
  changes a schema existing consumers iterate over.

## D9 — Missing-source (claim-level) findings

- **Decision**: The deterministic verification report (per-source statuses,
  per-department counts) is appended to the **inspector's input** when — and only
  when — the hook is active, with an instruction to name specific claims lacking
  sources; those named claims flow into the report's `missing` list and into `fixes`.
  *(Amended at implementation, 2026-07-04)*: named unsourced claims also fail the
  cycle's verification signal (`ok=False` ⇒ retry) — this is the one verification
  failure mode a re-synthesis can actually repair (department source counts are fixed
  once departments have run), so it is what makes the retry loop convergent; a
  guard filters "none"/"n/a"-style all-clear lines so an explicit all-clear can never
  read as a claim and spuriously block. The *count* gate remains fully deterministic.
- **Rationale**: Spec assumption "missing-source detection is engine-assisted";
  identifying *claims* is reasoning (Principle I: through the CLI subprocess).
  Additive: with the hook off, `_inspect_prompt` is byte-identical. Enriching the
  inspector's *input* is the established pattern boundary — the contract protects its
  *output* parsing (`_short_verdict`), which is untouched.
- **Alternatives considered**: heuristic sentence-level claim detection in Python —
  rejected: exactly the "invented information" class of brittleness this brick exists
  to kill; the existing `_extract_sources` docstring already warns against heuristic
  prose parsing.

## D10 — Configuration surface (implements Q2/Q3)

- **Decision**:
  - `VerificationConfig(frozen dataclass): min_sources: int = 3, resolve: bool = False`.
  - CLI (`agency run` / `resume` / `batch run`): `--min-sources N` (0 disables the
    gate entirely), `--resolve-sources` (enables online liveness — the dedicated
    per-mission network opt-in).
  - Studio request field: `"verification": {"min_sources": int, "resolve": bool}` on
    `POST /api/mission` (dict-shaped, coerced by `_resolve_verification` in
    `runner_bridge` — and defensively in `run_mission_cli`, mirroring the escalation
    dict-coercion fix).
  - GUI: one "Verify sources online" toggle at mission launch (maps to
    `resolve: true`); `min_sources` stays at its default in the GUI (power users use
    the CLI flag), keeping the launch surface simple (Principle VIII).
- **Rationale**: Q2 (default 3), Q3 (dedicated switch, `--no-escalation` /
  `--escalation-budget` precedent), resume parity: on resume the pinned envelope's
  verification config wins over the request body, exactly like escalation.
- **Alternatives considered**: exposing `min_sources` in the GUI launch form —
  deferred: adds a numeric field non-technical users can't evaluate; revisit in the
  Brick 7 magic-box redesign.

## D11 — Checkpoint / resume parity

- **Decision**: `_checkpoint` snapshots gain an optional `verifications` list (like
  `escalation`); `_validate_resume_state` tolerates its absence (older snapshots
  resume cleanly) and validates its shape when present; a resumed mission re-runs
  verification for the cycle it re-enters (the re-synthesis produces new text anyway).
- **Rationale**: Crash-recovery invariant from Brick 1/2 — resume must reproduce the
  state as-if the crash never happened; verification is recomputed rather than
  trusted from the snapshot because the re-run synthesis text is authoritative.
- **Alternatives considered**: trusting snapshot verification results — rejected:
  they describe a superseded deliverable.

## D12 — Studio / GUI surfacing

- **Decision**: `run_mission_cli` emits `on_event` frames
  `{"phase": "verify", "iteration": N, "status": "start"}` and
  `{"phase": "verify", "iteration": N, "status": "done", "ok": bool,
  "rate": float | null, "checked": int}`; `server.py` passes them through SSE
  unchanged (same as every existing phase). `types.ts` adds `VerifyEvent`;
  `Timeline.tsx` renders the verify step per iteration; `MissionDetail.tsx` renders
  the rate (with the `null` → "unverified" distinction) and the per-source report from
  `dossier.verification`. `runner_bridge._dossier_md` gains a
  `## Source verification` section (rate per department + overall, statuses,
  truncation note) rendered only when the key exists.
- **Rationale**: FR-009/FR-010, SC-002; follows the exact pattern of every existing
  event type (RetrievalEvent, WebSearchEvent…) and the additive dossier-section rule
  (`escalation`, `residual_risk` render conditionally today).
- **Alternatives considered**: a separate GUI page — rejected (spec assumption: no new
  reporting artifact).

## D13 — Reference pattern & licensing

- **Decision**: gpt-researcher (Apache-2.0) is used strictly as a concept reference —
  its source-tracking/validation pipeline shape (collect → validate → attach to
  report) informs D7/D8. No code, prompts, or assets are copied; no new entry in
  `docs/LICENSES.md` is required (nothing reused). Re-verify at review time.
- **Rationale**: Spec FR-015; Constitution IX.

## D14 — Test strategy (offline)

- **Decision**:
  - `agencykit/tests/test_verification.py`: URL extraction/attribution/dedup, the
    classification table (probe seam monkeypatched per row), policy refusals (http,
    private IP — assert the probe seam is *never called*), gate math incl. zero/exempt,
    rate math incl. `null`, truncation.
  - `agencykit/tests/test_engine.py` additions: hook-off byte-identical run;
    hook-on pass; hook-on block → fixes injected → retry; inspector-PASS +
    verification-FAIL → retried (Q5); cap → `residual_risk`; checkpoint/resume with
    verifications; cancellation unchanged.
  - repo `tests/test_server_verification.py`: request-field parsing (valid, missing,
    junk), resume-envelope precedence, SSE `verify` frame passthrough,
    dossier JSON passthrough.
  - `MissionDetail.test.tsx` / `Timeline.test.tsx`: rate rendering, `null` →
    "unverified" label, verify phase in timeline.
- **Rationale**: Constitution VII; the probe seam is the new monkeypatch boundary,
  exactly parallel to `cli_engine._call`.

## Deferred items resolved from the clarify session

| Deferred item | Resolution |
|---|---|
| Exact probe mechanics (timeout, fallback) | D3 (HEAD, 5 s, no GET fallback) |
| Verification work caps | D5 (50 URLs/cycle, 8 workers, 60 s clamp, cached re-cycles) |
| Rate numerator vs. ambiguous | D6 (ambiguous excluded from rate, counted by gate) |
