# CLI Verification — Brick 9 engine invocations

**Date**: 2026-07-07 · **Method**: local `--help` (authoritative) on installed binaries + official docs cross-check. This note feeds `/speckit-plan`; the argv here are the verified reference for `ENGINE_SPECS`.

## Installed on this machine

| Engine key | Binary | Installed | Version | Product |
|---|---|---|---|---|
| `claude-code` | `claude` | ✅ | 2.1.201 | Claude Code |
| `codex` | `codex` | ✅ | codex-cli 0.142.5 | OpenAI Codex CLI |
| `antigravity` | `agy` | ✅ | 1.0.14 | Google Antigravity CLI |
| `opencode` | `opencode` | ✅ | 1.17.9 | opencode |
| ~~`gemini`~~ | ~~`gemini`~~ | ❌ absent | — | Gemini CLI — **deprecated**, consumer requests stopped 2026-06-18; replaced by Antigravity CLI |

## Verified invocations

### claude-code — VALIDATED, current spec is correct
- **run**: `claude --allowedTools WebSearch -p "<prompt>"` — `-p/--print` non-interactive; `WebSearch` built-in tool.
- **route**: `claude -p "<prompt>"`.
- **MCP**: supports `--mcp-config <path> --strict-mcp-config` (the `--allowedTools` family). Only engine that speaks this flag.
- No change needed.

### codex — target of validation (has real web search)
- `codex exec [OPTIONS] [PROMPT]` — **`exec` is a subcommand and MUST come first**.
- `--search` is a **global** flag (before the subcommand) → sets `web_search="live"` (codex also has web search on by default in *cached* mode). Satisfies the Art. I precondition.
- `--sandbox` / `--color` / `-o/--output-last-message` / `--json` are **`exec` options** (after the subcommand). `--color` **errors at the top level** (`error: unexpected argument '--color' found`).
- **Proposed run**: `codex --search exec --color never --sandbox read-only -- "<prompt>"` — parses OK (verified).
- **Proposed route**: `codex --search exec --color never --sandbox read-only -- "<prompt>"` (same shape).
- ⚠️ **Current registry BUG**: the existing `route_cmd = ("codex", "--color", "never", "--sandbox", "read-only", "--")` has **no `exec` subcommand** → forwards to the **interactive** CLI (hangs headless until timeout, then keyword fallback), and `--color` is invalid at the top level. Must be fixed as part of validating codex. Existing `run_cmd` (`codex --search exec ...`) parses but should be re-confirmed.

### antigravity (`agy`) — new candidate, replaces gemini
- **Headless**: `agy --print "<prompt>"` (aliases `-p`, `--prompt`) = "Run a single prompt non-interactively and print the response". `--print-timeout` default 5m.
- `--dangerously-skip-permissions` = auto-approve tool calls — **likely required** for headless web search (no interactive approval available).
- ⚠️ **No dedicated web-search flag**. Antigravity's web search is tool/plugin-driven → guaranteed headless web search is **NOT** established by a CLI flag. Must be proven in live-test before any `validated=True`. Starts `validated=False`.
- **Proposed run/route**: `agy --print "<prompt>"` (add `--dangerously-skip-permissions` if live-test shows tool approval blocks search).

### opencode — new candidate
- **Headless one-shot**: `opencode run "<message>"` with `--format json` for raw events. This is the correct subprocess prompt→stdout shape.
- ❗ `opencode serve` (the PLAN Brick 1 reference) starts an **HTTP server** — wrong shape for the run/route contract; do **not** use it for the EngineSpec.
- ⚠️ Web search = **Exa AI**, available **only** with the OpenCode provider **or** `OPENCODE_ENABLE_EXA=<truthy>`. Env-/provider-gated, not guaranteed → `validated=False`; whether it can honestly declare `web_search_headless=True` is a live-test decision.
- `--model provider/model`, `--agent`, `--dir` available. Server binds `127.0.0.1` by default (relevant only if `serve` were ever used).

## Follow-ups for the plan
- Fix codex `route_cmd` (and re-confirm `run_cmd`) — the interactive-fallback route path is a real defect the contract tests should catch.
- Register `antigravity` (`agy --print`) and `opencode` (`opencode run`) as `validated=False` candidates.
- Remove the `gemini` slot; selecting it becomes an unknown-engine error (verify message lists current engines).
- PLAN.md Brick 1 line "References: opencode `serve`" is inaccurate for the contract shape — note the correction (`opencode run`) rather than editing the pinned brick history unless the owner wants it fixed.
- Compatibility matrix must mark antigravity/opencode web search as *config-gated / unproven*, not a plain ✓.

## Sources
- Codex CLI reference — https://developers.openai.com/codex/cli/reference
- Gemini→Antigravity transition — https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
- opencode CLI — https://opencode.ai/docs/cli/ · web search (Exa) — https://opencode.ai/docs/tools/
