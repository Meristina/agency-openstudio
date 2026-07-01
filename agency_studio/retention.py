"""retention — bound ``studio_assets/`` disk growth with an oldest-first size cap.

Every mission's generated assets (Wave 3: ``missions/<id>/{images,audio}/``) and every
ad-hoc gallery asset (Wave 2: ``images/``/``audio/`` from the manual Image/Voice tabs)
accumulate under the served assets root and are **never** otherwise removed. On the 16 GB
target Mac that grows without a ceiling. :func:`prune_assets` is the bounded-cache cap: it
deletes the **oldest** asset units first until the root's total size is back under a byte
budget, exactly like an LRU disk cache.

It is deliberately stdlib-only, best-effort, and safe:

  * it only ever walks and deletes *inside* the given assets root, by an allow-list of the
    two asset subtrees (``missions/`` and the ``images/``/``audio/`` gallery) — the transient
    ``uploads/`` subtree (``/api/stt`` unlinks its own uploads) is simply never visited;
  * it never follows symlinks — sizes are read with ``follow_symlinks=False`` and
    ``rglob`` does not descend into directory symlinks — so a stray link can neither inflate
    the total nor be deleted through;
  * a unit modified within ``min_age_seconds`` of now is **protected** (still counted toward
    the total, never evicted), so an asset a render just wrote or a gallery image a user just
    generated can't be deleted out from under an in-flight mission / an open tab;
  * it never raises — a missing root, a raced deletion, or an unreadable file is swallowed —
    and a delete that *fails* is not counted as freed, so the caller's reported total is honest
    and the loop keeps trying older units rather than stopping over budget.

The tradeoff (accepted for a local single-user tool): pruning an old mission's dir breaks that
mission's live ``/media/...`` gallery links, and a *re-export* of that mission to PDF loses its
images (the exporter reads them from disk at export time, dropping a missing embed to its
caption). A PDF exported *before* the prune is self-contained and unaffected.
"""

from __future__ import annotations

import os
import shutil
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

# The two ad-hoc gallery subdirs whose *individual files* are prunable units (Wave 2 manual
# Image/Voice tabs). Mission asset dirs live under ``missions/`` and are pruned whole. Only
# these subtrees are ever walked — an allow-list, so ``uploads/`` (and anything else) is left
# untouched without needing an explicit skip.
_GALLERY_DIRS = ("images", "audio")
_MISSIONS_DIR = "missions"

# Default recency grace: a unit touched within this many seconds of now is never evicted. Long
# enough to cover a mission still in flight (it already wrote its assets but hasn't finished) and
# a gallery image a user just generated and is still viewing.
DEFAULT_RECENT_GRACE_SECONDS = 300.0


@dataclass(frozen=True)
class _Unit:
    """One asset unit: a whole ``missions/<id>/`` dir, or a single ad-hoc gallery file.
    ``size`` is its total bytes; ``mtime`` is its age key (newest mtime within, so a mission
    dir touched by a recent render sorts as recent — LRU by last use, intentional). ``kept``
    marks a unit that counts toward the total but must never be evicted (the just-rendered
    mission named in ``keep``)."""
    path: Path
    size: int
    mtime: float
    kept: bool = False


@dataclass(frozen=True)
class PruneResult:
    """What a prune did — for the caller to log. ``removed`` is the unit paths actually
    deleted, ``bytes_freed`` their total size, ``total_before``/``total_after`` the root's
    size around the prune."""
    removed: "list[Path]"
    bytes_freed: int
    total_before: int
    total_after: int


def _dir_size_and_mtime(path: Path) -> "tuple[int, float]":
    """Recursive byte total and newest mtime under ``path`` — regular files only, never
    following a symlink (so a link can't inflate the size with its target). A vanished or
    unreadable entry contributes 0 rather than aborting the walk."""
    total = 0
    try:
        newest = path.stat().st_mtime
    except OSError:
        newest = 0.0
    for child in path.rglob("*"):  # rglob does not descend into directory symlinks
        try:
            st = os.lstat(child)  # lstat: never follows a symlink (a link counts as itself)
        except OSError:
            continue  # raced deletion / broken link — skip, don't abort the whole walk
        if stat.S_ISREG(st.st_mode):
            total += st.st_size
            if st.st_mtime > newest:
                newest = st.st_mtime
    return total, newest


def _iter_units(assets_root: Path, keep: "frozenset[str]") -> "Iterable[_Unit]":
    """Yield every asset unit under ``assets_root``: each ``missions/<id>/`` dir as one unit
    (flagged ``kept`` when its id is in ``keep`` — it still counts toward the total, but won't
    be evicted), plus each individual regular file under the ad-hoc gallery dirs. Only these
    subtrees are visited (``uploads/`` is never walked); silent on a missing/!dir root."""
    missions = assets_root / _MISSIONS_DIR
    if missions.is_dir():
        for child in missions.iterdir():
            if not child.is_dir():
                continue
            size, mtime = _dir_size_and_mtime(child)
            yield _Unit(child, size, mtime, kept=child.name in keep)
    for sub in _GALLERY_DIRS:
        gallery = assets_root / sub
        if not gallery.is_dir():
            continue
        for child in gallery.iterdir():
            try:
                st = os.lstat(child)  # lstat: a symlinked gallery entry is never followed
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                yield _Unit(child, st.st_size, st.st_mtime)


def _remove(path: Path) -> bool:
    """Delete a unit (a dir tree or a single file). Returns True on success, False if the
    delete failed (a locked/permission-denied file, a partial rmtree) — the caller then does
    *not* count it as freed. An already-gone file counts as success (it occupies nothing)."""
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def prune_assets(
    assets_root: "str | Path",
    *,
    budget_bytes: int,
    keep: "Iterable[str]" = (),
    min_age_seconds: float = 0.0,
    now: "Optional[float]" = None,
) -> PruneResult:
    """Delete oldest asset units under ``assets_root`` until its total size is ≤ ``budget_bytes``.

    ``keep`` names ``missions/<id>`` ids that must never be pruned (the just-rendered mission).
    ``min_age_seconds`` protects any unit modified within that window of ``now`` (default
    ``time.time()``) — an in-flight mission's or a just-generated gallery asset's files — so
    a live asset is never evicted out from under its writer/viewer. A non-positive
    ``budget_bytes`` disables the cap (a no-op, never a wipe) — a guard against a misconfigured
    0/negative budget deleting everything. Never raises: a missing root, a raced deletion, or an
    unreadable file is swallowed, so a caller on the mission path can invoke it best-effort.
    """
    root = Path(assets_root)
    keep_set = frozenset(keep)
    if budget_bytes <= 0 or not root.is_dir():
        return PruneResult([], 0, 0, 0)

    units = list(_iter_units(root, keep_set))
    # ``total`` is the whole tree (kept + recent units included — they occupy real disk). A unit
    # is evictable only if it is neither kept nor recently touched; evict those oldest-first.
    # If the protected units alone still exceed the budget, we evict every evictable unit and
    # stop as far under budget as we can, never touching a protected one.
    cutoff = (time.time() if now is None else now) - max(0.0, min_age_seconds)
    total = sum(u.size for u in units)
    total_before = total
    evictable = sorted(
        (u for u in units if not u.kept and u.mtime <= cutoff), key=lambda u: u.mtime
    )
    removed: "list[Path]" = []
    for unit in evictable:
        if total <= budget_bytes:
            break
        if _remove(unit.path):  # only count a delete that actually happened
            removed.append(unit.path)
            total -= unit.size
    return PruneResult(removed, total_before - total, total_before, total)
