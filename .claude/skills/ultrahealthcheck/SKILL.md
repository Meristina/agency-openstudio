---
name: ultrahealthcheck
description: >-
  Full-spectrum multi-agent health audit of the agency-kit repo. Fans out
  agency-healthcheck, clean-code-guard, docs-guard, and test-guard in parallel,
  then converges: /agency.goal fixes every finding, /code-review verifies the
  result. Requires ultracode (multi-agent workflow). Run after any significant
  change set or before a release.
---

# /ultrahealthcheck — full-spectrum repo audit (ultracode)

This skill launches an **ultracode multi-agent workflow**. It fans four guard
passes out in parallel, consolidates findings, fixes them end-to-end with
`/agency.goal`, then verifies the clean state with `/code-review`.

**Invoke this skill only when ultracode is available** — it requires the
Workflow tool and spawns multiple subagents.

---

## What it does

```
Phase 1 — parallel fan-out (4 agents)
  ├─ agency-healthcheck   → 9-dept architecture consistency audit
  ├─ clean-code-guard     → production code quality (Clean Code / SOLID / AI guardrails)
  ├─ docs-guard           → documentation accuracy (CLAUDE.md, ARCHITECTURE.md, GUIDE.md, README.md)
  └─ test-guard           → test code quality (all files under tests/)

Phase 2 — consolidate
  → Merge all findings; deduplicate overlapping items; classify:
      BLOCKING  — fails tests, breaks imports, wrong behaviour, false docs
      IMPORTANT — quality debt, stale references, test bloat
      CLEANUP   — minor inconsistencies

Phase 3 — fix (if any findings)
  → /agency.goal "<consolidated fix list>"
      Ordered by dependency: BLOCKING → IMPORTANT → CLEANUP
      Each fix verified inline before moving to the next

Phase 4 — verify
  → /code-review ultra
      Independent adversarial review of the diff produced in Phase 3
      Must PASS before the skill exits
```

---

## How to invoke

```
/ultrahealthcheck
```

No argument needed. The skill reads the full repo from the current working
directory.

---

## Workflow script (Claude invokes this via the Workflow tool)

When this skill is invoked, call the **Workflow tool** with the following
script:

