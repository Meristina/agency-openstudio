#!/usr/bin/env bash
# healthcheck-gate.sh — Stage 2 Stop-hook gate: agency-kit arborescence audit.
#
# Chains BEHIND guard-gate.sh: it stays silent until stage 1 has passed for the
# current change set (the guard marker matches the live fingerprint), so the two
# gates never block at the same time. Once guards pass, it blocks once and tells
# the agent to run the `agency-healthcheck` skill — verifying the 9-department
# wiring of the agency-kit brain this studio wraps — then record completion with
# `--mark`.
#
# Two modes:
#   (default)  read the Stop-hook JSON on stdin, decide block-or-allow.
#   --mark     fingerprint the current change set as "audited" and store it.
#
# Loop safety mirrors stage 1 (own marker + stop_hook_active). Shared
# fingerprint/emit logic lives in guard-lib.sh.

set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$DIR/guard-lib.sh"
GUARD_MARKER="$GUARD_ROOT/.claude/.guard-state"
MARKER="$GUARD_ROOT/.claude/.healthcheck-state"

# ── --mark: record the current state as audited ────────────────────────────
if [ "${1:-}" = "--mark" ]; then
  mkdir -p "$GUARD_ROOT/.claude"
  sig=$(compute_signature)
  printf '%s\n' "$sig" > "$MARKER"
  echo "healthcheck gate: recorded audited state ($sig)"
  exit 0
fi

# ── default: Stop-hook decision ────────────────────────────────────────────
input=$(cat 2>/dev/null || true)
stop_active=$(read_stop_active "$input")

git -C "$GUARD_ROOT" rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -n "$(guardable_state)" ] || exit 0

sig=$(compute_signature)

# Chain gate: do nothing until stage 1 (guards) has passed for THIS exact state.
guard_done=$(cat "$GUARD_MARKER" 2>/dev/null || echo "")
[ "$sig" = "$guard_done" ] || exit 0

prev=$(cat "$MARKER" 2>/dev/null || echo "")

# Already audited this exact state → allow (turn may end).
[ "$sig" = "$prev" ] && exit 0
# Already inside a Stop-hook continuation → don't block again (loop safety).
[ "$stop_active" = "true" ] && exit 0

emit_block "HEALTHCHECK GATE (stage 2 of 2 — the guard gate already passed for this change set) — the agency-kit department wiring has not been audited for this brick. Run the \`agency-healthcheck\` skill: verify the 9-department arborescence (product · marketing · solve · finance · comms · data · ops · people · tech) across the agency-kit brain this studio wraps — the sibling agency-kit / agency-cli checkout, plus any kit files this change touched. Fix any stale department reference it flags.
If this change set does not touch agency-kit's department wiring (e.g. studio server/GUI/hook files only), a quick 'N/A — no department files changed' is a valid pass.
When done, record completion so this gate stops blocking:
   bash \"\$CLAUDE_PROJECT_DIR/.claude/hooks/healthcheck-gate.sh\" --mark
Then stop."
