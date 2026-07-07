# Phase 0 Research — Real Multi-CLI (Brick 9)

All unknowns are resolved: the CLI invocations were verified end-to-end during specify (see [research-cli.md](research-cli.md) for the raw `--help` evidence and sources), and the two architectural decisions were settled in the Session 2026-07-07 clarifications. This file consolidates the decisions that drive the design.

## D1 — codex registry entry: fix the malformed route, split search on/off by phase

**Decision**: Correct the codex `EngineSpec` to:
- `run_cmd = ("codex", "--search", "exec", "--color", "never", "--sandbox", "read-only", "--skip-git-repo-check", "--")` — global `--search` (live web search) before the `exec` subcommand; exec options after; `--` terminates flags so `_call`'s appended prompt is positional.
- `route_cmd = ("codex", "exec", "--color", "never", "--sandbox", "read-only", "--skip-git-repo-check", "--")` — **no `--search`**: routing is a cheap JSON-array classification that must not spend a live web search.

**Rationale**: The current entry is broken two ways (verified): `--color` is an `exec` option that **errors at the top level** (`error: unexpected argument '--color' found`), and the existing `route_cmd` has **no `exec` subcommand**, so codex would forward to its *interactive* CLI and hang headless until the route timeout, then silently fall back to `keyword_classify`. `--search` is a global flag (sets `web_search="live"`); it belongs before `exec` and only on the research path. `--skip-git-repo-check` avoids codex refusing to run when the mission's CWD is not a git repo.

**Alternatives considered**: (a) Keep `--search` on both run and route — rejected: wastes a live search on every routing call and slows the loop. (b) Drop the sandbox flags — rejected: `--sandbox read-only` is the safe posture for a research subprocess and was the original intent. Exact placement is confirmed by live parse checks (`codex exec --color never --sandbox read-only --help` → PARSES OK; `codex --search exec --help` → PARSES OK).

## D2 — antigravity replaces gemini (binary `agy`)

**Decision**: Remove the `gemini` slot; register `antigravity`:
- `run_cmd = ("agy", "--print")`, `route_cmd = ("agy", "--print")` — `--print` (aliases `-p`/`--prompt`) runs a single prompt non-interactively and prints the response; `_call` appends the prompt.
- `web_search_headless = False`, `validated = False` at registration.
- Live-test open item: Antigravity's web search is **tool-driven** (no dedicated flag). Headless tool execution likely needs `--dangerously-skip-permissions` (auto-approve tool calls). The live-test determines whether adding that flag yields genuine headless web search; only then may `web_search_headless`/`validated` flip to `True`.

**Rationale**: Google transitioned Gemini CLI → Antigravity CLI; the consumer `gemini` binary stopped serving requests 2026-06-18 and is absent locally, while `agy` 1.0.14 is installed and exposes a real headless print mode. Declaring `web_search_headless=False` initially is the honest state (no guaranteed search flag) and is permitted because the engine is unvalidated.

**Alternatives considered**: keep `gemini` pointing at `agy` (rejected — name ≠ binary, misleading); keep both `gemini` and `antigravity` (rejected by owner — the consumer `gemini` is dead). Owner decision: replace.

## D3 — opencode uses `run`, not `serve`

**Decision**: Register `opencode`:
- `run_cmd = ("opencode", "run")`, `route_cmd = ("opencode", "run")` — `opencode run "<message>"` is a one-shot prompt→stdout; `_call` appends the prompt as the trailing positional.
- `web_search_headless = False`, `validated = False` at registration.
- Live-test open item: opencode's web search is **Exa-based**, enabled only via the OpenCode provider or `OPENCODE_ENABLE_EXA=<truthy>` in the engine's environment. The live-test runs with that env set and verifies real searched sources before any flip.

**Rationale**: `opencode serve` starts a long-lived **HTTP server** (binds a host/port) — the wrong shape for the run/route subprocess contract and a needless new network surface (Art. V/VI). `opencode run` matches how every other engine is driven. The PLAN Brick 1 reference to `opencode serve` is inaccurate for the contract; noted in research-cli.md (the pinned brick text is left unedited unless the owner asks).

