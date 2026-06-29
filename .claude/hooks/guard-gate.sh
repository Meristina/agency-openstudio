#!/usr/bin/env bash
# guard-gate.sh — Stop-hook quality gate for Agency Studio.
#
# Fires when a "brick" of work (a module / fix) leaves uncommitted code or doc
# changes that have NOT yet passed the guard gate. It blocks the turn from
# ending and tells the agent to run the `guard-skills` skill + `/code-review`,
# fix findings, then record completion with `--mark`.
#
# Two modes:
#   (default)  read the Stop-hook JSON on stdin, decide block-or-allow.
#   --mark     fingerprint the current changed-file state as "reviewed" and
#              store it, so the next Stop allows (called by the agent after the
#              guard pass is satisfied).
#
# Loop safety: the gate never blocks twice for the same code state (the marker
# fingerprint) and never blocks when the Stop hook is already active
# (`stop_hook_active`), so a fix→stop→fix cycle cannot spin forever.
#
# Portable: POSIX-ish bash (macOS bash 3.2), only git + shasum required.

set -u

ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
MARKER="$ROOT/.claude/.guard-state"

# Files this gate cares about. Source + docs; build output is gitignored so it
# never appears in `git status` here.
is_guardable() {
  case "$1" in
    *.py|*.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs|*.css|*.md) return 0 ;;
    *) return 1 ;;
  esac
}

# The current uncommitted guardable change set, one "path:blob-hash" line per
# changed or untracked guardable file (":deleted" when the file is gone).
# Empty output ⇒ nothing to guard. Both the signature and the "any changes?"
# check derive from this single parse.
guardable_state() {
  git -C "$ROOT" status --porcelain --untracked-files=all 2>/dev/null \
  | while IFS= read -r line; do
      path="${line#???}"                       # strip the 3-char "XY " prefix
      case "$path" in *" -> "*) path="${path##* -> }" ;; esac  # rename → new name
      path="${path%\"}"; path="${path#\"}"      # unquote odd names
      is_guardable "$path" || continue
      if [ -f "$ROOT/$path" ]; then
        h=$(git -C "$ROOT" hash-object "$ROOT/$path" 2>/dev/null || echo missing)
      else
        h="deleted"
      fi
      printf '%s:%s\n' "$path" "$h"
    done
}

# Fingerprint of the change set: its lines sorted and hashed (empty ⇒ empty).
compute_signature() {
  guardable_state | LC_ALL=C sort | shasum -a 256 | cut -d' ' -f1
}

# ── --mark: record the current state as reviewed ───────────────────────────
if [ "${1:-}" = "--mark" ]; then
  mkdir -p "$ROOT/.claude"
  sig=$(compute_signature)
  printf '%s\n' "$sig" > "$MARKER"
  echo "guard gate: recorded reviewed state ($sig)"
  exit 0
fi

# ── default: Stop-hook decision ────────────────────────────────────────────
input=$(cat 2>/dev/null || true)
stop_active=$(printf '%s' "$input" \
  | grep -o '"stop_hook_active"[[:space:]]*:[[:space:]]*[a-z]*' \
  | head -1 | grep -o '[a-z]*$')

# Not a git repo, or nothing guardable changed → allow.
git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -n "$(guardable_state)" ] || exit 0

sig=$(compute_signature)
prev=$(cat "$MARKER" 2>/dev/null || echo "")

# Already reviewed this exact state → allow.
[ "$sig" = "$prev" ] && exit 0

# Already inside a Stop-hook continuation → don't block again (loop safety).
[ "$stop_active" = "true" ] && exit 0

# Block: tell the agent to run the gate, then record completion.
reason="GUARD GATE — you produced uncommitted code/doc changes that have not passed the module guard gate. Before you finish:
1. Run the \`guard-skills\` skill on the changed files (it routes production code → clean-code-guard, tests → test-guard, docs → docs-guard) AND run \`/code-review\` on the diff.
2. Enforce this repo's non-negotiables (loopback bind, path_inside, no CORS '*', validated URLs/checksums, MIT-only, stdlib core). Fix every must-fix finding.
3. When the gate is satisfied, record it so this gate stops blocking:
   bash \"\$CLAUDE_PROJECT_DIR/.claude/hooks/guard-gate.sh\" --mark
Then stop. (To intentionally bypass — e.g. a pure revert — run the --mark command without changes.)"

# Emit the block decision as JSON on stdout (Stop-hook contract).
esc=$(printf '%s' "$reason" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null)
if [ -n "$esc" ]; then
  printf '{"decision":"block","reason":%s}\n' "$esc"
else
  # Fallback if python3 is unavailable: exit code 2 surfaces stderr to the agent.
  printf '%s\n' "$reason" >&2
  exit 2
fi
exit 0
