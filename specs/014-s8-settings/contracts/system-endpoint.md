# Contract — `GET /api/system` (NEW, read-only)

The single new server surface S8 introduces. It exists to supply the two honest system facts the
frontend cannot truthfully invent (Principle III): the studio version and the local data
location.

## Request

```text
GET /api/system
```

- **No query parameters. No request body. No headers required beyond the same-origin default.**
- Method: **GET only**. No `PUT`/`POST`/`DELETE` variant exists (this endpoint has no write
  semantics).

## Response — 200 OK

```json
{
  "version": "0.0.0",
  "data_dir": "/Users/<user>/Library/Application Support/agency-studio/data"
}
```

| Field | Type | Source | Rule |
|---|---|---|---|
| `version` | string | `agency_studio.__version__` | Verbatim; never a fabricated or build-time-forked value |
| `data_dir` | string | `str(agency_studio.rag.data_dir())` | The server-computed absolute path of the **primary local data folder** (documents/settings/knowledge/selections); not derived from any user input. Represents the primary store only — missions (`project_root`) and produced media (`assets_root`) may live elsewhere and are out of scope for this field |

`Content-Type: application/json`. Response is deterministic for a given install (no per-request
computation beyond reading the version constant and the data-dir function).

## Security & invariants (Principle VI)

- **No user input** reaches the handler → **no `path_inside` / traversal surface**. The endpoint
  serves no user-named file; it returns a fixed server-computed path string.
- **No secret**: it returns only the version and the local user's own data directory, over the
  loopback bind (`127.0.0.1`, inherited from the server). No API key, token, or env value is
  read, returned, persisted, or logged.
- **Read-only / additive**: adding this route changes no existing response. Behavior of every
  other endpoint is byte-identical.
- **Scope honesty**: the endpoint reports the primary data directory only; the frontend labels
  it as such and must not present it as the location of every deliverable (missions live under
  `project_root`, produced media under `assets_root` — both out of scope for this endpoint).

## Handler placement

`agency_studio/server.py`: a new `if path == "/api/system": return self._handle_system()` in the
GET dispatch (alongside `/api/models`, `/api/capabilities`, …), and a small `_handle_system()`
returning the JSON above. Stdlib only (`json`); no new import beyond `agency_studio.__version__`
and the existing `rag`.

## Tests (offline, `tests/test_system_endpoint.py`)

1. `GET /api/system` returns 200 with a JSON object containing string `version` and `data_dir`.
2. `version` equals `agency_studio.__version__` (no fork/fabrication).
3. `data_dir` equals `str(rag.data_dir())` (monkeypatch `data_dir` to a temp path and assert the
   response reflects it).
4. Response contains **no** secret-looking field (no `key`, `token`, `secret`, env values).
5. No write path: the endpoint is reachable only via GET (a non-GET falls through to the normal
   not-found / method handling — asserted to not mutate anything).
