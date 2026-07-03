# The OpenMontage fusion — plan & record

**Status: brick A1 (local composition video) SHIPPED; brick A2 (full agentic pipeline)
DEFERRED.** This document is the WAVE-PLAN-style record of the fusion that created
**agency-openstudio**.

## The decision (2026-07-03)

The user chose a **full fusion** of agency-studio with
[calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) (AGPL-3.0, agentic video
production), in a **new repository** (agency-studio itself is untouched). Consequences,
all explicit user decisions:

- **Relicensing (one-way, irreversible):** the combined work is **AGPL-3.0-only**.
  Pre-fusion agency-studio code stays MIT-available (`LICENSE.MIT`). The charter's
  historical "MIT-compatible only / never AGPL" principle is superseded (`CLAUDE.md`,
  `docs/LICENSES.md`).
- **Vendoring:** `openmontage/` is a `git subtree --squash` import, **pinned at upstream
  `0c202b5`**. Update only via `git subtree pull`; avoid local edits inside the subtree
  (merge divergence). Its ~45 internal Claude Code skills load as *scoped* skills
  (they apply only when working on files under `openmontage/`).
- **Integration depth:** arbitrated by a 9-agent research + judge-panel workflow
  (3 readers → 3 advocates → 3 judges). Option A — *fusion + local video bridge* — won
  (A=23, B=18, C=11); the feasibility judge's sequencing concern was honored by landing
  the relicensing (PR-equivalent: the seed commit) before the bridge (its own PR).
  Option C (GUI unification with embedded Remotion previews) was rejected this pass:
  React 18→19 skew in the subtree, the separate Remotion company-license question, and
  6–9 days of greenfield with no prior art.

## Brick A1 — local composition video (SHIPPED)

The Wave-6 seedance brick made `video` an asset type, cloud-only (text-to-*footage*
doesn't fit a 16 GB Mac). OpenMontage ships a genuinely headless, zero-key *composition*
renderer — `remotion-composer/` (React scenes → h264 mp4) — so the fusion wires it in as
the studio's first **local** video backend:

- `agency_studio/openmontage_backend.py` — the `local` `(probe, load, run)` triple.
  `probe` gates on node/npx + the subtree + an **existing** `node_modules` (the studio
  never runs `npm install`, so `npx` can never fall through to a registry fetch —
  local-first). `run` shells `npx remotion render src/index.tsx Explainer … --codec h264`
  in `openmontage/remotion-composer/` (a **subprocess boundary** — the charter forbids
  importing openmontage in-process: `tools/base_tool.py` autoloads `.env` at import).
  Output is atomic (`.part.mp4` → rename): complete or absent, never truncated.
  Cancellation `killpg`s the whole render tree (Remotion's headless Chromium included),
  mirroring agency-kit's in-flight mission kill.
- `seedance.py` — registry entry `openmontage-remotion` (backend `local`, no endpoint,
  lazy-resolved in `_backend`) + the **`AGENCY_STUDIO_VIDEO_BACKEND`** env selector
  (`default_video_model()`, the `knowledge.make_extractor` pattern; a typo fails loud —
  it must never silently fall back to an off-machine call).
- `assets.py` — the marker gains an optional **`cuts`** composition structure, strictly
  whitelisted in `_clean_cuts`: only `text_card` / `hero_title` / `stat_card` / `callout`
  and only their text content fields. **Never a timing** (every cut gets a fixed
  `FIXED_CUT_SECONDS` slot, count capped at 12 → a 60 s cost ceiling the marker cannot
  raise) and **never a media reference** (`source` / `backgroundVideo` /
  `backgroundImage` / `images` / `audio` are dropped wholesale — an injected marker can
  never pull a local file into a rendered/exported video). Bad cuts degrade to the
  prompt-only `text_card` fallback, never to a drop.
- Everything downstream is untouched: the same `allow_video` per-mission opt-in (parse
  boundary), the same `asset` SSE phase, `/media` `.mp4` serving, gallery `<video>`, PDF
  localization. Server/GUI changes are copy only (the clause stanza + the toggle label).

**Verification:** the offline suite (no Node, no ffmpeg, no network) covers the probe
gates, fixed caps, cuts whitelist, atomic output, cancel/kill (real `/bin/sh` children),
and the env dispatch. **Live validation on the M4 Mac is deferred** (the Wave-2/5
pattern): `cd openmontage/remotion-composer && npm install`, sanity-check with
`python3 openmontage/render_demo.py`, then run a mission with the video flag on and
`AGENCY_STUDIO_VIDEO_BACKEND=openmontage-remotion`; verify gallery playback + PDF export.

## Brick A2 — the full agentic pipeline (DEFERRED — do not build casually)

Driving OpenMontage's 12-stage production pipelines (research → script → asset
generation → edit) through the studio's brain requires a new `cli_engine` invocation
variant: `cwd=openmontage/`, an expanded child sandbox (Bash/Read/Write vs the
departments' WebSearch-only `--allowedTools`), >900 s timeouts, and prompt-level
auto-approval of OpenMontage's human checkpoints. That is a **material
security-posture change** spanning both repos (like the Wave-6 MCP hook, via
agency-kit-studio), and it lands only as its own reviewed brick.

## Standing cautions

- No *documented* headless API upstream: A1 rides de-facto internals (`render_demo.py`'s
  invocation, the `SCENE_TYPES.md` props shape) — verified in the pinned revision;
  re-verify on every `git subtree pull`.
- Node 18+ is a runtime prerequisite of the local backend only (probe → clean 501 + hint
  when absent). HyperFrames (Node ≥ 22) stays out of scope.
- A Remotion render competes for RAM with warm models on the 16 GB Mac; it runs off the
  device worker (never blocks image/tts/stt/embed) and last in the render order.
