# Real-test report — live validation of every element on the target Mac

> **Scope.** A live, end-to-end validation pass over every element of Agency Studio defined
> across Waves 0–6, run on the **Apple-Silicon reference machine (M4, 16 GB)** — the environment
> the offline test suite deliberately stubs. Where the offline suite proves the *wiring*, this
> pass exercises the *real* path: real MLX models, a real `claude` CLI mission loop, real HTTP.
>
> **Why it matters.** The offline suite (421 tests) is green everywhere, but it stubs the model /
> network / CLI boundary. Running the real paths surfaced **two genuine code bugs** and **one
> hardware limit** the offline suite could not see — exactly what a live pass is for. Both bugs
> are fixed and merged; the limit is documented. A later live run also surfaced a **missing
> capability** rather than a bug — a mission that dies mid-flight lost all its work — which became
> the **checkpoint/resume** feature, itself then live-validated (see the crash-recovery section).

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

> **Live-environment caveat — image generation is the memory peak; don't co-run other heavy apps.**
> During a later sweep, a **macOS jetsam (OOM) kill** fired at 21:58 while `POST /api/image` was
> generating a FLUX image. The jetsam snapshot showed the studio server (`python3.12`) resident at
> **~12 GB** during FLUX generation, colliding with a **BlueStacks Android emulator at ~8 GB** the
> user had open — ~20 GB of demand on a 16 GB machine, so jetsam killed the largest process (the
> studio server). This is **not a code defect**: it's the same 16 GB mutual-exclusivity limit as
> **[#39]**, aggravated by an *external* multi-GB app the studio can't see (it only mutually-excludes
> its own models). The image/visual models (~12 GB) are the only heavy tenants — TTS/STT, embeddings,
> and every mission flag (RAG/graph/web/MCP/personas) are light. **Operational guidance:** close
> other multi-GB apps (emulators, extra IDEs) before running `POST /api/image` / `POST /api/visual`
> on the 16 GB reference Mac.

### Wave 4 — RAG / LocalDocs

