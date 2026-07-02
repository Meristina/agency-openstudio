# Real-test report — live validation of every element on the target Mac

> **Scope.** A live, end-to-end validation pass over every element of Agency Studio defined
> across Waves 0–6, run on the **Apple-Silicon reference machine (M4, 16 GB)** — the environment
> the offline test suite deliberately stubs. Where the offline suite proves the *wiring*, this
> pass exercises the *real* path: real MLX models, a real `claude` CLI mission loop, real HTTP.
>
> **Why it matters.** The offline suite (421 tests) is green everywhere, but it stubs the model /
> network / CLI boundary. Running the real paths surfaced **two genuine code bugs** and **one
> hardware limit** the offline suite could not see — exactly what a live pass is for. Both bugs
> are fixed and merged; the limit is documented.

## How to reproduce

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[media,studio,visual,boogu,pdf]"   # Mac only
brew install ffmpeg                                  # STT
agency-studio --host 127.0.0.1 --port 8765 --path .  # serves the built GUI + reads missions/
```
Then drive the HTTP API with `curl` (media/docs/visual endpoints) and `POST /api/mission`
(the SSE mission loop; needs the `claude` CLI logged in — real Opus spend).

## Result matrix

Legend: ✅ real path works · ⚠️ works-with-caveat / honest gap · ⛔ blocked (with cause).

### Waves 0–1 — server, GUI, mission core, security

| Element | Live test | Result |
|---|---|---|
| Server binds `127.0.0.1`, serves built GUI | `GET /` → `200` `index.html` | ✅ |
| History | `GET /api/missions` → 75→77 real dossiers | ✅ |
| Load a saved dossier | `GET /api/mission/{id}` → real goal / route / delivered | ✅ |
| **Mission core** (Mission A, goal → `solve`) | SSE `run → route → dept → synth → inspect → done`, **verdict PASS**, persisted to `missions/003-…` | ✅ |
| **Veto control loop (Constitution Art. IX)** (Mission B) | inspect **VETO → VETO → PASS-WITH-FIXES** over 3 iterations, then shipped with `residual_risk` ("Inspector did not PASS after 3 iteration(s)") | ✅ |
| **Stop mission** | `POST /api/mission/{run_id}/cancel` → `202` → SSE terminal `cancelled` → **no dossier saved** (count unchanged) | ✅ |
| Security — `path_inside()` | `curl --path-as-is` traversals (`/../etc/passwd`, `/media/../…`, `%2f`-encoded) → `404`, **zero `/etc/passwd` leak**; encoded path falls to the harmless SPA `index.html` | ✅ |
| Security — no CORS wildcard | `GET /api/models` response has **no `Access-Control-Allow-Origin: *`** | ✅ |
| PDF export | `GET /api/mission/{id}/pdf` → `501` clean (`[pdf]`/WeasyPrint absent) | ✅ (graceful) |

### Wave 2 — local multimodal

| Element | Live test | Result |
|---|---|---|
| TTS (Kokoro) | `POST /api/tts` → `.wav` in ~2.4 s | ✅ |
| STT (Whisper large-v3-turbo) | `POST /api/stt` on the TTS output → transcript in ~3.4 s | ✅ |
| `GET /api/models` | warm-model status + registries | ✅ |
| Warm / mutual-exclusion residency | resident switched `tts → stt → embed:…` across calls | ✅ |

#### Every registered model, individually

The image + embed registries each carry more than one model. All were exercised on the real
machine (not just the default):

| Kind | Model | Live test | Result |
|---|---|---|---|
| image | `flux-schnell` (default, 8-bit) | `POST /api/image` → 1024² PNG (~4.5 min) | ✅ |
| image | `flux2-klein-4b` (quantize-on-load) | `POST /api/image` → 1024² 8-bit PNG in **~85 s** | ✅ |
| image | `boogu-base` (experimental) | base + Qwen3-VL-8B conditioner **co-resident** → doesn't fit 16 GB → **swap-thrash (~19.7 GB swap), no diffusion step after ~9 min** | ⛔ **[#39]** |
| embed | `nomic-text-v1.5` (default, 768-dim) | `POST /api/docs` / `/api/visual` → real vectors | ✅ |
| embed | `bge-m3` (1024-dim, multilingual) | `ModelManager.embed(model="bge-m3")` → 2 vectors, **dim 1024**, resident `embed:bge-m3` | ✅ |
| stt | `whisper-large-v3-turbo` | `POST /api/stt` | ✅ |
| tts | `kokoro-v1.0` | `POST /api/tts` | ✅ |

So **6 of the 7 registered models work live**; only `boogu-base` fails, and only because it
exceeds the 16 GB memory budget (**[#39]**) — a hardware limit, not a code defect.

### Wave 4 — RAG / LocalDocs

| Element | Live test | Result |
|---|---|---|
| Doc ingest (`POST /api/docs`) | markitdown → chunk → embed (nomic) → `sqlite-vec` → **`201`** with a real chunk | ✅ (unblocked by **[#40]**) |
| Doc list / delete | `GET /api/docs` | ✅ |

### Wave 6 — visual RAG, and the mission opt-in flags

| Element | Live test | Result |
|---|---|---|
| Caption (Qwen2.5-VL, local MLX) | probe + `POST /api/visual` → accurate caption of a generated image | ✅ (fixed by **[#37]**) |
| **Visual RAG ingest** (`POST /api/visual`) | caption → embed → store → **`201`** (`lake.png`, 1 chunk) | ✅ |
| `GET /api/graph` · `/api/personas` · `/api/mcp` · `/api/visual` | read-side stats, no extra needed | ✅ (all `200`) |
| Mission flag **`visual`** (PixelRAG) | SSE `visual: done`, **hits 1 → `lake.png`** — the goal ("mountain lakes at sunrise") retrieved the ingested image's caption as context | ✅✅ **fully proven** live |
| Mission flag **`web_search`** | with `[web]` (ddgs) installed → SSE `websearch: done`, **hits 5, real result URLs** ("Top Marketing Strategies for Outdoor Brands", …) | ✅ **proven active** (real network fetch) |
| Mission flag **`mcp`** (resources) | with the `mcp` SDK + a real `@modelcontextprotocol/server-everything` in `mcp.json` → SSE `mcp: done`, **hits 5** (`architecture.md`, `features.md`, … from server `everything`) | ✅ **proven active** |
| Mission flag **`mcp_tools`** | same MCP server → SSE `mcp_tools: done`, **servers `["everything"]`** (a `--mcp-config` was built for the claude CLI) | ✅ **proven active** |
| Mission flag **`personas`** | a curated `personas/marketing/brand-strategist.md` in the store → SSE `persona: done`, **depts `["marketing"]`** (doctrine injected into the dept/synth prompts) | ✅ **proven active** |
| Mission flag **`knowledge`** / doc `retrieval` | the uninstallable-extra blocker is **removed** (**[#43]/[#45]**): extraction now runs on the `claude` CLI brain (`ClaudeCliExtractor`, no extra) by default, so a graph **can** be built with only the CLI on PATH. An **optional on-device backend** (GLiNER2, the `[kg]` extra; **[#47]/[#48]**) also ships for airgapped builds (`AGENCY_STUDIO_KG_BACKEND=gliner2`), hardened against the real `gliner2` API (dual output shape; **overlapping sliding windows** over the encoder limit so a long dossier is no longer head-truncated, **[#50]**; per-source triple dedup at the store). Neither live path was run here — the CLI build over real docs and the GLiNER2 model run are both manual steps (validated offline via stubbed boundaries; the GLiNER2 model is torch/Mac-deferred like Wave 2) | ✅ **unblocked** (two backends, build path buildable; live runs deferred) |

> **How the flags were proven active** (a second pass, after the first only saw them degrade): installed `[web]` (ddgs) and the `mcp` SDK, curated a persona file, wrote an `mcp.json` pointing at a real `@modelcontextprotocol/server-everything` stdio server, and ingested an image — then ran one mission with all flags on and read the pre-route SSE phases (cancelling before the full run to save Opus). **5 of 6 flags reached the active `done` state with real data**; only `knowledge` was not live-run — its build path is now **unblocked** ([#43]/[#45]: extraction moved to the `claude` CLI brain, no extra) with an optional on-device GLiNER2 backend too ([#47]/[#48]), the live build/model run remaining a manual step.
| Mission flag **`video`** (seedance) | `POST /api/video` → `404` (video is mission-only, not a standalone endpoint); render bridge + gates proven offline. In the live marketing mission **the departments did not emit an `asset` marker**, so no render fired — the `asset_clause` is optional ("Omit when no asset is warranted"). | ⚠️ wiring proven offline; **no marker emitted by the mission in the time budget** |

## Bugs found and fixed (this live pass)

| Ref | Bug | Fix |
|---|---|---|
| **#37** (merged) | `visual._run_local` passed raw bytes + a non-templated prompt to `mlx_vlm.generate` → `tuple index out of range` (the "validated live, deferred" caption path never worked with mlx-vlm 0.6.3) | image → temp-file path, `apply_chat_template(num_images=1)`, `image=[path]`, `.text`; regression test locks the surface |
| **#40** (merged, closes #38) | Embed path dead: `[studio]` missing `einops`; and transformers 5.x (needed by `[visual]`'s mlx-vlm) removed `batch_encode_plus` that mlx-embedding-models 0.0.11 still calls | added `einops`; `_shim_legacy_tokenizer` aliases `batch_encode_plus → __call__` (no `transformers<5` pin, which would break mlx-vlm) — `POST /api/docs` now `201` |
| **#39** (open) | `boogu-base` swap-thrashes on the 16 GB reference Mac (two heavyweight models co-resident) | documented the constraint in `models.py` (comment + `note` ">16 GB RAM"); guardrail / >16 GB re-validation is follow-up |

Also hardened, as a side effect of installing the extras on the reference Mac: several
"extra-absent → 501" tests assumed the extra was **absent** (offline CI) and failed when it was
actually installed. They now force the import/loader absent deterministically (the `#36` pattern),
so the suite is green whether or not the optional extras are present.

