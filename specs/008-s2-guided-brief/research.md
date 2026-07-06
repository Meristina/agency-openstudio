# Phase 0 Research: Guided Brief (S2)

**Date**: 2026-07-06 · **Input**: [spec.md](./spec.md) (clarified), [plan.md](./plan.md)

No NEEDS CLARIFICATION markers remained after `/speckit-clarify`; this research
resolves the **integration decisions** the plan depends on, each grounded in direct
inspection of the existing code (file:line refs current at time of writing).

## D1 — Brief → mission: compose a structured goal text, zero server change

**Decision**: `composeMission.ts` turns the completed brief into (a) a structured
plain-text goal — labeled sections for intent, deliverable type, sector/domain,
audience/objective/key-message answers, and the deliverable language ("Write the
deliverable in French.") — and (b) the existing request fields: `web_search`,
`video`, `assets`, and the `client`/`project`/`campaign` taxonomy strings.

**Rationale**: `POST /api/mission` already accepts everything the brief needs
(`_parse_mission_request`, `agency_studio/server.py:1241` — goal + opt-in flags +
taxonomy fields validated by `taxonomy.validate_fields`). The mission loop consumes a
goal string; a structured text brief is exactly what the router/departments expect.
Composing text client-side keeps the server byte-identical (Constitution X) and the
answers verbatim (Constitution III — the composer adds labels, never content).

**Alternatives considered**: a new server-side `brief` object/endpoint (rejected:
invasive, new surface to secure and test, no consumer — the loop wants a goal);
stuffing answers into JSON inside the goal (rejected: departments read prose, not
JSON; harms mission quality).

## D2 — Question sets: typed data modules, catalog-keyed

**Decision**: `questionSets.ts` declares the three v1 sets (research / strategy /
video) as typed data: each question = id, catalog key(s), input kind (choice / short
text / long text / language / sector), relevance predicate (deliverable type,
sector), default or skippable marker, and answer→composer mapping. The curated sector
list is data in the same module with an "other" free-text escape.

**Rationale**: the clarification fixed curated deterministic sets; data modules make
them offline-testable (shape test + catalog-completeness test), 100% localizable
through the umbrella's typed `CatalogKey` mechanism (`i18n/catalog.ts`), and
extensible per spec FR-003 (a new deliverable type = a new set, no flow redesign).

**Alternatives considered**: JSON files fetched at runtime (rejected: loses the typed
catalog-key check that keeps EN/FR complete); agent-generated questions (rejected by
clarification Q4).

## D3 — Draft: single versioned localStorage entry

**Decision**: `briefDraft.ts` persists one draft under a versioned key (e.g.
`studio.briefDraft.v1`): answers, flow position, and a schema version; `load` returns
null on version mismatch or parse failure (treated as "no draft"); `discard` removes
the key. Saves happen on every answer commit.

**Rationale**: matches the umbrella's established non-secret `localStorage` pattern
(language, client context — 007 plan "Storage"); satisfies spec FR-020/FR-021 (single
draft, restart survival, resume-or-discard) with no server surface. Answers are
user-authored, non-secret by FR-014 (the flow never collects credentials).

**Alternatives considered**: server-side drafts (rejected: new endpoint + persistence
for a strictly local, per-operator concern); multiple drafts (rejected by spec — at
most one).

## D4 — Web research default-on maps to the existing `web_search` flag

**Decision**: the composer sends `web_search: true` unless the operator switches the
plainly-worded research toggle off in the flow. The brief module owns this default;
`api.ts`'s `runMission` default (`false`, `api.ts:180`) is not changed — the brief
passes the value explicitly.

**Rationale**: clarification Q1 (spec FR-012a). Leaving `runMission`'s own default
untouched keeps every other caller (console) byte-identical (Constitution X).

**Alternatives considered**: flipping the default inside `runMission` (rejected:
changes console launch behavior — invasive); non-switchable always-on (rejected by
clarification).

## D5 — Capability blockers: pre-check at review, server 409 as the backstop

**Decision**: on entering the review with `video` (or asset-producing options)
enabled, the screen calls the existing `fetchCapabilities()` and shows a
plain-language blocker panel (with a link to `#/models`) when the needed family has
no usable backend. Launch failures still handle the server's pre-SSE JSON 409
(`mission blocked: required capabilities unavailable`, `server.py:1104-1109`) with
the same plain-language presentation — the brief is preserved either way.

**Rationale**: satisfies spec FR-013 ("at the latest, the review") with zero new
server surface; the server 409 arrives *before* the SSE stream opens, so a blocked
launch is a clean JSON error the screen can render without losing state (FR-019).

**Alternatives considered**: client-side preflight only (rejected: duplicates
authority — the server check is the truth); server check only (rejected: FR-013 wants
the blocker before launch).

## D6 — Paid/cloud labeling read from the Brick 4 inventory; selection stays in S7

**Decision**: when the video deliverable is chosen, the flow's rendering step reads
`fetchCapabilities()` and presents the *effective* video backend in plain language —
"on this machine (free)" vs "cloud service (paid, leaves your machine)" — with local
free as the presented default and an explicit opt-in acknowledgement when the
effective backend is cloud/paid. Changing which model/backend is selected remains
S7's job (`#/models`, Brick 4 selection API); the brief links there instead of
duplicating selection UI.

**Rationale**: spec FR-012 requires explicit labeling, not a second model-management
surface; Brick 4 already owns selection (`/api/capabilities/selection`,
`server.py:914`) and the inventory exposes what is key-gated/cloud. One owner per
concern keeps S2 simple (Constitution VIII) and additive (X).

**Alternatives considered**: embedding model pickers in the brief (rejected:
duplicates S7, widens scope); ignoring backend nature at brief time (rejected:
violates FR-012's explicit-labeling requirement).

## D7 — Launched run survives navigation: module-scoped mission session

**Decision**: `missionSession.ts` holds the in-flight launch outside the React tree:
it starts `runMission(...)` (which streams SSE via fetch, `api.ts:164`), records the
announced run id, buffers received events, exposes subscribe/cancel, and guards
against double launch (spec edge case). `GuidedBrief.tsx` renders the "launched"
state from the session; navigating away does not abort the fetch (the AbortSignal
belongs to the session, not the component). S3 will later consume the same session
for its timeline; until then the launched state shows a plain confirmation with the
run id and links to the missions area (placeholder) — satisfying FR-018's
"or its localized placeholder".

**Rationale**: the SSE connection is the run's lifeline from the browser's
perspective (`cancelMission` is the explicit kill, `api.ts:146`); tying it to a
component would make "navigate away" behave like an implicit cancel or an orphaned
stream. A tiny module singleton is the smallest structure that survives unmount, is
trivially testable with a mocked `runMission`, and gives S3 a ready seam.

**Alternatives considered**: keeping the stream in the screen component (rejected:
navigation kills or orphans the run); launching fire-and-forget without reading the
stream (rejected: no run id → no cancel, no confirmation); a full shell-level
mission store (rejected: S3's scope — YAGNI now, the session module is its seed).

## D8 — Expert knobs: server defaults, surfaced read-only on the review

**Decision**: the brief sends **no** `escalation` and **no** `verification` field;
the server applies its own defaults (`verification` → `{min_sources: 3, resolve:
false}`, `server.py:1303-1316`; `escalation` → agency-kit default). The review states
the effect in plain language ("The result will cite at least 3 sources.") as
read-only text.

**Rationale**: clarification Q3 (no expert knobs in v1) + spec FR-015 (defaulted
values that affect the production stay visible on the review). Omitting the fields —
rather than sending copies of today's defaults — means a future server-side default
change propagates without touching S2.

**Alternatives considered**: sending explicit defaults (rejected: freezes server
policy into the client); hiding the effect entirely (rejected by FR-015).

## D9 — Inline client creation: free-string taxonomy fields, no new endpoint

**Decision**: the attachment step offers the Brick 6 tree via the existing
`fetchTaxonomy()` for picking, pre-selects the shell's active client context, and
implements "create a client by name" (spec FR-010) as simply submitting a new
free-string `client` value with the mission — Brick 6's registry records the
attribution and the taxonomy tree grows from it.

**Rationale**: Brick 6's design derives the taxonomy from mission attributions
(fields validated by `taxonomy.validate_fields`, persisted by the registry); a new
name *is* creation. Zero new server surface.

**Alternatives considered**: a dedicated create-client endpoint (rejected: Brick 6
intentionally has no standalone CRUD; would be invasive); restricting to existing
clients (rejected by FR-010).
