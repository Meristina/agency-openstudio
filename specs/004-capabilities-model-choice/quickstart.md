# Quickstart: Capabilities & Model Choice (Brick 4)

## What this brick delivers

Open the studio → **Capabilities** view → see every model/tool family (image,
video, visual, embedding, KG extraction, STT, TTS, OpenMontage production tools,
MCP servers) with FREE/PAID and AVAILABLE/UNAVAILABLE + the exact step to enable
anything missing. Pick a default per model family; it persists across restarts. No
terminal, no env vars — though env vars still win when a power user sets them.

## Try it (once implemented)

```bash
# 1. Start the studio (no extras, no keys — worst case machine)
agency-studio                        # serves on 127.0.0.1:8765
open http://127.0.0.1:8765          # Capabilities view: everything listed,
                                    # unavailable entries show install/key hints

# 2. Inspect the inventory directly
curl -s http://127.0.0.1:8765/api/capabilities | python -m json.tool

# 3. Pick a default image model from the API (the GUI does the same)
curl -s -X PUT http://127.0.0.1:8765/api/capabilities/selection \
     -d '{"family": "image", "id": "flux2-klein-4b"}'

# 4. Restart the studio — the selection survives (selections.json in the data dir)
cat ~/.local/share/agency-studio/selections.json

# 5. Power-user override still wins, and the GUI shows the override banner
AGENCY_STUDIO_IMAGE_MODEL=flux-schnell agency-studio

# 6. Clear the selection → back to the built-in default
curl -s -X DELETE http://127.0.0.1:8765/api/capabilities/selection/image
```

## Verify (offline suite — no models, no keys, no network)

```bash
pytest tests/test_capabilities.py tests/test_server_capabilities.py -q
pytest -q          # full suite stays green (FR-014 / SC-006)
cd app/studio && npx vitest run   # GUI api layer
```

Key test seams: `AGENCY_STUDIO_DATA_DIR` (tmp selection store),
`capabilities._spawn_catalog` (OpenMontage probe stub),
`importlib.util.find_spec` / probe-module table (extras present/absent),
`monkeypatch.setenv` (keys + overrides).

## Resolution order (the one rule to remember)

```
env var  →  persisted selection (if available)  →  built-in default
```

Nothing set ⇒ byte-identical to pre-Brick-4 behavior.

## Known limits (by design, this brick)

- Key *setting* stays env-based; the GUI only shows presence + the var name.
- Production tools and MCP servers are inventory-only (no default selection).
- Paid entries show AVAILABLE on key *presence* — validity surfaces at use time.
- Switching the embedding default affects new stores; an existing vector store
  keeps its ingestion-time dimensions (re-ingest to migrate).
- Per-mission overrides and cross-platform runtime expansion are later bricks.