## Post-pass hardening (offline code-quality — still needs the same live validation)

These landed **after** the live pass, from a code audit of the deferred (Mac-only) paths — not
from a live run. They are offline-tested only; each still awaits the live validation noted above,
and this row is here so the next Mac pass knows what changed underneath it.

| Ref | Change | What the next live pass should confirm |
|---|---|---|
| **#50** (merged) | GLiNER2 relation extraction slides **overlapping windows** over long dossiers instead of head-truncating at `MAX_GLINER_CHARS`; duplicate triples are deduped **per source at the store** (weight counts sources, not windows/restatements) | On the Mac with `[kg]`: build a graph from a **long** (>2 KB) mission dossier and confirm relations from its tail appear in the graph, and a repeated relation has weight 1 per source |
| **#51** (merged) | Shape-robust adapters for the two deferred parse surfaces: `visual._caption_text` tolerates mlx-vlm `generate`'s `str` / `GenerationResult` / tuple returns; `mcp_client._text_of` drops non-`str`/blob resource parts instead of crashing `"\n".join` | On the Mac: confirm real mlx-vlm 0.6.3 captions still read correctly, and a real MCP server's blob/binary resource parts don't break `mcp: done` |
| **#52** (merged) | Return-type annotations on the internal mission-composition helpers (`server._resolve_*`, `assets` scan generators) | Nothing — annotation-only, no runtime effect |
| **#54** (merged) | `POST /api/graph/build` now **replaces** instead of accumulating: `GraphRetriever.rebuild` clears the store and re-extracts, so a re-run over unchanged docs/history no longer re-counts each source (weight inflation) or strands triples from since-deleted docs/missions. The replace is **failure-safe** — extraction runs to completion first, so an unreachable brain / runtime error raises with the previous graph intact (never wipes a good graph) | ✅ **live-validated on the reference Mac** (real `ClaudeCliExtractor`, real `claude` CLI): a real build extracted 3 triples (4 nodes / 3 edges); a **second** `rebuild` over the same source returned **identical counts _and_ weights** (not doubled — the fix); rebuilding after the source was removed **emptied** the graph (0/0, triples pruned). Third item — forcing the CLI unreachable mid-run — remains unit-only (`test_rebuild_failure_leaves_previous_graph_intact`); the extract-all-then-clear ordering is the same code path |

