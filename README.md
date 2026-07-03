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
