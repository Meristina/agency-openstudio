# Guided Brief Quickstart Smoke

Date: 2026-07-06

Served app: `npm run preview -- --host 127.0.0.1`

Preview check: `curl -i http://127.0.0.1:4173/` returned `HTTP/1.1 200 OK` and the built `dist` index.

## Outcomes

- PASS: intent handoff is covered by `GuidedBrief.test.tsx` and `Shell.test.tsx`; `#/brief?intent=...` renders the guided brief with the intent editable.
- PASS: all-defaults research launch is covered by `GuidedBrief.test.tsx`, `composeMission.test.ts`, and `Review.test.tsx`; review includes source minimum and launch captures a run id.
- PASS: video blocker is covered by `Review.test.tsx`; unavailable video capability shows a Models link and launch is not called.
- PASS: reload/resume draft is covered by `briefDraft.test.ts` and `GuidedBrief.test.tsx`; resume restores answers and step, discard starts clean.
- PASS: mid-flow language behavior is covered by `GuidedBrief.test.tsx`; answers remain and deliverable-language choice is independent.

Validation:

- `cd app/studio && npx vitest run` -> 184 passed.
- `cd app/studio && npm run build` -> passed.
- `pytest` at repo root -> 529 passed, 1 warning.