| Element | Live test | Result |
|---|---|---|
| Doc ingest (`POST /api/docs`) | markitdown → chunk → embed (nomic) → `sqlite-vec` → **`201`** with a real chunk | ✅ (unblocked by **[#40]**) |
| Doc list / delete | `GET /api/docs` | ✅ |

### Wave 6 — visual RAG, and the mission opt-in flags

| Element | Live test | Result |
|---|---|---|
| Caption (Qwen3-VL-8B, local MLX) | probe + `POST /api/visual` → accurate caption of a generated image | ✅ (fixed by **[#37]**) |
| **Visual RAG ingest** (`POST /api/visual`) | caption → embed → store → **`201`** (`lake.png`, 1 chunk) | ✅ |
| `GET /api/graph` · `/api/personas` · `/api/mcp` · `/api/visual` | read-side stats, no extra needed | ✅ (all `200`) |
| Mission flag **`visual`** (PixelRAG) | SSE `visual: done`, **hits 1 → `lake.png`** — the goal ("mountain lakes at sunrise") retrieved the ingested image's caption as context | ✅✅ **fully proven** live |
| Mission flag **`web_search`** | with `[web]` (ddgs) installed → SSE `websearch: done`, **hits 5, real result URLs** ("Top Marketing Strategies for Outdoor Brands", …) | ✅ **proven active** (real network fetch) |
| Mission flag **`mcp`** (resources) | with the `mcp` SDK + a real `@modelcontextprotocol/server-everything` in `mcp.json` → SSE `mcp: done`, **hits 5** (`architecture.md`, `features.md`, … from server `everything`) | ✅ **proven active** |
| Mission flag **`mcp_tools`** | same MCP server → SSE `mcp_tools: done`, **servers `["everything"]`** (a `--mcp-config` was built for the claude CLI) | ✅ **proven active** |
| Mission flag **`personas`** | a curated `personas/marketing/brand-strategist.md` in the store → SSE `persona: done`, **depts `["marketing"]`** (doctrine injected into the dept/synth prompts) | ✅ **proven active** |
| Mission flag **`knowledge`** / doc `retrieval` | **now fully live-proven** (Jul 2 evening sweep): `POST /api/graph/build` ran the real `ClaudeCliExtractor` over an ingested doc + mission history → a **202-node / 139-edge** graph; then a mission with `knowledge` on emitted SSE `graph: done`, **hits 9** entities seeded on the goal (`newsletter signup conversion`, `April redesign`, `marketing department`, …). The default CLI build needs no extra; the optional on-device GLiNER2 backend (**[#47]/[#48]/[#50]**, `[kg]` extra) stays torch/Mac-deferred (not exercised) | ✅✅ **fully proven** live (CLI build + retrieval) |

> **How the flags were proven active** (all six, across two sweeps): installed `[web]` (ddgs) and the `mcp` SDK, curated a persona file, wrote an `mcp.json` pointing at a real `@modelcontextprotocol/server-everything` stdio server, ingested a doc + an image, and built the knowledge graph — then ran one mission with **all six flags on** and read the pre-route SSE phases (cancelling before the departments to save Opus). **All 6 flags reached the active `done` state with real data** (`retrieval`/`websearch`/`mcp`/`graph`/`visual`/`mcp_tools`/`persona`); the `knowledge` live gap noted in the earlier pass is now **closed** (see the Jul 2 evening full sweep below). Only the GLiNER2 on-device KG backend remains torch/Mac-deferred.
| Mission flag **`video`** (seedance) | `POST /api/video` → `404` (video is mission-only, not a standalone endpoint); render bridge + gates proven offline. In the live marketing mission **the departments did not emit an `asset` marker**, so no render fired — the `asset_clause` is optional ("Omit when no asset is warranted"). | ⚠️ wiring proven offline; **no marker emitted by the mission in the time budget** |

## Bugs found and fixed (this live pass)

| Ref | Bug | Fix |
|---|---|---|
| **#37** (merged) | `visual._run_local` passed raw bytes + a non-templated prompt to `mlx_vlm.generate` → `tuple index out of range` (the "validated live, deferred" caption path never worked with mlx-vlm 0.6.3) | image → temp-file path, `apply_chat_template(num_images=1)`, `image=[path]`, `.text`; regression test locks the surface |
| **#40** (merged, closes #38) | Embed path dead: `[studio]` missing `einops`; and transformers 5.x (needed by `[visual]`'s mlx-vlm) removed `batch_encode_plus` that mlx-embedding-models 0.0.11 still calls | added `einops`; `_shim_legacy_tokenizer` aliases `batch_encode_plus → __call__` (no `transformers<5` pin, which would break mlx-vlm) — `POST /api/docs` now `201` |
| **#39** (open on 16 GB) | `boogu-base` swap-thrashes on the 16 GB reference Mac (two heavyweight models co-resident). **Two distinct blockers**, now understood separately: (1) **memory** — Boogu-Image (~10B) + its Qwen3-VL-8B `mlx_vlm` conditioner co-resident ≈ 20 GB, fatal on 16 GB (it never reached a first diffusion step); (2) **MLX-VLM thread affinity** — boogu drives the same `mlx_vlm` multi-stream path that hard-crashed `flux2-klein-4b` through the threaded server (**[#67]**), so it had a *second*, latent crash blocker that the memory wall masked. | (1) documented in `models.py` (comment + `note` ">16 GB RAM"); still open — a hardware limit, re-validate only on a **>16 GB** Mac. (2) **fixed by [#67]** (all device work on one worker thread), so a >16 GB re-validation now clears the thread blocker too and only has to answer the memory question. |

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

## Mission checkpoint / resume (crash-recovery) — born from a live failure, then live-validated

**What prompted it.** During this live pass, a full multi-department mission (`solve → product →
marketing`, ~19.5 min of real Opus) died at synthesis iteration 3 on a transient `API Error:
Connection closed mid-response`. Everything was lost — routing + all three completed departments +
two synth→inspect cycles — because the mission loop persisted only once, *after* it fully returned.
That's not a bug (the code did what it said); it's a **missing capability** a live run exposes and
an offline suite never would.

**The fix** (agency-kit **#12** + studio **#57**, both merged): two additive, default-None engine
hooks — `on_checkpoint` (a snapshot after every completed phase) and `resume_state` (re-enter a
mission mid-flight) — plus studio-side atomic checkpoint persistence under
`docs_root/checkpoints/`, a `resume_from` on `POST /api/mission`, `GET`/`DELETE /api/checkpoints`,
and a GUI « Reprendre la mission » button. Checkpoints fire **only after a verdict is recorded**
(so a snapshot's `delivered` was always inspected) and the iteration budget **continues** on
resume — Art. IX holds by construction. Delete on a clean finish or an explicit Stop; **keep** on
an error or a disconnect.

**Live crash-resume drill (reference Mac, real `claude` engine).** Started the studio, ran a real
`solve` mission, then **`SIGKILL`-ed the in-flight engine subprocess the instant synthesis began**
— the exact class of failure that lost the work above:

| Checkpoint of the drill | Observed | Result |
|---|---|---|
| Real mission to the crash point | `route → solve` dept (**188 s** of real work) → synthesis start | ✅ |
| Engine killed mid-synthesis | `_call` raised `RuntimeError: CLI engine 'claude' exited -9` | ✅ |
| Resumable error terminal frame | stream ended `{"phase":"error","resumable":true,"checkpoint":…}` — not a silent loss | ✅ |
| Checkpoint on disk | `checkpoints/<id>.json`: phase `dept`, route `["solve"]`, **full 18 671-char solve output preserved**, iteration 0 | ✅ |
| Resume skips completed work | at **0.0 s** replayed `route` + `dept solve` as `resumed:true` — no re-route, no re-running the 188 s department | ✅ |
| Veto loop continues on resume | synth 1 → **PASS-WITH-FIXES** → synth 2 → **PASS** (the Art. IX loop ran faithfully across the resume boundary) | ✅ |
| Clean finish | `done`, verdict **PASS**, dossier saved (built on the preserved solve output) | ✅ |
| Cleanup | checkpoints dir empty, `GET /api/checkpoints` → `[]` | ✅ |

The failure that first cost ~19 minutes now costs **nothing**: the completed department work is
preserved on disk and the resume picks up at synthesis without re-paying routing or the department.
Offline suites cover it too (agency-kit +11 tests, studio +12); the drill is the live proof.

## Full live validation sweep (Jul 2 evening) — every model, every path, on the M4

A single end-to-end pass that exercised **every runnable surface** on the reference Mac in one
session: all local models, all mission pipeline flags, and the checkpoint/resume loop. At the time
the only untested surfaces were the two **cloud** flows and the GLiNER2 backend — since then the
**cloud VLM has been live-validated** (see "Cloud backends" below), leaving only the seedance video
render (needs a Volcengine Ark key) and the optional GLiNER2 on-device KG backend (now installed +
tested — also below) as the last deferred items.

**Models — 7/7 loadable pass** (serial, honouring 16 GB mutual-exclusion):

| Model | Live result |
|---|---|
| TTS `kokoro-v1.0` | ✅ 3.19 s wav in ~4 s |
| STT `whisper-large-v3-turbo` | ✅ transcribed the wav back verbatim, ~4 s |
| image `flux-schnell` | ✅ 1024² PNG, 284 s |
| image `flux2-klein-4b` | ✅ 1024² PNG, 91 s |
| embed `nomic-v1.5` (768-dim) | ✅ via `POST /api/docs`, 6 s |
| embed `bge-m3` (1024-dim) | ✅ 2 vectors, dim 1024, resident `embed:bge-m3`, 5 s |
| visual VLM `Qwen3-VL-8B` | ✅ captioned a real image + embedded (2 chunks), 29 s |
| `boogu-base` | ⛔ known OOM ([#39], hardware — excluded; its separate MLX-VLM thread crash is fixed by [#67]) |

**Pipeline flags — all active in one all-flags mission** (pre-route phases read, then cancelled
before the departments):

| Flag | Live SSE result |
|---|---|
| `retrieval` (RAG/nomic, auto) | ✅ `hits 1` → `onboarding.txt` |
| `web_search` (ddgs) | ✅ `hits 5`, real URLs |
| `mcp` resources | ✅ `hits 5` from real `server-everything` (npx: `architecture.md`, `features.md`, …) |
| `knowledge` (graph) | ✅ built **202 nodes / 139 edges**, then `hits 9` entities on the goal |
| `visual` (PixelRAG) | ✅ `hits 2` → the Qwen3-VL image caption |
| `mcp_tools` | ✅ `servers: ["everything"]` (`--mcp-config` built) |
| `personas` | ✅ `depts: ["marketing"]` (curated brand-strategist injected) |

**Checkpoint/resume — re-proven fresh:** a `solve` mission crashed at synthesis (engine `SIGKILL`)
→ `error {resumable:true}` + a `GET /api/checkpoints` listing (phase `dept`, `depts_done:["solve"]`,
the 185 s department output preserved) → **resume** skipped `route`+`solve` at 0.0 s → synth→inspect
(`PASS-WITH-FIXES` → `PASS`) → `done` → checkpoint deleted. The **explicit-cancel** disposition was
also confirmed live (the all-flags mission's checkpoint was deleted on its endpoint cancel).

**Gates confirmed as designed:** `POST /api/video` → `404` (video is mission-only, not a standalone
endpoint); PDF export stays a graceful `501` with `[pdf]`/WeasyPrint absent.

_Note for a follow-up:_ the `knowledge` build produced 202 nodes including entities from the user's
**real global mission history** — the sweep server ran without HOME isolation, so this is expected
here, but it's worth a separate check that `GraphRetriever.build_from_history`'s project-scoping
matches the intended per-project vs global semantics. (Now fixed — a strict-scope build option so
the graph only absorbs missions explicitly stamped to the project.)

## Cloud backends + the last on-device extras (Jul 3)

Two deferred surfaces were *unimplemented stubs*, not just un-keyed: `seedance._run_cloud` (video)
and `visual._run_cloud` (VLM) each raised `Unavailable` after the key check. Both are now
**implemented** (stdlib `urllib` clients, source-driven from each provider's API) and offline-tested;
the video/VLM model ids are env-overridable (`AGENCY_STUDIO_VIDEO_MODEL` / `…_VISUAL_MODEL`) since
Ark/DashScope ids are account-specific.

| Element | Live test | Result |
|---|---|---|
| **Cloud VLM** (DashScope Qwen-VL) | with `AGENCY_STUDIO_VISUAL_API_KEY` set: `visual._run_cloud` on a test image (`qwen-vl-max`, `dashscope-intl`) → an accurate caption ("red circle on blue, 'SALE -50%', a promotional message"); and `POST /api/visual?cloud=1` → **`201`**, cloud caption → embed → stored | ✅ **live-proven** |
| **Cloud video** (seedance / Volcengine Ark) | client implemented (create-task → poll → download, https-checked); offline-tested. Live render **deferred** — needs a Volcengine Ark key (China region; BytePlus international would need an endpoint override) | 🟡 implemented; live render deferred (key) |
| **PDF export** (`[pdf]`) | installed `weasyprint` + `markdown`; `GET /api/mission/{id}/pdf` → **`200`**, a valid 67 KB PDF. macOS needs `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` at launch (homebrew glib/pango) | ✅ **live-proven** |
| **GLiNER2** on-device KG (`[kg]`) | installed `gliner2` (torch); `AGENCY_STUDIO_KG_BACKEND=gliner2` extracted 10 triples from sample text with **no `claude` CLI**, RAM safe (~1.3 GB) | ✅ **live-proven** |

## Post-#64 live re-validation (Jul 3) — real mission + the four core models, BlueStacks-safe

After the Waves 0–6 audit-hardening pass (**#64**), a fresh live run on the reference Mac to confirm
the fixes hold on the real path — deliberately run with **BlueStacks closed** for the FLUX step
(the documented 16 GB FLUX + external-app jetsam caveat, **[#61]**); the mission + light models ran
first with BlueStacks still up, since they carry no local-model RAM.

**A full three-department mission, run to completion:** `POST /api/mission` with a B2B-SaaS goal →
`route ["solve","product","marketing"]` → all three departments (solve 208 s · product 399 s ·
marketing 624 s) → **a real veto loop: VETO (it.1) → VETO (it.2) → PASS-WITH-FIXES (it.3)** →
`delivered:true`, dossier persisted (`missions/006-…`) and listed by the API. Total ~1185 s, 21 SSE
frames. The inspector's live web spot-checks **caught an untraceable "~75 % first-week churn /
NetSuite" figure and forced its retraction** across iterations — sourcing discipline working on real
data, not a stub.

**The four core local models, re-proven serial (16 GB mutual-exclusion held throughout):**

| Model | Live result | Resident after |
|---|---|---|
| TTS `kokoro` | ✅ 2.3 s wav | — |
| STT `whisper-large-v3-turbo` | ✅ TTS→STT round-trip, 3.5 s | `stt` |
| embed `nomic-v1.5` | ✅ `POST /api/docs` → `201`, 1 chunk | `embed:nomic-text-v1.5` |
| image `flux-schnell` (8-bit) | ✅ 768² PNG, 215 s, **no crash** | `flux-schnell` |

Each load **evicted the prior resident** as designed. FLUX loaded with BlueStacks closed: a load
spike to ~12 % free RAM, then steady ~31 %, never a jetsam — slow (~52 s/step, swap on 16 GB) but it
completed and produced a coherent, on-prompt hero image.

**First live sighting of a department emitting an `asset` marker — and the render gate working as
designed.** The marketing department *chose* to emit a `{"type":"image", …}` marker (the missing half
of the "Honest gaps" note below). It was **not** rendered because the mission ended `PASS-WITH-FIXES`,
and the render bridge is gated on the **exact `PASS` token** (`runner_bridge.py:200` — deliberate:
assets render only for a cleanly-passed deliverable). So the raw marker correctly stayed in the
deliverable and no FLUX render fired mid-mission. This is the documented gate behaving as specified —
which is why FLUX was validated deterministically via `/api/image` instead of gambling on a clean-PASS
mission. Half the gap is now closed (a real marker was emitted); the render-then-rewrite half still
awaits a mission that both emits a marker **and** earns a clean `PASS`.

**A server-crashing bug caught + fixed ([#67]) — `flux2-klein-4b` Metal thread affinity.** Rendering
klein-4b via the threaded server didn't just fail, it **killed the whole process**: MLX's Metal
streams are thread-affine, so driving a warm model from a fresh `ThreadingHTTPServer` request thread
aborted with `RuntimeError: There is no Stream(gpu, N) in current thread` → an uncaught `libc++abi`
terminate (not a catchable 500). `flux-schnell` happened to survive the pattern; the FLUX.2 path did
not. Confirmed by repro: klein renders fine **single-threaded** (~15 s from cache) but crashes through
the threaded server. **Fix:** `ModelManager` now runs every model load + inference on **one dedicated
worker thread** (`ThreadPoolExecutor(max_workers=1)`, stdlib) — streams stay valid, and it subsumes
the old inference lock; the cloud video render stays off the worker. Live-validated: klein-4b
512²/2-steps now returns `200` in **~12–15 s** through the threaded server, warm-reused across request
threads, zero crashes. This also removes boogu's *second* (latent) blocker — see **[#39]** above.

## Honest gaps / not covered live

- **An `asset` render inside a real mission — half closed (Jul 3).** The render bridge, marker
  parse/gate, `video`/image branches, and `asset` SSE frames are all covered by offline tests, and
  `/api/video`→404 confirms video is mission-only. A department **has now been observed emitting an
  image marker** on a real mission (the marketing dept, Jul 3 re-validation) — closing the "did a
  department ever choose to emit one?" half. The *render-then-rewrite* half is still unobserved,
  because that mission ended `PASS-WITH-FIXES` and the bridge renders only on the **exact `PASS`
  token** (`runner_bridge.py:200`, by design). So an end-to-end "department emits marker → studio
  renders → deliverable rewritten" needs a mission that both emits a marker **and** earns a clean
  `PASS`. Cause is legitimate (the capability clause is optional; the render gate is deliberate),
  not a defect.
- **The `knowledge` flag's active path — now CLOSED** (Jul 2 evening sweep). Both halves are
  live-proven on the reference Mac: the CLI **build** (`POST /api/graph/build` → real
  `ClaudeCliExtractor` → a 202-node / 139-edge graph; plus the **[#54]** rebuild lifecycle —
  idempotent replace + prune — confirmed live) **and** the mission-time **retrieval** end-to-end
  (a mission with `knowledge` on emitted `graph: done`, hits 9 entities seeded on the goal →
  `context_clause` injection). The only remaining KG gap is the **optional GLiNER2 on-device
  backend** (the `[kg]` extra; **[#47]/[#48]/[#50]**), which stays torch/Mac-deferred — not
  exercised, since the default CLI path needs no extra.
- **The cloud paths** — both `_run_cloud` clients are now implemented + offline-tested (Jul 3). The
  **cloud VLM is live-proven** (DashScope Qwen-VL). Only the **seedance video render** remains
  network-deferred — the client is done, but a live render needs a Volcengine Ark key (China region).

## Verdict — and an honest coverage split

Not everything is "green". Being precise about what the live pass actually proved:

- **Proven working on the live path** — server + GUI, history, dossier load, the full `route →
  departments → synthesis → inspector` loop **including a real veto → revise → PASS-WITH-FIXES
  cycle** (and a full three-department mission run to completion at the veto cap with `residual_risk`),
  Stop-with-no-persistence, the security guards, TTS, STT, **7 of 8 registered models** (both FLUX
  image models + both embed models + Whisper + Kokoro + the Qwen3-VL visual VLM), doc RAG ingest,
  the **crash-recovery checkpoint/resume loop**, and — after the Jul 2 evening sweep — **all 6
  mission flags** with their backends installed: `retrieval` (RAG), `web_search` (real ddgs),
  `mcp` resources + `mcp_tools` (a real `server-everything`), `knowledge` (a 202-node graph built
  then retrieved), `visual` (image caption→retrieval), and `personas` (a curated store) all reached
  the active `done` state with real data.
- **Since live-proven (Jul 3)** — PDF export (`[pdf]` installed → a real 67 KB PDF), the GLiNER2
  on-device KG backend (`[kg]` installed → triples with no CLI), and the **cloud VLM** (DashScope
  Qwen-VL → a real caption). See "Cloud backends".
- **Still not exercised live** — an `asset` marker emitted-**then-rendered** inside a mission. A
  department has now been seen *emitting* an image marker (Jul 3), but that mission ended
  `PASS-WITH-FIXES`, and the render bridge only fires on a clean `PASS` (by design), so the
  render-then-rewrite half still awaits a clean-PASS mission that emits a marker. Also the
  **seedance cloud video render** (client implemented + offline-tested; a live render needs a
  Volcengine Ark key).
- **Failed** — `boogu-base` (OOM / swap on 16 GB, **[#39]**). Its second, latent blocker — the
  MLX-VLM thread-affinity crash it shares with `flux2-klein-4b` — is since **fixed by [#67]**; the
  memory wall remains and is only re-testable on a >16 GB Mac.

The live pass paid for itself by catching two real bugs (#37, #40) and one hardware limit (#39)
the offline suite (421 tests) could not surface. But "the offline suite is green" and "every feature
is proven on real hardware" are **different claims** — this report is the honest boundary between
them.
