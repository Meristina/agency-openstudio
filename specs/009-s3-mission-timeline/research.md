# Phase 0 Research — Mission Timeline (S3)

All Technical Context items are resolved (no open NEEDS CLARIFICATION). This file records
the load-bearing design decisions, each grounded in the existing codebase and the four
`/speckit-clarify` answers (2026-07-06).

## D1. Reuse the existing pure fold — do not re-implement event grouping

- **Decision**: Consume the existing `app/studio/src/timeline.ts` — `groupTimeline(events): TimelineModel` and `runStatus(model)` — as the single source of the technical timeline model. S3 adds only a *presentation projection* on top; it never re-folds the raw event stream.
- **Rationale**: `groupTimeline` already handles every `MissionEvent` phase (route, dept, synth, inspect+verdict, verify, asset, the seven best-effort pre-route phases, and the three terminals done/error/cancelled), with correct de-duplication of repeated dept/iteration frames and a `never` exhaustiveness guard. Re-implementing would duplicate a tested contract and risk drift (Constitution X: additive, no behavior change). The fold is already React-free and unit-tested (`timeline.test.ts`), so it is directly reusable off the SSE stream S2 already accumulates in `missionSession.events`.
- **Alternatives considered**: (a) a new S3-specific fold — rejected: duplication + drift risk; (b) fold on the server and stream pre-grouped stages — rejected: server change, violates FR-016/Constitution X.

## D2. Human-stage projection: `TimelineModel → HumanStage[]` (curated + drill-down)

- **Decision**: A new pure function `humanStages(model, t): HumanStage[]` maps the 14-field `TimelineModel` into a small ordered set of operator-facing stages, matching clarification Q2 (curated stages + optional drill-down):
  1. **Preparation / gathering facts** — present only if any of `retrieval | visual | websearch | mcp | mcpTools | graph | persona` is non-null; its drill-down lists those sub-activities in plain language (e.g. "checked X sources", "consulted prior material"), each shown only when it actually occurred (FR-003).
  2. **Departments at work** — from `model.depts` (+ `route`); drill-down lists each department's plain-language name and done/running state.
  3. **Drawing everything together** — from `model.synth` iterations.
  4. **Quality inspection** — from `model.inspect` + `model.verify` iterations; **multiple iterations render as successive "quality round N" entries** (the fix loop, FR-004), never as an error.
  5. **Producing media** — present only if `model.assets` is non-empty (image/tts/video renders); drill-down shows each asset's state.
- Each `HumanStage` carries `{ key, state: "upcoming"|"running"|"done"|"skipped", detail: HumanDetail[] }`. State is derived from the underlying steps (any running ⇒ running; all done ⇒ done; none started ⇒ upcoming). The default view shows the stage rows; the detail array is revealed on expand.
- **Rationale**: Keeps the projection pure and offline-testable (Constitution VII); default view stays legible for non-technical operators (Constitution VIII / umbrella S3 one-liner) while curious users get depth. Department/phase → plain-language labels come from the catalog, so **no raw key, engine name, or phase code ever reaches the DOM** (FR-005, SC-002).
- **Alternatives considered**: (a) curated stages only, no detail — rejected by clarification Q2; (b) full per-event list — rejected (overwhelming, largest test surface); the dev console already provides the raw view.

## D3. Reload → checkpoint-resume via a local follow pointer

- **Decision**: On launch and on every terminal, S3 writes a single **follow pointer** to `localStorage`: `{ runId, status, missionId?, resumable?, checkpoint? , updatedAt }`. `missionSession` is in-memory and is lost on a full reload; the pointer is what survives. On mount, if the in-memory session is idle **but** a pointer exists whose last state was interrupted/resumable, S3 offers **resume-or-dismiss**; resume calls the existing `POST /api/mission` with `{ resume_from: <runId> }` (server documents this at `server.py:16`, "run (or resume, via body {resume_from: id})", stable id across resume at `server.py:564-565`). A pointer whose last state was `done` shows the completion handoff (D5) instead; a pointer with no checkpoint falls back to the honest terminal/empty state.
- **Rationale**: Honors clarification Q1 (no live re-attach; offer checkpoint-resume) **without any server change** — the resume endpoint and on-disk checkpoints already exist; S3 only needs to remember the run id locally. Same local-only, non-secret persistence pattern as the S2 brief draft and umbrella preferences (Constitution IV/VI). In-app navigation still shows the live run because `missionSession` is a module-level singleton that survives route changes (FR-015).
- **Alternatives considered**: (a) true live re-attach to a running SSE — rejected: requires a new server-side run-registry/reconnect stream (out of scope, FR-016); (b) forget the run on reload and always start over — rejected: dishonest/wasteful, contradicts Q1 and Constitution III's honesty spirit; (c) server endpoint to list resumable checkpoints — rejected: unnecessary server surface when the run id is cheap to persist locally.

