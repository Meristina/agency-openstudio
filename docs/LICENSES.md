# Third-party component licenses — Agency Studio

**Discipline**: Agency Studio is **MIT**. We only reuse/port **MIT or Apache-2.0** code.
Any **AGPL** component is **ruled out** (viral license that would contaminate the whole
project) — we borrow only its *concepts*, never its code.

## Evaluated components

| Component | Intended role | License | Decision |
|---|---|---|---|
| **agency-kit** | Orchestration core (reused) | MIT | ✅ Project core |
| **Uncensored-Local-Studio** | Local multimodal patterns (SD/Whisper/Kokoro) | MIT | ✅ Patterns reused, **code hardened** (not its flawed server) |
| **GPT4All** | LocalDocs / RAG pattern | MIT | ✅ Concept reused |
| **microsoft/markitdown** | Document → Markdown ingestion (Wave 4) | MIT | ✅ Direct dependency |
| **claude CLI** | Knowledge-graph extraction (Wave 6) — default, the studio's brain | Anthropic (subscription) | ✅ Reused; extraction is reasoning → runs on the CLI, no new dep (#43/#45) |
| **GLiNER2** (`gliner2`) | Knowledge graphs — optional on-device extraction backend (the `[kg]` extra) | Apache-2.0 | ✅ Optional local plug-in (airgapped builds; `AGENCY_STUDIO_KG_BACKEND=gliner2`) |
| **agency-agents** | Doctrine personas (Wave 6) | MIT | ✅ Curated import |
| **PixelRAG** | Visual RAG (Wave 6, cloud) | Apache-2.0 | ✅ Opt-in mode |
| **seedance-2.0** | Video modality (Wave 6, cloud) | MIT | ✅ Cloud mode |
| **awesome-llm-apps** | Inspiration catalog | Apache-2.0 | 📚 Reference, not a dependency |
| **Jan** | Mature LLM runner (MCP, OpenAI-compat) | **AGPL-3.0** | ❌ Concepts only, **never the code** |
| **chunkr** | Document OCR/chunking | **AGPL-3.0** | ❌ Ruled out (AGPL + heavy Rust/Docker/Postgres service, not a lib) |
| **Blaizzy/mlx-embeddings** | MLX embeddings (Wave 4 candidate) | **GPL-3.0** | ❌ Ruled out (GPL) — used MIT `taylorai/mlx_embedding_models` instead |
| **EmbeddingGemma** | On-device embedding model (Wave 4 candidate) | Gemma Terms | ❌ Not OSI MIT/Apache (use restrictions) — used nomic-embed (Apache) / bge-m3 (MIT) |
| **LM Studio** | LLM runner | Proprietary | ❌ Closed, not reusable |

## Wave 2 runtime dependencies — the `[media]` extra (shipped)

All MIT/Apache/BSD; lazily imported so the core has zero runtime deps. Model **weights**
are downloaded at runtime into the OS cache, never bundled or committed.

| Component | Role | License | Notes |
|---|---|---|---|
| **mflux** (`filipstrand/mflux`) | FLUX image generation, MLX-native | MIT | ✅ Direct dependency |
| **mlx-whisper** | Speech-to-text (Whisper), MLX-native | MIT | ✅ Direct dependency |
| **kokoro-onnx** | Text-to-speech (Kokoro-82M), ONNX | MIT | ✅ Direct dependency |
| **soundfile** | Write synthesized audio to WAV | BSD-3-Clause | ✅ Direct dependency |
| **FLUX.1-schnell** weights | Image model (default) | Apache-2.0 | ✅ Loaded from a **non-gated** pre-quantized 8-bit mflux mirror (`dhairyashil/FLUX.1-schnell-mflux-8bit`) — the official BFL repo is gated; the weights themselves are Apache-2.0 |
| **FLUX.2-klein-4B** weights (`black-forest-labs/FLUX.2-klein-4B`) | Image model (selectable) | Apache-2.0 | ✅ Non-gated (HF-verified); loaded via mflux's `flux2_klein_4b` config, `quantize=8` |
| **Whisper large-v3-turbo** (mlx-community) | STT model | MIT | ✅ Non-gated HF repo |
| **Kokoro-82M** weights (ONNX + voices) | TTS model | Apache-2.0 | ✅ Pinned by URL + SHA-256 (see `engines/models.py`) |
| **ffmpeg** | Audio decode for STT (system tool) | LGPL/GPL (build-dependent) | ⚠️ **System dependency, not bundled or linked** — invoked as a separate process by `mlx-whisper` (`brew install ffmpeg`). No distribution, so its license does not affect Agency Studio's. |

### Experimental image backend — the `[boogu]` extra

Isolated behind its own backend + extra; an unvetted, work-in-progress **community** port
(reviewed as such, opt-in only). All MIT/Apache.

| Component | Role | License | Notes |
|---|---|---|---|
| **boogu-image-mlx** (`xocialize/boogu-image-mlx`) | MLX port of Boogu-Image | MIT | ⚠️ git-installed (not on PyPI), WIP community port — opt-in `[boogu]` extra only |
| **mlx-vlm** | Qwen3-VL conditioner runtime | MIT | ✅ |
| **Boogu-Image-0.1-Base** weights (mlx-community 4-bit) | Image model | Apache-2.0 | ✅ non-gated |
| **Qwen3-VL-8B-Instruct** weights (mlx-community 4-bit) | Text/instruction conditioner | Apache-2.0 | ✅ non-gated |

## Wave 4 runtime dependencies — the `[studio]` extra (shipped, offline-first slice)

All MIT/Apache; lazily imported so the core keeps zero runtime deps. Model **weights** are
downloaded at runtime into the HF cache, pinned to an immutable commit SHA, never bundled.

| Component | Role | License | Notes |
|---|---|---|---|
| **microsoft/markitdown** | Document (PDF/docx/pptx/…) → markdown | MIT | ✅ Direct dependency (lazy; absent ⇒ 501) |
| **mlx_embedding_models** (`taylorai/mlx_embedding_models`) | MLX-native text embeddings | MIT | ✅ Direct dependency (chosen over GPL `Blaizzy/mlx-embeddings`) |
| **sqlite-vec** (`asg017/sqlite-vec`) | SQLite vector search extension | Apache-2.0/MIT | ✅ Direct dependency; a pure-Python cosine fallback covers builds without loadable extensions |
| **nomic-embed-text-v1.5** weights (default) | Embedding model | Apache-2.0 | ✅ Non-gated HF repo, pinned by commit SHA (`engines/models.py`) |
| **bge-m3** weights (option) | Embedding model | MIT | ✅ Non-gated HF repo, pinned by commit SHA |

## Rule for contributors / agents

Before adding a dependency or porting third-party code: **check the license**. If it is not
MIT/Apache-2.0/BSD/ISC (or an equivalent permissive license), do not integrate it — open a
discussion. When in doubt about AGPL/GPL: **concepts only**.

## Attribution

Ports of MIT/Apache code retain their original copyright notice in the affected files, as
required by those licenses.
