# Agency OpenStudio — the ultimate 360 agency

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](./LICENSE)

**A complete multimedia, B2B, and event agency driven by CLI coding agents on monthly
subscriptions — zero marginal cost per mission.** The user steps into a "magic box":
they describe what they want (research, a strategy, a campaign, a video, an event…)
and the agency researches the live internet, decides, produces, and exports the
deliverable — from brief to final video.

## The three pillars (one self-contained repo)

| Pillar | Directory | Role |
|---|---|---|
| **agency-kit** (studio fork) | [`agencykit/`](./agencykit/) | The brain: route → 9 specialist departments (solve, product, marketing, finance, comms, data, ops, people, tech) → synthesis → inspector with veto power. Multi-engine: claude-code / codex / gemini. Mandatory internet research, cited sources. |
| **OpenMontage** | [`openmontage/`](./openmontage/) | Production: 122 tools (free local / GPU / paid API), 13 video pipelines, Remotion + HyperFrames rendering. |
| **The studio** | [`agency_studio/`](./agency_studio/) + [`app/studio/`](./app/studio/) | The local server (Python stdlib, zero dependencies), the local multimodal engines (image, voice, RAG, video), and the web GUI. |

## Quick start

```bash
# 1. The venv + the brain (the vendored agency-kit fork) + the studio
python3 -m venv .venv && source .venv/bin/activate
pip install -e ./agencykit
pip install -e .

# 2. A CLI agent on PATH (the validated v1 engine is claude)
#    claude / codex / gemini — see agencykit/README.md

# 3. Launch
agency-studio          # (alias: agency-openstudio) → http://127.0.0.1:8765
```

Optional extras (lazily imported; absent ⇒ clean 501 + install hint):
`[media]` Apple Silicon image/STT/TTS · `[studio]` RAG · `[web]` web search ·
`[mcp]` MCP resources · `[visual]` visual RAG · `[pdf]` export. Local video
(OpenMontage/Remotion) needs Node 18+ and a one-time `npm install` in
`openmontage/remotion-composer/` (`AGENCY_STUDIO_VIDEO_BACKEND=openmontage-remotion`).

## Model defaults

The GUI opens on the magic box home: describe what you want to produce, then start a
brief. The old developer console remains available at `#/console`; the shell also
provides persistent navigation, an EN/FR language switcher, and client context.

Use the Studio **Models** screen to see available/free/paid models and pick defaults.
Resolution order: **env var → persisted GUI selection → platform-aware default** — a power-user
env var overrides the saved selection; without either, the built-in default is used when
available, otherwise the first available sibling is used:

`AGENCY_STUDIO_IMAGE_MODEL`, `AGENCY_STUDIO_VIDEO_BACKEND`,
`AGENCY_STUDIO_VISUAL_BACKEND`, `AGENCY_STUDIO_EMBED_MODEL`,
`AGENCY_STUDIO_KG_BACKEND`, `AGENCY_STUDIO_STT_MODEL`, `AGENCY_STUDIO_TTS_MODEL`.

## Clients, projects, and campaigns

The mission form accepts optional **Client**, **Project**, and **Campaign** fields.
New tagged missions store those fields in their own dossier; old missions are not
rewritten. Attribution resolves in this order: side-band override, dossier fields,
then defaults (`Studio` plus the workspace directory name, or `Unassigned` when no
workspace stamp exists).

The local server exposes `GET /api/taxonomy`, filtered `GET /api/missions?client=...`,
and `POST /api/mission/{id}/assign` for reassignment. Overrides and first-typed
display names live in `~/.agency/taxonomy.json`, written atomically; reassignment
only changes that registry file.

## Cross-platform local backends

`pip install 'agency-studio[media]'` works on macOS, Linux, and Windows. MLX packages are
Darwin-only; off-Mac the extra installs the portable TTS subset (`kokoro-onnx`,
`soundfile`). Image/STT/embeddings use user-installed binaries instead:

- Image: `stable-diffusion.cpp` (`sd`) plus the pinned GGUF model file in the studio
  models directory.
- STT: `whisper.cpp` (`whisper-cli`) plus the pinned Whisper model file.
- Embeddings: a local `llama.cpp` embedding server on `http://127.0.0.1:8080`, or
  `AGENCY_STUDIO_EMBED_GATEWAY_URL` pointing to loopback.

The Capabilities tab shows the exact missing binary/model/gateway hint.

## Roadmap

Development follows **[`PLAN.md`](./PLAN.md)** — bricks 0 through 9, each a full
**spec-kit** cycle (constitution → specify → plan → tasks → implement). Governance:
the spec-kit constitution (`.specify/memory/constitution.md`); agent context:
[`AGENTS.md`](./AGENTS.md) (canonical — `CLAUDE.md` is a symlink).

## License

**AGPL-3.0-only** (the combined work, since the OpenMontage fusion). Pre-fusion
agency-studio code remains available under MIT ([`LICENSE.MIT`](./LICENSE.MIT)).
Third-party components: [`docs/LICENSES.md`](./docs/LICENSES.md). Fusion decision
record: [`docs/OPENMONTAGE-FUSION.md`](./docs/OPENMONTAGE-FUSION.md). Pre-fusion
history (Waves 0–6): [`docs/legacy/`](./docs/legacy/).
