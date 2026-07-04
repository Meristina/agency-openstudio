# Contract: Dossier Verification Record & Rendering

**Feature**: `003-verifiable-sources` | Consumers: store readers, `dossier.md` readers, GUI, PDF export

## Structured record (`dossier["verification"]`)

Present **iff** the verification hook was active for the run. JSON-serializable.

```json
{
  "min_sources": 3,
  "resolve": true,
  "cycles": [
    {
      "iteration": 1,
      "ok": false,
      "resolve": true,
      "rate": 0.4,
      "truncated": 0,
      "per_dept": {
        "marketing": {"counted": 2, "min": 3, "ok": false},
        "product":   {"counted": 5, "min": 3, "ok": true}
      },
      "sources": [
        {"url": "https://example.com/a", "status": "resolved",
         "detail": "HTTP 200", "depts": ["marketing"]},
        {"url": "https://dead.example/x", "status": "unresolved",
         "detail": "HTTP 404", "depts": ["marketing"]}
      ],
      "missing": ["Claim 'market grows 12% CAGR' cites no source"]
    }
  ],
  "final": { "…": "== cycles[-1]" }
}
```

Guarantees:

- `status` ∈ {`resolved`, `ambiguous`, `unresolved`, `unverified`, `unverifiable`} —
  exactly one per source (SC-006).
- `rate` is `null` whenever `resolve` was off or the network was globally
  unavailable — never `0.0` for "unchecked" (US2 scenario 3).
- `cycles[i].iteration` pairs with `verdicts[j].iteration` — the two signals of
  clarify Q5; neither list references the other's content.
- `verdicts` schema is unchanged; `_last_verdict` semantics are unchanged.
- Delivery gate: mission delivered-as-verified ⇔ last verdict not in retry set AND
  `final.ok` is true. At the iteration cap with `final.ok == false`,
  `dossier["residual_risk"]` names the verification failure.

## Rendered dossier (`missions/<id>/dossier.md`)

New section, rendered by `runner_bridge._dossier_md` **only when the key exists**
(same conditional pattern as `residual_risk`):

```markdown
## Source verification

- Verified-source rate: 40% (2 of 5 checkable) — online resolution: ON
- Minimum per department: 3

| Department | Counted | Min | OK |
|---|---|---|---|
| marketing | 2 | 3 | ❌ |
| product | 5 | 3 | ✅ |

- Unresolved: https://dead.example/x (HTTP 404)
- Missing sources: Claim 'market grows 12% CAGR' cites no source
- (URLs beyond the per-cycle cap, if any: "N sources not checked — cap reached")
```

Offline mode renders: `Verified-source rate: unverified (resolution not enabled) —
counted 5 cited sources`.

## Backward compatibility

- Stored missions without the key load, list, render, and export unchanged.
- `dossier["sources"]` (existing flat URL list) continues to be written and rendered
  in its existing `## Sources` section.