## D4. Cancel-with-confirm and the finish/cancel race

- **Decision**: The stop control requires an explicit plain-language confirmation (work will be lost), then calls `missionSession.cancel()` — which already `controller.abort()`s the SSE fetch and `POST`s `/api/mission/{runId}/cancel` (returns 202). The control is hidden once `status` is settled (`done|failed|cancelled`) and guarded against double-activation. The finish/cancel race is already resolved inside `missionSession.launch`'s catch (a settled reset/terminal is not overwritten); S3 renders strictly off the session's final `status`, so exactly one terminal is shown (FR-009, US2 scenario 5).
- **Rationale**: Reuses the existing, already-hardened cancel path (`api.ts:cancelMission`, `missionSession.cancel`) and its race handling; S3 adds only the confirmation and the settled-state gating. No new cancellation semantics (Constitution X).
- **Alternatives considered**: cancel without confirmation — rejected: discards work silently (FR-007); a new cancel endpoint — unnecessary.

## D5. Done handoff → existing mission-detail surface + PDF (interim until S4)

- **Decision**: On `terminal.kind === "done"`, the completion panel shows the verdict and forward actions that reuse existing endpoints: **Open details** (loads the dossier via `getMission(missionId)` / navigates to the existing mission-detail surface) and **Download PDF** (`fetchMissionPdf(missionId)` → Blob, `[pdf]` extra). When S4 (Deliverable Library) ships, the primary forward action re-targets the library; the panel structure is unchanged (clarification Q3, FR-010).
- **Rationale**: Gives the operator a real, usable deliverable at completion from day one ("never a dead end", FR-013) using surfaces that already exist (`api.ts:getMission/fetchMissionPdf`, `components/MissionDetail.tsx`), with no new server work.
- **Alternatives considered**: a coming-soon placeholder (rejected by Q3 — operator can't reach their work); PDF-only (rejected — narrower than a full detail view).

## D6. Promote `missionSession` to a shared location

- **Decision**: Move `screens/brief/missionSession.ts` → `screens/session/missionSession.ts` (and its test), updating the two import sites (S2's `GuidedBrief.tsx` launcher, S3's follower). Behavior byte-identical.
- **Rationale**: The launch session is now shared by two screens (S2 writes, S3 reads); a brick-local `brief/` path would make S3 depend on S2's internal folder. A neutral `session/` home reflects the shared ownership. Pure move + import update (Constitution X).
- **Alternatives considered**: leave it under `brief/` and import across screens — rejected: leaks S2 internals into S3; re-export shim — rejected: needless indirection.

## D7. Latency, bursts, and unknown-event safety

- **Decision**: The projection is a synchronous pure fold recomputed from `session.events` on each subscription publish; a stage reflects a received event within one render frame (Performance Goal). A burst just yields more events before the next paint — `groupTimeline` de-duplicates, so the final model is order-correct regardless of batching (FR-006). An unrecognized event phase hits `groupTimeline`'s `default` branch (ignored) and never reaches the projection, so it cannot leak a raw code or crash the view.
- **Rationale**: Resolves the one deferred spec item (a quantified freshness target) with the natural push-model answer — no polling, no manual refresh (FR-001). Reuses the fold's existing safety guarantees.
- **Alternatives considered**: a hard millisecond SLA with instrumentation — rejected: over-specification for a local pure-state update; throttled re-render — rejected: unnecessary at mission event volumes.

## D8. Connection-lost presentation

- **Decision**: A mid-run stream drop surfaces via the shell's existing connection state (the umbrella `ConnectionBanner`) plus a calm in-screen note; already-rendered stages are preserved, and the follow pointer enables the reload/resume path (D3). No raw error, no frozen spinner (FR-016).
- **Rationale**: Reuses the umbrella's connection indicator (consistency, Constitution VIII); `missionSession` surfaces a non-AbortError failure as `status:"failed"` with a message that S3 wraps in plain language (FR-011).
- **Alternatives considered**: a bespoke S3 connection widget — rejected: duplicates the shell banner.

## Dependencies, licensing, security

- **New dependencies**: none. **`docs/LICENSES.md`**: no change (Constitution IX).
- **Server surface**: none touched — bind/CORS/`path_inside`/https-only/keys-env-only all unchanged (Constitution VI); the dev console's raw `Timeline.tsx` stays byte-identical.
- **Offline tests**: a simulated event source (an array of `MissionEvent`s pushed through a fake `runMission`) plus mocked `cancelMission`/`getMission`/`fetchMissionPdf`; no network, CLI, or live server (Constitution VII).
