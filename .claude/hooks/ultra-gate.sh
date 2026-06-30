#!/usr/bin/env bash
# ultra-gate.sh — Stage 3 Stop-hook gate: full /ultrahealthcheck (the expensive one).
#
# /ultrahealthcheck is a multi-agent workflow (~10 min, hundreds of k tokens). Running
# it on every brick would crush production speed, so this gate is OFF by default and
# only fires when the audit is genuinely WARRANTED ("trancher si nécessaire"):
#
#   (a) RELEASE MODE — an arm marker (.claude/.ultra-armed) is present. Set it before a
#       release / PR to main with `ultra-gate.sh --arm`; clear with `--disarm`.
#   (b) LARGE BATCH  — the uncommitted guardable change set exceeds a high threshold
#       (AGENCY_ULTRA_FILE_THRESHOLD, default 8 files) — a milestone-sized change.
#
# Otherwise it stays silent: routine multi-file bricks are never blocked here.
#
# Chains BEHIND stage 2: it does nothing until the healthcheck gate has passed for the
# current change set, so at most one of the three gates blocks at a time.
#
# Modes:
#   (default)  read the Stop-hook JSON on stdin, decide block-or-allow.
#   --mark     fingerprint the current change set as "ultra-audited".
#   --arm      enter release mode (force the gate on until the next ultra+disarm).
#   --disarm   leave release mode.
#
# Loop safety: own marker + stop_hook_active. Shared logic lives in guard-lib.sh.

set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$DIR/guard-lib.sh"
HEALTH_MARKER="$GUARD_ROOT/.claude/.healthcheck-state"
MARKER="$GUARD_ROOT/.claude/.ultra-state"
ARM_MARKER="$GUARD_ROOT/.claude/.ultra-armed"
THRESHOLD="${AGENCY_ULTRA_FILE_THRESHOLD:-8}"

case "${1:-}" in
  --mark)
    mkdir -p "$GUARD_ROOT/.claude"
    sig=$(compute_signature)
    printf '%s\n' "$sig" > "$MARKER"
    echo "ultra gate: recorded ultra-audited state ($sig)"
    exit 0 ;;
  --arm)
    mkdir -p "$GUARD_ROOT/.claude"
    : > "$ARM_MARKER"
    echo "ultra gate: ARMED — /ultrahealthcheck will be required at the next Stop (release mode)."
    exit 0 ;;
  --disarm)
    rm -f "$ARM_MARKER"
    echo "ultra gate: disarmed (release mode off)."
    exit 0 ;;
esac

# ── default: Stop-hook decision ────────────────────────────────────────────
input=$(cat 2>/dev/null || true)
stop_active=$(read_stop_active "$input")

git -C "$GUARD_ROOT" rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -n "$(guardable_state)" ] || exit 0

sig=$(compute_signature)

# Chain: do nothing until stage 2 (healthcheck) has passed for THIS exact state.
health_done=$(cat "$HEALTH_MARKER" 2>/dev/null || echo "")
[ "$sig" = "$health_done" ] || exit 0

# Already ultra-audited this exact state → allow.
prev=$(cat "$MARKER" 2>/dev/null || echo "")
[ "$sig" = "$prev" ] && exit 0

# Decide NECESSITY: armed (release) or a large batch. Otherwise skip silently —
# this is the speed guard: routine bricks never trigger the expensive workflow.
file_count=$(guardable_state | grep -c .)
armed=""; [ -f "$ARM_MARKER" ] && armed="yes"
if [ -z "$armed" ] && [ "$file_count" -le "$THRESHOLD" ]; then
  exit 0   # not necessary → no ultrahealthcheck
fi

# Already inside a Stop-hook continuation → don't block again (loop safety).
[ "$stop_active" = "true" ] && exit 0

if [ -n "$armed" ]; then
  trigger="release mode is ARMED (.claude/.ultra-armed present)"
  extra="When the audit passes, record it AND leave release mode:
   bash \"\$CLAUDE_PROJECT_DIR/.claude/hooks/ultra-gate.sh\" --mark
   bash \"\$CLAUDE_PROJECT_DIR/.claude/hooks/ultra-gate.sh\" --disarm"
else
  trigger="this is a large change set ($file_count guardable files > threshold $THRESHOLD)"
  extra="When the audit passes, record it:
   bash \"\$CLAUDE_PROJECT_DIR/.claude/hooks/ultra-gate.sh\" --mark"
fi

emit_block "ULTRA GATE (stage 3 of 3 — stages 1 & 2 already passed) — $trigger, so the full multi-agent audit is warranted before this ships. Run \`/ultrahealthcheck\` (it fans out the 4 guards + agency-healthcheck in parallel, consolidates, fixes BLOCKING/IMPORTANT, and adversarially reviews the diff). Adapt its scope to agency-studio's real surface (agency_studio/ + app/studio/ + tests/ + docs), not agency-kit's.
$extra
Then stop. (To skip intentionally — e.g. the large diff is a vendored drop or pure data — run --mark without running the audit.)"
