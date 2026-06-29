"""agency-studio — launch the local Mission Console web GUI.

Thin wrapper around ``agency_studio.server.serve``. The heavy lifting (route →
execute → synthesize → inspect) stays in agency-kit; this only starts the local
HTTP/SSE server. Requires agency-kit importable (``agency_cli`` / ``agency_kit``)
— it is the orchestration brain the studio wraps.

Usage:
    agency-studio                       # serve on 127.0.0.1:8765
    agency-studio --port 9000           # custom port
    agency-studio --path /some/project  # where missions/ is written
"""

import argparse
import sys

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agency-studio",
        description="Local-first agentic studio — Mission Console web GUI over agency-kit.",
    )
    p.add_argument("--version", action="version", version=f"agency-studio {__version__}")
    p.add_argument("--host", default="127.0.0.1",
                   help="bind host — loopback only (default: 127.0.0.1)")
    p.add_argument("--port", type=int, default=8765, help="bind port (default: 8765)")
    p.add_argument("--path", default=".",
                   help="project dir where missions/ output is written (default: .)")
    p.add_argument("--static-root", default=None,
                   help="path to the built GUI (default: <path>/app/studio/dist if present)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        from . import server
        # Fail fast with a clear message if the orchestration brain is absent.
        import agency_cli.runner_bridge  # noqa: F401
    except ImportError as e:
        print(
            f"error: agency-studio needs agency-kit installed and importable — {e}\n"
            f"       install the kit (editable) and the studio extras:\n"
            f'         pip install -e /path/to/agency-kit\n'
            f'         pip install -e ".[studio]"',
            file=sys.stderr,
        )
        return 2
    try:
        server.serve(
            host=args.host, port=args.port,
            project_root=args.path, static_root=args.static_root,
        )
    except ValueError as e:  # loopback guard / bad host
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
