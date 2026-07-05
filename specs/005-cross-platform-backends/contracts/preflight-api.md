# Contract: Mission preflight (FR-012)

## Where

The existing mission-start handler (POST that launches a mission), before any
engine subprocess or asset work is spawned. No new endpoint.

## Needed-families derivation (from the mission request)

| Mission request option | Families preflighted |
|---|---|
| assets enabled (image/speech markers allowed) | `image`, `tts` |
| video opt-in flag | `video` |
| documents attached / RAG enabled | `embedding` |
| audio input to transcribe | `stt` |

Only requested families are checked — a text-only mission preflights nothing and
launches exactly as today (byte-identical, Principle X).

## Behavior

- `capabilities.preflight(families)` resolves each family's active entry
  (env > selection > platform-aware default) and probes it.
- All requested families available → launch proceeds; no response-shape change.
- Any blocker → **HTTP 409**, mission not launched, nothing spawned:

```json
{
  "error": "mission blocked: required capabilities unavailable",
  "blockers": [
    {
      "family": "image",
      "entry": "stable-diffusion-cpp",
      "reason": "missing_model_files",
      "enablement": "place <file> (sha256-pinned, <source URL>) in <models dir>"
    }
  ]
}
```

- Every blocker lists `family`, active `entry`, machine-readable `reason`, and the
  human `enablement` hint — the complete list, not just the first (spec FR-012).

## GUI

The mission form renders `blockers[]` from the 409 payload in its existing
launch-error surface (family name + hint per line, link to the capabilities
panel). No new component.

## Offline tests

Handler tests monkeypatch the capability probes to simulate: all-available (200
launch path unchanged), one blocker, multiple blockers, and text-only mission
(preflight not invoked).
