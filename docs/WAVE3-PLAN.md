# Wave 3 — Multimodal as a department deliverable · Implementation Plan

> Status: **SHIPPED** (all six build-order steps landed). Produced after a read-only
> investigation pass + an adversarial multi-agent reflection gate. This plan supersedes
> the naive sketch in `ROADMAP.md §Wave 3` with the corrections that pass surfaced.

## Goal (ROADMAP, verbatim)

> Hook in agency-kit's `_dept_prompt` + post-processing that detects an asset request
> (campaign image, TTS narration) → `local_media`. Assets in `missions/<id>/assets/`.

## What the reflection pass corrected (load-bearing)

1. **"Generated after it passes inspection" is FALSE by default.** `run_mission_cli`
   returns a populated `delivered` even when the Inspector VETOed at `MAX_ITERS`
   (it only attaches `residual_risk`). → Asset generation **must gate strictly on
   `runner_bridge._last_verdict(dossier) == 'PASS'`** (the exact token — not
   "residual_risk absent", because an unrecognized verdict also breaks the loop
   early with no residual_risk yet no clean PASS).
2. **Studio-side-only prompt injection is impossible.** `_dept_prompt`/`_synth_prompt`
   are agency-kit-internal and take no studio text; the only existing hooks are
   `on_event`/`should_cancel`. Injecting via `goal` pollutes the slug/router/inspector.
   → A **new additive default-None param** is the only correct mechanism.
3. **Three distinct directories.** The store `~/.agency/missions/<ts-slug>/` (read by
   the GUI `store.load` + PDF export), the project `<root>/missions/<NNN-slug>/`
   (= `MissionResult.path`), and `<root>/studio_assets/` (the **only** root served by
   `/media`, mapped by `_media_url` via `relative_to(assets_root)`). → Assets **must**
   live under `studio_assets/` or `_media_url` raises `ValueError` (500) and the GUI/PDF
   never see them. The roadmap's literal "`missions/<id>/assets/`" would orphan them.
4. **One ModelManager process-wide.** The detached mission worker only holds
   `project_root`; building a `ModelManager` there = a **second** resident-model holder,
   breaking the 16 GB mutual-exclusivity invariant. → Asset rendering must reuse the
   server's single warm `ModelManager` (or the same instance, threaded through).
5. **Best-effort, never destructive.** Asset failure (`MediaUnavailable` — note it
   subclasses `ImportError` — or a Metal crash like the z-image timeout) must **never**
   discard an already-inspected PASS deliverable. Persist intent: deliverable first,
   assets best-effort.
6. **Stop must cover the render phase.** `should_cancel` is only polled inside
   `run_mission_cli`; the asset loop runs after it returns, so Stop currently wouldn't
   abort a multi-minute GPU render. → Thread `should_cancel` into the asset loop.

## The 3 decisions (final)

- **D1 — clause injection:** new additive default-None `asset_clause: Optional[str] = None`
  on `run_mission_cli`, appended inside `_dept_prompt`/`_synth_prompt` only when set
  (byte-identical standalone, exactly the `on_event`/`should_cancel` precedent). Markers
  parsed **only** from the inspected `dossier['delivered']`, never `dept_outputs`.
- **D2 — post-processing:** new additive default-None hook in
  `runner_bridge._run_and_persist`, invoked **after** `run_mission_cli` returns but
  **before** `store.save`/`serialize_dossier`, fed the studio's single warm
  `ModelManager`, gated on `PASS`, writing into `studio_assets/missions/<mission_id>/`,
  best-effort, covering `run()` + `resume()` uniformly.
- **D3 — scope:** strict whitelist. Type allowlist `{image, tts}` (STT excluded);
  **route-conditioned at render time** (honor `image` only if `marketing` in route,
  `tts` only if `comms` in route — read from `dossier['route']`, robust to where the
  marker physically sits); hard caps (≤4 images, ≤2 TTS per mission); a **separate
  small marker model allowlist** (`flux-schnell` only — excludes `boogu`); a TTS voice
  allowlist; dimension/step/length clamps moved **into `ModelManager`** as the shared
  chokepoint; any `path`/`filename` field in the marker JSON is dropped; all writes go
  through `ModelManager` (uuid filenames only).

## Marker protocol

A department (or the synthesis) may embed a fenced block in `delivered`:

````
```asset
{"type": "image", "prompt": "A bold minimalist hero banner for ...", "model": "flux-schnell"}
```
````
````
```asset
{"type": "tts", "text": "Welcome to ...", "voice": "af_heart"}
```
````

