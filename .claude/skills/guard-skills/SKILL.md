---
name: guard-skills
description: "Umbrella guard gate run after producing a module/brick of work, before it is presented, committed, or merged. Routes each changed file to the right specialist guard — production code to clean-code-guard, test code to test-guard, documentation to docs-guard — and reports a single consolidated verdict. Invoked by the Stop-hook quality gate (.claude/hooks/guard-gate.sh) whenever uncommitted code/doc changes exist, and usable manually with 'run the guard gate', 'guard this change', or 'run guard-skills'. After the gate is satisfied, record completion so the hook stops blocking. DO NOT USE for conceptual questions, running tests, CI config, or git workflow."
---

# guard-skills — the module guard gate

You just produced (or are about to ship) a **brick** of work — a module, a
feature, a fix. This skill is the **gate it must pass** before it is presented,
committed, or merged. It does not invent its own rules: it **routes** the
changed files to the three specialist guards already in this repo and converges
their findings into one verdict.

This skill is invoked automatically by the **Stop-hook gate**
(`.claude/hooks/guard-gate.sh`) whenever there are uncommitted code or doc
changes that have not yet passed the gate. It can also be run manually.

## The three guards it dispatches to

| Changed file kind | Guard skill | Jurisdiction |
|---|---|---|
| Production code (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`, …) | **clean-code-guard** | Clean Code / SOLID / DRY-KISS-YAGNI + 14 LLM failure modes |
| Test code (`test_*.py`, `*.test.ts`, files under `tests/`) | **test-guard** | The 9 testing rules — behavior-not-implementation, justified mocks, no bloat |
| Documentation (`.md`, docstrings, README, ROADMAP) | **docs-guard** | Every symbol/flag/sample verified against source; no docs-vs-code drift |

Plus the repo-wide quality pass: **`/code-review`** on the working diff (the
gate runs the two together — `/code-review` for correctness/bug findings,
guard-skills for the craft + accuracy layer).

## Procedure

1. **List the changed files.** `git status --porcelain --untracked-files=all`.
   Ignore anything gitignored (`dist/`, `node_modules/`, `*.tsbuildinfo`).
2. **Classify each file** by the table above. A change set usually spans more
   than one guard (e.g. `server.py` + `test_server.py` + `README.md`).
3. **Run each relevant guard** in guard-pass / review mode against *only the
   changed files* (read each guard's `SKILL.md` for its rules and references):
   - production code → `clean-code-guard`
   - test code → `test-guard`
   - docs → `docs-guard`
4. **Run `/code-review`** on the same diff for correctness and simplification
   findings.
5. **Honour this project's non-negotiables** while reviewing (CLAUDE.md /
   docs/SECURITY.md / docs/LICENSES.md): loopback-only bind, `path_inside()` on
   every static handler, no `Access-Control-Allow-Origin: *`, validated download
   URLs + verified checksums, MIT-compatible only (never copy AGPL), stdlib
   zero-dependency core, image and LLM never co-resident. Treat a violation of
   any of these as **must-fix**.
6. **Fix every must-fix finding** before the work ships. Should-fix and
   worth-noting findings: fix or explicitly flag to the user.
7. **Record gate completion** so the Stop hook stops blocking:

   ```bash
   bash "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-gate.sh" --mark
   ```

   Run `--mark` **last**, after the final fix — it fingerprints the exact code
   state you reviewed. Any later edit invalidates it and re-arms the gate
   (that is intended: changed code gets re-reviewed).

## Verdict format

Report one consolidated block:

```
GUARD GATE — <n> files: <p> code · <t> test · <d> docs
clean-code-guard: <PASS | findings…>
test-guard:       <PASS | findings…>
docs-guard:       <PASS | findings…>
/code-review:     <PASS | findings…>
project invariants: <PASS | violation…>
→ verdict: PASS (gate recorded) | FIXED-THEN-PASS | BLOCKED (must-fix open)
```

## What this skill does not do

- It does not run the test suite or linters — those are tool-level steps; use
  the project's runners (`pytest`, `npm run build`). This is the judgement gate.
- It does not replace the specialist guards — it dispatches to them. When a
  guard's rule needs its reasoning or a citation, read that guard's
  `references/`.
- It does not fire on chat-only or conceptual turns — only when a brick of
  code/docs was actually produced.
