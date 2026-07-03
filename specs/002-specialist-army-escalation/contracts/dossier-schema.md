# Contract: Dossier & Checkpoint Schema (additive)

## Dossier

The dict returned by `run_mission_cli` (and persisted by `runner_bridge`) gains ONE
optional top-level key. All existing keys are unchanged in name, type, and semantics.

```jsonc
{
  // ── existing, unchanged ──
  "goal": "…", "route": ["marketing"], "context": null,
  "dept_outputs": {"marketing": "…"},
  "decisions": [], "sources": [], "open_to_verify": [],
  "direction_check": null, "verdicts": [ … ], "iteration": 1, "delivered": "…",

  // ── NEW — present ONLY when escalation ran for ≥1 department ──
  "escalation": {
    "marketing": {
      "budget": 4,
      "consumed": 4,                             // == count of non-skipped invocations
      "est_tokens": 35900,                       // advisory, chars/4 heuristic
      "selection": {
        "officers": ["officer-2-strategy"],
        "soldiers": ["soldier-stp", "soldier-positioning"],
        "rationale": {"officer-2-strategy": "…", "soldier-stp": "…"}
      },
      "invocations": [
        {"role": "selection", "name": "commander-marketing-selection", "task": "…",
         "output": "…", "est_tokens": 900},
        {"role": "commander", "name": "commander-marketing", "task": "…",
         "output": "…", "est_tokens": 8000},
        {"role": "officer", "name": "officer-2-strategy", "task": "…",
         "output": "…", "est_tokens": 15000},
        {"role": "soldier", "name": "soldier-stp", "task": "…",
         "output": "…", "est_tokens": 12000},
        {"role": "soldier", "name": "soldier-positioning",
         "skipped": "budget-exhausted", "est_tokens": 0}
        // 4 non-skipped invocations == consumed; the 5th selected specialist
        // exceeded the cap of 4 and is explicitly skipped
      ]
    },
    "comms": {
      "budget": 6, "consumed": 3, "est_tokens": 19000,
      "selection": {"officers": ["comms/O6-events"], "soldiers": ["…"],
                     "rationale": {"comms/O6-events": "event mission"}},
      "invocations": [
        {"role": "officer", "name": "comms/O6-events", "virtual": true, "…": "…"}
      ]
    }
  }
}
```

**Guarantees**:
- Escalation off / budget 0 ⇒ the `escalation` key is ABSENT and the dossier is
  byte-identical to the pre-feature dossier (SC-003).
- `consumed <= budget` for every department (SC-002).
- Every invocation carries either `output` or `skipped`, never both.
- A department that ran doctrine-only under active escalation carries
  `"no_escalation": "<reason>"` instead of `selection`/`invocations` — the decision is
  explicit, never silent (US1 scenario 3).

## Checkpoint snapshot (version stays 1)

The `"dept"`-phase snapshot MAY carry an `escalation` key with traces of COMPLETED
departments only:

```jsonc
{ "version": 1, "phase": "dept", …existing fields…,
  "escalation": { "marketing": { …DeptEscalationTrace… } } }   // optional
```

- `_validate_resume_state`: missing `escalation` ⇒ `{}` (pre-feature snapshots resume
  unchanged).
- Resume re-runs any department NOT in `dept_outputs` from scratch, escalation included —
  the existing invariant, unchanged.
- Checkpoints still fire ONLY at the documented boundaries; none fire mid-escalation.
