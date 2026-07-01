"""Tests for the studio_assets/ retention cap (``agency_studio.retention``).

Fully offline: builds a fake assets tree under ``tmp_path``, stamps deterministic mtimes
with ``os.utime`` (so oldest-first ordering is exact, not wall-clock flaky), and asserts
what ``prune_assets`` evicts. No server, no models.
"""

import os
from pathlib import Path

from agency_studio import retention


def _write(path: Path, size: int, mtime: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\0" * size)
    os.utime(path, (mtime, mtime))


def _mission(root: Path, mission_id: str, *, images=(), audio=(), mtime: float) -> None:
    mdir = root / "missions" / mission_id
    for i, size in enumerate(images):
        _write(mdir / "images" / f"{i}.png", size, mtime)
    for i, size in enumerate(audio):
        _write(mdir / "audio" / f"{i}.wav", size, mtime)
    # Backdate the mission dir too: _dir_size_and_mtime seeds "newest" off the dir's own mtime,
    # which the OS set to now when the subdirs were created — else the grace window sees the
    # whole (file-backdated) mission as freshly touched and protects it.
    os.utime(mdir, (mtime, mtime))


def _total(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def test_under_budget_is_a_noop(tmp_path):
    _mission(tmp_path, "001", images=(100, 100), mtime=1000)
    result = retention.prune_assets(tmp_path, budget_bytes=10_000)
    assert result.removed == [] and result.bytes_freed == 0
    assert (tmp_path / "missions" / "001").is_dir()


def test_evicts_oldest_missions_until_under_budget(tmp_path):
    _mission(tmp_path, "old", images=(400,), mtime=1000)
    _mission(tmp_path, "mid", images=(400,), mtime=2000)
    _mission(tmp_path, "new", images=(400,), mtime=3000)  # total 1200
    result = retention.prune_assets(tmp_path, budget_bytes=900)  # must drop ~1 unit (oldest)
    assert not (tmp_path / "missions" / "old").exists(), "oldest mission evicted first"
    assert (tmp_path / "missions" / "mid").is_dir() and (tmp_path / "missions" / "new").is_dir()
    assert _total(tmp_path) <= 900
    assert result.total_before == 1200 and result.total_after == 800


def test_keep_protects_the_current_mission_even_if_oldest(tmp_path):
    _mission(tmp_path, "current", images=(500,), mtime=1000)  # oldest, but kept
    _mission(tmp_path, "other", images=(500,), mtime=2000)
    retention.prune_assets(tmp_path, budget_bytes=600, keep={"current"})
    assert (tmp_path / "missions" / "current").is_dir(), "kept mission never evicted"
    assert not (tmp_path / "missions" / "other").exists(), "a non-kept newer unit goes instead"


def test_uploads_subtree_is_never_touched(tmp_path):
    _write(tmp_path / "uploads" / "in.wav", 10_000, 500)  # transient STT input, huge + oldest
    _mission(tmp_path, "001", images=(400,), mtime=1000)
    retention.prune_assets(tmp_path, budget_bytes=1)  # budget forces eviction of everything prunable
    assert (tmp_path / "uploads" / "in.wav").is_file(), "uploads/ is excluded from retention"
    assert not (tmp_path / "missions" / "001").exists()


def test_prunes_adhoc_gallery_files_oldest_first(tmp_path):
    _write(tmp_path / "images" / "a.png", 400, 1000)  # oldest
    _write(tmp_path / "audio" / "b.wav", 400, 3000)   # newest
    retention.prune_assets(tmp_path, budget_bytes=500)
    assert not (tmp_path / "images" / "a.png").exists()
    assert (tmp_path / "audio" / "b.wav").is_file()


def test_missions_and_gallery_evicted_by_global_age_order(tmp_path):
    # A gallery file older than a mission dir is evicted before it — one global oldest-first order.
    _write(tmp_path / "images" / "old.png", 400, 1000)
    _mission(tmp_path, "newer", images=(400,), mtime=2000)
    retention.prune_assets(tmp_path, budget_bytes=500)
    assert not (tmp_path / "images" / "old.png").exists(), "older gallery file goes first"
    assert (tmp_path / "missions" / "newer").is_dir()


def test_nonpositive_budget_disables_cap_never_wipes(tmp_path):
    _mission(tmp_path, "001", images=(999,), mtime=1000)
    for budget in (0, -1):
        result = retention.prune_assets(tmp_path, budget_bytes=budget)
        assert result.removed == [], "a 0/negative budget disables the cap, not wipes everything"
        assert (tmp_path / "missions" / "001").is_dir()


def test_missing_root_is_a_silent_noop(tmp_path):
    result = retention.prune_assets(tmp_path / "does-not-exist", budget_bytes=1000)
    assert result.removed == [] and result.bytes_freed == 0


def test_result_reports_freed_bytes_and_totals(tmp_path):
    _mission(tmp_path, "old", images=(600,), mtime=1000)
    _mission(tmp_path, "new", images=(600,), mtime=2000)
    result = retention.prune_assets(tmp_path, budget_bytes=700)
    assert result.total_before == 1200
    assert result.bytes_freed == 600 and result.total_after == 600
    assert result.removed == [tmp_path / "missions" / "old"]


def test_recent_units_are_protected_by_the_grace_window(tmp_path):
    # A unit touched within min_age_seconds of now is never evicted, even when over budget —
    # this is what shields an in-flight mission / a just-generated gallery image from a
    # concurrent prune. Uses explicit now for determinism.
    _mission(tmp_path, "old", images=(600,), mtime=1000)       # ancient → evictable
    _mission(tmp_path, "fresh", images=(600,), mtime=10_000)   # within the grace of now
    result = retention.prune_assets(
        tmp_path, budget_bytes=100, min_age_seconds=100, now=10_050,  # cutoff = 9_950
    )
    assert not (tmp_path / "missions" / "old").exists(), "the ancient unit is evicted"
    assert (tmp_path / "missions" / "fresh").is_dir(), "a recent unit is protected even over budget"
    assert result.total_after == 600, "protected bytes remain; the cap is briefly exceeded, not violated"


def test_failed_delete_is_not_counted_as_freed(tmp_path, monkeypatch):
    # If a unit can't be deleted (locked file, partial rmtree), it must NOT be counted as freed;
    # the loop moves on to the next oldest instead of stopping while still over budget.
    _mission(tmp_path, "old", images=(600,), mtime=1000)
    _mission(tmp_path, "old2", images=(600,), mtime=1500)
    real_remove = retention._remove

    def fake_remove(path):
        return False if path.name == "old" else real_remove(path)  # 'old' is undeletable

    monkeypatch.setattr(retention, "_remove", fake_remove)
    result = retention.prune_assets(tmp_path, budget_bytes=700)  # total 1200 → must free ~600
    assert (tmp_path / "missions" / "old").is_dir(), "the undeletable unit is left in place"
    assert not (tmp_path / "missions" / "old2").exists(), "the loop moved on to the next oldest"
    assert result.removed == [tmp_path / "missions" / "old2"]
    assert result.bytes_freed == 600 and result.total_after == 600  # only the real delete counted
