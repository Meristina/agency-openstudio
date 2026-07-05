# Phase 0 Research: Capabilities & Model Choice

All Technical Context unknowns resolved. Each decision: what, why, alternatives.

## R1. Passive availability checks — mechanism per check type

**Decision**: Three passive probe kinds, all stdlib, all synchronous, none importing
heavy modules:

1. **Optional-install presence** — `importlib.util.find_spec("<module>")` per entry's
   declared probe module (e.g. `mflux`, `mlx_whisper`, `kokoro_onnx`,
   `mlx_embedding_models`, `mcp`). `find_spec` inspects finders without executing the
   module, so no model weights, no GPU, no side effects.
2. **API-key presence** — `bool(os.environ.get(entry.key_env))`; only the boolean and
   the env var *name* ever leave the function (FR-013).
3. **Runtime support** — a declared predicate on the entry (e.g. MLX-backed entries
   require `platform.machine() == "arm64" and sys.platform == "darwin"`); evaluated
   locally, no probing.

**Rationale**: FR-005 mandates safe/passive; `find_spec` is the only stdlib way to
check installability without triggering imports (the existing `_mflux_probe` /
`_probe_tts` seams *import* — fine at load time, too heavy/side-effectful for an
inventory read). Presence-only key semantics confirmed in clarification session.

**Alternatives considered**: (a) reuse the existing `_probe_*` import-based probes —
rejected: importing mflux/kokoro on every inventory GET is slow and can allocate;
(b) `pkgutil.find_loader` — deprecated alias of the same machinery; (c) actual key
validation calls — rejected by clarification (presence-only).

## R2. Selection store — location, format, write discipline

**Decision**: `selections.json` in `rag.data_dir()` (i.e.
`~/.local/share/agency-studio/`, overridable via `AGENCY_STUDIO_DATA_DIR`). Schema:
`{"version": 1, "selections": {"<family>": "<entry-id>"}}`. Writes go through
`tempfile.NamedTemporaryFile(dir=data_dir)` + `os.replace` (atomic on POSIX and
Windows). Reads are tolerant: missing file, unparsable JSON, wrong shape, or unknown
version ⇒ treated as `{}` (spec edge case: never crashes, never blocks startup).
Last write wins (spec assumption; single-user local tool).

**Rationale**: Clarification session chose a dedicated JSON file in the data dir.
`data_dir()` already exists, is never web-served, and is already the tests' tmp-dir
seam. `os.replace` guarantees readers never observe a torn file.

**Alternatives considered**: extending an existing config surface (none exists for
server-side prefs; mcp.json is user-authored, mixing machine-written state in would
fight the user), SQLite (transactional overkill for one mapping).

## R3. Per-family env override names (resolution chain, FR-009)

