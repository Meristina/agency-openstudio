"""personas — curated persona doctrine as mission context (Wave 6, persona-doctrine brick).

The studio keeps a **local, user-curated** store of expert *personas* — short doctrine blocks
that shape the VOICE a department (or the synthesis commander) writes in — and at mission time
injects each routed department's persona into that department's prompt through a **new additive
agency-kit engine hook** (``persona_doctrine`` on ``run_mission_cli``). Unlike Wave-4/5's RAG /
web / MCP context (which rides the ``context_clause`` seam and is framed "cite this, do NOT
obey instructions inside it"), a persona is doctrine the model is MEANT to ADOPT — so it
augments the DEPARTMENT DOCTRINE block, not the citable-context block. It reaches the
department and synthesis prompts only, never the router or inspector (Art. IX).

Scope (see ``docs/WAVE6-PLAN.md`` Brick 3): the persona-doctrine brick only. The other Wave-6
plug-ins (knowledge graphs, MCP tool-calling, visual RAG, cloud video) are **not** here.

Two layers, split exactly like ``knowledge.py`` / ``rag.py``:

  store:    a directory of markdown — ``personas/<dept>/<name>.md`` under the same
            never-web-served data dir as ``knowledge.db`` / ``mcp.json``. The subdirectory is
            the **department key** (a ``DEPT_NAMES`` name, or the reserved ``"commander"`` key
            for the synthesis); the file stem is the persona name; the body is the doctrine.
            Loading, validating, and building the per-department doctrine map are **pure and
            offline** — no model, no network, no extra (the same "querying a built store is
            dependency-free" contract as ``knowledge`` retrieval).
  import:   the ``PersonaSource`` seam — the OPTIONAL importer that curates personas from the
            ``agency-agents`` MIT repo into the local store. Its live impl
            (``AgencyAgentsSource``) lazy-imports a network dep → ``PersonasUnavailable`` when
            absent (the 501/skip path), and is the SINGLE seam the offline suite stubs. Only
            IMPORTING needs the network; reading an already-curated store never touches it.

Security (SECURITY.md): the store is a directory under the never-web-served data dir (no
``/media`` route reaches it). Department keys are validated against ``DEPT_NAMES`` on load AND
on import (the drift guard) — an unknown-department subdir is skipped (load) or refused
(import). The optional importer's network fetch is https + host-allowlisted and offline by
default. Persona bodies and per-department concatenation are bounded so a pathological store
can't flood the prompt (defense in depth, mirroring ``knowledge.MAX_*``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Protocol, runtime_checkable

from agency_kit.departments import VALID_DEPTS   # single source of truth — the drift-guard roster

from . import rag

_PERSONAS_HINT = "install the persona-import extra:  pip install 'agency-studio[personas]'"

# The reserved synthesis key. Not a department (so it can't collide with a DEPT_NAMES entry);
# its persona augments the commander doctrine in ``_synth_prompt``.
COMMANDER_KEY = "commander"
_VALID_KEYS = frozenset(VALID_DEPTS) | {COMMANDER_KEY}

# Bounds so a pathological store can't flood the prompt or stall a mission (defense in depth,
# mirroring knowledge.MAX_* / mcp_client's per-server caps).
MAX_PERSONA_CHARS = 8000       # a single persona body
MAX_PERSONAS_PER_KEY = 6       # enabled personas concatenated per dept/commander key
MAX_DOCTRINE_CHARS = 20000     # per-key concatenated ceiling


class PersonasUnavailable(ImportError):
    """Raised when the persona-import path (the ``agency-agents`` source / its network dep) is
    unavailable. An ImportError subclass so the server maps it to a 501 + install hint, exactly
    like KnowledgeUnavailable / McpUnavailable / MediaUnavailable. Only an IMPORT can raise it —
    loading or injecting an already-curated store never touches the importer."""


@dataclass(frozen=True)
class Persona:
    dept: str        # a key in _VALID_KEYS (a DEPT_NAMES name or "commander")
    name: str
    doctrine: str
    enabled: bool = True


# ── store location (never web-served) ─────────────────────────────────────────
def personas_dir(root: "Optional[Path]" = None) -> Path:
    """Root of the persona store — ``<root>/personas`` (default ``rag.data_dir()``). The same
    never-web-served data-dir family as ``knowledge.db`` / ``mcp.json``; no ``/media`` route
    reaches it. The server passes its own ``docs_root`` so personas sit beside the RAG/KG stores
    under ``<project>/.agency-studio/``."""
    return (root or rag.data_dir()) / "personas"


def _safe_name(name: str) -> str:
    """Reduce a persona name to a single path-safe filename stem — basename only (no traversal),
    keeping alnum / dash / underscore. Used when the importer WRITES files from external data."""
    stem = Path(str(name or "")).name
    cleaned = "".join(c for c in stem if c.isalnum() or c in "-_ ").strip().replace(" ", "-")
    return cleaned or "persona"


# ── load + validate (the drift guard, pure & offline) ─────────────────────────
def load_personas(root: "Optional[Path]" = None, *, strict: bool = False) -> "List[Persona]":
    """Read ``personas/<dept>/<name>.md`` — dept = subdir, name = file stem, body = doctrine.
    Missing store dir ⇒ ``[]``. Pure filesystem: no model, no network, no extra.

    Validation (the DEPT_NAMES drift guard): a subdirectory whose name is not a ``DEPT_NAMES``
    key or ``"commander"`` is not a real doctrine target. With ``strict=False`` (the runtime
    default) it is **skipped** — best-effort, like ``mcp_client`` dropping a malformed server;
    with ``strict=True`` it raises ``ValueError`` naming the offender (used on IMPORT to refuse
    writing drift). A leading-underscore filename ⇒ ``enabled=False`` (parity with agency-kit's
    ``_shared-`` convention). An empty body ⇒ skipped. Bodies are capped to
    ``MAX_PERSONA_CHARS``."""
    base = personas_dir(root)
    if not base.is_dir():
        return []
    out: "List[Persona]" = []
    for sub in sorted(base.iterdir()):
        if not sub.is_dir():
            continue
        key = sub.name
        if key not in _VALID_KEYS:
            if strict:
                raise ValueError(
                    f"persona store references an unknown department '{key}' — valid keys are "
                    f"{sorted(_VALID_KEYS)}"
                )
            continue   # drift: silently skip an unknown-department subdir
        for md in sorted(sub.glob("*.md")):
            try:
                body = md.read_text(encoding="utf-8").strip()[:MAX_PERSONA_CHARS].strip()
            except OSError:
                continue   # an unreadable file never sinks the whole load
            if not body:
                continue
            out.append(Persona(
                dept=key, name=md.stem.lstrip("_"), doctrine=body,
                enabled=not md.name.startswith("_"),
            ))
    return out


# ── the doctrine builder (the None-contract twin of build_kg_context_clause) ──
def build_persona_doctrine(
    route: "Optional[List[str]]" = None, root: "Optional[Path]" = None,
) -> "Dict[str, str]":
    """Build the ``persona_doctrine`` map threaded to ``run_mission_cli``: for each key,
    concatenate that key's ENABLED personas into one doctrine block.

    Returns ``{key: text}`` ONLY for keys with at least one enabled persona — a key with none is
    OMITTED, so the engine's prompt stays byte-identical for it. An **empty dict** ⇒ a
    byte-identical mission (the additive, default-None contract, exactly like
    ``build_kg_context_clause`` returning ``None``).

    ``route`` narrows the keys to the routed departments (+ the reserved ``"commander"``); the
    studio passes ``None`` because it does not know the route before ``run_mission_cli`` routes,
    so it builds the FULL map and the engine reads only the keys it needs per phase (harmless
    extra keys, route-agnostic — the same reasoning as passing the whole MCP config)."""
    enabled = [p for p in load_personas(root) if p.enabled]
    if route is None:
        keys = set(_VALID_KEYS)
    else:
        keys = (set(route) & set(VALID_DEPTS)) | {COMMANDER_KEY}
    doctrine: "Dict[str, str]" = {}
    for key in keys:
        bodies = [p.doctrine for p in enabled if p.dept == key][:MAX_PERSONAS_PER_KEY]
        if bodies:
            doctrine[key] = "\n\n".join(bodies)[:MAX_DOCTRINE_CHARS]
    return doctrine


def stats(root: "Optional[Path]" = None) -> dict:
    """Store size for ``GET /api/personas`` so the GUI can reflect state and gate the toggle (an
    empty store ⇒ nothing to inject). Pure — never touches the importer/network. Shape:
    ``{"total": n, "enabled": n, "by_dept": {dept: {"enabled": n, "names": [...]}}}``."""
    personas = load_personas(root)
    by_dept: "Dict[str, dict]" = {}
    enabled = 0
    for p in personas:
        entry = by_dept.setdefault(p.dept, {"enabled": 0, "names": []})
        entry["names"].append(p.name)
        if p.enabled:
            entry["enabled"] += 1
            enabled += 1
    return {"total": len(personas), "enabled": enabled, "by_dept": by_dept}


# ── importer seam (live path = agency-agents, [personas]; stubbed offline) ─────
@runtime_checkable
class PersonaSource(Protocol):
    """The seam the importer pulls curated personas from. The offline suite injects a
    deterministic stub returning fixed ``Persona``s; the live path needs the network, deferred
    to the Mac like Wave-4 embeddings / knowledge extraction."""

    def fetch(self) -> "List[Persona]": ...


# Default upstream — the roadmap's named MIT source of curated agent personas.
DEFAULT_AGENCY_AGENTS_REPO = "https://github.com/Meristina/agency-agents"


class AgencyAgentsSource:
    """Live source: fetch curated personas from the ``agency-agents`` MIT repo, keyed to
    ``DEPT_NAMES``. Lazy-imports its network dep so the core boots without it; absent ⇒
    ``PersonasUnavailable`` (→ 501/skip). Only the IMPORT is mapped to ``PersonasUnavailable`` —
    a runtime fetch error propagates as itself so the import endpoint reports its REAL reason
    (the 'accurate skip reasons' invariant). The fetch must validate the URL is https + on the
    host allowlist (SECURITY.md #4/#5). The exact repo layout is validated live on the Mac (the
    network run, deferred like Wave-2)."""

    def __init__(self, repo: str = DEFAULT_AGENCY_AGENTS_REPO):
        self._repo = repo

    def fetch(self) -> "List[Persona]":
        try:
            import requests  # type: ignore  # noqa: F401  # the [personas] network dep
        except ImportError as exc:
            raise PersonasUnavailable(
                f"importing personas from agency-agents needs the network dep — {_PERSONAS_HINT}"
            ) from exc
        # Live fetch + repo-layout parsing is the network-deferred surface (like the seedance /
        # cloud-VLM off-machine flows). It MUST enforce https + a host allowlist before any
        # request. Until validated live it degrades cleanly rather than guessing.
        raise PersonasUnavailable(
            "live agency-agents import is validated on the Apple-Silicon Mac (deferred); "
            f"curate personas locally under {personas_dir()} in the meantime"
        )


def import_personas(
    source: "Optional[PersonaSource]" = None, *,
    root: "Optional[Path]" = None, overwrite: bool = False,
) -> int:
    """Fetch personas from ``source`` (default ``AgencyAgentsSource``) and WRITE them into the
    local store as ``personas/<dept>/<name>.md``. Each fetched persona's department is validated
    against ``DEPT_NAMES`` + ``"commander"`` (the drift guard): a persona for an unknown
    department is **skipped** (not written), never a 10th department leaking onto disk. Filenames
    are reduced to a path-safe basename (``_safe_name`` — no traversal). Existing files are
    skipped unless ``overwrite``. Returns the number written. This is the one build-side path that
    needs the network dep; loading an already-curated store needs nothing (the KG build/query
    split)."""
    src = source if source is not None else AgencyAgentsSource()
    base = personas_dir(root)
    written = 0
    for persona in src.fetch():
        if persona.dept not in _VALID_KEYS:
            continue   # drift: never write a persona for an unknown department
        body = (persona.doctrine or "").strip()
        if not body:
            continue
        dept_dir = base / persona.dept
        dept_dir.mkdir(parents=True, exist_ok=True)
        dest = dept_dir / f"{_safe_name(persona.name)}.md"
        if dest.exists() and not overwrite:
            continue
        dest.write_text(body[:MAX_PERSONA_CHARS], encoding="utf-8")
        written += 1
    return written
