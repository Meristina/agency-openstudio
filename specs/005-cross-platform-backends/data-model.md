# Data Model: Cross-Platform Backends

**Feature**: 005-cross-platform-backends | **Date**: 2026-07-05

No persistent-storage schema changes: `selections.json` (version 1, family →
entry id) is untouched. This brick adds registry rows, one new pure-data result
shape (Blocker), and new probe reason codes.

## Registry rows (in `agency_studio/engines/models.py`)

### ImageModel — new row `stable-diffusion-cpp`

| Field | Value / rule |
|---|---|
| `id` | `stable-diffusion-cpp` |
| `label` | Stable Diffusion (CPU, stable-diffusion.cpp) |
| `backend` | `sdcpp` — keys the new `_IMAGE_BACKENDS` triple |
| `binary` | `sd` (resolved via `shutil.which`) |
| `model_file` | `ModelFile` manifest: GGUF checkpoint, sha256-pinned, user-acquired |
| `steps_default` | backend-appropriate default (research: distilled-model step count) |
| `default` | `False` — MLX default untouched on Mac; platform-aware `_default()` promotes it off-Mac |
| `note` | portable CPU backend; runs on macOS / Linux / Windows |

### SttModel — new row `whisper-cpp` (+ new `backend` discriminator)

`SttModel` gains a `backend: str` field (default `"mlx"` so the existing row is
byte-identical without edits to its literal).

| Field | Value / rule |
|---|---|
| `id` | `whisper-cpp` |
| `backend` | `whispercpp` — keys the new `_STT_BACKENDS` triple |
| `binary` | `whisper-cli` |
| `model_file` | `ModelFile`: ggml/GGUF Whisper model, sha256-pinned, user-acquired |
| `default` | `False` |

### EmbedModel — new row `nomic-embed-gguf` (+ new `backend` discriminator)

`EmbedModel` gains `backend: str = "mlx"` (existing rows byte-identical).

| Field | Value / rule |
|---|---|
| `id` | `nomic-embed-gguf` |
| `backend` | `llamacpp-gateway` |
| `gateway_env` | `AGENCY_STUDIO_EMBED_GATEWAY_URL` (default `http://127.0.0.1:8080`) |
| `ndim` | must equal the served GGUF model's dimensions (existing re-ingest note carries over) |
| `default` | `False` |

### TtsModel — no new row

`kokoro-v1.0` is already portable (ONNX); no schema or row change.

## Probe reason codes (extends `capabilities.UnavailableReason`)

Existing: `missing_extra`, `missing_key`, `unsupported_runtime`, `catalog_error`.

| New code | Meaning | Enablement content |
|---|---|---|
| `missing_binary` | required CLI binary not on PATH | pinned release + install location hint |
| `missing_model_files` | binary/extra present, model file absent | exact file, pinned source URL, destination dir |
| `model_files_mismatch` | model file present but sha256 differs from manifest | re-download instruction with pinned source |
| `gateway_down` | gateway URL is valid loopback but service unreachable | start-command hint for the local service |

Validation rules:

- A gateway URL with a non-loopback host is a configuration **error** (hard
  reject at validation time), not an availability state — it never reaches a probe.
- Reason codes are machine-readable (GUI badges/tests key on them); `enablement`
  is the human string.

## Blocker (new pure-data shape, `capabilities.preflight` output)

| Field | Type | Notes |
|---|---|---|
| `family` | str | one of the requested families |
| `entry` | str | the active (resolved) entry id that is unavailable |
| `reason` | str | probe reason code (table above + existing codes) |
| `enablement` | str \| null | install/start hint |

`preflight(families)` returns `[]` when the mission may launch; a non-empty list is
serialized verbatim into the 409 payload (see `contracts/preflight-api.md`).

## State transitions

Availability is stateless-per-read (probe on inventory read / preflight / ensure),
same as Brick 4 — no caching added for the new backends beyond what exists. The
selection lifecycle (set / clear / stale) is unchanged; a persisted selection whose
backend is absent on this machine surfaces through the existing `selected_stale`
mechanism plus the new reason codes.
