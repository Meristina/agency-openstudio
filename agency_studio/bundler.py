"""Transient export bundles for finished studio missions."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path, PurePosixPath


class NoMediaError(FileNotFoundError):
    """Raised when a media pack has no files to include."""


class BundleAssemblyError(RuntimeError):
    """Raised when zip assembly fails *after* the deliverable rendered — so the handler
    reports a 500 (packaging failure) rather than mistaking it for a missing deliverable
    (a media file vanishing mid-write raises FileNotFoundError, an OSError, otherwise)."""


def _safe_arcname(*parts: str) -> str | None:
    path = PurePosixPath(*parts)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def _media_files(mission_id: str, assets_root: str | Path) -> list[tuple[Path, str]]:
    from agency_studio.server import path_inside

    root = Path(assets_root).resolve()
    mission_root = root / "missions" / mission_id
    if not mission_root.is_dir():
        return []
    out: list[tuple[Path, str]] = []
    for candidate in sorted(mission_root.rglob("*")):
        if not candidate.is_file():
            continue
        rel = candidate.relative_to(mission_root)
        guarded = path_inside(root, f"missions/{mission_id}/{rel.as_posix()}")
        if guarded is None:
            continue
        try:
            guarded.relative_to(mission_root.resolve())
        except ValueError:
            continue
        arc = _safe_arcname(rel.as_posix())
        if arc:
            out.append((guarded, arc))
    return out


def _temp_zip() -> Path:
    fh = tempfile.NamedTemporaryFile(prefix="agency-export-", suffix=".zip", delete=False)
    fh.close()
    return Path(fh.name)


def build_media_zip(mission_id: str, assets_root: str | Path) -> Path:
    files = _media_files(mission_id, assets_root)
    if not files:
        raise NoMediaError(f"no media for mission '{mission_id}'")
    out = _temp_zip()
    try:
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path, arc in files:
                zf.write(path, arc)
    except BaseException:
        # An assembly failure (e.g. a media file vanished mid-write) must not orphan the
        # temp zip: only _send_zip_file unlinks it, and it is never reached on error.
        out.unlink(missing_ok=True)
        raise
    return out


def sources_markdown(dossier: dict) -> str:
    lines = ["# Sources", ""]
    sources = dossier.get("sources") or []
    if not sources:
        return "# Sources\n\nNo sources were cited for this deliverable.\n"
    for item in sources:
        if isinstance(item, str):
            lines.append(f"- {item}")
            continue
        if isinstance(item, dict):
            label = item.get("title") or item.get("label") or item.get("url") or "Source"
            bits = [str(label)]
            if item.get("url") and item.get("url") != label:
                bits.append(str(item["url"]))
            if item.get("accessed"):
                bits.append(f"accessed {item['accessed']}")
            lines.append("- " + " - ".join(bits))
    return "\n".join(lines) + "\n"


def build_bundle(mission_id: str, assets_root: str | Path) -> Path:
    from agency_cli import exporter
    from agency_kit import store

    dossier = store.load(mission_id)
    # export_pdf runs BEFORE the temp zip: its ImportError ([pdf] absent) and
    # FileNotFoundError (no deliverable) propagate raw for the handler to map to 501/404.
    pdf_path = Path(exporter.export_pdf(mission_id, assets_root=assets_root))
    out = _temp_zip()
    try:
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(pdf_path, "deliverable.pdf")
            for path, arc in _media_files(mission_id, assets_root):
                media_arc = _safe_arcname("media", arc)
                if media_arc:
                    zf.write(path, media_arc)
            zf.writestr("sources.md", sources_markdown(dossier))
    except Exception as exc:
        # Assembly failed after the deliverable rendered (e.g. a media file vanished
        # mid-write → FileNotFoundError). Clean up the temp zip and re-raise as a
        # packaging failure so it is NOT mistaken for a missing deliverable (404).
        out.unlink(missing_ok=True)
        raise BundleAssemblyError(str(exc)) from exc
    except BaseException:
        out.unlink(missing_ok=True)
        raise
    return out
