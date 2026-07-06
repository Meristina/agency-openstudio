# Phase 1 Data Model: Guided Brief (S2)

**Date**: 2026-07-06 · **Input**: [spec.md](./spec.md) Key Entities, [research.md](./research.md)

All entities are frontend-only (TypeScript, `app/studio/src/screens/brief/`); the
server keeps its existing mission request shape (see
[contracts/brief-mission-mapping.md](./contracts/brief-mission-mapping.md)).

## Brief

The structured result of the flow. One instance drives the whole screen.

| Field | Type | Notes |
|---|---|---|
| `intent` | `string` | Required. Seeded from `?intent=` (URL-decoded, trimmed) or asked as step 1. Length-limited (generous, stated limit — spec edge case). |
| `deliverableType` | `"research" \| "strategy" \| "video"` | Required. Selects the question set (v1 trio, clarification Q2). |
| `sector` | `{ id: string } \| { other: string }` | Curated list id, or free text via the "other" escape. Skippable → `null`. |
| `answers` | `Record<QuestionId, Answer>` | Only answers for questions the active set marked relevant. |
| `deliverableLanguage` | `string` (BCP-47-ish label, e.g. `"en"`, `"fr"`, free choice) | Required. Defaults to interface language; independent thereafter (FR-008). |
| `research` | `boolean` | Mission internet research. Default `true` (FR-012a, clarification Q1). |
| `attachment` | `ClientAttachment \| null` | `null` ⇒ unassigned bucket. |
| `options` | `ProductionOption[]` | Effective per-type options (e.g. video rendering acknowledgement). |

**Validation rules** (all with plain-language, localized messages):
- `intent` non-empty after trim; over-limit flagged, never silently truncated.
- Required steps: intent, deliverable type, deliverable language (FR-005) — everything else defaults or skips.
- `attachment` names must pass the client-side mirror of Brick 6 `clean_name` rules (non-empty, sane length) so the server's 400 is never the first feedback.

## QuestionSet / Question

Curated typed data (`questionSets.ts`), one set per deliverable type.

| Field | Type | Notes |
|---|---|---|
| `type` | deliverable type | Set selector. |
| `questions` | `Question[]` | Ordered. |
| `Question.id` | `string` | Stable; keys `Brief.answers`. |
| `Question.kind` | `"choice" \| "shortText" \| "longText" \| "language" \| "sector" \| "toggle" \| "attachment"` | Input component selector (`attachment` = the US3 taxonomy picker step). |
| `Question.labelKey` / `helpKey` / per-choice keys | `CatalogKey` | Every visible string is a typed catalog key (FR-007) — completeness enforced by test. |
| `Question.relevant?` | predicate on partial Brief | Sector/type-conditional questions (FR-002). |
| `Question.defaultValue?` / `skippable` | | FR-005. |
| `Question.compose` | mapping into the goal text / flags | Consumed by `composeMission` (research D1/D2). |

**Rule**: adding a deliverable type = adding a `QuestionSet` entry; no flow-engine change (FR-003).

## BriefDraft

Single localStorage entry (`studio.briefDraft.v1`, research D3).

| Field | Type | Notes |
|---|---|---|
| `version` | `1` | Mismatch ⇒ treated as no draft. |
| `brief` | partial `Brief` | Answers so far. |
| `stepIndex` | `number` | Resume position (FR-021). |

Lifecycle: saved on every answer commit → offered as resume-or-discard on entry →
cleared on discard and on successful launch. Never synced, never secret (FR-020).

## ProductionOption

Plain-language descriptor of a choice that affects how the mission runs (spec entity).

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | e.g. `videoRendering`. |
| `labelKey` / `valueKey` | `CatalogKey` | Review display. |
| `paidOffMachine` | `boolean` | `true` ⇒ explicit opt-in acknowledgement required; default is always the free/local value (FR-012). Mission research is **not** one of these (FR-012a). |

## ClientAttachment

| Field | Type | Notes |
|---|---|---|
| `client` | `string` | Existing (picked from `fetchTaxonomy()` tree) or new free string (inline creation, research D9). |
| `project` / `campaign` | `string \| null` | Optional drill-down. |

## MissionSession

Module-scoped singleton (research D7) — the launched run's browser-side lifeline.

| Field | Type | Notes |
|---|---|---|
| `state` | `"idle" \| "launching" \| "running" \| "failed" \| "done"` | Double-launch guard: `launch()` is a no-op unless `idle`/`failed`. |
| `runId` | `string \| null` | From the first SSE frame; enables `cancelMission`. |
| `events` | `MissionEvent[]` | Buffered for the future S3 timeline. |
| `error` | localized description \| `null` | 409 blockers and transport errors, plain language (FR-019). |

## Screen state machine (`GuidedBrief.tsx`)

```text
entry ──draft?──> resumePrompt ──resume──> flow(stepIndex)
  │                    └──discard──> flow(0)
  └─no draft─────────────────────────> flow(0)
flow(n) ──back/next (answers kept)──> flow(n±1) ──last──> review
review ──edit(q)──> flow(at q) ──return──> review
review ──launch──> launching ──runId──> launched   (draft cleared)
                      └──409/error──> review+error  (brief intact, retry allowed)
```

State transitions preserve answers in every arrow above except `discard` (FR-006,
FR-016, FR-019, FR-021).
