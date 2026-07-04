"""Batch mission queue — `agency batch add / run / status / clear`.

Queue : ~/.agency/batch-queue.tsv  (id, goal, priority, status, notes)
State : ~/.agency/batch-state.tsv  (id, status, started_at, finished_at, last_verdict, retries, mission_id)

Design: sequential. Each goal runs through the local agent CLI engine
(`runner_bridge.run`); state is written per-job so `--retry-failed` can re-run
goals that errored.
"""

import csv
import sys
import time
from datetime import datetime
from pathlib import Path

from agency_kit.store import agency_dir as _agency_dir

_QUEUE_COLS = ["id", "goal", "priority", "status", "notes"]
_STATE_COLS = ["id", "status", "started_at", "finished_at", "last_verdict", "retries", "mission_id"]


def _queue_path() -> Path:
    return _agency_dir() / "batch-queue.tsv"


def _state_path() -> Path:
    return _agency_dir() / "batch-state.tsv"


def _acquire_lock() -> bool:
    """Atomically acquire the batch-state write lock (mkdir = O_CREAT|O_EXCL on POSIX)."""
    try:
        (_agency_dir() / ".batch-state.lock").mkdir(exist_ok=False)
        return True
    except FileExistsError:
        return False


def _release_lock() -> None:
    try:
        (_agency_dir() / ".batch-state.lock").rmdir()
    except Exception:
        pass


def _read_tsv(path: Path) -> list:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _write_tsv(path: Path, cols: list, rows: list) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def _write_state(state: dict) -> None:
    for _ in range(20):
        if _acquire_lock():
            try:
                _write_tsv(_state_path(), _STATE_COLS, list(state.values()))
            finally:
                _release_lock()
            return
        time.sleep(0.05)
    print("[batch] warning: could not acquire state lock — job state not written", file=sys.stderr)


def _next_id(rows: list) -> int:
    if not rows:
        return 1
    return max(int(r.get("id", 0) or 0) for r in rows) + 1


def add(goal: str, priority: int = 5, notes: str = "") -> int:
    """Append a goal to the batch queue."""
    rows = _read_tsv(_queue_path())
    new_id = _next_id(rows)
    rows.append({"id": new_id, "goal": goal, "priority": priority, "status": "pending", "notes": notes})
    rows.sort(key=lambda r: int(r.get("priority", 5) or 5))
    _write_tsv(_queue_path(), _QUEUE_COLS, rows)
    print(f"[batch] Added #{new_id}: {goal[:70]}")
    return 0


def status() -> int:
    """Print queue + state summary."""
    queue = _read_tsv(_queue_path())
    state = {r["id"]: r for r in _read_tsv(_state_path())}
    if not queue:
        print('Batch queue is empty.  Add a goal:  agency batch add "<your goal>"')
        return 0
    print(f"\n{'#':<4}  {'STATUS':<22}  {'VERDICT':<15}  GOAL")
    print("-" * 96)
    for q in queue:
        qid = str(q.get("id", ""))
        s = state.get(qid, {})
        st = s.get("status") or q.get("status", "pending")
        verdict = s.get("last_verdict") or "—"
        goal_str = (q.get("goal") or "")[:52]
        if len(q.get("goal", "")) > 52:
            goal_str += "…"
        print(f"{qid:<4}  {st:<22}  {verdict:<15}  {goal_str}")
    done = sum(1 for q in queue if state.get(str(q.get("id", "")), {}).get("status") == "done")
    print(f"\n{done}/{len(queue)} completed.")
    return 0


def run(retry_failed: bool = False, limit: int = 0, engine: str = "claude-code", escalation=None, verification=None) -> int:
    """Run pending goals sequentially through the engine, updating state after each."""
    # Pre-flight the engine ONCE: an unknown or unvalidated --engine is a permanent
    # configuration error, not a per-goal failure. Refusing up front leaves the whole
    # queue untouched (nothing flipped to 'failed', no retry counters burned) so a
    # corrected re-run still finds the goals pending.
    from .engines.cli_engine import ensure_production_engine, EngineNotValidated
    try:
        ensure_production_engine(engine)
    except (EngineNotValidated, ValueError) as exc:
        print(f"[batch] Refusing to run: {exc}")
        return 2

    queue = _read_tsv(_queue_path())
    state = {r["id"]: r for r in _read_tsv(_state_path())}

    targets = []
    for q in queue:
        qid = str(q.get("id", ""))
        current = state.get(qid, {}).get("status") or q.get("status", "pending")
        if current == "pending":
            targets.append(q)
        elif current == "failed" and retry_failed:
            targets.append(q)

    if not targets:
        print("[batch] Nothing to run. All goals are done or failed.")
        return 0
    if limit:
        targets = targets[:limit]

    print(f"[batch] {len(targets)} goal(s) to process via {engine}.")

    from . import runner_bridge

    ok = fail = 0
    for q in targets:
        qid = str(q["id"])
        goal = q["goal"]
        print(f"\n[batch] #{qid} — {goal[:70]}")

        s = state.get(qid) or {}
        s.update({
            "id": qid,
            "status": "running",
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "finished_at": "",
            "last_verdict": "",
            "retries": str(int(s.get("retries") or 0) + 1),
            "mission_id": s.get("mission_id", ""),
        })
        state[qid] = s
        _write_state(state)

        try:
            result = runner_bridge.run(goal, engine=engine, escalation=escalation, verification=verification)
        except Exception as exc:
            s["status"] = "failed"
            s["last_verdict"] = f"ERROR: {str(exc)[:80]}"
            s["finished_at"] = datetime.now().isoformat(timespec="seconds")
            state[qid] = s
            _write_state(state)
            print(f"  [batch] #{qid} FAILED — {exc}")
            fail += 1
            continue

        s["mission_id"] = result.path.name
        s["finished_at"] = datetime.now().isoformat(timespec="seconds")
        s["status"] = "done"
        # Record the real Inspector verdict (PASS / PASS-WITH-FIXES / VETO), not a
        # blanket 'DELIVERED' — a VETOed mission must not display as a clean success.
        s["last_verdict"] = runner_bridge._last_verdict(result.dossier)
        ok += 1
        state[qid] = s
        _write_state(state)
        print(f"  [batch] #{qid} done — {result.path} [{s['last_verdict']}]")

    print(f"\n[batch] {ok} done, {fail} failed.")
    return 0 if fail == 0 else 1


def clear(status_filter: str = "done") -> int:
    """Remove entries with a given status from the queue."""
    rows = _read_tsv(_queue_path())
    state = {r["id"]: r for r in _read_tsv(_state_path())}
    before = len(rows)
    kept = [
        r for r in rows
        if (state.get(str(r.get("id", "")), {}).get("status") or r.get("status")) != status_filter
    ]
    _write_tsv(_queue_path(), _QUEUE_COLS, kept)
    print(f"[batch] Removed {before - len(kept)} '{status_filter}' entries from queue.")
    return 0
