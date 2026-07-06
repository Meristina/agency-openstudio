# Implementation Plan: Mission Timeline — Follow a Running Production, Live and in Human Terms (Brick 7 · Screen S3)

**Branch**: `009-s3-mission-timeline` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-s3-mission-timeline/spec.md`

## Summary

S3 replaces the `#/missions` coming-soon placeholder with the Mission Timeline screen:
a live, plain-language presentation of a running production. It is a **pure presentation
layer** over infrastructure that already exists — it reuses the S2 launch session
(`screens/brief/missionSession.ts`, which holds the live SSE stream and exposes
`{status, runId, events, error}` with cancel) and the existing pure fold
`timeline.ts` (`groupTimeline(events) → TimelineModel`, `runStatus(model)`), and adds a
**human-stage projection** that maps the technical `TimelineModel` into a small curated
set of operator-facing stages (gather facts → departments → synthesis → quality
inspection, with optional activities shown only when present), each expandable to
plain-language per-activity detail. On top of that projection: a cancel-with-confirm
control, the three terminal states (finished / stopped / error) with their forward
actions, an empty state, and a locally-persisted **follow pointer** so a full app reload
can honestly offer checkpoint-resume rather than pretend the live stream survived.

Technically: a new self-contained `screens/missions/` module in the React 19 + Vite app
(`app/studio/`), new `missions.*` EN/FR catalog keys, and four declared integration
edits (router status flip, placeholder-list removal, promote `missionSession` out of the
brick-local `brief/` folder into a shared location, and the agent-context marker).
**Zero server changes, zero new dependencies**: cancel uses the existing
`POST /api/mission/{id}/cancel`; resume uses the existing `POST /api/mission`
`{resume_from}` body; the done handoff reuses the existing `getMission` / `fetchMissionPdf`
mission-detail surface until S4 ships. The developer console's raw `Timeline.tsx` is left
byte-identical.

## Technical Context

**Language/Version**: TypeScript ~5.7 (frontend only); Python 3.11+ server **unchanged**.

**Primary Dependencies**: React 19, Vite 6 (pre-existing). **Zero new runtime or dev dependencies** — the human-stage projection is a pure function over the existing `TimelineModel`; the follow pointer uses `localStorage`.

**Storage**: Browser `localStorage` for a single, non-secret **follow pointer** (last run id + coarse status + resumable/checkpoint marker), same local-only pattern as the umbrella language/client-context and the S2 brief draft. No server-side storage changes.

**Testing**: Vitest 3 + @testing-library/react + jsdom (existing setup), fetch/SSE mocked via the existing test doubles; root `pytest` suite untouched and stays green (server not modified).

**Target Platform**: Desktop browser on the operator's machine, served by the local stdlib server at `127.0.0.1` from `app/studio/dist` (existing static route).

**Project Type**: Web application frontend feature (one inventoried screen) over the existing local HTTP/SSE server.

**Performance Goals**: Each mission event is reflected in the projected stages within one render frame (< ~100 ms; pure local state fold, no network round-trip); a burst of events collapses to a correct ordered model with no dropped/duplicated stage; cancel confirmation resolves the terminal state within one frame of the cancel path returning.

**Constraints**: Constitution I–XI; umbrella cross-cutting rules (i18n catalogs, design system + WCAG 2.1 AA incl. live-region announcement of stage changes, shared loading/empty/error/connection states, tone of voice — zero machinery terms); additive delivery — server and dev console byte-identical; spec clarifications (2026-07-06): reload → checkpoint-resume (no live re-attach), curated stages + optional drill-down, done handoff → existing mission-detail view until S4, single active run in v1.

**Scale/Scope**: 1 screen, ~5 projected human stages over the 14 `TimelineModel` fields, 3 terminal states, 1 follow-pointer store, 2 locales (~50–70 new catalog keys), ~5–6 test files. No backend files touched.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v1.0.0).

