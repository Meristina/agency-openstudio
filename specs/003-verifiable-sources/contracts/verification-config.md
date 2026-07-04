# Contract: Verification Configuration Surface

**Feature**: `003-verifiable-sources` | Consumers: `agency` CLI users, studio server, `runner_bridge` callers

## CLI flags (`agency run` / `agency resume` / `agency batch run`)

| Flag | Type / default | Behavior |
|---|---|---|
| `--min-sources N` | int, default `3` | Minimum counted sources per deployed department. `0` disables the source gate entirely — mission behavior is byte-identical to pre-feature. Negative ⇒ argparse error. |
| `--resolve-sources` | store_true, default off | The dedicated per-mission network opt-in: liveness-probe cited URLs (HTTPS-only HEAD). Without it, no verification network call is ever made. |

Rules:

- Flags compose with existing ones (`--engine`, `--no-escalation`, …) with no interaction.
- On `agency resume`, the **pinned mission envelope's** verification config wins over
  freshly passed flags (same precedence rule as escalation on resume).
- `--resolve-sources` with `--min-sources 0` still produces the *report/rate* — the
  gate never blocks. (`min_sources=0` disables blocking, not visibility, when resolve
  is explicitly requested; with neither flag non-default the offline gate applies.)

## Library hook (`run_mission_cli`)

```python
run_mission_cli(goal, engine, ..., verification: Optional[VerificationConfig] = None)
```

- `None` (default) ⇒ loop, prompts, events, dossier **byte-identical** to pre-feature
  (Principle X). No `verification` key in the dossier.
- Dict-shaped input is coerced defensively (same rule as the `escalation` dict
  coercion) — `{"min_sources": int, "resolve": bool}`.
- The hook never alters: verdict tokens, `_short_verdict` parsing, `verdicts` schema,
  `MAX_ITERS`, cancellation (`MissionCancelled` before persistence ⇒ no dossier, no
  verification record).

## Studio request field (`POST /api/mission`)

```json
{"goal": "…", "verification": {"min_sources": 3, "resolve": false}}
```

- Field optional. Absent ⇒ server default `{"min_sources": 3, "resolve": false}`
  (gate ON offline — clarified Q1).
- Junk values ⇒ coerced field-by-field to defaults (never a 500; same tolerance as
  the `escalation` request field).
- On `{"resume_from": id}` the body's `verification` is ignored; the pinned
  envelope's value wins (mirrors escalation resume precedence).

## GUI launch surface

- One toggle: **"Verify sources online"** → `verification.resolve = true`. Default off.
- `min_sources` is not exposed in the GUI launch form (stays at server default;
  CLI is the power-user override — Principle VIII).
