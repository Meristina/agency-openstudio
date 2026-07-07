# Contract — Engine Registry (Brick 9)

The interface this feature exposes is the **engine registry** and the `--engine` selection behavior. This contract is what the offline suite (`agencykit/tests/test_engine_contract.py`) verifies. No network, no real CLI, no Node.

## C1 — Registered roster

`ENGINE_SPECS` keys after this brick are exactly: `{claude-code, codex, antigravity, opencode}`. `gemini` is absent.

- **Test**: assert key set equals the above; `"gemini" not in ENGINE_SPECS`.
- **Test**: `ENGINES` and `_ROUTE_CMD` views have the same keys as `ENGINE_SPECS` (existing `test_engine_views_match_specs…` — re-passes with the new roster).

## C2 — Per-engine argv is well-formed and non-interactive

For every spec, both `run_cmd` and `route_cmd` invoke the engine non-interactively and return stdout when driven through `_call` against a fake binary.

- **Test** (extends existing `test_call_run_and_route_commands_return_stdout_for_each_spec`): a fake binary named for each spec's `run_cmd[0]`/`route_cmd[0]` echoes its last arg; `_call(list(spec.run_cmd), "x")` and `_call(list(spec.route_cmd), "x")` both return `"x"`. This is exactly the check the malformed codex `route_cmd` would fail today → the fix is a regression guard.
- **Contract note**: `codex.route_cmd` MUST contain the `exec` subcommand (no interactive fallback) and MUST NOT contain `--search` (routing spends no live search). `codex.run_cmd` MUST contain global `--search` before `exec`.

## C3 — Refusal of unvalidated engines (no silent substitution)

`run_mission_cli(engine=E)` for any registered `E` with `validated=False` raises `EngineNotValidated` **before** any binary lookup or subprocess, naming `E`, "NOT validated", and the validated alternative(s).

- **Test** (extends existing parametrized refusal test): parametrize over `["codex", "antigravity", "opencode"]` (pre-live-test state). `_call` is monkeypatched to fail if invoked. Assert message contains the engine name, `"NOT validated"`, and `"claude-code"`.

## C4 — Unknown / removed engine

`run_mission_cli(engine="gemini")` (and any unknown name) raises `ValueError` whose message lists the currently registered engines and the validated set — never a silent fallback to another engine.

- **Test** (new): `pytest.raises(ValueError, match="Unknown engine")`; assert `"gemini"` in message and the message lists current engines.

## C5 — Validated ⇒ headless web search invariant (unchanged)

`EngineSpec.__post_init__` rejects `validated=True` with `web_search_headless=False`. Any engine flipped to `validated=True` (codex now; antigravity/opencode iff their live-test passes) MUST already declare `web_search_headless=True`.

- **Test** (existing `test_engine_spec_rejects_validated_without_headless_web_search` + `test_validated_specs_declare_headless_web_search`) — re-passes; add a case asserting the post-live-test codex spec satisfies it.

## C6 — Kill-tree on cancel/timeout (all engines)

Cancelling or timing out `_call` terminates the whole process group. Covered generically by the existing `@requires_posix` tree tests (`test_call_cancel_kills_parent_and_child`, `test_call_timeout_kills_parent_and_child`) — engine-agnostic, so they already cover the new engines' invocation shape. No per-engine duplication needed.

## C7 — Matrix reflects the registry (FR-011)

A test parses the compatibility-matrix rows in `agencykit/README.md` and asserts, for each row: the engine name exists in `ENGINE_SPECS`; the row's validation status matches `spec.validated`; every registered engine has exactly one row (no missing/extra rows); no row marked `validated` shows a non-affirmative headless-web-search cell.

- **Test** (new, offline — reads the committed README file): fail loud on any drift. This is the guard that keeps the published matrix honest as `validated` flips land.

## C8 — Mission-loop invariance (FR-007 / FR-012)

The `claude-code` run stays byte-identical; the veto loop, prompts, `_short_verdict`, and `_with_mcp` gating are untouched. Adding engines changes only `ENGINE_SPECS` (+ its views) and docs/tests.

- **Test** (existing `test_run_mission_validated_engine_proceeds_past_guards`, `test_registered_validated_fake_engine_runs_full_mission`) — re-pass unchanged, proving the loop is engine-agnostic and a newly-registered validated (fake) engine drives it end-to-end.

## Live-validation (out of the offline suite — FR-015/016)

Not part of this contract's automated checks. The live-test report (data-model.md) is the human/CI-run evidence that gates each `validated=True` flip. The offline suite asserts *registry shape and behavior*, never a live capability.