- [x] **I. Brain = subscription CLI agents**: PASS — no reasoning path added; S3 only renders events the existing mission loop already emits; launching/resuming delegates to the existing CLI-engine mission loop.
- [x] **II. Engine neutrality**: PASS — the timeline never names an engine and maps only engine-neutral event phases; no engine-specific branch; the Engine contract and production-engine guard are untouched.
- [x] **III. No invented information**: PASS — S3 presents the inspector's progress and verdict in human terms; it neither performs nor weakens verification; no fabricated stage/progress (unknown events are folded/ignored, never invented); the veto loop is untouched.
- [x] **IV. Local-first & offline-by-default**: PASS — presentation-only, no new network behavior; cancel/resume/detail reuse existing local endpoints; the follow pointer is local, non-secret; no per-mission network opt-in is added or changed.
- [x] **V. Subprocess boundaries**: PASS — frontend-only; no `openmontage/` import, no subtree edits; the mission subprocess is driven by the unchanged server.
- [x] **VI. Security**: PASS — server byte-identical (bind/CORS/`path_inside()`/https-only unchanged); no secret-entry or secret-display surface (FR-018); the follow pointer stores no secrets and no off-machine data.
- [x] **VII. Offline tests**: PASS — all new behavior covered by Vitest with a simulated event source and mocked cancel/resume/detail fetches (projection, live updates, fix-loop presentation, cancel/confirm, terminal resolution, resume offer, empty & connection-lost states); no network/CLI/live server. Root pytest suite unaffected.
- [x] **VIII. End-user simplicity**: PASS — S3 *is* the "watch it happen" promise: curated plain-language stages, no machinery terms (wording audit SC-002/§tone), keyboard-operable, one-action stop, never a dead end.
- [x] **IX. License**: PASS — zero new components; nothing to add to `docs/LICENSES.md`.
- [x] **X. Additive over invasive**: PASS — a placeholder route becomes a shipped screen (the umbrella's designed lifecycle); server, mission loop, veto loop, and the dev console's raw timeline are untouched; promoting `missionSession` to a shared path is a move + import update with byte-identical behavior.
- [x] **XI. English everywhere**: PASS — code/docs/commits in English; operator-facing strings live only in the EN/FR end-user catalogs (explicitly permitted).

**Post-Phase-1 re-check (2026-07-06)**: design artifacts (research, data-model, contracts,
quickstart) confirm zero server changes, zero new dependencies, no engine or mission-loop
surface, presentation-only projection over the existing fold, and reuse of existing
cancel/resume/detail endpoints — all gates hold as marked.

## Project Structure

### Documentation (this feature)

```text
specs/009-s3-mission-timeline/
├── spec.md              # Feature spec (clarified 2026-07-06)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── event-stage-mapping.md   # TimelineModel → curated human stages + drill-down + catalog-key contract
│   └── session-handoff.md       # missionSession consumption, cancel/resume/detail endpoints, follow-pointer & terminal handoff
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
app/studio/src/
├── screens/
│   ├── missions/
│   │   ├── MissionTimeline.tsx     # Screen: subscribes to missionSession, renders stages/terminal/empty/connection states
│   │   ├── StageList.tsx           # The curated human stages with per-stage optional drill-down (expand)
│   │   ├── humanStages.ts          # Pure projection: TimelineModel → HumanStage[] (+ human iteration/fix-loop labels)
│   │   ├── TerminalPanel.tsx       # Finished / stopped / error panels + forward actions (detail/PDF, retry, resume, new)
│   │   ├── CancelControl.tsx       # Stop button + plain-language confirm, double-activation guard
│   │   └── followPointer.ts        # Single localStorage follow pointer: record/read/clear, resumable marker
│   ├── session/
│   │   └── missionSession.ts       # MOVED here from screens/brief/ (shared by S2 launch + S3 follow); behavior byte-identical
│   └── placeholders.tsx            # `missions` entry removed (S4–S6, S8 remain)
├── shell/router.ts                 # `missions` route status: "placeholder" → "shipped"
├── timeline.ts                     # REUSED as-is (groupTimeline / runStatus) — not modified
├── i18n/
│   ├── catalog.ts                  # + missions.* typed keys (stages, statuses, cancel, terminals, empty, connection)
│   ├── en.ts                       # + EN strings (fallback source of truth)
│   └── fr.ts                       # + FR strings
└── api.ts                          # REUSED as-is: cancelMission, runMission({resumeFrom} → resume_from body), getMission, fetchMissionPdf

Co-located tests (existing convention):
├── screens/missions/humanStages.test.ts       # TimelineModel → stages: order, presence/absence of optional steps, fix-loop labels, unknown-event safety
├── screens/missions/MissionTimeline.test.tsx   # Live updates from simulated stream, empty state, connection-lost, a11y/keyboard + live-region announce
├── screens/missions/CancelControl.test.tsx     # Confirm required, cancel path exercised, no double-activation, race-with-finish consistency
├── screens/missions/TerminalPanel.test.tsx     # Finished→detail/PDF, error→retry, error+checkpoint→resume, never a dead end
├── screens/missions/followPointer.test.ts      # Record on launch/terminal, resumable marker, reload→resume-offer, single pointer
└── screens/session/missionSession.test.ts      # MOVED with the module; existing coverage stays green

tests/                                           # Python suite — no changes (server untouched)
```

**Structure Decision**: one new self-contained module `screens/missions/` inside the
existing frontend project, consuming the umbrella's shell/i18n/design-system layers, the
existing pure `timeline.ts` fold, and the existing `api.ts` client. The S2 launch session
(`missionSession`) is promoted from `screens/brief/` to a neutral `screens/session/`
location so both the S2 launcher and the S3 follower import it from one shared place (a
move + import-path update, behavior byte-identical). The only other edits outside the new
module are the declared integration points: the router status flip, the Shell mount, the
placeholder-list removal, and the i18n catalog additions (plus the additive `resumeFrom`
field on the shared `composeMission` draft that resume reuses). No backend directories are touched.

## Complexity Tracking

> No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