**Alternatives considered**: `opencode serve` + HTTP client (rejected — violates the subprocess-only shape, adds a bind/CORS surface); `--format json` on `run` (rejected for the deliverable path — the mission loop consumes the assistant's text answer, not a JSONL event stream; default formatted output is what synthesis/inspect read).

## D4 — `web_search_headless` semantics for config-gated engines (from clarification Q1)

**Decision**: Permissive rule. An engine whose web search is config-/env-gated MAY declare `web_search_headless=True` **only** when (a) the required configuration is explicitly documented in the matrix, AND (b) a live-test has proven real headless web search under that configuration. Absent that proof it declares `False`. The `EngineSpec.__post_init__` invariant (validated ⇒ web_search_headless) is unchanged and still enforced.

**Rationale**: Honors Art. I/II ("guaranteed headless web search") without over-restricting: a documented, live-proven env toggle is a legitimate guarantee, but a bare config *possibility* is not. The matrix must therefore show config-gated search distinctly (e.g. "✅ via `OPENCODE_ENABLE_EXA`"), never a plain ✓ that implies zero setup.

**Alternatives considered**: Strict (only an argv flag we pass counts) — rejected by owner as too restrictive, would make opencode/antigravity permanently non-promotable. Studio-managed env injection — rejected for this brick (keeps agency-kit engine-agnostic; the studio wiring is out of scope here).

## D5 — validation scope: attempt all three, gate each flip on its own live-test (from clarification Q2)

**Decision**: The brick attempts live validation of codex, antigravity, and opencode. Each `EngineSpec` flips to `validated=True` (and, for the config-gated pair, `web_search_headless=True`) **only** when its own live-test in the Brick-9 report demonstrates a completed mission with resolvable, verified sources. The offline-committable baseline registers all three (codex fixed; antigravity/opencode added) with the fixes above; the minimum bar to close the brick is `claude-code` + `codex` validated.

**Rationale**: Codex has a guaranteed search flag → most likely to pass. Antigravity/opencode are uncertain (tool-/env-gated), so the brick must not *require* them, but should still try (and record failures). This matches the clarified done-criteria and prevents the brick from stalling on upstream limitations.

**Sequencing consequence**: In `tasks.md`, the `validated=True` flip for each engine is a **separate task gated on the live-test report**, downstream of registry wiring + offline contract tests. The offline suite never asserts a live capability; it asserts registry shape, refusal, argv parse (fake binary), and matrix-vs-registry consistency.

## D6 — compatibility matrix location & shape

**Decision**: The authoritative engines × capabilities matrix lives in **`agencykit/README.md`**, replacing the existing 3-column engine table (currently at ~line 79). Columns: Engine (`--engine`) · Run / Route invocation · Headless web search (with config note) · MCP `--mcp-config` support · Kill-tree on cancel · Validation status. The root `README.md` engine mentions (lines ~15, ~27–28) are updated to name the current roster and link to the matrix. `agencykit/CLAUDE.md`'s `ENGINE_SPECS` example block is reconciled to the new roster.

**Rationale**: The engine detail already lives in `agencykit/README.md` (the brain's readme, where `--engine` is documented); the fuller matrix belongs there, with the root README as the pointer. A matrix-vs-registry consistency test (see contracts) keeps it honest, satisfying FR-011.

**Alternatives considered**: Root README as the authoritative matrix — rejected: the root README is the studio overview, not the engine reference; duplicating the full matrix there invites drift.

## D7 — offline test strategy

**Decision**: Extend `test_engine_contract.py` (mirror its existing patterns): (1) parametrized refusal test now covers `antigravity` and `opencode` (unvalidated → `EngineNotValidated`); (2) a removed-engine test asserts `run_mission_cli(engine="gemini")` raises the unknown-engine `ValueError` listing current engines (no silent substitution); (3) fake-binary run/route parse tests for each new engine (the existing `test_call_run_and_route_commands_return_stdout_for_each_spec` already iterates all specs — the fix makes codex's route path valid there); (4) a matrix-vs-registry consistency test (parse the README matrix rows, assert engine names + validation flags match `ENGINE_SPECS`).

**Rationale**: Keeps the suite fully offline (Art. VII) while proving the registry shape, the two behavioral guarantees (refusal, unknown-engine), and doc-vs-code consistency. The codex route fix is *caught* by the existing per-spec route test, which today would fail against the malformed entry — turning the bug into a regression guard.

**Open items remaining**: none blocking. All live-capability questions are deliberately deferred to the live-test report (D5), by design not by omission.