Parse rules (all enforced in `assets.py`):
- Only fenced blocks with info-string `asset`. Each block byte-bounded (skip if > 8 KB)
  before `json.loads`; each parse wrapped in try/except (skip on
  `JSONDecodeError`/`RecursionError`, never abort the loop).
- Result must be a `dict` with `type ∈ {image, tts}`. Unknown types ignored.
- **Field whitelist:** `image → {prompt, model}`, `tts → {text, voice}`. Every other
  key (incl. `path`/`filename`/`width`/`height`/`steps`/`seed`) is **ignored** —
  untrusted output never picks compute size or output path.
- `prompt`/`text` length-capped (≤ 2 KB) → skip/truncate over-length.
- `model` validated against the **marker** allowlist (not the full registry); unknown
  or non-allowlisted (e.g. `boogu-base`) → reject at parse time (before any load).
- `voice` validated against `ALLOWED_VOICES`; default `af_heart` if absent/invalid.
- Per-mission caps: stop honoring image markers after 4, TTS after 2. Over-cap markers
  are **dropped at the parse boundary** — silently, exactly like malformed / off-route /
  unparseable markers. The manifest only ever contains entries for markers that were
  actually rendered/attempted, so a dropped marker never reaches the manifest or the GUI
  gallery. (Resolved in #19: `rewrite_delivered` now clears **every** `asset` fence, so no
  raw JSON block survives into the deliverable/PDF — a rendered block becomes its clean
  reference (`ok`), an *attempted-then-failed* block (`failed`/`skipped`, which has a
  manifest entry with a `reason`) becomes a neutral `_[… unavailable]_` placeholder, and a
  parse-dropped block — off-route / over-cap / non-allowlisted / malformed, with **no**
  manifest entry — is stripped outright. `_build_render_assets` runs the rewrite even when
  zero markers parse, so a pure off-route fence is stripped without touching the GPU.)
- Route gate: drop `image` markers unless `marketing ∈ dossier['route']`; drop `tts`
  unless `comms ∈ dossier['route']`.

## File-by-file changes

