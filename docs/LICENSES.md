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
| **hyper-extract** | Knowledge graphs (Wave 6) | Apache-2.0 | ✅ Optional plug-in |
| **agency-agents** | Doctrine personas (Wave 6) | MIT | ✅ Curated import |
| **PixelRAG** | Visual RAG (Wave 6, cloud) | Apache-2.0 | ✅ Opt-in mode |
| **seedance-2.0** | Video modality (Wave 6, cloud) | MIT | ✅ Cloud mode |
| **awesome-llm-apps** | Inspiration catalog | Apache-2.0 | 📚 Reference, not a dependency |
| **Jan** | Mature LLM runner (MCP, OpenAI-compat) | **AGPL-3.0** | ❌ Concepts only, **never the code** |
| **chunkr** | Document OCR/chunking | **AGPL-3.0** | ❌ Ruled out (AGPL + heavy Rust/Docker service) |
| **LM Studio** | LLM runner | Proprietary | ❌ Closed, not reusable |

## Rule for contributors / agents

Before adding a dependency or porting third-party code: **check the license**. If it is not
MIT/Apache-2.0/BSD/ISC (or an equivalent permissive license), do not integrate it — open a
discussion. When in doubt about AGPL/GPL: **concepts only**.

## Attribution

Ports of MIT/Apache code retain their original copyright notice in the affected files, as
required by those licenses.
