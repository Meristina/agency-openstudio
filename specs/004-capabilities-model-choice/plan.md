# Implementation Plan: Capabilities & Model Choice (the end of env-only)

**Branch**: `004-capabilities-model-choice` | **Date**: 2026-07-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-capabilities-model-choice/spec.md`

## Summary

Brick 4 turns model/tool selection from an env-only, terminal-bound affair into a
first-class in-interface capability. One new stdlib module
(`agency_studio/capabilities.py`) aggregates the existing registries — image, video,
visual, embedding, KG extraction, plus newly promoted STT/TTS registries, the
OpenMontage tool catalog (across a subprocess boundary), and the MCP server config —
into an honest inventory (FREE/PAID, AVAILABLE/UNAVAILABLE + reason + enablement
step, all checks passive). A JSON selection store in the studio data directory
persists per-family defaults; a single documented resolution chain
(env var → persisted selection → built-in default) is threaded through every
consumer with byte-identical behavior when nothing is set. Two new endpoints
(`GET /api/capabilities`, `PUT/DELETE /api/capabilities/selection`) and a new
Capabilities view in the React GUI expose it — no terminal, no restart.

## Technical Context

**Language/Version**: Python 3.11+ (stdlib-only core), TypeScript/React 18 + Vite (GUI)

**Primary Dependencies**: None new. Core stays stdlib; existing optional extras
([media], [studio], [visual], [mcp], …) are only *probed*, never imported eagerly.
Presence checks use `importlib.util.find_spec` (no heavy import), key checks use
`os.environ` presence, OpenMontage enumeration crosses a subprocess boundary.

**Storage**: `selections.json` (family → entry id) in the existing studio data dir
(`rag.data_dir()`, i.e. `~/.local/share/agency-studio`, `AGENCY_STUDIO_DATA_DIR`
override) — atomic write (tmp + `os.replace`), tolerant load (missing/corrupt ⇒ `{}`).

**Testing**: pytest at repo root (`tests/`), fully offline — registries, subprocess
catalog probe, env, and data dir all stubbed/monkeypatched; vitest for the GUI
(`app/studio/src/*.test.ts*`).

**Target Platform**: User's local machine (macOS Apple-Silicon primary today; entries
unsupported elsewhere report UNAVAILABLE "unsupported runtime" — Brick 5 widens this).
Server binds `127.0.0.1` only.

**Project Type**: Web application — stdlib HTTP/SSE server (`agency_studio/server.py`)
+ React GUI (`app/studio/`).

**Performance Goals**: `GET /api/capabilities` responds < 500 ms without the
OpenMontage catalog (pure in-process presence checks); the catalog subprocess probe is
cached per server process (explicit `?refresh=1` re-probe) so the common path never
pays subprocess latency twice.

**Constraints**: Passive availability only (no network, no paid calls, key
presence-only — FR-005/FR-013); byte-identical behavior with no selection and no env
(FR-009, Constitution X); offline test suite (FR-014, Constitution VII); no in-process
`openmontage/` import (Constitution V).

**Scale/Scope**: 6 model families (~10 registry entries today) + 2 promoted families
(STT/TTS, 1 entry each) + ~122 OpenMontage tools + ≤8 MCP servers (mcp_client
`MAX_SERVERS`). Single-user local tool; last-write-wins on the selection store.

### Existing surface being aggregated (verified against source)

| Family | Registry / source | Default today | Env override today |
|---|---|---|---|
| image | `engines/models.py` `IMAGE_MODELS` (3 entries) | `DEFAULT_IMAGE_MODEL="flux-schnell"`; per-request `model` param (server.py:1884) | none (new: `AGENCY_STUDIO_IMAGE_MODEL`) |
| video | `seedance.py` `VIDEO_MODELS`; `default_video_model()` reads env at call time, fail-loud | `DEFAULT_VIDEO_MODEL="seedance-2.0"` | `AGENCY_STUDIO_VIDEO_BACKEND` (+`_VIDEO_API_KEY`, `_VIDEO_MODEL` for the cloud api_model string) |
| visual | `visual.py` `VISUAL_MODELS` (local/cloud qwen3-vl) | `DEFAULT_VISUAL_MODEL="qwen3-vl-local"` | none for registry choice (new: `AGENCY_STUDIO_VISUAL_BACKEND`; note `AGENCY_STUDIO_VISUAL_MODEL` is taken — it overrides the cloud api_model) |
| embedding | `engines/models.py` `EMBED_MODELS` | `DEFAULT_EMBED_MODEL="nomic-text-v1.5"` | none (new: `AGENCY_STUDIO_EMBED_MODEL`) |
| kg-extraction | `knowledge.py` `make_extractor` (claude \| gliner2) | `"claude"` | `AGENCY_STUDIO_KG_BACKEND` (+`_KG_GLINER_MODEL`) |
| stt | ad-hoc: `models.STT_HF_REPO` pinned, mlx-whisper (`local_media.py`) | whisper-large-v3-turbo | none (new registry + `AGENCY_STUDIO_STT_MODEL`) |
| tts | ad-hoc: kokoro-onnx `"kokoro-v1.0"` (`local_media.py`) | kokoro-v1.0 | none (new registry + `AGENCY_STUDIO_TTS_MODEL`) |
| production-tools | `openmontage/tools/tool_registry.py` `ToolRegistry` (`ToolRuntime` = LOCAL/LOCAL_GPU/API/HYBRID) — **subprocess boundary only** (registry autoloads `.env` on import) | n/a (inventory-only) | n/a |
| mcp | `mcp_client.py` `list_servers()` from `mcp.json` in data dir | n/a (inventory-only) | n/a |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — no reasoning involved; the
  inventory/selection surface is pure bookkeeping. The `claude` KG extractor entry
  keeps running through the CLI subprocess exactly as today.
- [x] **II. Engine neutrality**: PASS — no engine-specific behavior added; the
  Engine contract is untouched.
- [x] **III. No invented information**: PASS — mission research, citation, and the
  inspector/veto contract (Brick 3 postcondition) are untouched (spec assumption).
- [x] **IV. Local-first & offline-by-default**: PASS — the brick makes free/paid
  *more* explicit (cost class on every entry); availability checks are passive with
  zero network; cloud stays env-keyed opt-in.
- [x] **V. Subprocess boundaries**: PASS — the OpenMontage catalog is enumerated via
  a subprocess probe (mirroring `openmontage_backend._spawn_render`'s seam), never
  an in-process import; vendored subtrees unmodified.
- [x] **VI. Security**: PASS — new endpoints ride the existing `127.0.0.1`-only
  server, no CORS `*`, no new static routes; API keys: presence boolean + env var
  *name* only (FR-013); selection store contains entry ids only, never keys.
- [x] **VII. Offline tests**: PASS — every new behavior (inventory, store,
  resolution, endpoints, catalog probe) is designed around monkeypatchable seams;
  FR-014/SC-006 make the offline suite a hard requirement.
- [x] **VIII. End-user simplicity**: PASS — this brick *is* the simplicity play:
  see + pick in the GUI, zero terminal; env vars demoted to power-user override.
- [x] **IX. License**: PASS — no new components; nothing to add to
  `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — resolution hooks insert between the
  existing env-read and built-in default; with no selections file and no env, every
  consumer path is byte-identical (FR-009 scenario 3); registries gain entries, no
  existing entry changes.
- [x] **XI. English everywhere**: PASS.

*Post-Phase-1 re-check (after data-model + contracts): all gates still PASS — the
contract exposes no key values (VI), the data model adds only additive registry
dataclasses and a default-absent JSON store (X), and every contract example carries
its offline-test stubbing note (VII).*

## Project Structure

### Documentation (this feature)

```text
specs/004-capabilities-model-choice/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── capabilities-api.md   # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
agency_studio/
├── capabilities.py          # NEW — inventory aggregation, SelectionStore, resolution chain
├── server.py                # + GET /api/capabilities, PUT/DELETE /api/capabilities/selection;
│                            #   consumers switch default-lookup to the resolution chain
├── engines/
│   ├── models.py            # + SttModel/TtsModel dataclasses, STT_MODELS/TTS_MODELS registries
│   │                        #   (wrapping today's pinned repos; FR-004)
│   └── local_media.py       # reads STT/TTS entry from the registry instead of constants
├── seedance.py              # default_video_model(): selection inserted between env and default
├── visual.py                # visual default resolved through the chain
├── knowledge.py             # make_extractor default resolved through the chain
├── rag.py                   # Retriever default embed model resolved through the chain
└── mcp_client.py            # unchanged (list_servers() reused by the inventory)

app/studio/src/
├── api.ts                   # + capabilities fetch/select/clear calls + types
├── components/
│   └── Capabilities.tsx     # NEW — the capabilities view (inventory + pickers)
└── capabilities-api.test.ts # NEW — vitest coverage for the API layer

tests/
├── test_capabilities.py     # NEW — inventory, store, resolution, catalog probe (stubbed)
└── test_server_capabilities.py  # NEW — endpoint contract tests (offline)
```

**Structure Decision**: Web-application layout already in place — stdlib server
package `agency_studio/` + React GUI `app/studio/`. The feature adds one new core
module, one new GUI component, and two new test modules; everything else is additive
edits at existing seams.

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.
