# Data Model: Capabilities & Model Choice

Python types live in `agency_studio/capabilities.py` (new) and
`agency_studio/engines/models.py` (STT/TTS promotion). TypeScript mirrors live in
`app/studio/src/types.ts`. All dataclasses frozen, stdlib-only.

## Enumerations

### Family (str enum)

`image | video | visual | embedding | kg-extraction | stt | tts |
production-tools | mcp`

- `SELECTABLE_FAMILIES` = the first seven (model families).
- `production-tools` and `mcp` are inventory-only (clarifications): a PUT selecting
  them is refused with 400.

### CostClass (str enum)

`free | paid | free_paid` — `free_paid` is the dual badge, used only by
HYBRID-tier production tools (clarification: LOCAL/LOCAL_GPU ⇒ `free`, API ⇒
`paid`, HYBRID ⇒ `free_paid`).

### Availability (str enum)

`available | unavailable`

### UnavailableReason (str enum, machine-readable — FR-002)

| code | meaning | enablement step carried |
|---|---|---|
| `missing_extra` | optional install absent (`find_spec` miss) | pip install hint, e.g. `pip install 'agency-studio[media]'` |
| `missing_key` | required API key env var unset | the env var *name*, e.g. `AGENCY_STUDIO_VIDEO_API_KEY` |
| `unsupported_runtime` | platform predicate false (e.g. MLX off Apple-Silicon) | short explanation ("requires Apple-Silicon macOS; Brick 5 adds siblings") |
| `catalog_error` | family-level source unreadable (OpenMontage probe failed, mcp.json unreadable) | the probe/parse error summary |
| `unknown_entry` | (stale selections only) selected id no longer in any registry | "re-select from the current inventory" |

## Entities

### CapabilityEntry

The unit of the inventory (FR-002, FR-003).

| field | type | notes |
|---|---|---|
| `id` | str | stable identifier — registry key (`flux-schnell`), tool name, or MCP server name |
| `label` | str | human-readable (`ImageModel.label`, tool display name, server name) |
| `family` | Family | |
| `cost` | CostClass | static, declared (spec assumption); tier-derived for production tools |
| `availability` | Availability | computed passively at read time (R1) |
| `reason` | UnavailableReason \| None | required iff `unavailable` |
| `enablement` | str \| None | human-actionable step, required iff `unavailable` |
| `tier` | str \| None | `local \| local_gpu \| api \| hybrid` — production-tools only (FR-003; `ToolRuntime` values) |
| `note` | str | short descriptor (existing registry `note`; embedding entries carry the ndim-coupling warning, R7) |
| `default` | bool | true for the built-in default of a selectable family |
| `key_env` | str \| None | env var *name* for paid entries (never the value — FR-013) |

### CapabilityFamilyView

One family block in the inventory payload.

| field | type | notes |
|---|---|---|
| `family` | Family | |
| `selectable` | bool | false for `production-tools`, `mcp` |
| `entries` | list[CapabilityEntry] | registry order; never hidden when empty/broken — carries a family-level `catalog_error` entry state instead (spec edge cases) |
| `selected` | str \| None | persisted selection id, if any |
| `selected_stale` | bool | selection exists but entry is now unavailable/unknown (FR-011) |
| `env_override` | str \| None | env var name currently overriding this family (FR-010), else None |
| `active` | str | the id resolution would return right now (env → selection → default) |

### CapabilityInventory

`{"families": [CapabilityFamilyView, ...], "generated_at": iso8601}` — read-only,
recomputed per GET (OpenMontage block served from the per-process cache, R4).

### SelectionStore (persisted)

File: `<data_dir>/selections.json` (R2).

```json
{
  "version": 1,
  "selections": { "image": "flux2-klein-4b", "video": "seedance-2.0" }
}
```

- **Identity/uniqueness**: at most one entry id per family (dict key).
- **Validation on write**: family ∈ SELECTABLE_FAMILIES; id exists in that family's
  registry; entry currently available (FR-008) — else the write is refused, store
  untouched.
- **Validation on read**: none enforced (tolerant load, R2); staleness is computed
  at inventory/resolution time, not persisted (FR-011).
- **Atomicity**: tmp file + `os.replace`; last write wins.

### Registry additions (engines/models.py — FR-004)

`SttModel` / `TtsModel` frozen dataclasses: `id, label, note, repo,
revision, probe_module, default`. Registries `STT_MODELS` / `TTS_MODELS`
(insertion-ordered dicts, same pattern as `IMAGE_MODELS`). Initial entries wrap
today's constants exactly (R6): `whisper-large-v3-turbo`, `kokoro-v1.0`.

## State transitions

### Selection lifecycle (per family)

```
(no selection) --PUT valid id--> (selected)
(selected)     --PUT other id--> (selected')          [last write wins]
(selected)     --DELETE-------> (no selection)
(selected)     --entry becomes unavailable--> (selected, stale)   [computed, not stored]
(selected, stale) --resolution--> behaves as (no selection)       [FR-011 fallback]
(selected, stale) --entry restored--> (selected)                  [no user action]
```

### Resolution (per consuming operation — FR-009)

```
resolve(family):
  env = os.environ[family.env_var]        # read at call time
  if env set:   validate against registry → fail-loud on unknown (R3) → use env
  elif store[family] set AND entry available: use selection
  else:         use built-in default      # byte-identical to today
```

Consumers wired to `resolve()`: image handler default (server.py:1884), 
`seedance.default_video_model()`, visual default, `rag.Retriever` embed default,
`knowledge.make_extractor`, STT/TTS backend loaders. In-flight operations keep the
model they started with (spec assumption).

## Volume / scale assumptions

≤ ~150 entries total (10 model entries + ~122 tools + ≤8 MCP servers); one JSON
file < 1 KB; no pagination needed; inventory recompute is O(entries) with only
`find_spec`/env/platform lookups per entry.
