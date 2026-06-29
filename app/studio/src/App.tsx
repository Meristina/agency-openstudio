// Scaffold Mission Console. Intentionally minimal: it proves all three API
// paths end-to-end (list missions, run a mission over SSE with a live event
// log, and the terminal done/error frame). The full timeline + Markdown dossier
// render lands in the next Wave 1 step — this is the wiring checkpoint.

import { useCallback, useEffect, useRef, useState } from "react";
import { listMissions, runMission } from "./api";
import type { MissionEvent, MissionSummary } from "./types";

function summarize(e: MissionEvent): string {
  switch (e.phase) {
    case "route":
      return `route → ${e.route.join(" · ")}`;
    case "dept":
      return `dept ${e.dept} — ${e.status}`;
    case "synth":
      return `synth #${e.iteration} — ${e.status}`;
    case "inspect":
      return e.verdict
        ? `inspect #${e.iteration} — verdict ${e.verdict}`
        : `inspect #${e.iteration} — start`;
    case "done":
      return `done — ${e.verdict ?? "delivered"} (${e.mission_id ?? "?"})`;
    case "error":
      return `error — ${e.message}`;
  }
}

export default function App() {
  const [missions, setMissions] = useState<MissionSummary[]>([]);
  const [goal, setGoal] = useState("");
  const [events, setEvents] = useState<MissionEvent[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
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

  const onRun = useCallback(async () => {
    const trimmed = goal.trim();
    if (!trimmed || running) return;
    setRunning(true);
    setError(null);
    setEvents([]);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      await runMission(
        trimmed,
        (e) => setEvents((prev) => [...prev, e]),
        { signal: ctrl.signal },
      );
      await refreshMissions();
    } catch (e) {
      if (!ctrl.signal.aborted) {
        setError(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }, [goal, running, refreshMissions]);

  const onCancel = useCallback(() => abortRef.current?.abort(), []);

  return (
    <div className="app">
      <header className="topbar">
        <h1>Agency Studio</h1>
        <span className="tag">Mission Console · scaffold</span>
      </header>

      <main className="grid">
        <section className="panel">
          <h2>New mission</h2>
          <textarea
            className="goal"
            placeholder="Describe the mission goal…"
            value={goal}
            onChange={(ev) => setGoal(ev.target.value)}
            disabled={running}
            rows={4}
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
          <ol className="timeline">
            {events.length === 0 && <li className="muted">No events yet.</li>}
            {events.map((e, i) => (
              <li key={i} className={`ev ev-${e.phase}`}>
                {summarize(e)}
              </li>
            ))}
          </ol>
        </section>

        <aside className="panel">
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
                <code>{m.mission_id}</code>
                {m.goal ? <span className="goal-text"> — {m.goal}</span> : null}
              </li>
            ))}
          </ul>
        </aside>
      </main>
    </div>
  );
}
