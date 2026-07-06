# Contract — Session Consumption, Control Endpoints & Handoff

How S3 consumes the S2 launch session, drives the existing local control endpoints, and
persists the follow pointer. **No new server endpoints, no new mission semantics** — every
call below already exists. This contract covers FR-007–FR-017.

## 1. Session consumption (read side)

S3 subscribes to the shared `missionSession` (moved to `screens/session/missionSession.ts`):

```ts
missionSession.subscribe((s) => { /* s: {status, runId, events, error} */ })
```

- `status` maps to the screen mode: `launching|running` ⇒ live-follow; `done` ⇒ finished;
  `failed` ⇒ error (message wrapped in plain language); `cancelled` ⇒ stopped; `idle` ⇒
  empty/resume-offer (see §4).
- `events` is fed to `groupTimeline(events)` → `TimelineModel` → `humanStages(...)` every publish.
- **In-app navigation** preserves the run because `missionSession` is a module-level
  singleton (FR-015); returning to `#/missions` re-subscribes and re-renders current progress.

## 2. Cancel (FR-007–FR-009)

- Trigger: Stop button → **plain-language confirm** (work will be lost) → on confirm only:
  ```ts
  await missionSession.cancel()   // aborts the SSE fetch AND POSTs the cancel endpoint
  ```
- Under the hood (unchanged): `cancel()` calls `controller.abort()` then
  `cancelMission(runId)` → `POST /api/mission/{runId}/cancel` (returns **202**; `api.ts:146`).
- The Stop control is **not rendered** when `status ∈ {done, failed, cancelled}` and is
  disabled after first activation (double-activation guard).
- **Finish/cancel race**: `missionSession.launch`'s catch already refuses to overwrite a
  settled state; S3 renders strictly off the final `status`, so exactly one terminal shows
  (FR-009).

## 3. Terminal handoff (FR-010–FR-013)

| `status` / `terminal` | Forward action | Existing call |
|-----------------------|----------------|---------------|
| `done` | Open details | `getMission(missionId)` → dossier (mission-detail surface); until S4, this is the interim destination |
| `done` | Download PDF | `fetchMissionPdf(missionId)` → Blob (`GET /api/mission/{id}/pdf`, `[pdf]` extra) |
| `failed` + resumable pointer | Resume | `runMission(goal, onEvent, { resumeFrom: runId })` — re-enters live-follow |
| `failed` (not resumable) | Retry / Return | navigate `#/brief` |
| `cancelled` | Start another | navigate `#/brief` |

- The launched brief/production stays identifiable in every terminal (FR-013); no state is
  a dead end (every panel has ≥1 forward action).
- Error `message` is always rendered through a plain-language wrapper; raw text is never the
  primary message (FR-011).

## 4. Follow pointer & reload → resume (FR-016, FR-017; clarification Q1)

**Write** (`followPointer.record`): on launch (`{runId, status:"running"}`) and on each
terminal (`done` ⇒ `{status:"done", missionId}`; `error` ⇒
`{status:"error", resumable, checkpoint}`; `cancelled` ⇒ `{status:"cancelled"}`).

**Read on mount** (`followPointer.read`), when the in-memory session is `idle`:

| Pointer state | S3 behavior |
|---------------|-------------|
| none | **Empty state** — plain-language "nothing running" + CTA → `#/brief` (FR-014, US4) |
| `status:"error"`, `resumable:true` | **Resume offer** — resume (`runMission {resumeFrom: runId}`) or dismiss (clears pointer → empty) |
| `status:"done"` | **Completion handoff** — the finished panel with detail/PDF actions (§3) |
| `status:"running"`/`"cancelled"`/error-non-resumable | Honest terminal/empty state (the live stream did not survive the reload; no fabricated progress) |

- The pointer is the **only** thing that survives a full reload (the SSE stream does not);
  S3 never claims the live stream continued (FR-017).
- The resume endpoint and on-disk checkpoints already exist (`server.py:16`, `:564-565`);
  S3 adds no server surface.

## 5. Connection loss (FR-016)

- A mid-run non-abort failure surfaces as `status:"failed"`; combined with the shell's
  existing `ConnectionBanner`, S3 shows a **calm** connection-lost note, **preserves
  already-rendered stages**, and offers the reload/resume path. Never a raw error or a
  frozen spinner.

## 6. Security invariants (unchanged; FR-018, Constitution VI)

- No secret is accepted, displayed, or persisted anywhere on this screen; the follow
  pointer stores only `runId`/status/missionId/checkpoint (non-secret, local-only).
- No server file is modified: bind `127.0.0.1`, no CORS `*`, `path_inside()`, https-only,
  keys-env-only all remain exactly as-is.

## Test contract (offline)

- **CancelControl.test.tsx**: no cancel without confirm; on confirm `cancelMission` is
  called and `status` settles to `cancelled`; control absent when settled; no double-fire.
- **TerminalPanel.test.tsx**: `done` ⇒ detail + PDF actions call `getMission`/
  `fetchMissionPdf`; `error`+checkpoint ⇒ resume calls `runMission` with `resumeFrom`;
  `error` no checkpoint ⇒ only retry/return; every terminal has a forward action.
- **followPointer.test.ts**: record on launch/terminal; single pointer; reload with
  resumable error pointer ⇒ resume offer; with done pointer ⇒ completion handoff; dismiss
  clears; no secret fields present.
- **MissionTimeline.test.tsx**: simulated stream drives live stage updates; empty state when
  idle+no pointer; connection-lost preserves stages; keyboard-operable; stage changes
  announced via an ARIA live region (WCAG 2.1 AA, FR-019).
