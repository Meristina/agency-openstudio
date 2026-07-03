"""integrations — agent-harness adapters.

Single source of truth = the payload's `.agency/commands/*.md` (YAML frontmatter with
`description` (+ `argument-hint`) and a body using `$ARGUMENTS`). Each adapter transcodes that
into the target harness's native command format. No harness is privileged — "OpenAI" is not a
harness; the OpenAI-ecosystem target is **codex** (`.codex/prompts/`).

| harness  | dir                          | file                    | format                         |
|----------|------------------------------|-------------------------|--------------------------------|
| claude   | .claude/commands/            | agency.<n>.md           | MD + frontmatter (as-is)       |
| codex    | .codex/prompts/              | agency-<n>.md           | MD + frontmatter (passthrough) |
| cursor   | .cursor/commands/            | agency-<n>.md           | MD, NO frontmatter             |
| copilot  | .github/prompts/             | agency-<n>.prompt.md    | YAML frontmatter + body        |
| gemini   | .gemini/commands/agency/     | <n>.toml                | TOML (description + prompt)    |
| opencode | .opencode/commands/          | agency-<n>.md           | MD + frontmatter (description) |

Agency-Kit slash commands: /agency.mission, /agency.frame, /agency.inspect,
/agency.product, /agency.marketing, /agency.solve, /agency.finance,
/agency.comms, /agency.data, /agency.ops, /agency.people, /agency.tech

Claude also receives the agents+skills engine (the units the commands drive).
"""

import shutil
from pathlib import Path

SUPPORTED = ("claude", "codex", "cursor", "copilot", "gemini", "opencode")


def _parse_command(path: Path):
    """Return (name, description, body) from a source command markdown file."""
    from agency_kit.store import split_frontmatter
    text = path.read_text(encoding="utf-8")
    name = path.stem  # e.g. "mission"
    fm, body = split_frontmatter(text)
    body = body.lstrip("\n") if fm else text
    description = ""
    for line in fm.splitlines():
        if line.strip().startswith("description:"):
            description = line.split(":", 1)[1].strip().strip('"').strip("'")
            break
    description = description or f"Agency-Kit /{name}"
    return name, description, body


def _command_files(sources: dict):
    return sorted((sources["commands"]).glob("*.md"))


def _commands(sources: dict):
    for f in _command_files(sources):
        yield _parse_command(f)


def _write(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _install_claude(sources, target) -> dict:
    cmds = 0
    for f in _command_files(sources):
        _write(target / ".claude" / "commands" / f"agency.{f.name}", f.read_text(encoding="utf-8"))
        cmds += 1
    # the engine the commands drive
    for f in sources["agents"].glob("*.md"):
        _write(target / ".claude" / "agents" / f.name, f.read_text(encoding="utf-8"))
    skills_dir = sources["skills"]
    if skills_dir.is_dir():
        for d in skills_dir.iterdir():
            if d.is_dir():
                shutil.copytree(d, target / ".claude" / "skills" / d.name, dirs_exist_ok=True)
    return {"commands": cmds,
            "agents": len(list(sources["agents"].glob("*.md"))),
            "skills": sum(1 for d in skills_dir.iterdir() if d.is_dir()) if skills_dir.is_dir() else 0}


def _install_codex(sources, target) -> dict:
    # Codex custom prompts use the SAME format as our source (YAML frontmatter with
    # description/argument-hint + $ARGUMENTS) -> near-passthrough copy.
    n = 0
    for f in _command_files(sources):
        _write(target / ".codex" / "prompts" / f"agency-{f.name}", f.read_text(encoding="utf-8"))
        n += 1
    return {"commands": n,
            "note": "codex: .codex/prompts/agency-*.md -> /prompts:agency-<name>. "
                    "Codex also reads ~/.codex/prompts/ (home-scoped): copy them there for global use."}


def _install_cursor(sources, target) -> dict:
    n = 0
    for name, _desc, body in _commands(sources):
        _write(target / ".cursor" / "commands" / f"agency-{name}.md", body)  # no frontmatter
        n += 1
    return {"commands": n, "note": "cursor: body-only Markdown in .cursor/commands/ (no frontmatter)"}


def _install_copilot(sources, target) -> dict:
    n = 0
    for name, desc, body in _commands(sources):
        content = f"---\ndescription: {desc}\nmode: agent\n---\n\n{body}"
        _write(target / ".github" / "prompts" / f"agency-{name}.prompt.md", content)
        n += 1
    return {"commands": n, "note": "copilot: .github/prompts/*.prompt.md (mode: agent)"}


def _toml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')


def _install_gemini(sources, target) -> dict:
    n = 0
    for name, desc, body in _commands(sources):
        prompt = _toml_escape(body).replace("$ARGUMENTS", "{{args}}")
        content = f'description = "{desc}"\nprompt = """\n{prompt}\n"""\n'
        _write(target / ".gemini" / "commands" / "agency" / f"{name}.toml", content)
        n += 1
    return {"commands": n, "note": "gemini: .gemini/commands/agency/*.toml -> /agency:<name> (args {{args}})"}


def _install_opencode(sources, target) -> dict:
    n = 0
    for name, desc, body in _commands(sources):
        content = f"---\ndescription: {desc}\n---\n\n{body}"
        _write(target / ".opencode" / "commands" / f"agency-{name}.md", content)
        n += 1
    return {"commands": n, "note": "opencode: .opencode/commands/agency-*.md ($ARGUMENTS supported)"}


_ADAPTERS = {
    "claude": _install_claude,
    "codex": _install_codex,
    "cursor": _install_cursor,
    "copilot": _install_copilot,
    "gemini": _install_gemini,
    "opencode": _install_opencode,
}


def install(agent: str, sources: dict, target: Path) -> dict:
    """Write harness-specific command/engine files into `target`. Returns a summary."""
    agent = agent.lower()
    if agent not in _ADAPTERS:
        raise ValueError(f"unsupported agent {agent!r}; choose from {SUPPORTED}")
    summary = {"agent": agent}
    summary.update(_ADAPTERS[agent](sources, Path(target)))
    return summary
