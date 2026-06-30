// Wave 1 Mission Console: submit a goal → live SSE timeline → on completion,
// load and render the saved dossier. A history sidebar lists saved missions;
// clicking one loads its dossier into the same detail pane.

import { useCallback, useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { getMission, listMissions, runMission } from "./api";
import Timeline from "./components/Timeline";
import MissionDetail from "./components/MissionDetail";
import { summaryVerdictClass } from "./types";
import type { Dossier, MissionEvent, MissionSummary } from "./types";

export default function App() {
  const [missions, setMissions] = useState<MissionSummary[]>([]);
  const [goal, setGoal] = useState("");
  const [events, setEvents] = useState<MissionEvent[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<Dossier | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Live "working" feedback: tick an elapsed-seconds counter for the duration of
  // a run. The final value persists after completion (until the next run starts).
  useEffect(() => {
    if (!running) return;
    const start = Date.now();
    setElapsed(0);
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 1000);
    return () => clearInterval(id);
  }, [running]);

  const refreshMissions = useCallback(async () => {
    setNotice(null);  // a manual refresh supersedes the "stopped watching" notice
    try {
      setMissions(await listMissions());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void refreshMissions();
  }, [refreshMissions]);

  const openMission = useCallback(async (id: string) => {
    setSelectedId(id);
    setDetailLoading(true);
    setError(null);
    setNotice(null);  // opening a mission supersedes the "stopped watching" notice
    try {
      setDetail(await getMission(id));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const onRun = useCallback(async () => {
    const trimmed = goal.trim();
    if (!trimmed || running) return;
    setRunning(true);
    setError(null);
    setNotice(null);
    setEvents([]);
    setDetail(null);
    setSelectedId(null);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    let completedId: string | null = null;
    try {
      await runMission(
        trimmed,
        (e) => {
          setEvents((prev) => [...prev, e]);
          if (e.phase === "done" && e.mission_id) completedId = e.mission_id;
        },
        { signal: ctrl.signal },
      );
      await refreshMissions();
      if (completedId) await openMission(completedId);
    } catch (e) {
      // Aborting only stops the live stream — the mission keeps running on the
      // server and will be saved to History. Say so, rather than silently dropping.
      if (ctrl.signal.aborted) {
        setNotice("Stopped watching. The mission keeps running on the server and will appear in History when it finishes — use Refresh to check.");
      } else {
        setError(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }, [goal, running, refreshMissions, openMission]);

  // "Stop watching" aborts the live SSE stream only; the server-side mission
  // continues to completion and is persisted (see the catch handler above).
  const onStopWatching = useCallback(() => abortRef.current?.abort(), []);

  // ⌘/Ctrl+Enter submits from the goal box (a plain Enter stays a newline).
  const onGoalKeyDown = useCallback(
    (ev: KeyboardEvent<HTMLTextAreaElement>) => {
      if (ev.key === "Enter" && (ev.metaKey || ev.ctrlKey)) {
        ev.preventDefault();
        void onRun();
      }
    },
    [onRun],
  );

  return (
    <div className="app">
      <header className="topbar">
        <h1>Agency Studio</h1>
        <span className="tag">Mission Console</span>
      </header>

      <main className="layout">
        <section className="panel run-panel">
          <h2>New mission</h2>
          <textarea
            className="goal"
            placeholder="Describe the mission goal…"
            value={goal}
            onChange={(ev) => setGoal(ev.target.value)}
            onKeyDown={onGoalKeyDown}
            disabled={running}
            rows={3}
          />
          <div className="row">
            <button onClick={onRun} disabled={running || !goal.trim()}>
              {running ? "Running…" : "Run mission"}
            </button>
            {running && (
              <button className="ghost" onClick={onStopWatching}>
                Stop watching
              </button>
            )}
            <span className="hint">⌘/Ctrl+Enter to run</span>
          </div>
          {error && <p className="error">{error}</p>}
          {notice && <p className="notice">{notice}</p>}

          <div className="row between">
            <h3>Live timeline</h3>
            {(running || elapsed > 0) && (
              <span className={`elapsed ${running ? "live" : ""}`}>
                {running && <span className="pulse" />}
                {elapsed}s
              </span>
            )}
          </div>
          <Timeline events={events} />
        </section>

        <aside className="panel history-panel">
          <div className="row between">
            <h2>History</h2>
            <button className="ghost" onClick={() => void refreshMissions()}>
              Refresh
            </button>
          </div>
          <ul className="missions">
            {missions.length === 0 && <li className="muted">No saved missions.</li>}
            {missions.map((m) => (
              <li key={m.mission_id}>
                <button
                  className={`mission-item ${selectedId === m.mission_id ? "selected" : ""}`}
                  onClick={() => void openMission(m.mission_id)}
                >
                  <span className="mission-item-head">
                    <code>{m.mission_id}</code>
                    {m.verdict && (
                      <span className={`badge ${summaryVerdictClass(m.verdict)}`}>{m.verdict}</span>
                    )}
                  </span>
                  {m.goal ? <span className="goal-text">{m.goal}</span> : null}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="panel detail-panel">
          <MissionDetail dossier={detail} loading={detailLoading} />
        </section>
      </main>
    </div>
  );
}
