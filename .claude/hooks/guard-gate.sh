#!/usr/bin/env bash
# guard-gate.sh — Stage 1 Stop-hook quality gate for Agency Studio.
#
# Fires when a "brick" of work (a module / fix) leaves uncommitted code or doc
# changes that have NOT yet passed the guard gate. It blocks the turn from
# ending and tells the agent to run the `guard-skills` skill + `/code-review`,
# fix findings, then record completion with `--mark`. Once recorded, stage 2
# (healthcheck-gate.sh) chains behind it for the same change set.
#
# Two modes:
#   (default)  read the Stop-hook JSON on stdin, decide block-or-allow.
#   --mark     fingerprint the current change set as "reviewed" and store it, so
#              the next Stop allows (called by the agent after the guard pass).
#
# Loop safety: never blocks twice for the same change-set fingerprint, and never
# blocks while the Stop hook is already active, so fix→stop→fix cannot spin.
#
# Shared fingerprint/emit logic lives in guard-lib.sh.

set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$DIR/guard-lib.sh"
MARKER="$GUARD_ROOT/.claude/.guard-state"

# ── --mark: record the current state as reviewed ───────────────────────────
if [ "${1:-}" = "--mark" ]; then
  mkdir -p "$GUARD_ROOT/.claude"
  sig=$(compute_signature)
  printf '%s\n' "$sig" > "$MARKER"
  echo "guard gate: recorded reviewed state ($sig)"
  exit 0
fi

# ── default: Stop-hook decision ────────────────────────────────────────────
input=$(cat 2>/dev/null || true)
stop_active=$(read_stop_active "$input")

# Not a git repo, or nothing guardable changed → allow.
git -C "$GUARD_ROOT" rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -n "$(guardable_state)" ] || exit 0

sig=$(compute_signature)
prev=$(cat "$MARKER" 2>/dev/null || echo "")

# Already reviewed this exact state → allow (stage 2 takes over).
[ "$sig" = "$prev" ] && exit 0
# Already inside a Stop-hook continuation → don't block again (loop safety).
[ "$stop_active" = "true" ] && exit 0

emit_block "GUARD GATE (stage 1 of 2) — you produced uncommitted code/doc changes that have not passed the module guard gate. The change set may span the studio repo AND/OR the sibling agency-kit brain checkout it wraps — review whichever actually changed (\`git status\` in each). Before you finish:
1. Run the \`guard-skills\` skill on the changed files (it routes production code → clean-code-guard, tests → test-guard, docs → docs-guard) AND run \`/code-review\` on the diff.
2. Enforce this repo's non-negotiables (loopback bind, path_inside, no CORS '*', validated URLs/checksums, MIT-only, stdlib core). Fix every must-fix finding.
3. When the gate is satisfied, record it so this gate stops blocking:
   bash \"\$CLAUDE_PROJECT_DIR/.claude/hooks/guard-gate.sh\" --mark
Then stop — stage 2 (agency-healthcheck) will run next. (To intentionally bypass — e.g. a pure revert — run the --mark command without changes.)"
