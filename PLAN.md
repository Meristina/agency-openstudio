# PLAN.md — Agency 360: the brick-by-brick roadmap

Each brick is a full **spec-kit** cycle — `/speckit.specify` → `/speckit.clarify` →
`/speckit.plan` → `/speckit.tasks` → `/speckit.implement` — independently mergeable, in
this order. Governance lives in the constitution (`.specify/memory/constitution.md`);
agent context in `AGENTS.md`.

**Vision**: a multimedia / B2B 360 / event agency driven by subscription CLI agents
(zero marginal cost), with mandatory and verifiable internet research, production all
the way to video, a "magic box" interface for non-technical users, cross-platform,
free/paid model choice.

---

## Brick 0 — Foundations *(done — `3089b23`)*

Spec-kit initialized (`specify init` + claude integration), constitution ratified by
the user, canonical `AGENTS.md` + `CLAUDE.md` symlink, `agencykit/` (the
agency-kit-studio fork, pinned) and `openmontage/` (pinned) vendored, this PLAN.md
committed.
**Done when**: `specify check` passes, the studio suite (484 tests) and the agencykit
suite (160 tests) are green, and the repo installs standalone
(`pip install -e ./agencykit && pip install -e .`).

## Brick 1 — The Engine contract (multi-CLI abstraction, claude validated) *(done — `a3f9b30`)*

Formalize the `ENGINES` dict in `agencykit/agency_cli/engines/cli_engine.py` into an
explicit `Engine` contract: `run(prompt)` / `route(prompt)` / declared capabilities
(`web_search_headless: bool` — a constitutional precondition) / kill-tree on cancel.
**claude-code is the only validated v1 engine**; codex/gemini stay registered but
marked unvalidated. Offline contract suite (one fake binary per engine).
References: opencode `serve`, rivet-dev/sandbox-agent.
**Done when**: a mission runs unchanged on claude; adding an engine = one contract
implementation + its suite, with zero changes to the mission loop.

## Brick 2 — The specialist army plays (a real marketing / B2B / event agency) *(done — `1ea04d7`, #4)*

Today the mission loop only loads the condensed doctrine (`_shared-{dept}.md`) — the
commanders/officers/soldiers of the 9 department kits
(`agencykit/agency_cli/payload/`: 177 agents, 110 skills) never participate. Wire a
**budget-controlled escalation**: condensed doctrine → the phase's officer → the method
soldier (JTBD, STP, Pareto, PERT…), selected by the department's router. Event work
(comms-kit) and B2B 360 become operational.
**Done when**: a marketing mission actually invokes ≥1 officer + ≥1 soldier, traced in
the dossier; the per-department token cost stays bounded and measured.

## Brick 3 — Verifiable internet (from soft guarantee to postcondition) *(done — `ab7f796`, #5)*

The "no invented information" mandate is prompt-only today. Harden it: extract
citations from the deliverable, resolve URLs (HEAD, offline-stubbed in tests), enforce
a minimum source count per department, and enrich the inspector verdict with a
verification report. Reference pattern: gpt-researcher (Apache-2.0).
**Done when**: a deliverable without resolvable sources is blocked by the inspector
with an actionable report; the verified-source rate shows in the dossier and the GUI.

## Brick 4 — Capabilities & model choice (the end of env-only) *(done — `6e71879`, #6)*

`GET /api/capabilities` aggregates every registry (IMAGE_MODELS, VIDEO_MODELS,
VISUAL_MODELS, EMBED_MODELS, KG extractors, STT/TTS to be promoted into registries)
**plus the OpenMontage ToolRegistry** (its LOCAL / LOCAL_GPU / API axis = native
free/paid metadata). Server-side persisted selection (settings) exposed to the user —
env vars remain the override.
**Done when**: the user picks their models/tools (free/paid, available/unavailable)
from the interface without touching a terminal.

## Brick 5 — Cross-platform ("any machine") *(done — `0744a1f`, #8)*

Non-Mac backends behind the existing registries, same pattern as
`openmontage-remotion`: image (stable-diffusion.cpp MIT, or a LocalAI MIT gateway),
STT (whisper.cpp / faster-whisper), TTS (Piper / Kokoro-onnx CPU), embeddings
(llama.cpp `/v1/embedding`). Every backend: probe → clean 501 when absent.
**Done when**: the same mission with assets runs on a Linux/Windows box without MLX,
with the offline suite green everywhere.

## Brick 6 — Clients & projects *(done — `c8abe89`, #9)*

A client / project / campaign taxonomy above the store (the existing `project_root`
stamp is the hook): dossier fields, grouping endpoints, soft migration of existing
missions.
**Done when**: history is browsable by client and campaign, and every deliverable
belongs to a project.

## Brick 7 — The magic box (full custom UI redesign) *(umbrella merged — `652777a`, #11; S2 Guided Brief merged — `3643772`, #12; remaining screens ship via child specs)*

A new front-end application: **a single entry point** ("what do you want to
produce?"), a guided brief by sector/domain/deliverable type, a live mission timeline,
a **deliverable library** per client, **import** of existing material (docs, images,
briefs, videos), **export bundles** (PDF / media zip / full dossier), EN/FR i18n, and
the model panel (Brick 4). Every screen gets its own spec.
UX references: AnythingLLM (workspace = project), Jan (local-first).
**Done when**: a non-technical user produces a complete deliverable
(research → strategy → video → export) unassisted.

## Brick 8 — Deliverable recipes (mission → production in one click)

Expose the 13 OpenMontage pipelines plus composed agency recipes (full campaign,
client pitch, turnkey event, social content pack): a recipe chains mission
(departments) → assets (image/voice) → composition (video) → export.
**Done when**: "launch a campaign for X" produces the strategy dossier AND the
associated creatives in a single run.

## Brick 9 — Real multi-CLI

codex and gemini validated end-to-end against the Brick 1 contract (headless web
search verified per engine), opencode added; an engines × capabilities compatibility
matrix published in the README.
**Done when**: the same mission passes on two engines with comparable dossiers and
verified sources (Brick 3) on each.

---

## Invariants (all bricks)

Offline suite green on every merge · zero runtime dependencies in the core ·
subprocess boundaries respected · per-mission network opt-in · security (127.0.0.1, no
CORS `*`, path guards, env-only keys) · Conventional Commits + squash PRs to `main` ·
agency-kit's veto loop never changes behavior.
