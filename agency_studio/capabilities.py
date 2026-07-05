"""Passive capability inventory and model default selection.

Inventory checks are passive by contract: optional extras are probed with
``find_spec``, API keys by presence only, and OpenMontage only through a subprocess.
"""

from __future__ import annotations

import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from . import mcp_client, rag
from .engines import models

Family = str
CostClass = str
Availability = str
UnavailableReason = str

FAMILIES = (
    "image", "video", "visual", "embedding", "kg-extraction", "stt", "tts",
    "production-tools", "mcp",
)
SELECTABLE_FAMILIES = frozenset(FAMILIES[:7])

ENV_VARS = {
    "image": "AGENCY_STUDIO_IMAGE_MODEL",
    "video": "AGENCY_STUDIO_VIDEO_BACKEND",
    "visual": "AGENCY_STUDIO_VISUAL_BACKEND",
    "embedding": "AGENCY_STUDIO_EMBED_MODEL",
    "kg-extraction": "AGENCY_STUDIO_KG_BACKEND",
    "stt": "AGENCY_STUDIO_STT_MODEL",
    "tts": "AGENCY_STUDIO_TTS_MODEL",
}


@dataclass(frozen=True)
class CapabilityEntry:
    id: str
    label: str
    family: Family
    cost: CostClass
    availability: Availability
    reason: UnavailableReason | None = None
    enablement: str | None = None
    tier: str | None = None
    note: str = ""
    default: bool = False
    key_env: str | None = None


@dataclass(frozen=True)
class CapabilityFamilyView:
    family: Family
    selectable: bool
    entries: list[CapabilityEntry]
    selected: str | None
    selected_stale: bool
    env_override: str | None
    active: str


def _entry_dict(entry: CapabilityEntry) -> dict:
    return asdict(entry)


def _family_dict(view: CapabilityFamilyView) -> dict:
    data = asdict(view)
    data["entries"] = [_entry_dict(e) for e in view.entries]
    return data


# Probe module → the pyproject extra that provides it (drives the install hint).
_EXTRA_FOR_PROBE = {
    "mflux": "media",
    "boogu_image_mlx": "boogu",
    "mlx_whisper": "media",
    "kokoro_onnx": "media",
    "soundfile": "media",
    "mlx_embedding_models": "studio",
    "mlx_vlm": "visual",
    "mcp": "mcp",
    "gliner": "kg",
}


def _extra_available(module: str) -> tuple[Availability, UnavailableReason | None, str | None]:
    if importlib.util.find_spec(module):
        return "available", None, None
    extra = _EXTRA_FOR_PROBE.get(module)
    hint = f"pip install 'agency-studio[{extra}]'" if extra else f"install the '{module}' package"
    return "unavailable", "missing_extra", hint


def _key_present(env_name: str) -> tuple[Availability, UnavailableReason | None, str | None]:
    if os.environ.get(env_name):
        return "available", None, None
    return "unavailable", "missing_key", env_name


def _runtime_supported(entry: object) -> tuple[Availability, UnavailableReason | None, str | None]:
    backend = getattr(entry, "backend", "")
    probe = getattr(entry, "probe_module", "")
    needs_mlx = backend in {"mflux", "boogu", "local"} or probe.startswith("mlx")
    if needs_mlx and not (sys.platform == "darwin" and platform.machine() == "arm64"):
        return "unavailable", "unsupported_runtime", "requires Apple-Silicon macOS; Brick 5 adds siblings"
    return "available", None, None


def _first_unavailable(*checks: tuple[Availability, UnavailableReason | None, str | None]):
    for availability, reason, enablement in checks:
        if availability == "unavailable":
            return availability, reason, enablement
    return "available", None, None


