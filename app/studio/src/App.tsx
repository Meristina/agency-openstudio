// Wave 1 Mission Console: submit a goal → live SSE timeline → on completion,
// load and render the saved dossier. A history sidebar lists saved missions;
// clicking one loads its dossier into the same detail pane.

import { useCallback, useEffect, useRef, useState } from "react";
import { getMission, listMissions, runMission } from "./api";
import Timeline from "./components/Timeline";
import MissionDetail from "./components/MissionDetail";
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
  const abortRef = useRef<AbortController | null>(null);

  const refreshMissions = useCallback(async () => {
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
      if (!ctrl.signal.aborted) setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }, [goal, running, refreshMissions, openMission]);

  const onCancel = useCallback(() => abortRef.current?.abort(), []);

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
            disabled={running}
            rows={3}
          />
          <div className="row">
            <button onClick={onRun} disabled={running || !goal.trim()}>
              {running ? "Running…" : "Run mission"}
            </button>
            {running && (
              <button className="ghost" onClick={onCancel}>
                Cancel
              </button>
            )}
          </div>
          {error && <p className="error">{error}</p>}

          <h3>Live timeline</h3>
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
                  <code>{m.mission_id}</code>
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
