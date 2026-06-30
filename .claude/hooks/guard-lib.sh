#!/usr/bin/env bash
# guard-lib.sh — shared helpers for the Stop-hook gates.
#
# Sourced (not executed) by guard-gate.sh (stage 1) and healthcheck-gate.sh
# (stage 2). Defines the project root, the change-set fingerprint both gates key
# off, the stop_hook_active parse, and the block-decision emitter. Keeping this
# in one place means both gates see the *same* "brick" and chain cleanly.
#
# Portable: POSIX-ish bash (macOS bash 3.2); git + shasum required, python3
# optional (only to JSON-escape the block reason; there is a fallback).

GUARD_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Files the gates care about: source + docs. Build output is gitignored, so it
# never reaches `git status` here.
is_guardable() {
  case "$1" in
    *.py|*.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs|*.css|*.md) return 0 ;;
    *) return 1 ;;
  esac
}

# The current uncommitted guardable change set, one "path:blob-hash" line per
# changed or untracked guardable file (":deleted" when the file is gone). Empty
# output ⇒ nothing to guard. The signature and the "any changes?" check both
# derive from this single parse.
guardable_state() {
  git -C "$GUARD_ROOT" status --porcelain --untracked-files=all 2>/dev/null \
  | while IFS= read -r line; do
      local path h
      path="${line#???}"                       # strip the 3-char "XY " prefix
      case "$path" in *" -> "*) path="${path##* -> }" ;; esac  # rename → new name
      path="${path%\"}"; path="${path#\"}"      # unquote odd names
      is_guardable "$path" || continue
      if [ -f "$GUARD_ROOT/$path" ]; then
        h=$(git -C "$GUARD_ROOT" hash-object "$GUARD_ROOT/$path" 2>/dev/null || echo missing)
      else
        h="deleted"
      fi
      printf '%s:%s\n' "$path" "$h"
    done
}

# Fingerprint of the change set: its lines sorted and hashed. The same change
# set always produces the same signature, so a gate that recorded a signature
# can tell whether the work has since changed.
compute_signature() {
  guardable_state | LC_ALL=C sort | shasum -a 256 | cut -d' ' -f1
}

# Echo "true"/"false": is the Stop hook already in a continuation? Read from the
# hook's stdin JSON. Used to never block twice in one fix→stop→fix cycle.
read_stop_active() {
  printf '%s' "$1" \
  | grep -o '"stop_hook_active"[[:space:]]*:[[:space:]]*[a-z]*' \
  | head -1 | grep -o '[a-z]*$'
}

# Emit a Stop-hook block decision for the given reason, then exit the gate.
# Prefers JSON on stdout (python3 escapes the reason); falls back to exit 2 with
# the reason on stderr when python3 is unavailable.
emit_block() {
  local esc
  esc=$(printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null)
  if [ -n "$esc" ]; then
    printf '{"decision":"block","reason":%s}\n' "$esc"
    exit 0
  fi
  printf '%s\n' "$1" >&2
  exit 2
}