> **Scope note (post `/code-review`):** the safety surface is enforced **at the
> untrusted boundary** (the marker parser in step 3, the HTTP routes), **not** silently
> inside the shared `ModelManager` — silent clamping/truncation there is invisibly-wrong
> for the existing HTTP callers, and adding `out_dir`/`MARKER_IMAGE_MODELS` before a
> consumer exists violates CLAUDE.md ("do not invent implementation that the roadmap
> defers"). So each control lands **with the step that consumes it**: marker caps + safe
> fixed dims + the marker model allowlist in step 3 (`assets.py`, at parse time);
> `out_dir` in step 5 (the per-mission writer). **Step 1 ships only what the existing
> `/api/tts` route consumes today: the voice allowlist + its 400 mapping.**

### 1. `agency_studio/engines/models.py` — DONE (step 1)
- Add `ALLOWED_VOICES: frozenset[str]` — the Kokoro v1.0 **en-us** voices (the
  `synthesize` backend forces `lang="en-us"`); default `af_heart`. Consumed now by both
  `/api/tts` (400) and `ModelManager.synthesize` (backend chokepoint).
- (No change to the existing full `IMAGE_MODELS` registry used by the GUI.)
- *Deferred to step 3:* `MARKER_IMAGE_MODELS = {"flux-schnell"}` lands **with** the
  marker parser that enforces it — added as dead code here it is a false guarantee.

### 2. `agency_studio/engines/local_media.py` — DONE (step 1, minimal)
- `synthesize`: validate `voice ∈ models.ALLOWED_VOICES` (raise `ValueError`) so a direct
  caller can't reach the backend with an unlisted voice — mirrors the existing model-id
  double-check in `generate_image`. Filenames stay uuid-only (traversal-safe).
- *Deferred to its consumer:* `out_dir` (step 5, the per-mission writer); dimension/step
  bounds + prompt/text caps are enforced at the **untrusted boundary** — the marker
  parser forces safe fixed dims and bounds length at parse time (step 3), and the HTTP
  routes already reject out-of-range dims/steps with a 400. The manager does **not**
  silently clamp/truncate the existing callers' inputs.

### 2b. `agency_studio/server.py` — DONE (step 1)
- `_handle_synthesize`: validate a client-supplied `voice` against
  `models.ALLOWED_VOICES` up front → **400** with the allowlist (mirrors the image
  handler), so an unknown voice is an actionable client error, not the generic 500 the
  manager's `ValueError` would become under `except Exception`. A falsy/omitted voice
  falls through to `synthesize`'s `af_heart` default.

### 3. `agency_studio/assets.py` (NEW — pure, offline-testable)
- `parse_markers(delivered: str, route: list[str]) -> list[AssetRequest]`: extract +
  validate + route-gate + cap. Pure, no I/O.
- `render(manager: ModelManager, requests, *, out_dir: Path, should_cancel) -> list[dict]`:
  for each request, check `should_cancel()` first (abort cleanly), call the injected
  `manager.generate_image/synthesize(out_dir=out_dir)`, batch by modality (all images
  then all TTS) to avoid evict/reload thrash, catch per-asset errors → record
  `{type, status: ok|failed|skipped, reason, url, model, voice, seconds, prompt, text,
  block}` (only the fields meaningful to that entry's type/status). Never
  raises. `block` is the source ```asset block's ordinal (0-based over all well-formed
  blocks), stamped by `parse_markers` so the rewrite can pair an entry back to its exact
  block by position.
- `rewrite_delivered(delivered, manifest) -> str`: **cosmetic** swap of each rendered
  marker block for a clean reference (`![caption](/media/...)` / audio caption), pairing
  block↔entry by the `block` ordinal — never by prompt/text content, which collides when
  two markers share text (a rejected block beside a valid one would cross-match). No
  semantic edit — keeps the text the Inspector verdict refers to intact in meaning;
  `_extract_sources` already ran inside `run_mission_cli`, so sourcing is unaffected.
- Takes an **injected** `ModelManager` so tests stub the backends.

### 4. `agency-kit/engines/cli_engine.py` (D1 — additive only)
- `run_mission_cli(..., asset_clause: Optional[str] = None)`.
- `_dept_prompt(dept, goal, dept_outputs, asset_clause=None)` and
  `_synth_prompt(..., asset_clause=None)`: append the clause verbatim only when set.
- **None ⇒ byte-identical** to standalone agency-kit (the on_event/should_cancel rule).

### 5. `agency-kit/runner_bridge.py` (D2 — additive only)
- `_run_and_persist(..., asset_clause=None, render_assets: Optional[Callable[[dict], None]] = None)`:
  - pass `asset_clause` to `run_mission_cli`;
  - after it returns, **if `render_assets and _last_verdict(dossier) == 'PASS'`**:
    `try: render_assets(dossier) except Exception: pass` (best-effort) — the callable
    mutates `dossier['assets']` (manifest) and cosmetically rewrites `dossier['delivered']`;
  - **then** `store.save` + `serialize_dossier` (so both persisted copies carry assets).
- `run()` and `resume()` both forward the two new params → uniform coverage.
- `_dossier_md`: additive `## Assets` section keyed on `dossier.get('assets')` (renders
  nothing when absent → byte-identical for non-studio runs).

### 6. `agency_studio/server.py` (wire it up)
- Build the `render_assets` closure over the **single warm** `self._media_manager()`,
  the studio assets root, and `cancel_event.is_set` (so Stop aborts mid-render). It
  writes into `studio_assets/missions/<dossier['mission_id']>/{images,audio}/`.
- Pass `asset_clause=<generic capability clause>` + `render_assets=<closure>` into
  `runner_bridge.run(...)` in `_worker`.
- Assets under `studio_assets/...` serve via the **existing** `/media` route +
  `path_inside(assets_root)` guard (a subtree of `assets_root` — no widened root, no new
  route, no traversal exposure). Confirm `_media_url` maps them.
- Emit SSE `{"phase": "asset", "status": "start|done|failed", "kind": "image|tts", "url": ...}`
  frames from inside the worker scope before the `None` sentinel; add asset URLs +
  partial-render state (`rendered N of M`) to the terminal `done` frame.

### 7. `app/studio/src/` (GUI)
- Handle the new `asset` SSE phase in the timeline; render a per-mission asset gallery
  from the manifest; show partial/failed state.

### 8. `agency-kit/exporter.py` (PDF — fix orphaning)
- `weasyprint.HTML(string=html, base_url=str(deliverable.parent))` and embed images as
  on-disk relative paths (copied next to the store `deliverable.md`) or `data:` URIs.
- Audio: render a `Generated audio: <file> (N s)` caption — a PDF cannot play sound.

## Test plan (offline, network/CLI/MLX stubbed — mirrors Wave 2)

- `assets.py` units: malformed-JSON skip; field stripping (`path`/`width` ignored);
  per-mission cap enforcement; route gate (image dropped when no marketing); model
  allowlist (boogu rejected at parse); voice allowlist; length bounds.
- `local_media` units (step 1, DONE): `synthesize` rejects an unlisted voice. (`out_dir`
  honored + safe-dim/length bounds move to the steps that introduce their callers — the
  marker parser bounds at parse time, the per-mission writer passes `out_dir`.)
- `server` unit (step 1, DONE): `/api/tts` with an unlisted voice → 400 + allowlist.
- `runner_bridge` units (stubbed `run_mission_cli` returning a marker-bearing
  `delivered`): PASS → assets rendered + manifest in dossier; non-PASS → skipped;
  `[media]` absent (`MediaUnavailable`) → recorded skip, **deliverable still persisted**;
  asset render raises → deliverable still persisted; `resume()` regenerates; `_dossier_md`
  byte-identical when `assets` absent.
- **Invariant test:** standalone agency-kit offline suite byte-identical with the new
  params defaulting to None.
- `should_cancel` fires mid-render → loop aborts, partial manifest recorded.

## Known residuals (documented, accepted for a local single-user tool)

- **Image content is not content-inspected.** The Inspector gates the *prompt text*
  (incidentally, via `delivered`), not the generated pixels. TTS is a faithful render of
  inspected text; image is the elevated-risk path — mitigated by the PASS gate +
  verbatim prompt + render-time route gate. Stated, not waved away.
- **Disk growth — capped (#21).** `studio_assets/` (per-mission `missions/<id>/` +
  the ad-hoc `images/`/`audio/` gallery) is now bounded by an oldest-first retention cap
  (`agency_studio/retention.py`), enforced after each render (`keep={mission_id}`) and once
  at startup. Budget defaults to 2 GiB, set with `--media-budget-mb` (0 disables). A recency
  grace protects assets touched in the last 5 min (an in-flight mission / a just-generated
  gallery image), and every eviction prints a one-line notice — it is **never silent**
  (including the first boot after upgrade, where an existing >2 GiB `studio_assets/` is
  trimmed; pass `--media-budget-mb 0` to keep everything). Transient `uploads/` is never
  walked (STT unlinks its own uploads). Tradeoff: evicting an old mission's dir breaks its
  live `/media` gallery links **and a later re-export of that mission to PDF loses its images**
  (the exporter reads assets from disk at export time, dropping a missing embed to its
  caption). A PDF exported *before* the prune is self-contained and unaffected.
- **Resume regenerates** assets under a fresh mission id (no reuse) — consistent with
  how resume already re-runs the whole mission. Documented, not a bug.
- **An unterminated `asset` opener survives rewrite.** `rewrite_delivered` (#19) strips every
  *well-formed* (properly closed) `asset` fence, but a malformed opener with **no** closing
  fence can't be bounded by `_scan_asset_blocks` (which, by its anti-swallow rule, emits it as
  passthrough text so it can't consume a following valid block). Its fence is therefore left
  in place: stripping would mean deleting the unbounded tail of real prose after it — a worse
  failure than a stray fence. This is a model-output error (the Inspector-passed text emitted
  an unclosed marker), not the parse-dropped / failed / skipped cases #19 resolves.

## Build order

1. **DONE** — `/api/tts` voice hardening: `ALLOWED_VOICES` (`models.py`), `synthesize`
   re-validation (`local_media.py`), and the route's 400 mapping (`server.py`). (The rest
   of the once-planned "chokepoint" — safe fixed dims, length caps, the marker model
   allowlist, `out_dir` — moves to the steps that consume it; see the scope note above.)
2. `agency_studio/assets.py` + its units — incl. `MARKER_IMAGE_MODELS`, marker length
   caps, and safe fixed dims enforced **at parse time** (the untrusted boundary).
3. `asset_clause` param in `cli_engine.py` + byte-identical test.
4. `render_assets` hook + `## Assets` in `runner_bridge.py` + tests.
5. Server wiring + `should_cancel` in the asset loop + SSE `asset` phase.
6. **DONE** — GUI asset timeline (`asset` SSE phase folded into `timeline.ts`) +
   per-mission gallery (`AssetGallery.tsx`, from `dossier.assets`) + the PDF orphan fix
   (`exporter._localize_assets` resolves `/media/<rel>` → on-disk file:// URIs, audio →
   caption; `export_pdf` gains an optional `assets_root`). **Wave 3 complete.**
