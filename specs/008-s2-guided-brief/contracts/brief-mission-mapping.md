# Contract: Brief → Mission Launch (S2 ↔ existing server)

**Consumer**: `composeMission.ts` + `missionSession.ts` · **Provider**: existing
`POST /api/mission` (`agency_studio/server.py` — **unchanged by this feature**).

## Request body produced by the brief

| Body field | Source in Brief | Rule |
|---|---|---|
| `goal` | composed text (below) | Operator answers verbatim, labeled sections, no fabricated content. |
| `engine` | — | Omitted → existing API-client default (`claude-code`); S2 never selects engines. |
| `web_search` | `brief.research` | **`true` by default** (FR-012a); `false` only on explicit operator switch-off. |
| `video` | deliverable type = video | `true` only for the video deliverable. |
| `assets` | per question set | Only when the type's set enables asset production (v1: the video type only); never implicitly `true` for research/strategy. |
| `mcp`, `knowledge`, `mcp_tools`, `personas`, `visual` | — | Always `false` in v1 (not brief concerns; console still exposes them). |
| `escalation`, `verification` | — | **Omitted** → server defaults apply (research D8); effects shown read-only on the review. |
| `client`, `project`, `campaign` | `brief.attachment` | Free strings (Brick 6 `clean_name` semantics); omitted when unassigned. New client name ⇒ inline creation (research D9). |
| `resume_from` | — | Never sent by S2 (crash-recovery is a console/S3 concern). |

## Composed goal text (shape, not verbatim template)

Labeled plain-text sections, in this order, skipping empty ones:
`Intent` (operator's text, verbatim) · `Deliverable` (type, in English for the
mission loop) · `Deliverable language` ("Write the deliverable in <language>.") ·
`Sector / domain` · one line per answered type-specific question (question label +
answer verbatim) · `Constraints` (if answered).

Rules: answers are never paraphrased, summarized, or augmented; empty/skipped
answers produce no line; the composed text is deterministic for a given brief
(snapshot-testable).

## Responses the brief must handle

| Response | Meaning | Screen behavior |
|---|---|---|
| `200` + SSE stream | Launch accepted | First frame carries the run id → state `running`; stream owned by `missionSession` (survives navigation); draft cleared. |
| `409` JSON `{error, blockers[]}` | Capability preflight failed (pre-SSE) | Plain-language blocker panel + link to `#/models`; brief intact; retry allowed (FR-013/FR-019). |
| `400` JSON | Bad field (e.g. invalid client name) | Should be prevented client-side; if it happens: plain-language error, brief intact. |
| `422` JSON | Engine not validated | Plain-language error, brief intact (no engine choice in S2 — points to console/settings). |
| Network failure / service down | Studio unreachable | Shell connection-state language; brief intact; retry allowed. |

## Invariants

- Zero server changes: this contract only *selects among* existing request fields and
  existing responses.
- A default-launch (operator changed nothing) enables `web_search` only — zero paid
  or off-machine options (SC-004 test hook: assert on the composed body).
- One completed brief ⇒ at most one launch (double-activation guard in
  `missionSession`).