## Honest gaps / not covered live

- **An `asset` render inside a real mission.** The render bridge, marker parse/gate, `video`/image
  branches, and `asset` SSE frames are all covered by offline tests, and `/api/video`→404 confirms
  video is mission-only. But a real department did not *choose* to emit an image/video marker in
  the marketing mission run, so an end-to-end "department emits marker → studio renders → deliverable
  rewritten" was not observed. Cause is legitimate (the capability clause is optional), not a defect.
- **The `knowledge` flag's active path.** Unblocked (**[#43]/[#45]**): the uninstallable
  `hyper-extract` extra was dropped and extraction now runs on the `claude` CLI brain
  (`ClaudeCliExtractor`, no extra) by default, so a graph is buildable with only the CLI on PATH.
  An **optional on-device backend** (GLiNER2, the `[kg]` extra; **[#47]**, hardened in **[#48]**
  against the real `gliner2` dual output shape, then **[#50]** replacing the encoder-window
  head-truncation with overlapping sliding windows + per-source dedup) also ships for airgapped
  builds (`AGENCY_STUDIO_KG_BACKEND=gliner2`). Neither live path was run here — the CLI build over
  real docs and the GLiNER2 model run are manual steps (GLiNER2 is torch/Mac-deferred like Wave 2).
  The default **CLI build path is now live-proven** on the reference Mac: a real
  `ClaudeCliExtractor` build over sample text extracted correct triples into the graph, and the
  **[#54]** rebuild lifecycle (replace, not accumulate; prune removed sources) was confirmed live —
  identical counts/weights on re-run, and an emptied graph after the source was removed. What is
  **still not live-run** is the mission-time retrieval end-to-end (seed → 1-hop neighbourhood →
  `context_clause` injection into a real mission) and the GLiNER2 backend. (The other four flags —
  `web`, `mcp` resources, `mcp_tools`, `personas` — were **proven active** with their backends
  installed; see the Wave-6 table.)
- **The cloud paths** — seedance video render (`_run_cloud`) and the optional cloud VLM — remain
  network-deferred (no live endpoint / API key), as designed.

## Verdict — and an honest coverage split

Not everything is "green". Being precise about what the live pass actually proved:

- **Proven working on the live path** — server + GUI, history, dossier load, the full `route →
  departments → synthesis → inspector` loop **including a real veto → revise → PASS-WITH-FIXES
  cycle**, Stop-with-no-persistence, the security guards, TTS, STT, **6 of 7 models** (both FLUX
  image models + both embed models + Whisper + Kokoro), doc RAG ingest, and **5 of 6 mission
  flags** with their backends installed — `visual` (image caption→retrieval), `web_search` (real
  ddgs results), `mcp` resources + `mcp_tools` (a real `server-everything` MCP server), and
  `personas` (a curated store) all reached the active `done` state with real data.
- **Partly live-proven, rest deferred** — the `knowledge` flag: the uninstallable-extra blocker is
  gone (**[#43]/[#45]** — default extraction runs on the `claude` CLI brain, no extra; plus an
  optional on-device GLiNER2 backend, **[#47]/[#48]**, whose long-dossier handling is now
  overlapping sliding windows rather than head-truncation, **[#50]**). The **CLI graph build is now
  live-proven** on the reference Mac — a real `ClaudeCliExtractor` extracted correct triples, and
  the **[#54]** rebuild lifecycle (idempotent replace + prune) was confirmed live. Still deferred:
  the mission-time retrieval end-to-end (seed → neighbourhood → `context_clause` in a real mission)
  and the GLiNER2 model run.
- **Not exercised live** — an `asset` marker actually emitted-then-rendered inside a mission (no
  department chose to emit one), the real PDF render (`[pdf]` absent → 501), and the cloud paths
  (seedance render / cloud VLM, network-deferred by design).
- **Failed** — `boogu-base` (OOM / swap on 16 GB, **[#39]**).

The live pass paid for itself by catching two real bugs (#37, #40) and one hardware limit (#39)
the offline suite (421 tests) could not surface. But "the offline suite is green" and "every feature
is proven on real hardware" are **different claims** — this report is the honest boundary between
them.
