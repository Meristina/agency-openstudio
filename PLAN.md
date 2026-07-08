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

## Brick 7 — The magic box (full custom UI redesign) *(umbrella merged — `652777a`, #11; S2 Guided Brief merged — `3643772`, #12; S3 Mission Timeline merged — `94e51cc`, #13; S4 Deliverable Library merged — `e40c0e1`, #14; S5 Import merged — `7fd9923`, #15; S6 Export merged — `d22c9c4`, #16; S7 Capability & Model Panel merged — `5c36bcf`, #17; S8 Settings merged — `99efe87`, #18; S1 Home merged — `71b14f8`, #19; all child-spec screens shipped)*

A new front-end application: **a single entry point** ("what do you want to
produce?"), a guided brief by sector/domain/deliverable type, a live mission timeline,
a **deliverable library** per client, **import** of existing material (docs, images,
briefs, videos), **export bundles** (PDF / media zip / full dossier), EN/FR i18n, and
the model panel (Brick 4). Every screen gets its own spec.
UX references: AnythingLLM (workspace = project), Jan (local-first).
**Done when**: a non-technical user produces a complete deliverable
(research → strategy → video → export) unassisted.

## Brick 8 — Deliverable recipes (mission → production in one click) *(merged — `92a704e`, #20; recipe engine + composed-recipe done-when landed; production-pipeline runner deferred — see below)*

Expose the 13 OpenMontage pipelines plus composed agency recipes (full campaign,
client pitch, turnkey event, social content pack): a recipe chains mission
(departments) → assets (image/voice) → composition (video) → export.
**Done when**: "launch a campaign for X" produces the strategy dossier AND the
associated creatives in a single run.

**Delivered**: an additive recipe engine (`agency_studio/recipes/` — default-empty
registry, sequential orchestrator streaming the mission SSE vocabulary, 3 endpoints
reusing the run registry) with the **composed-recipe done-when met for real** — the
`full-campaign` run produces the sourced, veto-gated dossier AND a guaranteed-**local**
composition video (`openmontage_backend`, subprocess) plus a bundle, in one run. All 13
production pipelines are exposed in the catalog (EN/FR), launchable, and degrade to an
honest 501 when their runtime is absent. Local-first with explicit cloud opt-in (keys
env-only), single active run, cancel/kill-tree; inspector veto byte-identical; offline
tests green.

**Follow-up landed** (`#22`, issue #21 · T025/T026): the production-pipeline **agentic
runner** (the "A2" work) is now wired — a production recipe drives its OpenMontage
pipeline's `executive-producer` skill via a CLI-agent **subprocess** in `openmontage/`
(cwd = subtree, no in-process import), with kill-tree cancel, a manifest-derived hard
timeout, `OM_ARTIFACT` sentinel parsing, atomic + symlink-safe output, and a lightweight
deliverable record in the store (retrievable via library/export, FR-018/FR-019). An absent
runtime or an honest agent failure degrades to a clean error frame — never a fabricated
video or verdict (Principle III). Not validatable offline by nature (needs Node + skills +
tools + a validated CLI engine), so only the subprocess spawn is the monkeypatched boundary.
Runner is documented **trusted-operator-only** (127.0.0.1 single-operator studio); a hard
OS/container sandbox for untrusted input is the next security step.

**Per-stage resume landed** (`#23`, issue #21 · T043/T044/T039): a recipe that fails at a
**post-mission** stage now snapshots a recipe checkpoint (`completed_stages` + replayable
`outputs`, reusing the mission checkpoint seam, distinguished by `kind`) and offers a
resume that **replays the completed mission** — reloading its dossier, never re-running the
veto-gated mission — and restarts at the failed stage. `POST /api/recipe` accepts
`resume_from`; the mission listing/resume paths skip recipe checkpoints so the two resume
lanes stay isolated. Additive: without `resume_from`, behavior is byte-identical.

**Recipe frontend tests landed** (`#24`, issue #21 · T019/T032/T037 + T045 timeline-reuse):
vitest coverage for the catalog (composed + production, EN/FR, plain-language tier badges)
and launch (posts subject + opt-ins, hands off to the `#/missions` timeline; local stage
never opt-in, cloud opt-in default-off; empty subject never launches). Frontend suite 290
green, tsc clean. (Frontend is not in CI — pytest + CodeRabbit are the gates — so it is
validated locally.)

**Resume affordance wired** (`#25`, issue #21 · T045): a recipe run that fails at a
post-mission stage now resumes from the UI — `missionSession.resume` dispatches on the
tracked run kind to `POST /api/recipe {resume_from}` (via `recipesApi.resumeRecipe`), so the
existing timeline resume button works for recipes with no change to the shared
timeline/TerminalPanel. Immediate same-session resume works; a reload-then-resume (in-memory
kind lost) is a noted small follow-up.

**Guided-Brief recipe entry wired** (`#26`, issue #21 · T030): the brief's deliverable-type
step offers "recipe" (EN/FR), which hands off to the `#/recipes` catalog instead of composing
a mission (guarded so it never keys `questionSets`; leaves no phantom draft) — closing FR-002's
single entry point. Mission flow byte-identical.

**Issue #21 fully addressed** (#22 runner · #23 resume backend · #24 catalog/launch tests ·
#25 resume affordance · #26 brief entry). Only honest, explicitly-noted edges remain as small
future work: persisting the run kind for a reload-then-resume, and a hard OS/container sandbox
for the production runner under untrusted input. Brick 8 is now complete end-to-end — the 13
production pipelines really run (subprocess CLI-agent), recipes resume per stage, and every
surface is reachable and tested.

## Brick 9 — Real multi-CLI *(done — `1ac3eda`)*

codex validated end-to-end against the Brick 1 contract (headless web search via
`--search`, sources resolved per the live-test report); the deprecated gemini slot
replaced by antigravity (Gemini CLI → Antigravity CLI upstream, binary `agy`) and
opencode added — both registered as refused candidates until their own live-test
proves headless web search (antigravity tool-driven, opencode Exa/`OPENCODE_ENABLE_EXA`,
neither proven); an engines × capabilities compatibility matrix published in
`agencykit/README.md`, guarded by a matrix-vs-registry consistency test.
**Done when**: the same mission passes on two engines with comparable dossiers and
verified sources (Brick 3) on each. ✅ claude-code + codex (offline suite green;
`--engine gemini` now errors as unknown, no silent substitution).

### Deferred follow-ups *(closed #30/#31 — not on the critical path)*

Two Brick 9 tracking issues were closed as documented deferrals, not abandoned. Each is
blocked on an **external** dependency, not repo effort, so an open ticket would have implied
pending code that doesn't exist. Reopen (or file a fresh scoped issue) when the trigger is met.

**Live-validate antigravity & opencode** (`#30`): both engines already ship in the correct
fail-safe posture (`validated=False` / `web_search_headless=False` → refused, no silent
substitution, `EngineSpec` invariant holds), and claude-code + codex already cover
production. The remaining work is *environment-dependent* — real `agy` / `opencode` CLIs,
live network, working auth — none of which run in the offline suite. Procedure when a
maintainer has the environment: run each engine end-to-end, apply the Brick 3 postcondition
(min sources/department + URL resolution); on pass set `validated=True` **and**
`web_search_headless=True` in `cli_engine.py`, update the `agencykit/README.md` matrix (the
consistency test enforces the row), and append the run to
`docs/legacy/brick9-multi-cli-live-test.md`; on fail keep it refused and document the limit.
**Reopen trigger:** a maintainer has the CLI + network to run the live test.

**Antigravity init-harness adapter** (`#31`): additive polish to the `agency init --agent`
scaffolder (a separate axis from `ENGINE_SPECS` — never touches the mission loop). Blocked on
an external fact: Antigravity's slash-command / prompt directory format is **not documented
in-repo**, and Constitution Art. III (no-invented-info) forbids guessing it. Plan once the
format is confirmed from official docs: add `_install_antigravity` to `integrations.py`,
register it in `_ADAPTERS`, add `"antigravity"` to `SUPPORTED`, update the `--agent` help in
`cli.py` + `agencykit/CLAUDE.md`, and add per-harness coverage in `tests/test_cli.py`. Keep
`gemini` as a legacy adapter (still writes valid `.gemini/commands/agency/*.toml`); remove
only as a deliberate separate change. **Reopen trigger:** Antigravity's command format is
confirmed from official docs.

---

## Invariants (all bricks)

Offline suite green on every merge · zero runtime dependencies in the core ·
subprocess boundaries respected · per-mission network opt-in · security (127.0.0.1, no
CORS `*`, path guards, env-only keys) · Conventional Commits + squash PRs to `main` ·
agency-kit's veto loop never changes behavior.
