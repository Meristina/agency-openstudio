# Security — Agency Studio

Non-negotiable posture, applied **from Wave 0**. It deliberately takes the opposite stance
of the flaws found in existing local runners (notably Uncensored-Local-Studio: server
exposed on `0.0.0.0` + path traversal).

## Hard rules

| # | Rule | Why |
|---|---|---|
| 1 | **Bind `127.0.0.1` only** (never `0.0.0.0`). | Avoids silent LAN exposure. A "privacy" studio must not be drivable from another machine on the network. |
| 2 | **No `Access-Control-Allow-Origin: *`.** Local origin only. | Prevents a third-party website from calling the local API from the browser. |
| 3 | **`path_inside()` on 100% of static file serving.** | Blocks path traversal (`GET /../../etc/passwd`). Resolve the path and verify it stays under `dist/`. |
| 4 | **Validate scheme/host of download URLs.** | Prevents downloading arbitrary URLs (SSRF / untrusted content). |
| 5 | **Verify checksums of downloaded binaries/models.** | Supply-chain guard before executing a local binary. |
| 6 | **No telemetry, no secrets in plaintext.** | Consistent with the local-first ethos. |

## Regression test (from Wave 0)

```bash
# Path traversal blocked
curl --path-as-is http://127.0.0.1:<port>/../../../../etc/passwd   # → expect 404

# The server listens ONLY on loopback
lsof -iTCP -sTCP:LISTEN | grep <port>                              # → 127.0.0.1 only
```

Both checks are part of Wave 0's definition of done and must be covered by
`tests/test_server.py`.

## `path_inside()` reference implementation

```python
from pathlib import Path

def path_inside(child: str | Path, parent: str | Path) -> bool:
    """True if resolved `child` stays under `parent` (anti path-traversal)."""
    parent = Path(parent).resolve()
    try:
        Path(child).resolve().relative_to(parent)
        return True
    except ValueError:
        return False
```
