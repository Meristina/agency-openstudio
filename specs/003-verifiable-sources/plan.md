# Implementation Plan: Verifiable Internet (Enforced Source Postcondition)

**Branch**: `003-verifiable-sources` | **Date**: 2026-07-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-verifiable-sources/spec.md`

## Summary

Harden Constitution Principle III from a prompt-level mandate into a runtime-verified
postcondition. A new stdlib-only verification module (`agencykit/agency_cli/verification.py`,
mirroring the Brick 2 `escalation.py` precedent) deterministically extracts cited URLs
from every department output and the synthesized deliverable, optionally liveness-checks
them (HTTPS-only HEAD probes, opt-in per mission, stubbed offline by default), counts
per-department sources against a configurable minimum (default 3), and records a
verification result per synth→inspect cycle **as its own signal alongside the inspector
verdict** (never rewriting it). An unmet minimum re-enters the existing veto loop with
the verification failures injected as required fixes; at the iteration cap the failure
lands in `residual_risk`. The verified-source rate is serialized into the dossier
(`runner_bridge`) and rendered in the studio GUI mission view. Library-level wiring is
an additive default-`None` hook on `run_mission_cli` (byte-identical when absent);
product-level default is gate-ON in offline mode (clarified Q1).

## Technical Context

**Language/Version**: Python 3.10+ (agencykit + agency_studio, stdlib-only core);
TypeScript / React 18 + Vite (app/studio)

**Primary Dependencies**: none new. Liveness probing uses stdlib
`urllib.request` + `ssl` + `ipaddress` + `concurrent.futures`; GUI uses the existing
React stack; no `pip` additions anywhere.

**Storage**: existing dossier dict → `~/.agency` store JSON + project-local
`missions/<id>/dossier.md` (new `verification` key + rendered section; additive).

**Testing**: `pytest` — agencykit suite (`agencykit/tests/`, run from that directory)
+ studio suite (repo-root `tests/`); `vitest` for `app/studio/src`. All offline: the
probe function is monkeypatched exactly like the engine subprocess boundary.

**Target Platform**: user's local machine, cross-platform (macOS / Linux / Windows);
server bound to `127.0.0.1` only.

**Project Type**: imported orchestration library (agencykit) + stdlib local web
service (agency_studio) + web GUI (app/studio).

**Performance Goals**: verification adds bounded overhead per cycle — ≤ 50 unique URLs
probed (dedup first), 5 s per-probe timeout, small stdlib thread pool (8 workers) ⇒
worst-case ≈ 35 s per cycle with resolution on; zero overhead with resolution off
(pure text extraction, sub-millisecond).

**Constraints**: zero new runtime deps; offline-by-default (probe path never runs
without the per-mission opt-in); HTTPS-only outbound, no private/loopback targets;
additive default-`None` library hook (byte-identical off); veto-loop verdict contract
(`PASS` / `PASS-WITH-FIXES` / `VETO`, `_short_verdict`) untouched.

**Scale/Scope**: deliverables typically cite 5–100 URLs; missions deploy 1–9
departments; one verification result per synth→inspect cycle (≤ `MAX_ITERS` = 3).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — URL extraction and liveness
  probing are deterministic runtime checks, not reasoning; the only reasoning added
  (naming unsourced claims) rides the existing inspector CLI subprocess call. No
  token-billed API anywhere.
- [x] **II. Engine neutrality**: PASS — verification wraps the engine-neutral mission
  loop after `_call` returns text; nothing engine-specific. Unvalidated-engine refusal
  (`ensure_production_engine`) is untouched.
- [x] **III. No invented information**: PASS — this feature *is* the Brick 3 hardening
  Principle III explicitly names (citation extraction, URL resolution, minimum source
  count per department; unsourced deliverable blocked).
- [x] **IV. Local-first & offline-by-default**: PASS — resolution is a dedicated
  per-mission opt-in (clarified Q3), default off; the default gate runs purely on
  local text extraction. No cloud, no keys, no new implicit network path.
- [x] **V. Subprocess boundaries**: PASS — all changes live in `agencykit/` (the one
  permitted imported library, same as Brick 2's `escalation.py`), `agency_studio/`,
  and `app/studio/`; `openmontage/` untouched; engines still subprocess-only.
- [x] **VI. Security**: PASS — probes are HTTPS-only, refuse literal-IP
  private/loopback/link-local hosts and non-https schemes without fetching, attach no
  credentials, and are time/count-bounded. Server bind / CORS / `path_inside()` /
  env-only keys are untouched.
- [x] **VII. Offline tests**: PASS — the probe function is a module-level seam
  monkeypatched in tests (same discipline as `cli_engine._call`); suites stay green
  with no network, no CLI, no Node, no GPU.
- [x] **VIII. End-user simplicity**: PASS — GUI gets one "Verify sources online"
  toggle at mission launch and a read-only rate display; defaults are sensible
  (gate on, min 3); CLI flags remain the power-user override.
- [x] **IX. License**: PASS — gpt-researcher (Apache-2.0) is a concept reference only;
  no code copied, nothing new to record in `docs/LICENSES.md` (re-checked at review).
- [x] **X. Additive over invasive**: PASS with one justified exception — the
  default-`None` hook keeps loop, prompts, and dossier behavior byte-identical when
  absent; `_short_verdict` and the verdict tokens are never altered (verification is
  recorded as a separate signal — clarified Q5). The single invasive delta — the
  unified URL matcher slightly changing `dossier["sources"]` for edge-case citations
  — is justified in Complexity Tracking (review finding: two patterns let the dossier
  and the gate extract different URL sets).
- [x] **XI. English everywhere**: PASS — all artifacts in English.

**Post-Phase-1 re-check (2026-07-04)**: design artifacts (data-model, contracts) hold
all eleven gates — the resume-state extension and SSE event are additive optional
fields; no violation introduced. Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/003-verifiable-sources/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── verification-config.md   # config + CLI flags + studio request field
│   ├── dossier-verification.md  # dossier["verification"] schema + rendered section
│   └── http-api-gui.md          # /api/mission field, SSE "verify" event, GUI contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
agencykit/agency_cli/
├── verification.py            # NEW — VerificationConfig, extraction, probe, gate, report
├── engines/cli_engine.py      # hook: verification param, per-cycle check, loop gate,
│                              #   enriched inspector input, dossier["verification"],
│                              #   checkpoint/resume carry verification state
├── runner_bridge.py           # _resolve_verification (mirror _resolve_escalation),
│                              #   dossier.md "Source verification" section
├── cli.py                     # flags: --min-sources N, --resolve-sources, on
│                              #   run / resume / batch run
└── tests/
    ├── test_verification.py   # NEW — extraction, classification, gate, report (offline)
    └── test_engine.py         # loop-integration additions (probe + _call monkeypatched)

agency_studio/
└── server.py                  # parse "verification" request field, pass through to
                               #   runner_bridge, SSE passthrough of "verify" events

tests/
└── test_server_verification.py  # NEW — request parsing, SSE event, dossier passthrough

app/studio/src/
├── types.ts                   # VerifyEvent + dossier verification types
├── components/Timeline.tsx    # render "verify" phase in the mission timeline
├── components/MissionDetail.tsx  # verified-source rate + report display
├── components/MissionDetail.test.tsx  # rate display (incl. "unverified" mode)
└── App.tsx                    # "Verify sources online" launch toggle → request field
```

**Structure Decision**: same three-surface layout every studio brick uses — brain logic
in the `agencykit/` fork (import-permitted library; `escalation.py` precedent), server
pass-through in `agency_studio/server.py`, presentation in `app/studio/src`. No new
top-level directories.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle X (byte-identical off): `_extract_sources` now uses the unified Brick 3 URL matcher, so `dossier["sources"]` can differ from the pre-feature output for edge-case citations (markdown-backtick-wrapped or malformed URLs) even with verification disabled | The dossier's sources list and the verification gate MUST extract the identical URL set — with two patterns, a cited URL could appear in the dossier without ever being seen by the verifier (review finding), a drift hole in exactly the trust surface this brick hardens; the unified pattern also stops recording markdown artifacts (`` https://x` ``) as sources | Keeping the legacy pattern for the dossier preserved byte-identical output but institutionalized the drift; the delta is confined to URLs that were captured incorrectly in the first place |
