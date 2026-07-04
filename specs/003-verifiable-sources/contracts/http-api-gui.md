# Contract: HTTP API, SSE Stream & GUI Surface

**Feature**: `003-verifiable-sources` | Consumers: `app/studio` GUI, any local API client

## `POST /api/mission` (existing endpoint — additive field)

Request body gains the optional `verification` object (see
`verification-config.md`). Everything else unchanged. Server remains bound to
`127.0.0.1`, no CORS `*`, no new endpoint.

## SSE stream (existing mission stream — new phase frames)

Two frames per synth→inspect cycle. The `start` frame precedes the inspect frames
(URL extraction/probing runs first so the deterministic report can enrich the
inspector's input — D9); the `done` frame follows the verdict (the `missing` list
comes from the inspector's output):

```json
{"phase": "verify", "iteration": 1, "status": "start"}
{"phase": "verify", "iteration": 1, "status": "done",
 "ok": false, "rate": 0.4, "checked": 5}
```

- `rate`: number 0–1, or `null` when resolution is off.
- `checked`: number of unique URLs evaluated this cycle (post-dedup, post-cap).
- Frames appear **only** when the hook is active — a `verification: null` /
  min-0 mission's stream is byte-identical to today.
- The existing `done` frame is unchanged (the GUI reads the final rate from the
  mission dossier, not the stream).

## GUI contract (`app/studio/src`)

| Surface | Behavior |
|---|---|
| Launch form (`App.tsx`) | Checkbox **"Verify sources online"**, default unchecked; sends `verification: {"resolve": true}` when checked, omits the field otherwise (server default applies). |
| Timeline (`Timeline.tsx`) | Renders the `verify` phase per iteration: spinner on `start`; on `done`, "✓ sources verified (87%)" / "✗ sources below minimum" / "sources counted (unverified)" when `rate` is `null`. |
| Mission detail (`MissionDetail.tsx`) | When `dossier.verification` exists: rate headline — a `null` rate renders "unverified — resolution not enabled" when `verification.resolve` is false, and "unverified — network unavailable or no checkable sources" when resolution was enabled but the cycle degraded (never conflate the two) — plus per-department table, per-source status list, missing-claims list, truncation note. When absent: no verification UI at all (old missions render exactly as today). |
| Types (`types.ts`) | `VerifyEvent`, `MissionVerification`, `CycleVerification`, `SourceRecord` — optional-field style matching existing event interfaces. |

Accessibility / simplicity: status is conveyed by text + symbol (not color alone);
no terminal or configuration file required for any of the above (Principle VIII).

## Failure modes

| Case | Contract |
|---|---|
| Junk `verification` body field | Coerced to defaults; mission runs; no 500. |
| Mission cancelled mid-verify | Existing cancellation contract: no dossier, no partial verification record, stream ends with the existing cancel/error frame. |
| Old stored missions (no `verification` key) | `GET /api/mission/{id}` returns them unchanged; GUI renders no verification section. |
