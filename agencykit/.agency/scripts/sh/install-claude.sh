#!/usr/bin/env bash
# install-claude.sh — install the Agency-Kit command pack into ~/.claude.
# Commands become /agency.<name> ; the engine they invoke = the agents mirror.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEST="${CLAUDE_HOME:-$HOME/.claude}"

mkdir -p "$DEST/commands" "$DEST/agents"

# 1) Commands → /agency.<name>  (dotted namespace)
for f in "$ROOT"/.agency/commands/*.md; do
  name="$(basename "$f" .md)"
  cp "$f" "$DEST/commands/agency.${name}.md"
done

# 2) The engine the commands drive: full agent bundle from the bundled payload
# (payload/agents has 100+ files from all kits; root/agents has only 3 agency-level files)
PAYLOAD_AGENTS="$ROOT/agency_cli/payload/agents"
if [ -d "$PAYLOAD_AGENTS" ]; then
  cp "$PAYLOAD_AGENTS"/*.md "$DEST/agents/"
else
  cp "$ROOT"/agents/*.md "$DEST/agents/"
fi

# 3) Skills (optional — only if the skills/ directory exists at root)
if [ -d "$ROOT/skills" ]; then
  mkdir -p "$DEST/skills"
  cp -R "$ROOT"/skills/* "$DEST/skills/"
  SKILL_COUNT=$(ls -d "$ROOT"/skills/*/ 2>/dev/null | wc -l | tr -d ' ')
else
  SKILL_COUNT=0
fi

echo "Installed into $DEST :"
echo "  commands : $(ls "$ROOT"/.agency/commands/*.md | wc -l | tr -d ' ') → /agency.<name>"
AGENT_SRC="$PAYLOAD_AGENTS"; [ -d "$AGENT_SRC" ] || AGENT_SRC="$ROOT/agents"
echo "  agents   : $(ls "$AGENT_SRC"/*.md | wc -l | tr -d ' ')"
echo "  skills   : ${SKILL_COUNT}"
echo "Try:  /agency.mission \"<your goal>\""