```javascript
export const meta = {
  name: 'ultrahealthcheck',
  description: 'Full-spectrum multi-agent health audit: guard skills → fix → review',
  phases: [
    { title: 'Guard', detail: 'agency-healthcheck + clean-code-guard + docs-guard + test-guard in parallel' },
    { title: 'Consolidate', detail: 'merge findings, classify severity' },
    { title: 'Fix', detail: '/agency.goal fixes all findings in dependency order' },
    { title: 'Review', detail: '/code-review ultra — adversarial verification of the fix diff' },
  ],
}

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id:       { type: 'string' },
          file:     { type: 'string' },
          line:     { type: 'string' },
          severity: { type: 'string', enum: ['BLOCKING', 'IMPORTANT', 'CLEANUP'] },
          summary:  { type: 'string' },
          fix:      { type: 'string' },
        },
        required: ['id', 'file', 'severity', 'summary'],
      },
    },
    verdict: { type: 'string', enum: ['CLEAN', 'ISSUES'] },
  },
  required: ['findings', 'verdict'],
}

// Phase 1 — parallel guard passes
phase('Guard')
const guards = await parallel([
  () => agent(
    'Run /agency.healthcheck: read every key file in the agency-kit repo and verify ' +
    'the 9-department architecture (product · marketing · solve · finance · comms · ' +
    'data · ops · people · tech) is consistently reflected across agency_kit/, agency_cli/, ' +
    'agents/, skills/, .agency/commands/, tests/, and docs/config files. ' +
    'Follow the full checklist in .claude/skills/agency-healthcheck/SKILL.md. ' +
    'Return structured findings.',
    { label: 'agency-healthcheck', phase: 'Guard', schema: FINDINGS_SCHEMA }
  ),
  () => agent(
    'Run clean-code-guard on all production code in agency_kit/ and agency_cli/ ' +
    '(exclude tests/). Apply all 23 imperatives from .claude/skills/clean-code-guard/SKILL.md. ' +
    'Focus on AI-specific guardrails (rules 15–22) and SOLID/DRY violations. ' +
    'Return structured findings.',
    { label: 'clean-code-guard', phase: 'Guard', schema: FINDINGS_SCHEMA }
  ),
  () => agent(
    'Run docs-guard on CLAUDE.md, docs/ARCHITECTURE.md, GUIDE.md, README.md, and ' +
    'all files under agents/ and .agency/commands/. Verify every referenced symbol, ' +
    'command, env var, and code sample against the actual source. ' +
    'Follow .claude/skills/docs-guard/SKILL.md. Return structured findings.',
    { label: 'docs-guard', phase: 'Guard', schema: FINDINGS_SCHEMA }
  ),
  () => agent(
    'Run test-guard on all files under tests/ (conftest.py, test_structure.py, ' +
    'test_mission_harness.py, test_cli.py). Apply all 9 rules from ' +
    '.claude/skills/test-guard/SKILL.md. Return structured findings.',
    { label: 'test-guard', phase: 'Guard', schema: FINDINGS_SCHEMA }
  ),
])

// Phase 2 — consolidate
phase('Consolidate')
const allFindings = guards
  .filter(Boolean)
  .flatMap(r => r.findings)

if (allFindings.length === 0) {
  log('All guards CLEAN — no findings. Skipping fix and review phases.')
  return { verdict: 'CLEAN', findings: [] }
}

log(`${allFindings.length} finding(s) across 4 guards. Classifying and deduplicating.`)

const consolidation = await agent(
  'Consolidate these findings from 4 parallel guard passes into a single ordered fix list. ' +
  'Deduplicate overlapping items (same file/line from multiple guards = one item). ' +
  'Classify each as BLOCKING (breaks tests/imports/behaviour/false docs), ' +
  'IMPORTANT (quality debt, stale refs), or CLEANUP (minor). ' +
  'Order by dependency: BLOCKING first, then IMPORTANT, then CLEANUP. ' +
  'State the total count. Findings:\n\n' +
  JSON.stringify(allFindings, null, 2),
  { label: 'consolidate', phase: 'Consolidate', schema: FINDINGS_SCHEMA }
)

log(`Consolidated: ${consolidation.findings.length} item(s) to fix.`)

// Phase 3 — fix
phase('Fix')
const fixList = consolidation.findings
  .map((f, i) => `[${f.id || i + 1}] ${f.summary} — ${f.file}${f.line ? ':' + f.line : ''} — ${f.severity}${f.fix ? ' — Fix: ' + f.fix : ''}`)
  .join('\n')

await agent(
  'Run /agency.goal to fix all findings below. Follow the /agency.goal protocol exactly:\n' +
  '1. Audit the findings list and order by dependency (BLOCKING → IMPORTANT → CLEANUP).\n' +
  '2. For each item: fix it, verify it (run pytest tests/ -v for code changes), mark ✓ done.\n' +
  '3. After all items: run the full test suite and confirm 76 passed.\n' +
  '4. Deliver verdict: DONE (all fixed, tests pass) or PARTIAL (list blockers).\n\n' +
  'Findings to fix:\n' + fixList,
  { label: '/agency.goal', phase: 'Fix' }
)

// Phase 4 — review
phase('Review')
const review = await agent(
  'Run /code-review ultra on the diff produced by the fix phase. ' +
  'This is an independent adversarial review — assume nothing was done correctly ' +
  'and verify from scratch. Check: (1) all findings from the guard phase are actually ' +
  'fixed; (2) no regressions introduced; (3) tests still pass; (4) no new violations ' +
  'of clean-code-guard or docs-guard rules. ' +
  'Verdict: PASS (all clear) or FAIL (list what remains).',
  { label: '/code-review ultra', phase: 'Review', schema: {
    type: 'object',
    properties: {
      verdict: { type: 'string', enum: ['PASS', 'FAIL'] },
      remaining: { type: 'array', items: { type: 'string' } },
      summary: { type: 'string' },
    },
    required: ['verdict', 'summary'],
  }}
)

log(`Final verdict: ${review.verdict} — ${review.summary}`)
return {
  verdict: review.verdict,
  findingsFixed: consolidation.findings.length,
  remaining: review.remaining || [],
  summary: review.summary,
}
```

---

## Pass criteria

- Phase 1: all 4 guards return structured findings (empty = clean for that guard).
- Phase 3: `pytest tests/ -v` shows all tests passing after fixes.
- Phase 4: `/code-review ultra` returns **PASS**.
- Final output: `verdict: PASS`, `remaining: []`.

## When to use

| Trigger | Run |
|---|---|
| After a large change set (>3 files) | ✅ |
| Before a release / PR to main | ✅ |
| After adding a department or skill | ✅ |
| After a single typo fix | ❌ use `/agency.healthcheck` alone |
| After adding one test | ❌ use `test-guard` alone |
