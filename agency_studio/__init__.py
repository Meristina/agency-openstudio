"""agency_studio — local-first web GUI that wraps agency-kit's mission loop.

The core stays in agency-kit (route → execute → synthesize → inspect with veto).
This package adds ONLY a thin local layer: a stdlib HTTP/SSE server that streams
live mission progress (via agency-kit's observational ``on_event`` hook) to a web
GUI. No heavy reasoning lives here — see CLAUDE.md / ROADMAP.md.
"""

__version__ = "0.0.0"
