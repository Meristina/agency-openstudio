"""context_block — the single formatter for a ``context_clause`` block.

RAG (local docs), web search, and MCP resources all hand the departments the same shape: a
short header paragraph, then numbered ``[n] label`` citations each followed by their text.
This is that one formatter, so the ``[n]``-citation convention lives in exactly one place
(the per-source *header* — including its prompt-injection guidance — stays with each caller,
since the guidance legitimately differs by source).
"""

from __future__ import annotations

from typing import List, Optional, Tuple


def format_context_block(header: str, entries: "List[Tuple[str, str]]") -> "Optional[str]":
    """Format ``entries`` (``(label, text)`` pairs) under ``header`` as a ``context_clause``
    block. Returns ``None`` when there is nothing usable to inject (no entries, or all
    blank), so a block with no content is byte-identical to none at all — the shared
    default-None contract (``asset_clause`` / the RAG clause)."""
    usable = [(label, text) for (label, text) in entries if (label or text)]
    if not usable:
        return None
    lines = [header, ""]
    for i, (label, text) in enumerate(usable, start=1):
        lines.append(f"[{i}] {label}")
        if text:
            lines.append(text)
        lines.append("")
    return "\n".join(lines).rstrip()
