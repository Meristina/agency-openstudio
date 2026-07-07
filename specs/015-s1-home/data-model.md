# Phase 1 Data Model — S1 Home

S1 introduces **no new persisted entity**, **no new store**, and **no new endpoint**. It
reads existing client-side state and one existing read-only endpoint, and derives
**ephemeral view-models** in a pure `homeModel.ts` for display. Nothing here defines a new
database, table, file format, or wire contract.

## 1. Existing state Home reads (no copy owned by Home)

| Source | Origin (single source of truth) | Storage | Home usage |
|---|---|---|---|
| Unfinished brief draft | `screens/brief/briefDraft.ts` (`loadBriefDraft`) | `localStorage` `studio.briefDraft.v1` | Read only — detect resumability; navigate to resume the brief |
| Recent missions | `api.ts` `listMissions()` → `GET /api/missions` | server (read-only) | Read only — up to 5, global, most-recent-first |
| Follow-pointer (live run) | `screens/missions/followPointer.ts` (`read`) | `localStorage` `agency.studio.followPointer.v1` | Read only — decide whether a mission is the in-progress live run |
| Active working context | `shell/ClientContext.tsx` (`useClientContext`) | `localStorage` `agency-studio.prefs.clientContext` | Read only — render the read-only context label; never edited by Home |

Home **writes nothing** except the intent it hands to the brief route
(`#/brief?intent=…`), which is byte-identical to today's behavior.

## 2. RecentMissionItem (ephemeral view-model — derived by `homeModel.ts`)

The plain-language, display-ready projection of one `MissionSummary`. Derived, never
persisted.

| Field | Type | Source | Notes |
|---|---|---|---|
| `label` | string | `MissionSummary.goal` (trimmed, truncated) | Human goal; falls back to a generic catalog label if goal is empty. **Never** a raw `mission_id` |
| `statusKey` | `CatalogKey` | derived from `delivered` / `verdict` / in-progress signal | One of the `home.recent.*` status keys (in progress / delivered / needs attention) — catalog-driven, never a raw verdict token |
| `target` | string (hash URL) | `mission_id` + state | `#/missions` if this is the in-progress live run (matches `followPointer.runId`), else `#/library?deliverable=<mission_id>` |
| `key` | string | `MissionSummary.mission_id` | React list key / internal only — **not** rendered as operator content |

- **Cardinality / ordering**: at most **5** items, most-recent-first (the API order is
  preserved; the model only caps and maps). A "see all" affordance links to `#/library`
  (the full browsable list of work — `#/missions` shows only the live/last run).
- **State → target rule (FR-005, D2)**: a mission is treated as **in-progress** when it
  matches the persisted `followPointer.runId` with a running status; such a mission targets
  the live timeline (`#/missions`). Every other mission targets its Library deliverable
  (`#/library?deliverable=<mission_id>`). No new per-mission route is introduced.
- **Status mapping**: `delivered === true` → delivered; a terminal non-pass verdict →
  needs-attention; otherwise → in-progress. All three resolve to a `home.recent.*` catalog
  key; the raw `verdict` string is never displayed.

## 3. ResumeDraftView (ephemeral view-model)

| Field | Type | Source | Notes |
|---|---|---|---|
| `canResume` | boolean | `hasResumableDraft(loadBriefDraft())` | True when a non-empty unfinished brief exists |
| `target` | string | constant | `#/brief` (the guided brief reopens itself at the saved `stepIndex` via the existing draft-resume flow) |

Home does not reconstruct the brief; it only detects a resumable draft and navigates —
the guided brief owns draft loading and step restoration (existing `brief.draft.*` flow).

## 4. ContextLabelView (ephemeral view-model)

| Field | Type | Source | Notes |
|---|---|---|---|
| `text` | string \| null | `useClientContext()` (`client`/`project`/`campaign`) | Plain composed label of the active scope; `null` when nothing is set |
| `noneKey` | `CatalogKey` | constant | `home.context.none` — shown when `text` is null ("no context / all work"), never a blank/broken label |

Read-only. Editing the context stays in S8 Settings; Home never mutates it (FR-012).

## 5. Validation & honesty rules (cross-cutting)

- **No invented state (III)**: `RecentMissionItem[]` is exactly the (capped) mapping of
  the real `listMissions()` result. An **empty** result renders the calm empty state; a
  **failed** load renders an honest load-error note — the two are distinct and never
  conflated into a false "no work" (D4, FR-008).
- **Start flow independence (FR-007)**: the start section renders synchronously and is
  never gated on the recent-work read.
- **No raw machine tokens (VIII)**: `mission_id`, `runId`, and `verdict` are internal
  only; operator-facing content is always a plain label + a catalog-keyed status/label.
- **Byte-identical intent→brief (X)**: the start action builds the same
  `#/brief?intent=<encoded>` URL as today, including the empty-intent case.