def _local_entry(family: Family, entry: object, probe_module: str, *, note: str = "",
                 extra_probes: tuple[str, ...] = ()) -> CapabilityEntry:
    availability, reason, enablement = _first_unavailable(
        _runtime_supported(entry),
        _extra_available(probe_module),
        *(_extra_available(m) for m in extra_probes),
    )
    return CapabilityEntry(
        id=getattr(entry, "id"),
        label=getattr(entry, "label"),
        family=family,
        cost="free",
        availability=availability,
        reason=reason,
        enablement=enablement,
        note=note or getattr(entry, "note", ""),
        default=bool(getattr(entry, "default", False)),
    )


def _paid_entry(family: Family, entry: object, key_env: str) -> CapabilityEntry:
    availability, reason, enablement = _key_present(key_env)
    return CapabilityEntry(
        id=getattr(entry, "id"),
        label=getattr(entry, "label"),
        family=family,
        cost="paid",
        availability=availability,
        reason=reason,
        enablement=enablement,
        note=getattr(entry, "note", ""),
        default=bool(getattr(entry, "default", False)),
        key_env=key_env,
    )


def image_entries() -> list[CapabilityEntry]:
    out = []
    for entry in models.IMAGE_MODELS.values():
        probe = "boogu_image_mlx" if entry.backend == "boogu" else "mflux"
        out.append(_local_entry("image", entry, probe))
    return out


def video_entries() -> list[CapabilityEntry]:
    from . import seedance
    out = []
    for entry in seedance.VIDEO_MODELS.values():
        if entry.backend == "cloud":
            out.append(_paid_entry("video", entry, seedance.CLOUD_API_KEY_ENV))
        else:
            out.append(CapabilityEntry(
                id=entry.id, label=entry.label, family="video", cost="free",
                availability="available", note="local OpenMontage subprocess",
                default=entry.default,
            ))
    return out


def visual_entries() -> list[CapabilityEntry]:
    from . import visual
    out = []
    for entry in visual.VISUAL_MODELS.values():
        if entry.backend == "cloud":
            out.append(_paid_entry("visual", entry, visual.CLOUD_API_KEY_ENV))
        else:
            out.append(_local_entry("visual", entry, "mlx_vlm"))
    return out


def embedding_entries() -> list[CapabilityEntry]:
    note = "Switching affects new stores; re-ingest existing stores with different dimensions."
    return [_local_entry("embedding", e, "mlx_embedding_models", note=f"{e.note}. {note}") for e in models.EMBED_MODELS.values()]


def kg_entries() -> list[CapabilityEntry]:
    claude = CapabilityEntry(
        id="claude", label="Claude CLI", family="kg-extraction", cost="free",
        availability="available" if shutil.which("claude") else "unavailable",
        reason=None if shutil.which("claude") else "missing_extra",
        enablement=None if shutil.which("claude") else "install and authenticate Claude Code",
        note="subscription CLI brain", default=True,
    )
    gliner_avail = _extra_available("gliner")
    return [
        claude,
        CapabilityEntry(
            id="gliner2", label="GLiNER2", family="kg-extraction", cost="free",
            availability=gliner_avail[0], reason=gliner_avail[1],
            enablement=gliner_avail[2],
            note="on-device extraction",
        ),
    ]


def stt_entries() -> list[CapabilityEntry]:
    return [_local_entry("stt", e, e.probe_module) for e in models.STT_MODELS.values()]


def tts_entries() -> list[CapabilityEntry]:
    # Synthesis needs BOTH deps _probe_tts gates on: the engine (kokoro_onnx) and the
    # wav writer (soundfile) — probing only one would show AVAILABLE yet fail at /api/tts.
    return [_local_entry("tts", e, e.probe_module, extra_probes=("soundfile",))
            for e in models.TTS_MODELS.values()]


_CATALOG_CACHE: list[CapabilityEntry] | None = None
_CATALOG_LOCK = threading.Lock()  # the threading HTTP server can probe concurrently


