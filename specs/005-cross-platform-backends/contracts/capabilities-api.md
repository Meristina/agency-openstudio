# Contract: Capabilities API deltas (Brick 5)

The Brick 4 endpoints keep their shapes; this brick only adds entries, reason
codes, and platform-aware default semantics.

## GET /api/capabilities (unchanged shape)

Per-family view fields unchanged: `family`, `selectable`, `entries[]`, `selected`,
`selected_stale`, `env_override`, `active`.

### New entries appearing in `entries[]`

| family | id | cost | notes |
|---|---|---|---|
| image | `stable-diffusion-cpp` | `free` | portable CPU backend |
| stt | `whisper-cpp` | `free` | portable CPU backend |
| embedding | `nomic-embed-gguf` | `free` | loopback llama.cpp gateway |
| tts | *(none — `kokoro-v1.0` becomes AVAILABLE off-Mac once `[media]` installs there)* | | |

### New `reason` values (entry-level)

`missing_binary` · `missing_model_files` · `model_files_mismatch` · `gateway_down`
(alongside existing `missing_extra` / `missing_key` / `unsupported_runtime` /
`catalog_error`). `enablement` always accompanies an unavailable entry.

Platform-awareness guarantee: on Linux/Windows, MLX-bound entries report
`unsupported_runtime` (explicit "not supported on this platform" text), never a
generic import error (spec FR-005).

### `active` semantics (platform-aware default)

With no env override and no valid selection:
`active` = the `default=True` entry **if AVAILABLE**, else the first AVAILABLE
entry in registry order, else the `default=True` entry. (Previously: always the
`default=True` entry.) On a Mac with the default available, output is
byte-identical to Brick 4.

## PUT /api/capabilities/{family}/selection (unchanged)

Same 200/400/409 contract; 409 for an unavailable entry now carries the new reason
codes where applicable.

## Consumption endpoints (unchanged contract, new backends behind them)

`/api/image`, `/api/stt`, `/api/tts`, embed-consuming paths: absent portable
backend → HTTP 501, body `{"error": "<human reason — install hint>"}` (the
existing `MediaUnavailable` → ImportError → 501 mapping). Never a 500/crash for an
absence-class failure; subprocess timeout → clean error, never a hang.
