# Real-test report — live validation of every element on the target Mac

> **Scope.** A live, end-to-end validation pass over every element of Agency Studio defined
> across Waves 0–6, run on the **Apple-Silicon reference machine (M4, 16 GB)** — the environment
> the offline test suite deliberately stubs. Where the offline suite proves the *wiring*, this
> pass exercises the *real* path: real MLX models, a real `claude` CLI mission loop, real HTTP.
>
> **Why it matters.** The offline suite (387 tests) is green everywhere, but it stubs the model /
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
| Mission flag **`web_search`** | SSE `websearch: skipped` ("web-search extra not installed") | ⚠️ **skip-only** (the `[web]` backend was absent — the *active* fetch path is NOT proven, only the degrade) |
| Mission flag **`mcp`** (resources) | SSE `mcp: done`, hits 0 (no MCP servers configured) | ⚠️ **empty-only** (no server → 0 resources; the *active* read path is NOT proven) |
| Mission flag **`mcp_tools`** | SSE `mcp_tools: skipped` ("no enabled MCP servers configured") | ⚠️ **skip-only** (needs a real MCP server) |
| Mission flag **`personas`** | SSE `persona: skipped` ("no personas curated in the store") | ⚠️ **skip-only** (needs a curated persona store) |
| Mission flag **`knowledge`** / doc `retrieval` | no phase emitted (no graph built / no docs in this store) | ⚠️ **not-exercised** (correct opt-in gate, but the *active* retrieval was never run) |
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

## Honest gaps / not covered live

- **An `asset` render inside a real mission.** The render bridge, marker parse/gate, `video`/image
  branches, and `asset` SSE frames are all covered by offline tests, and `/api/video`→404 confirms
  video is mission-only. But a real department did not *choose* to emit an image/video marker in
  the marketing mission run, so an end-to-end "department emits marker → studio renders → deliverable
  rewritten" was not observed. Cause is legitimate (the capability clause is optional), not a defect.
- **`web` / `mcp` / `knowledge` / `personas` flags with their backends present.** Verified only in
  the graceful-skip state (those extras / a real MCP server / a built graph / curated personas were
  not set up). The skip path is the tested behaviour; the active path needs those resources.
- **The cloud paths** — seedance video render (`_run_cloud`) and the optional cloud VLM — remain
  network-deferred (no live endpoint / API key), as designed.

## Verdict — and an honest coverage split

Not everything is "green". Being precise about what the live pass actually proved:

- **Proven working on the live path** — server + GUI, history, dossier load, the full `route →
  departments → synthesis → inspector` loop **including a real veto → revise → PASS-WITH-FIXES
  cycle**, Stop-with-no-persistence, the security guards, TTS, STT, **6 of 7 models** (both FLUX
  image models + both embed models + Whisper + Kokoro), doc RAG ingest, and the **`visual`** flag
  end-to-end (real caption → embed → retrieval into a mission).
- **Only seen degrading, NOT proven functional** — the `web_search`, `mcp`, `mcp_tools`,
  `knowledge`, and `personas` flags. Their backends (`[web]`, a real MCP server, a built graph,
  a curated persona store) were not set up, so only the skip / empty path ran. A ✅ on these means
  "degrades correctly", **not** "the feature works".
- **Not exercised live** — an `asset` marker actually emitted-then-rendered inside a mission (no
  department chose to emit one), the real PDF render (`[pdf]` absent → 501), and the cloud paths
  (seedance render / cloud VLM, network-deferred by design).
- **Failed** — `boogu-base` (OOM / swap on 16 GB, **[#39]**).

The live pass paid for itself by catching two real bugs (#37, #40) and one hardware limit (#39)
the 387-test offline suite could not surface. But "the offline suite is green" and "every feature
is proven on real hardware" are **different claims** — this report is the honest boundary between
them.
