# Data Model: Verifiable Internet (Enforced Source Postcondition)

**Feature**: `003-verifiable-sources` | **Date**: 2026-07-04

All structures are plain stdlib types (frozen dataclasses + dicts/lists), consistent
with the dossier's JSON-through-every-brief design and the `EscalationConfig` precedent.

## VerificationConfig (frozen dataclass — `agency_cli/verification.py`)

| Field | Type | Default | Meaning |
|---|---|---|---|
| `min_sources` | `int` | `3` | Minimum counted sources per deployed department. `0` ⇒ gate disabled entirely (byte-identical path at the product layer; the engine hook receives `None`). |
| `resolve` | `bool` | `False` | The dedicated per-mission network opt-in. `False` ⇒ no probe runs, statuses are `unverified`, gate counts extracted sources. |

**Validation**: `min_sources >= 0` (negative rejected at construction, the same
fail-fast-at-registration discipline as `EngineSpec.__post_init__`); dict coercion
accepts `{"min_sources": int, "resolve": bool}` with the same defaults.

**Resolution rule (product layer)**: `min_sources == 0` **and** `resolve == False` ⇒
callers pass `verification=None` to `run_mission_cli`, so the engine path is
byte-identical (Principle X). `min_sources == 0` with `resolve == True` ⇒ the config
object is passed through — **report-only mode** (report and rate produced, gate
trivially passes). `min_sources > 0` ⇒ the config object is passed through.

## SourceRecord (dict — one per unique cited URL)

| Key | Type | Meaning |
|---|---|---|
| `url` | `str` | The de-duplicated cited URL (first-seen order, trailing punctuation stripped — reuses the `_SOURCE_URL_RE` extraction shape). |
| `status` | `str` | One of `resolved` \| `ambiguous` \| `unresolved` \| `unverified` \| `unverifiable` (exactly one — SC-006). |
| `detail` | `str` | Human-readable probe outcome (`"HTTP 200"`, `"HTTP 404"`, `"timeout"`, `"policy: non-https"`, `"resolution not enabled"`, …). |
| `depts` | `list[str]` | Departments whose output cites this URL; `[]` if cited only by the synthesis. |

**State transitions**: none persisted — a record is computed fresh per cycle
(re-synthesis produces new text); a per-mission `url → (status, detail)` probe cache
short-circuits re-probing unchanged URLs across cycles (D5).

## CycleVerification (dict — one per synth→inspect cycle, parallel to a `verdicts` entry)

| Key | Type | Meaning |
|---|---|---|
| `iteration` | `int` | Matches the cycle's `verdicts[i]["iteration"]` — the pairing key between the two independent signals (Q5). |
| `ok` | `bool` | Verification outcome for this cycle: `True` ⇒ every deployed department met its minimum AND the inspector named no unsourced claims (D9 as amended). |
| `resolve` | `bool` | Whether online resolution was active for this cycle. |
| `sources` | `list[SourceRecord]` | Per-source detail (post-dedup, post-cap). |
| `per_dept` | `dict[str, {"counted": int, "min": int, "ok": bool}]` | Gate math per deployed department (D7 as amended: probes ran ⇒ counted = resolved + ambiguous among checked sources; offline/degraded ⇒ counted = cited − known-bad). |
| `rate` | `float \| None` | `resolved / checkable` (D6); `None` when `resolve` is off or the cycle is degraded by total network outage (D3) — never conflated with `0.0`. |
| `missing` | `list[str]` | Claims named by the inspector as lacking sources (engine-assisted, D9); `[]` when none/indeterminate. |
| `truncated` | `int` | URLs dropped by the per-cycle cap (`0` when none — SC-008). |

## Dossier extension (additive keys on the existing dossier dict)

```python
dossier["verification"] = {            # present ONLY when the hook was active (Principle X)
    "min_sources": int,                # the enforced minimum
    "resolve": bool,                   # whether online resolution was opted in
    "cycles": [CycleVerification, …],  # one per completed synth→inspect cycle
    "final": CycleVerification,        # == cycles[-1]; what the delivered text scored
}
```

- `dossier["verdicts"]` — **unchanged schema** (engine/verdict/detail/iteration).
  Consumers (`_last_verdict`, `batch_runner`, `render_assets` PASS gate) keep exact
  behavior.
- `dossier["residual_risk"]` — existing key; its text now also covers a
  verification failure standing at the iteration cap (FR-008). Existing trigger
  (retry verdict at cap) unchanged.
- `dossier["sources"]` — existing extracted-URL list, untouched (kept for backward
  compatibility of stored missions and `_dossier_md`'s existing Sources section).

## Checkpoint / resume-state extension (additive)

| Key | Where | Rule |
|---|---|---|
| `verifications` | checkpoint snapshots (`_checkpoint`) | Optional `list[CycleVerification]`, parallel to `verdicts`; copied per-cycle like `verdicts`. |
| `verifications` | `_validate_resume_state` | Absent ⇒ valid (pre-feature snapshots resume cleanly). Present ⇒ must be a list with `len == len(verdicts)`; contents are informational — the re-entered cycle **recomputes** verification (D11). |

**Invariant preserved**: a snapshot's `delivered` was always inspected *and* verified
(checkpoints keep firing only after a completed cycle); the resume re-runs both.

## Event-stream extension (SSE / `on_event`)

`VerifyEvent` (new phase, two frames per cycle):

```json
{"phase": "verify", "iteration": 1, "status": "start"}
{"phase": "verify", "iteration": 1, "status": "done",
 "ok": true, "rate": 0.87, "checked": 23}
```

`rate` is `null` when resolution is off. All existing event phases unchanged.

## GUI types (`app/studio/src/types.ts`)

- `VerifyEvent` — mirrors the SSE frames above (same optional-fields style as
  `InspectEvent`).
- `MissionVerification` / `CycleVerification` / `SourceRecord` interfaces — mirror the
  dossier extension for `MissionDetail` rendering (rate, per-dept table, source list,
  `null`-rate → "unverified (resolution not enabled)" label).

## Entity relationships

```text
VerificationConfig ─┬─ drives ──► CycleVerification (one per synth→inspect cycle)
                    │                 │ pairs-by-iteration with verdicts[i] (Q5: two signals)
                    │                 ├── contains ──► SourceRecord (per unique URL)
                    │                 └── per_dept keyed by route departments
                    └─ resolve=True gates the probe (network opt-in)

dossier.verification.final ──► rendered in dossier.md + MissionDetail (rate, report)
CycleVerification.ok == False ──► fixes injected ──► next synthesis (existing loop)
```
