# AGENTS.md — Agency OpenStudio ("Agency 360")

Canonical agent context for this repository. `CLAUDE.md` is a symlink to this file;
other agent CLIs (codex, gemini, opencode…) read this file directly. Phase-gated
governance lives in the spec-kit constitution (`.specify/memory/constitution.md`) once
ratified — this file must never contradict it.

## What this project is

**The ultimate 360 agency**: a multimedia / B2B / event agency driven end-to-end by
**CLI coding agents on monthly subscriptions** (zero marginal API cost). One repo,
three vendored pillars:

| Pillar | Where | Role |
|---|---|---|
| **agency-kit (studio fork)** | `agencykit/` | The brain: route → 9 departments → synthesize → inspect (veto). Multi-engine (`ENGINES` dict: claude-code / codex / gemini). Mandatory internet research (its constitution Art. I). |
| **OpenMontage** | `openmontage/` | Video/image production: 122 tools (LOCAL / LOCAL_GPU / API tiers), 13 pipelines, Remotion + HyperFrames rendering. |
| **The studio** | `agency_studio/` + `app/studio/` | The stdlib HTTP/SSE server, local multimodal engines (image/STT/TTS/RAG/video), and the web GUI — evolving into the "magic box" for non-technical users. |

The roadmap is **`PLAN.md`** (bricks 0–9), executed brick by brick through spec-kit
(`/speckit.specify` → `plan` → `tasks` → `implement`).

## Design principles (do not violate)

- **Brain = subscription CLI agents.** All heavy reasoning (routing, departments,
  synthesis, inspection, extraction) runs through a CLI agent subprocess — never a
  token-billed API. Engine-neutral by design: any engine satisfying the Engine contract
  (headless run + guaranteed headless web search) may drive the agency; `claude` is the
  v1 validated engine.
- **No invented information.** Missions research on the live internet and cite
  verifiable sources; the inspector spot-checks and holds veto power. Hardening this
  from a prompt-level mandate into a runtime post-condition is Brick 3.
- **Local-first multimodal, cross-platform.** Local models by default (free); cloud
  providers are explicit, opt-in, env-keyed choices (paid). Apple-Silicon engines
  (MLX) get non-Mac siblings behind the same registries (Brick 5). A mission never
  touches the network except through explicit per-mission opt-in flags.
- **Zero runtime dependencies for the core.** The server is Python stdlib. Everything
  else is a lazily-imported optional extra; absent ⇒ clean 501 + install hint.
- **Subprocess boundaries.** `openmontage/` and the CLI engines are driven across
  subprocess boundaries only. Never import `openmontage/` in-process (its
  `tools/base_tool.py` autoloads `.env` at import). `agencykit/` is the one exception:
  it is the orchestration library the studio imports (`agency_cli` / `agency_kit`),
  installed editable from the subtree (`pip install -e ./agencykit`).
- **Security is non-negotiable.** Bind `127.0.0.1` (never `0.0.0.0`), no
  `Access-Control-Allow-Origin: *`, `path_inside()` on every static handler, https-only
  outbound, API keys env-only (never request fields, never persisted, never logged).
  See `docs/SECURITY.md`.
- **Additive over invasive.** Extensions land as default-`None` hooks and registry
  entries (`IMAGE_MODELS` / `VIDEO_MODELS` / `VISUAL_MODELS` / `make_extractor` pattern)
  so existing behavior stays byte-identical. agency-kit's veto-loop logic
  (Constitution Art. IX) must never change behavior.
- **License: AGPL-3.0-only** (since the OpenMontage fusion; pre-fusion studio code stays
  MIT-available in `LICENSE.MIT`). Reusing open-source code is welcome — record every
  component in `docs/LICENSES.md`.
- **Simple for the end user.** Every user-facing surface must be operable by a
  non-technical user: one entry point, guided briefs, sensible defaults, import/export.

## Vendored subtrees — rules of engagement

- `openmontage/` — pinned (upstream `calesthio/OpenMontage@0c202b5`), update only via
  `git subtree pull`, avoid local edits (merge divergence). Its internal `CLAUDE.md` /
  `.claude/` skills govern that subtree only (they load as scoped skills).
- `agencykit/` — the agency-kit-studio fork (pinned @ `fc8ac76`), carrying the studio
  hooks (`on_event`, `should_cancel`, `asset_clause`, `context_clause`,
  `persona_doctrine`, `mcp_config_path`, checkpoint/resume). Same subtree rules. The
  specialist army (marketing-kit, comms-kit, … 9 kits) is snapshotted in
  `agencykit/agency_cli/payload/`.

## Conventions

- Python: stdlib-first for the core; type hints; offline tests (monkeypatch the
  subprocess/network boundary — no CLI, no network, no Node needed to run the suite).
- Frontend: React + Vite under `app/studio/` (the magic-box redesign is Brick 7).
- Commits: Conventional Commits; branch before non-trivial work; PRs squash-merge to
  `main`.
- Tests: `pytest` at the repo root collects `tests/` only (`openmontage/` and
  `agencykit/` carry their own suites — run those from their directories).

## History

Pre-fusion history (agency-studio's Waves 0–6, live-test reports, the old roadmap) is
archived in `docs/legacy/`. The OpenMontage fusion decision record is
`docs/OPENMONTAGE-FUSION.md`.
