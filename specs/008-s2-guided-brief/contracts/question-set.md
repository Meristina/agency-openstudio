# Contract: Question-Set Data Shape (S2 internal, extension seam)

**Provider**: `questionSets.ts` · **Consumers**: flow engine (`GuidedBrief.tsx` /
`FlowStep.tsx`), review (`Review.tsx`), composer (`composeMission.ts`), tests.

## Shape (per deliverable type)

```ts
interface QuestionSet {
  type: "research" | "strategy" | "video";   // v1 trio (clarification Q2)
  questions: Question[];                      // ordered
}

interface Question {
  id: string;                                 // stable, keys Brief.answers
  kind: "choice" | "shortText" | "longText" | "language" | "sector" | "toggle" | "attachment";
  // "attachment" (introduced by US3) renders the Brick 6 client/project/campaign picker
  labelKey: CatalogKey;                       // typed — catalog completeness enforced
  helpKey?: CatalogKey;
  choices?: { id: string; labelKey: CatalogKey }[];   // kind === "choice"
  relevant?: (brief: PartialBrief) => boolean;        // FR-002 adaptivity
  defaultValue?: Answer;                      // FR-005: default XOR skippable
  skippable?: boolean;                        //   (required questions have neither)
  compose: ComposeRule;                       // goal-text line or flag mapping (D1)
}
```

## Rules

1. **Catalog-keyed text only**: every user-visible string a question contributes is a
   typed `CatalogKey` present in both `en.ts` and `fr.ts` — verified by an automated
   completeness test (FR-007; umbrella i18n contract applies unchanged).
2. **Required minimum**: across every set, only intent, deliverable type, and
   deliverable language may be non-defaultable/non-skippable (FR-005).
3. **Determinism**: `relevant` predicates are pure functions of the partial brief —
   same answers ⇒ same question sequence (clarification Q4; snapshot-testable).
4. **Extension = data**: adding a deliverable type or a sector adds entries to this
   module only; flow engine, review, and composer must not require changes (FR-003).
   This is the seam Brick 8 recipes will use.
5. **Plain language**: no key's EN/FR value may contain machinery terms (departments,
   engines, pipelines, flags) — enforced by the SC-007 wording audit over the
   `brief.*` catalog namespace.
6. **Paid/off-machine marking**: any question whose answer can enable a paid or
   off-machine behavior must carry the explicit marker so the flow renders the
   labeled opt-in (FR-012); mission research (`toggle`, default on) is exempt by
   FR-012a.
