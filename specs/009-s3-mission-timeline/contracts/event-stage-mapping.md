# Contract — Event → Human-Stage Mapping (`humanStages.ts`)

The projection contract: how the existing `TimelineModel` (from `groupTimeline(events)`)
becomes the curated operator-facing `HumanStage[]`. This is a **pure, synchronous,
offline-testable** function — no React, no fetch, no clock. It is the heart of FR-001–FR-006
and SC-002.

## Signature

```ts
humanStages(model: TimelineModel, t: Translate): HumanStage[]
```

`t` is the umbrella translator (so labels resolve from the EN/FR catalog; the function
itself emits catalog keys + interpolation values, never English literals).

## Ordered stage derivation

Stages are emitted in this fixed order, **each included only when its underlying data is present**:

| # | Stage `key` | Included when | `state` derivation | Drill-down (`detail`) |
|---|-------------|---------------|--------------------|------------------------|
| 1 | `prepare` | any of `retrieval, visual, websearch, mcp, mcpTools, graph, persona` ≠ null | running if any sub-step `running`; done if all present sub-steps `done`/`skipped` | one row per present sub-step: sources/material/knowledge/tools/personas, with plain-language `labelKey` + count |
| 2 | `departments` | `route` ≠ null OR `depts` non-empty | running if any dept not `done`; done if all `done` | one row per `depts[i]`: department plain-language name + running/done |
| 3 | `synthesis` | `synth` non-empty | running if any iteration not `done`; done if all `done` | rows per synthesis iteration (usually one) |
| 4 | `inspection` | `inspect` non-empty OR `verify` non-empty | running until the latest round has a verdict AND (no verify, or verify done); done when latest round settled | one `HumanIteration` per round (fix loop): round N, verdict, verified ok/rate |
| 5 | `media` | `assets` non-empty | running if any asset `running`; done if all `ok`/`failed`/`skipped` | one row per asset: kind (image/voice/video) + state, `failed`/`skipped` carry a plain reason |

**Terminal is NOT a stage** — it drives `TerminalPanel`, not `StageList` (see `session-handoff.md`).

## Fix-loop rule (FR-004)

Multiple `inspect`/`verify` iterations ⇒ multiple `HumanIteration` rows under the single
`inspection` stage, labelled as human "quality round N". A round that sent work back
(followed by a further synth/inspect iteration) is presented as **normal revision in
progress**, never as an error or stall. The stage stays `running` across rounds until the
final round settles.

## Wording rules (FR-005, SC-002)

- Every visible string resolves from a `missions.*` catalog key; **no** `dept` key,
  engine name, phase code, flag, or env var may appear in output — department keys map
  through `missions.dept.<key>` catalog entries (unknown dept key ⇒ a generic
  `missions.dept.generic` label, never the raw key).
- Counts/names are interpolation values passed to `t`, never concatenated English.
- Applies identically in EN and FR (catalog completeness enforced by the i18n test).

## Safety rules (FR-006)

- Input is always the output of `groupTimeline`, which already de-duplicates repeated
  dept/iteration frames and drops unknown phases via its `default` branch — so
  `humanStages` never receives a raw unknown event.
- `humanStages` must be **total**: any `TimelineModel` (including the empty
  `groupTimeline([])`) returns a valid array (possibly empty) and never throws.
- Ordering is deterministic and independent of event arrival batching (a burst yields the
  same array as the same events delivered one-by-one).

## Catalog keys introduced (`missions.*`)

Illustrative (final list finalized in tasks); EN + FR, keyed identically:

```
missions.stage.prepare / .departments / .synthesis / .inspection / .media           # stage titles
missions.state.upcoming / .running / .done / .skipped                                 # stage status labels
missions.round               # "Quality round {n}"
missions.detail.sources / .material / .knowledge / .tools / .personas / .asset        # drill-down labels
missions.dept.<deptKey> / missions.dept.generic                                       # plain department names
```

## Test contract (`humanStages.test.ts`)

1. `groupTimeline([])` ⇒ `humanStages` returns `[]` (drives the empty state upstream).
2. A representative stream (route + 3 depts + 2 synth/inspect rounds with a fix loop +
   websearch present, assets absent) ⇒ stages in fixed order, `prepare` present with a
   sources row, `media` **absent**, `inspection` with **two** `HumanIteration` rounds.
3. State transitions: a `dept start`-only model ⇒ `departments` stage `running`; add its
   `done` ⇒ `done`.
4. Absence: a plain run with no pre-route steps and no assets ⇒ neither `prepare` nor
   `media` appears (no empty placeholder).
5. Wording: assert **zero** raw dept keys / phase codes in the emitted keys+values; an
   unknown dept key falls back to `missions.dept.generic`.
