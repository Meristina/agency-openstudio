# Quickstart — Mission Timeline (S3)

How to build, test, and manually verify the S3 Mission Timeline. Frontend-only; the Python
server is not modified, so `pytest` at the repo root stays green without action.

## Prerequisites

- Node + the existing `app/studio/` toolchain (React 19, Vite 6, Vitest 3) — already installed.
- No new dependencies to add.

## Build & test (offline — the merge gate)

```bash
# from repo root
cd app/studio
npm run build          # tsc + vite build — must pass (types incl. new missions module)
npm test               # vitest — all suites incl. new screens/missions/* must pass, no network
```

```bash
# from repo root — server suite must remain green (server untouched)
pytest -q
```

The frontend suite runs fully offline: the mission stream is a simulated array of
`MissionEvent`s pushed through a fake `runMission`; `cancelMission`, `getMission`, and
`fetchMissionPdf` are mocked. No CLI engine, no live server, no Node server required.

## What ships (integration edits — keep the diff minimal)

1. **New module** `app/studio/src/screens/missions/` — `MissionTimeline.tsx`, `StageList.tsx`,
   `humanStages.ts`, `TerminalPanel.tsx`, `CancelControl.tsx`, `followPointer.ts` (+ tests).
2. **Move** `screens/brief/missionSession.ts` → `screens/session/missionSession.ts` (+ test);
   update the two import sites (S2 `GuidedBrief.tsx`, S3 `MissionTimeline.tsx`). Behavior
   byte-identical.
3. **Router** `shell/router.ts` — flip `missions` `status: "placeholder" → "shipped"`.
4. **Placeholders** `screens/placeholders.tsx` — remove the `missions` entry.
5. **Catalog** `i18n/catalog.ts` + `en.ts` + `fr.ts` — add `missions.*` keys (stages,
   statuses, rounds, drill-down labels, department names, cancel/confirm, terminal panels,
   empty & connection-lost). EN is the fallback source of truth; FR complete and identical-keyed.
6. **Agent context** — the SPECKIT marker in `AGENTS.md`/`CLAUDE.md` points to this plan.

Nothing else changes. `timeline.ts`, `api.ts`, the server, and the dev console's raw
`Timeline.tsx` are untouched.

## Manual smoke (with a real local run, optional)

1. `python -m app.studio` (or the documented launch) → open the magic box at `127.0.0.1`.
2. Launch a research brief from **S2 Guided Brief**; you are routed to **#/missions**.
3. **US1** — watch the stages appear live in plain language (gathering facts → departments →
   drawing together → quality inspection); confirm **no** department key, engine name, or
   phase code is visible; expand a stage to see per-activity detail.
4. **US2** — press **Stop**, confirm; the run halts and the timeline shows "stopped, nothing
   saved". Relaunch and let it finish instead.
5. **US3** — on success, use **Open details** / **Download PDF**; on a forced error with a
   checkpoint, confirm the **Resume** offer appears.
6. **US4** — navigate away and back to **#/missions**: the same run is still shown; with no
   run active, the empty state points to the Guided Brief.
7. **US5** — reload the page mid-run: confirm the screen does **not** claim the live run
   continued, and offers **checkpoint-resume** when a checkpoint exists.
8. Switch EN⇄FR mid-run: every stage/label re-renders, progress intact.

## Acceptance mapping (spec → verification)

| Spec | Verified by |
|------|-------------|
| FR-001–FR-006 (live stages, fix loop, drill-down, safety) | `humanStages.test.ts`, `MissionTimeline.test.tsx` |
| FR-007–FR-009 (cancel/confirm/race) | `CancelControl.test.tsx` |
| FR-010–FR-013 (terminals + handoff) | `TerminalPanel.test.tsx` |
| FR-014–FR-015 (reachability, session survival) | `MissionTimeline.test.tsx`, router test |
| FR-016–FR-017 (connection loss, reload → resume) | `followPointer.test.ts`, `MissionTimeline.test.tsx` |
| FR-018 (no secrets) | `followPointer.test.ts` (no secret fields), review |
| FR-019–FR-021 (foundation, i18n, offline tests) | i18n completeness test, a11y assertions, whole suite offline |
| SC-002 (zero machinery terms, both languages) | wording assertions in `humanStages.test.ts` + catalog completeness |
