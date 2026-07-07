# Brick 9 Multi-CLI Live-Test Report

Date: 2026-07-08

Representative mission goal used for all engines:

> Assess whether AI agent CLI tools are being adopted by agencies in 2026. Cite at least three current HTTPS sources.

Live runs used the mission loop with escalation disabled and source verification enabled:
`verification={"min_sources": 3, "resolve": True}`.

## Summary

| Engine | Outcome | Decision |
|---|---|---|
| `codex` | PASS | Set `validated=True`; keep `web_search_headless=True`. |
| `antigravity` | FAIL | Keep refused: final dossier failed inspector/source gate. |
| `opencode` | FAIL | Keep refused: CLI auth failed before a department output. |

## codex

- Config used: temporary in-process `validated=True` flip for the run; registry command `codex --search exec --color never --sandbox read-only --skip-git-repo-check --`.
- Dossier shape: route `["product"]`; `dept_outputs` contained `product`; `delivered=True`; final inspector verdict `PASS` after one VETO/re-synthesis cycle.
- Source verification: final product count `11/3`; 12 of 13 cited URLs resolved or were accepted as ambiguous (`openai.com` returned HTTP 403 to HEAD).
- Sample resolved URLs: `https://docs.anthropic.com/en/docs/claude-code/overview`, `https://blog.google/technology/developers/introducing-gemini-cli-open-source-ai-agent/`, `https://github.blog/news-insights/product-news/github-copilot-meet-the-new-coding-agent/`, `https://arxiv.org/abs/2607.01418`.
- Flip decision: PASS. `codex` is validated for production.

## antigravity

- Config used: temporary in-process `validated=True, web_search_headless=True` flip for the run; registry command `agy --print`.
- Dossier shape: route `["product"]`; `dept_outputs` contained `product`; `delivered=True`; final inspector verdict `VETO`.
- Source verification: final product count `0/3`; only `https://dora.dev` appeared, and it was not attributed to the `product` department.
- Flip decision: FAIL. Keep `validated=False` and `web_search_headless=False`.

## opencode

- Config used: temporary in-process `validated=True, web_search_headless=True` flip for the run; `OPENCODE_ENABLE_EXA=1`; registry command `opencode run`.
- Dossier shape: route returned `["people"]`, then the first department call failed before producing output.
- Failure: `CLI engine 'opencode' exited 1: Error: User not found.`
- Source verification: not reached.
- Flip decision: FAIL. Keep `validated=False` and `web_search_headless=False`.