def _spawn_catalog() -> str:
    script = (
        "import json;"
        "from tools.tool_registry import ToolRegistry;"
        "r=ToolRegistry();"
        "r.discover();"
        "print(json.dumps(r.support_envelope()))"
    )
    root = Path(__file__).resolve().parents[1] / "openmontage"
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(root),
        text=True,
        capture_output=True,
        timeout=20,
        check=True,
    )
    return proc.stdout


def production_tool_entries(refresh: bool = False) -> list[CapabilityEntry]:
    global _CATALOG_CACHE
    with _CATALOG_LOCK:
        return _production_tool_entries_locked(refresh)


def _production_tool_entries_locked(refresh: bool) -> list[CapabilityEntry]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None and not refresh:
        return _CATALOG_CACHE
    try:
        raw = json.loads(_spawn_catalog())
        tools = raw.get("tools", raw if isinstance(raw, list) else [])
        entries = []
        for item in tools:
            if not isinstance(item, dict):
                continue
            tool_id = str(item.get("name") or item.get("id") or "")
            if not tool_id:
                continue
            tier = str(item.get("tier") or item.get("runtime") or "").lower()
            cost = "free_paid" if tier == "hybrid" else "paid" if tier == "api" else "free"
            entries.append(CapabilityEntry(
                id=tool_id, label=str(item.get("label") or tool_id),
                family="production-tools", cost=cost, availability="available",
                tier=tier or None, note=str(item.get("description") or item.get("note") or ""),
            ))
        _CATALOG_CACHE = entries
    except Exception as exc:
        _CATALOG_CACHE = [CapabilityEntry(
            id="openmontage-catalog", label="OpenMontage catalog",
            family="production-tools", cost="free_paid", availability="unavailable",
            reason="catalog_error", enablement=str(exc), note="catalog probe failed",
        )]
    return _CATALOG_CACHE


def mcp_entries() -> list[CapabilityEntry]:
    try:
        servers = mcp_client.list_servers()
    except Exception as exc:
        return [CapabilityEntry(
            id="mcp-config", label="MCP config", family="mcp", cost="free",
            availability="unavailable", reason="catalog_error", enablement=str(exc),
        )]
    extra = _extra_available("mcp")
    out = []
    for server in servers:
        name = str(server.get("name") or "")
        if not name:
            continue
        availability, reason, enablement = extra
        command = server.get("command")
        if availability == "available" and command and not shutil.which(str(command)):
            availability, reason, enablement = "unavailable", "missing_extra", f"install command: {command}"
        out.append(CapabilityEntry(
            id=name, label=name, family="mcp", cost="free", availability=availability,
            reason=reason, enablement=enablement, note=str(server.get("transport") or ""),
        ))
    return out


BUILDERS: dict[Family, Callable[..., list[CapabilityEntry]]] = {
    "image": image_entries,
    "video": video_entries,
    "visual": visual_entries,
    "embedding": embedding_entries,
    "kg-extraction": kg_entries,
    "stt": stt_entries,
    "tts": tts_entries,
    "production-tools": production_tool_entries,
    "mcp": mcp_entries,
}


# One process-wide lock: handlers construct a fresh SelectionStore per request, so the
# read-modify-write in set()/clear() must serialize at module level or concurrent PUTs
# could drop each other's (unrelated) family selections. Reentrant because set()/clear()
# call save() while holding it. Cross-process writers stay last-write-wins (spec).
_SELECTION_LOCK = threading.RLock()


class SelectionStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (rag.data_dir() / "selections.json")

    def load(self) -> dict[str, str]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("selections"), dict):
            return {}
        return {str(k): str(v) for k, v in data["selections"].items() if k in SELECTABLE_FAMILIES and isinstance(v, str)}

    def save(self, selections: dict[str, str]) -> None:
        with _SELECTION_LOCK:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(dir=str(self.path.parent), prefix=".selections-", suffix=".json")
            tmp = Path(tmp_name)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump({"version": 1, "selections": selections}, fh, sort_keys=True)
                os.replace(tmp, self.path)
            finally:
                tmp.unlink(missing_ok=True)

    def set(self, family: Family, entry_id: str) -> None:
        with _SELECTION_LOCK:
            selections = self.load()
            selections[family] = entry_id
            self.save(selections)

    def clear(self, family: Family) -> None:
        with _SELECTION_LOCK:
            selections = self.load()
            selections.pop(family, None)
            self.save(selections)


