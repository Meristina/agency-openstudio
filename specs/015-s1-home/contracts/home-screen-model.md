# Contract — Home Screen Model (frontend)

S1 exposes **no new wire contract** (no endpoint added). This document is the **frontend
contract**: the region map, the existing sources of truth Home consumes, the pure-model
derivations, the navigation targets, the degradation rules, and the catalog keys. It is
the reference the tasks and tests are written against.

## A. Region map (one screen, four additive regions)

| Region | Component | Purpose | Data dependency |
|---|---|---|---|
| Start (P1) | `StartSection` | Question + intent textarea + start button | **None** — renders synchronously |
| Resume (P2) | `ResumeSection` | Unfinished brief + up-to-5 recent missions | `loadBriefDraft`, `listMissions` (fails soft) |
| Orient (P3) | `ShortcutsSection` | Shortcuts → Library / Import / Models | None (static nav) |
| Orient (P3) | `ContextLabel` | Read-only active-context label | `useClientContext` (synchronous) |

`Home.tsx` orchestrates: it renders Start + Shortcuts + ContextLabel immediately and loads
recent missions once for Resume, independently and fail-soft.

## B. Sources of truth (reused, not re-created)

| Concern | Reused API | Contract |
|---|---|---|
| Start → brief | `navigate("#/brief?intent=<encodeURIComponent(intent.trim())>")` | **Byte-identical** to today; empty intent → `#/brief` (no query), still navigates |
| Unfinished brief | `loadBriefDraft()` (`screens/brief/briefDraft.ts`) | Read only; resume via `navigate("#/brief")` (brief restores its own `stepIndex`) |
| Recent missions | `listMissions()` (`api.ts`, no filter) | Read only; global, most-recent-first; caller caps at 5 |
| Live-run detection | `followPointer.read()` (`screens/missions/followPointer.ts`) | Read only; a mission whose `mission_id`/`runId` matches the running pointer is "in progress" |
| Active context | `useClientContext()` (`shell/ClientContext.tsx`) | Read only; **never** mutated by Home |
| Navigation | `navigate()` (`shell/router.tsx`) | Existing hash router |

## C. Pure model — `homeModel.ts` (fully offline-testable)

```text
recentMissionsView(missions: MissionSummary[], pointer: FollowPointer | null): RecentMissionItem[]
  - take at most 5, preserving input order (most-recent-first)
  - for each: label = humanized goal (trim + truncate; fallback catalog label if empty)
              statusKey = delivered ? home.recent.delivered
                        : terminalFailVerdict ? home.recent.failedVerdict (needs attention)
                        : home.recent.inProgress
              target = isLiveRun(mission, pointer) ? "#/missions"
                                                   : `#/library?deliverable=${mission.mission_id}`
  - NEVER emit mission_id / runId / raw verdict as label or status text

hasResumableDraft(draft: BriefDraft | null): boolean
  - true when a non-empty unfinished brief exists

contextLabelView(ctx: {client,project,campaign}): { text: string | null }
  - compose a plain label from set parts; null when nothing is set (→ home.context.none)
```

Determinism: no clock, no randomness, no network — same inputs → same output.

## D. Navigation targets (all existing routes)

| Action | Target | Notes |
|---|---|---|
| Start brief | `#/brief?intent=…` / `#/brief` | Unchanged from today |
| Resume unfinished brief | `#/brief` | Brief restores saved step |
| Open in-progress mission | `#/missions` | Live timeline (matches follow-pointer) |
| Open completed mission | `#/library?deliverable=<mission_id>` | Existing Library focus param |
| See all recent work | `#/library` | Full browsable mission list (Library) — **not** `#/missions`, which shows only the live/last run |
| Shortcut: Library / Import / Models | `#/library` / `#/import` / `#/models` | Existing routes |

**No new route is registered; the `home` route stays `shipped`.**

## E. Degradation rules (honesty)

| Condition | Behavior |
|---|---|
| No draft **and** no missions | Calm empty state → guides to start; no blank/dead region |
| `listMissions()` rejects | Start flow fully usable; honest `home.recent.loadError` note; **no** false empty, **no** perpetual spinner |
| Recent list still loading | Start flow already interactive; Resume shows a bounded loading state (`state.loading`) that resolves or errors |
| Context unset | `home.context.none` label ("no context / all work"), never blank |

## F. Catalog keys (new `home.*`, added to `catalog.ts` + `en.ts` + `fr.ts`)

New (indicative; final names fixed in tasks):
`home.resume.title`, `home.resume.draft`, `home.resume.recentTitle`,
`home.recent.inProgress`, `home.recent.delivered`, `home.recent.failedVerdict`,
`home.recent.empty`, `home.recent.loadError`, `home.recent.seeAll`,
`home.shortcuts.title`, `home.shortcuts.library`, `home.shortcuts.import`,
`home.shortcuts.models`, `home.context.scopedTo`, `home.context.none`.

Reuse existing: `home.question`, `home.intentLabel`, `home.intentPlaceholder`,
`home.start`, `nav.*`, `context.*`, `brief.draft.*`, `state.loading`, `state.error`.

Every new key MUST exist in **both** `en.ts` and `fr.ts` (parity), typed via `CatalogKey`.

## G. Test contract (Vitest, offline)

- `homeModel.test.ts` — cap at 5; order preserved; in-progress vs delivered vs
  needs-attention → correct `statusKey` and `target` (`#/missions` vs
  `#/library?deliverable=<id>`); never emits raw `mission_id`/`verdict`;
  `hasResumableDraft` true/false; `contextLabelView` set/unset.
- `Home.test.tsx` — intent → `#/brief?intent=…` (and empty intent → `#/brief`)
  byte-identical; resume draft → `#/brief`; recent list renders + opens by state; empty
  state calm; `listMissions` rejection → start flow works + honest note (no false empty,
  no infinite spinner); EN + FR render; keyboard/a11y.

## H. Security / invariants

- No new endpoint, no new user-input surface (only the existing free-text intent, still
  URL-encoded into the brief route as today) → no traversal/injection surface added.
- No secret displayed, entered, persisted, or logged; no outbound network of Home's own;
  no network toggle (per-mission opt-in untouched).
- Served from `127.0.0.1`; no CORS `*`. `agencykit/` subtree untouched.
