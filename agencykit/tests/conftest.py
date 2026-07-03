"""Shared test setup.

The suite runs fully offline. After the openai-agents SDK path was removed, no
test imports the `agents` SDK or any department kit, so no stubbing is needed —
`agency_kit` is now pure-stdlib (router keyword classifier + departments + store)
and the engine path (`agency_cli/engines/cli_engine.py`) is exercised by
monkeypatching its subprocess call. This file is intentionally minimal.
"""