def _entries_for(family: Family, refresh: bool = False) -> list[CapabilityEntry]:
    if family == "production-tools":
        return production_tool_entries(refresh=refresh)
    return BUILDERS[family]()


def _default(entries: list[CapabilityEntry]) -> str:
    return next((e.id for e in entries if e.default), entries[0].id if entries else "")


def _selection_state(family: Family, entries: list[CapabilityEntry], selections: dict[str, str]):
    selected = selections.get(family)
    if not selected:
        return None, False
    by_id = {e.id: e for e in entries}
    entry = by_id.get(selected)
    return selected, entry is None or entry.availability != "available"


def resolve(family: Family, *, store: SelectionStore | None = None) -> str:
    if family not in SELECTABLE_FAMILIES:
        raise ValueError(f"family {family!r} is inventory-only")
    entries = _entries_for(family)
    by_id = {e.id: e for e in entries}
    env_name = ENV_VARS[family]
    env_value = (os.environ.get(env_name) or "").strip()
    if env_value:
        if env_value not in by_id:
            raise ValueError(f"unknown {env_name}={env_value!r} — available: {', '.join(by_id)}")
        return env_value
    selected = (store or SelectionStore()).load().get(family)
    if selected and by_id.get(selected) and by_id[selected].availability == "available":
        return selected
    return _default(entries)


def inventory(refresh: bool = False, *, store: SelectionStore | None = None) -> dict:
    selections = (store or SelectionStore()).load()
    families = []
    for family in FAMILIES:
        entries = _entries_for(family, refresh=refresh)
        selectable = family in SELECTABLE_FAMILIES
        selected, stale = _selection_state(family, entries, selections) if selectable else (None, False)
        env_name = ENV_VARS.get(family)
        env_override = env_name if env_name and os.environ.get(env_name) else None
        # The inventory must render even when the env override names an unknown id
        # (consumers still fail loud through resolve() — the view stays honest).
        if selectable:
            try:
                active = resolve(family, store=store)
            except ValueError:
                active = _default(entries)
        else:
            active = ""
        families.append(_family_dict(CapabilityFamilyView(
            family=family,
            selectable=selectable,
            entries=entries,
            selected=selected,
            selected_stale=stale,
            env_override=env_override,
            active=active,
        )))
    return {"families": families, "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}


def select(family: Family, entry_id: str, *, store: SelectionStore | None = None) -> dict | tuple[int, dict]:
    if family not in FAMILIES:
        return 400, {"error": f"unknown family {family!r}"}
    if family not in SELECTABLE_FAMILIES:
        return 400, {"error": f"family {family!r} is inventory-only"}
    entries = _entries_for(family)
    by_id = {e.id: e for e in entries}
    entry = by_id.get(entry_id)
    if entry is None:
        return 400, {"error": f"unknown entry {entry_id!r} for family {family!r}"}
    if entry.availability != "available":
        return 409, {"error": "entry unavailable", "reason": entry.reason, "enablement": entry.enablement}
    (store or SelectionStore()).set(family, entry_id)
    return next(f for f in inventory(store=store)["families"] if f["family"] == family)


def clear(family: Family, *, store: SelectionStore | None = None) -> int | tuple[int, dict]:
    if family not in FAMILIES:
        return 400, {"error": f"unknown family {family!r}"}
    if family not in SELECTABLE_FAMILIES:
        return 400, {"error": f"family {family!r} is inventory-only"}
    (store or SelectionStore()).clear(family)
    return 204
