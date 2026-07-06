# Phase 1 Data Model — Mission Timeline (S3)

S3 introduces **no persisted server entities**. It defines (a) a small view model projected
from the existing `TimelineModel`, and (b) one local, non-secret persistence record. All
types live in the frontend (`app/studio/src/screens/missions/`). Existing types
(`MissionEvent`, `TimelineModel`, `Terminal`, `missionSession` `State`) are reused as-is.

## Reused (unchanged) upstream types

- **`MissionEvent`** (`types.ts`) — the wire event union. Consumed read-only.
- **`TimelineModel`** (`timeline.ts`) — the folded technical model (fields: `retrieval, visual, websearch, mcp, mcpTools, graph, persona, route, depts[], synth[], inspect[], verify[], assets[], terminal`). Produced by `groupTimeline(events)`. **Source of the projection — never modified.**
- **`Terminal`** (`timeline.ts`) — `{kind:"done", verdict, missionId, path, residualRisk} | {kind:"error", message, resumable, checkpoint} | {kind:"cancelled"}`.
- **`missionSession` `State`** (`screens/session/missionSession.ts` after the move) — `{status:"idle"|"launching"|"running"|"cancelled"|"failed"|"done", runId, events[], error}`. Consumed via `subscribe`; controlled via `cancel()`.

## New view types (`humanStages.ts`)

### HumanStage

The unit the screen renders — one curated operator-facing stage.

| Field | Type | Notes |
|-------|------|-------|
| `key` | `HumanStageKey` | one of `"prepare" \| "departments" \| "synthesis" \| "inspection" \| "media"` — maps to a `missions.stage.*` catalog key |
| `state` | `"upcoming" \| "running" \| "done" \| "skipped"` | derived: any underlying step running ⇒ `running`; all present steps done ⇒ `done`; none started ⇒ `upcoming`; explicitly skipped ⇒ `skipped` |
| `detail` | `HumanDetail[]` | plain-language per-activity rows, revealed on drill-down; empty ⇒ no expander |

**Presence rule (FR-003)**: `prepare` appears only if ≥1 pre-route step is non-null; `media` appears only if `assets` is non-empty; `departments`/`synthesis`/`inspection` appear once the run has routed. A stage that never occurred is **omitted**, never shown as an empty placeholder.

### HumanDetail

| Field | Type | Notes |
|-------|------|-------|
| `labelKey` | `CatalogKey` | plain-language activity label (e.g. `missions.detail.sources`) |
| `value` | `string \| number \| null` | interpolated count/name (e.g. hits, department name) — never a raw phase code |
| `state` | `"running" \| "done" \| "skipped"` | per-activity state |

### HumanIteration (inspection fix loop)

Quality inspection renders each `inspect`/`verify` iteration as a numbered round.

| Field | Type | Notes |
|-------|------|-------|
| `round` | `number` | 1-based human round number (the fix loop; FR-004) |
| `verdict` | `string \| null` | inspector verdict token, shown in plain language, `null` while running |
| `verified` | `{ ok: boolean; rate: number \| null } \| null` | from the matching `verify` step, when present |

## New terminal view model (`TerminalPanel.tsx`)

Derived from `Terminal` + follow pointer; selects the panel and forward actions.

| Terminal kind | Panel | Forward actions |
|---------------|-------|-----------------|
| `done` | **Finished** (verdict + summary) | Open details (`getMission`/mission-detail), Download PDF (`fetchMissionPdf`), Start another (→ `#/brief`) |
| `error` (`resumable` + `checkpoint`) | **Error, recoverable** | Resume (`runMission {resumeFrom}`), Return to brief |
| `error` (not resumable) | **Error** | Retry (→ `#/brief`), Return to brief |
| `cancelled` | **Stopped** (nothing saved) | Start another (→ `#/brief`) |

## New persistence record (`followPointer.ts`)

A **single** local record (at most one, like the S2 draft), key namespaced e.g. `agency.studio.followPointer.v1`.

| Field | Type | Notes |
|-------|------|-------|
| `runId` | `string` | the run to cancel/resume/consult |
| `status` | `"running" \| "done" \| "cancelled" \| "error"` | coarse last-known state |
| `missionId` | `string \| null` | set on `done` — for detail/PDF handoff |
| `resumable` | `boolean` | set from an error terminal carrying a checkpoint |
| `checkpoint` | `string \| null` | checkpoint reference (resume uses `runId` as `resume_from`) |
| `updatedAt` | `number` | timestamp for staleness/debug (not a security field) |

**Invariants**: exactly one pointer at a time; written on launch and on each terminal; **contains no secrets and nothing sent off-machine** (Constitution VI, FR-018); cleared when the operator starts a new production or dismisses a resume offer. On mount: an idle in-memory session + a pointer with `status:"error"` & `resumable:true` ⇒ offer resume; `status:"done"` ⇒ offer the completion handoff; otherwise ⇒ empty state.

## State transitions (screen)

```
                 (S2 launch handoff, or #/missions with active session)
mount ──► live-follow ──[event stream]──► live-follow  (stages update per frame)
  │                          │
  │                          ├─[user Stop → confirm]──► stopped (terminal: cancelled)
  │                          ├─[done]───────────────► finished (terminal: done)
  │                          └─[error]──────────────► error / error-recoverable
  │
  ├─[no active session, no pointer]──────────────► empty (→ start a production)
  └─[no active session, resumable pointer]───────► resume-offer ──[resume]──► live-follow
                                                              └──[dismiss]──► empty
```

Connection loss during `live-follow` overlays the shell connection state without leaving
`live-follow` (already-rendered stages preserved); a subsequent reload uses the pointer path.