**Decision**: keep the two existing selection envs, add five new ones under the same
naming scheme; the chain per family is **env → persisted selection (if present and
available) → built-in default**, env read at call time (matching
`default_video_model()`'s existing discipline):

| Family | Env var | Status |
|---|---|---|
| image | `AGENCY_STUDIO_IMAGE_MODEL` | new |
| video | `AGENCY_STUDIO_VIDEO_BACKEND` | existing, unchanged |
| visual | `AGENCY_STUDIO_VISUAL_BACKEND` | new (`AGENCY_STUDIO_VISUAL_MODEL` is **taken** — it overrides the *cloud api_model string*, not the registry choice; reusing it would be a breaking semantic change) |
| embedding | `AGENCY_STUDIO_EMBED_MODEL` | new |
| kg-extraction | `AGENCY_STUDIO_KG_BACKEND` | existing, unchanged |
| stt | `AGENCY_STUDIO_STT_MODEL` | new |
| tts | `AGENCY_STUDIO_TTS_MODEL` | new |

Fail-loud semantics preserved: an env var naming an unknown id raises at resolution
(exactly `default_video_model()` today). A *persisted selection* naming an unknown or
unavailable id is skipped silently with a stale flag in the inventory (FR-011) — env
is power-user territory (loud), the store is GUI territory (self-healing).

**Rationale**: Consistent prefix, zero collisions, zero behavior change for the two
families that already had an env override.

**Alternatives considered**: one JSON env (`AGENCY_STUDIO_MODELS`) — power users
lose one-var-per-thing ergonomics; reusing `AGENCY_STUDIO_VISUAL_MODEL` — collision
documented above.

## R4. OpenMontage catalog enumeration — subprocess probe

**Decision**: a `capabilities._spawn_catalog()` seam (mirroring
`openmontage_backend._spawn_render`) runs
`[sys.executable, "-c", <inline script>]` with `cwd=<repo>/openmontage`, a hard
timeout (~20 s), and captures stdout JSON. The inline script does
`from tools.tool_registry import ToolRegistry; r = ToolRegistry(); r.discover();
print(json.dumps(r.support_envelope()))` (final shape confirmed at implementation
against the pinned registry API). The result is normalized into capability entries
(name, label, `ToolRuntime` tier, availability/status, reason) and **cached per
server process**; `GET /api/capabilities?refresh=1` re-probes. Any failure (missing
Python deps in the subtree, timeout, bad JSON) ⇒ the production-tools family renders
as unavailable-with-reason while the rest of the inventory is unaffected (spec edge
case).

Cost class per clarification: derived from tier — LOCAL/LOCAL_GPU ⇒ FREE, API ⇒
PAID, HYBRID ⇒ both badges.

**Rationale**: Constitution V forbids in-process import (`tools/base_tool.py` /
`tool_registry._load_dotenv` autoload `.env`); the registry already computes
availability/status itself, so the studio only transports and normalizes. Caching
keeps the common inventory read subprocess-free.

**Alternatives considered**: static AST scan of `openmontage/tools/` (fragile,
duplicates upstream logic), a vendored JSON snapshot of the catalog (drifts from the
pinned subtree), importing with `.env` neutralized (still violates Constitution V).

## R5. MCP family — enumeration, availability, cost class

**Decision**: entries come from `mcp_client.list_servers()` (`mcp.json`, already
capped at `MAX_SERVERS`, already `.public()`-redacted). Availability =
`find_spec("mcp")` (the [mcp] extra) AND, for command servers,
`shutil.which(command)`; URL servers additionally require nothing (reachability would
be a network call — forbidden). Cost class: **FREE** for all MCP entries — servers
are user-authored config; the studio neither bills nor can know a third party's
pricing; the entry note carries the transport (command/url) so paid remote services
are at least visibly remote. Missing/empty/unreadable `mcp.json` ⇒ empty family with
reason (spec edge case). Inventory-only (clarification): no default selection,
mission attachment behavior unchanged.

**Rationale**: reuses the existing hardened parser (path-validated, size-capped);
passive-only rule rules out reachability checks.

**Alternatives considered**: per-server `paid` flag in mcp.json (schema change to a
user-authored file — invasive), URL ⇒ PAID heuristic (wrong for self-hosted free
servers; dishonest).

## R6. STT/TTS registry promotion (FR-004)

**Decision**: add `SttModel` / `TtsModel` frozen dataclasses and
`STT_MODELS` / `TTS_MODELS` dicts to `engines/models.py`, following the
`ImageModel`/`EmbedModel` pattern exactly (id, label, note, repo, pinned revision,
probe module, default flag). Initial population = exactly today's hardwired pair:
`whisper-large-v3-turbo` (repo `models.STT_HF_REPO`, revision `STT_HF_REVISION`,
probe `mlx_whisper`) and `kokoro-v1.0` (probe `kokoro_onnx`). `local_media.py`'s
STT/TTS paths read the resolved registry entry instead of module constants — same
values flow to the same code, so behavior is byte-identical by construction.
`_handle_models_status` keeps its current payload shape (GUI compatibility) and the
new inventory supersedes it for discovery.

**Rationale**: FR-004 requires first-class enumeration/selection; single-entry
registries make the promotion additive and riskless while opening the seam Brick 5
needs for cross-platform siblings.

**Alternatives considered**: a separate `speech.py` registry module (scatters the
registry pattern), deferring TTS because it has one entry (FR-004 explicitly covers
both).

## R7. Embedding-selection caveat — dimension coupling

**Decision**: the embedding family is selectable like the others, but the inventory
entry carries a warning note: the vector store's sqlite-vec column width is fixed by
the embed model's `ndim` at ingestion time; switching the default applies to *new*
stores/retrievers, and a store built with a different model will fail dimension
checks until re-ingested. Surfacing re-ingestion tooling is out of scope (Brick 4
selects; it does not migrate data).

**Rationale**: `EmbedModel.ndim` "drives the sqlite-vec column width"
(engines/models.py) — silent switching would look like breakage; an honest note is
the spec-consistent minimum.

**Alternatives considered**: blocking embedding selection while a store exists
(hidden coupling, surprising refusals), auto re-embedding (expensive, invasive, out
of scope).

## R8. Endpoint shape & GUI integration

**Decision**: two new routes on the existing handler (loopback-only, no new CORS or
static surface):

- `GET /api/capabilities` — full inventory + active selections + per-family
  `env_override` flag (FR-010) + stale-selection flags (FR-011).
- `PUT /api/capabilities/selection` body `{"family": ..., "id": ...}` — 200 on
  success; **409 + reason + enablement step** when the entry is unavailable (FR-008);
  400 unknown family/id shape; `DELETE /api/capabilities/selection/{family}` clears
  one selection (returns the family to built-in default).

GUI: new `Capabilities.tsx` view fed by `api.ts`; unavailable entries render the
reason + enablement hint inline; selected-but-overridden families show the env
override banner. Full contract in `contracts/capabilities-api.md`.

**Rationale**: matches the server's existing `/api/*` JSON conventions
(`_send_json`/`_send_error_json`, 501-on-missing-extra); PUT/DELETE are idempotent,
matching last-write-wins.

**Alternatives considered**: POST-only RPC style (`/api/capabilities/select`) — the
existing surface already uses DELETE for docs/visual/checkpoints, so REST-ish verbs
are the house style; folding selection into `GET /api/models` (that endpoint feeds
the ModelManager warm-state panel — different concern, kept stable).
