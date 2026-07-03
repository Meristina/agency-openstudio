#!/usr/bin/env bash
# new-mission.sh — allocate the next mission folder and seed its dossier + deliverable.
# Usage: .agency/scripts/sh/new-mission.sh "<one-line goal>"
# Prints the created mission directory path (so a command can chain on it).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
GOAL="${1:-}"
if [ -z "$GOAL" ]; then
  echo "usage: new-mission.sh \"<one-line goal>\"" >&2
  exit 1
fi

MISSIONS="$ROOT/missions"
mkdir -p "$MISSIONS"

# next zero-padded NNN
LAST=$(ls -1 "$MISSIONS" 2>/dev/null | grep -E '^[0-9]{3}-' | sed -E 's/^([0-9]{3}).*/\1/' | sort -n | tail -1 || true)
NEXT=$(printf "%03d" $(( 10#${LAST:-000} + 1 )))

# slug from the goal (lowercase, alnum -> dashes, trimmed, max 6 words)
SLUG=$(printf '%s' "$GOAL" \
  | tr '[:upper:]' '[:lower:]' \
  | tr -cs 'a-z0-9' '-' \
  | sed -E 's/^-+//; s/-+$//' \
  | cut -d'-' -f1-6)
SLUG="${SLUG:-mission}"

DIR="$MISSIONS/${NEXT}-${SLUG}"
mkdir -p "$DIR"

# Use Python for template substitution — sed delimiters break when GOAL contains | or &
_fill_template() {
  python3 - "$1" "$2" "$3" "$4" <<'PYEOF'
import sys
tpl, mission_id, goal, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
text = open(tpl, encoding="utf-8").read()
text = text.replace("{{MISSION_ID}}", mission_id).replace("{{ONE_LINE_GOAL}}", goal)
open(out, "w", encoding="utf-8").write(text)
PYEOF
}

_fill_template "$ROOT/.agency/templates/dossier-template.md"     "${NEXT}-${SLUG}" "$GOAL" "$DIR/dossier.md"
_fill_template "$ROOT/.agency/templates/deliverable-template.md"  "${NEXT}-${SLUG}" "$GOAL" "$DIR/deliverable.md"

echo "$DIR"
