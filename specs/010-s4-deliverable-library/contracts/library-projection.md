# Contract — Library Projection (`libraryModel.ts`)

The pure, testable core of S4: turn the existing `MissionSummary[]` (plus the shell's
taxonomy and the operator's view state) into the grouped, searched, outcome-classified,
deduplicated `LibraryModel` the screen renders. No I/O, no network, no persistence — a
deterministic fold, so the whole projection is covered by offline unit tests
(Constitution VII).

## Signature

```ts
buildLibraryModel(
  missions: MissionSummary[],          // from listMissions()
  taxonomy: TaxonomyTree,              // from useClientContext().taxonomy
  scope: { client: string | null; project: string | null; campaign: string | null },
  view: { query: string; outcomeFilter: "all" | "successful" | "needs-attention" },
): LibraryModel
```

`classifyOutcome(m: MissionSummary): "successful" | "needs-attention"` and
`placementOf(m, taxonomy): TaxonomyPlacement` are exported helpers.

## Guarantees (asserted by `libraryModel.test.ts`)

1. **Dedup by mission identity (R3 / FR-014a / SC-002)**: the output contains **at most one
   Deliverable per `mission_id`**; a repeated id in the input collapses to one, keeping the
   first occurrence. An interrupted-then-resumed production (single durable dossier) yields
   exactly one card.
2. **Grouping (FR-002)**: Deliverables are grouped `client → project → campaign`; a
   deliverable with no client lands on the **unassigned** shelf; a deliverable whose
   client/project/campaign is not present in `taxonomy` is marked `orphaned` and also shown
   on the unassigned/orphaned shelf (never hidden — FR-013).
3. **Client-context scoping (FR-004)**: when `scope.client` is set, only that client's
   deliverables appear (further narrowed by `scope.project` / `scope.campaign` when set);
   when `scope.client` is null, all clients appear. Unassigned deliverables are shown only
   when no client scope is set (they belong to no client).
4. **Search (FR-006)**: `view.query` (case-insensitive, trimmed) matches against the
   deliverable **title** (`goal`) **and** its taxonomy placement text (client / project /
   campaign). Empty query ⇒ no narrowing. Matching is substring; narrows as typed.
5. **Outcome filter (FR-007)**: `view.outcomeFilter` narrows to that outcome, combined
   (AND) with scope and query. `"all"` ⇒ no narrowing.
6. **Empty-state flags (FR-012 / US2-AC3)**: exactly one of `isEmptyFirstRun`
   (input has zero missions), `isEmptyForContext` (missions exist but none in the active
   client scope), `isEmptyForQuery` (scope non-empty but query/filter matched nothing) is
   set when `total === 0`; a populated model sets none.
7. **No machinery leakage (FR-003 / SC-004)**: the model exposes `title`, friendly
   `producedAt`, `outcome`, and placement labels only — never `route` kit names, engine
   names, verdict codes, or paths. (Verdict codes are consumed by `classifyOutcome` and
   discarded; only the plain outcome enum leaves the projection.)
8. **Purity**: same inputs ⇒ deep-equal output; no `Date.now()`/random ordering — grouping
   and within-shelf order are stable (e.g. newest-first by the id timestamp prefix).

## Outcome classifier (R4)

```text
classifyOutcome(m):
  successful       ⇐ m.delivered is truthy AND lastVerdict(m.verdict) is a pass/soft-pass
  needs-attention  ⇐ otherwise (error / cancelled / vetoed / no clean delivery / in-progress verdict token)
```
Reuses `types.ts::summaryVerdictClass` / `lastVerdict` semantics (the same the console
uses); the projection maps them to the plain enum, and the i18n layer maps the enum to
localized labels — no raw verdict token is ever rendered.

## Catalog-key contract (i18n)

All operator-facing strings are `library.*` typed `CatalogKey`s (added to
`i18n/catalog.ts`, with EN in `en.ts` as the fallback source of truth and FR in `fr.ts`).
Required groups:

| Key group | Purpose |
|-----------|---------|
| `library.title`, `library.subtitle` | screen chrome |
| `library.shelf.unassigned` | unassigned/orphaned shelf label |
| `library.outcome.successful`, `library.outcome.needsAttention` | outcome badges/filter |
| `library.outcomeFilter.all\|successful\|needsAttention` | filter control |
| `library.search.placeholder`, `library.search.clear`, `library.search.noResults` | search UX |
| `library.card.untitled`, `library.card.producedOn` | card fields |
| `library.empty.firstRun.title\|body\|cta`, `library.empty.context.title\|body` | empty states |
| `library.state.loadError` | connection/load failure (shared error pattern) |

(Action/preview/filing keys are specified in `actions-and-filing.md`.) No `library.*` key
renders a mission id, kit name, or verdict code.
