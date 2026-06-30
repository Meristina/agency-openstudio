// Wave 1 Mission Console: submit a goal → live SSE timeline → on completion,
// load and render the saved dossier. A history sidebar lists saved missions;
// clicking one loads its dossier into the same detail pane.

import { useCallback, useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { cancelMission, getMission, getModelsStatus, listMissions, runMission } from "./api";
import Timeline from "./components/Timeline";
import MissionDetail from "./components/MissionDetail";
import ImagePanel from "./components/ImagePanel";
import VoicePanel from "./components/VoicePanel";
import Gallery from "./components/Gallery";
import { summaryVerdictClass } from "./types";
import type { Dossier, GalleryItem, MissionEvent, MissionSummary, ModelsStatus } from "./types";

type Tab = "mission" | "image" | "voice";

const TABS: Array<[Tab, string]> = [
  ["mission", "Mission"],
  ["image", "Image"],
  ["voice", "Voice"],
];

// Single source for the clean-cancel message (a `cancelled` terminal frame means the
// run was stopped before any persistence). The abort-fallback and raced-finish cases
// are genuinely different outcomes and carry their own honest wording.
const STOPPED_NOTICE = "Mission stopped — cancelled before it was saved.";

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
  const [tab, setTab] = useState<Tab>("mission");
  const [gallery, setGallery] = useState<GalleryItem[]>([]);
  const [modelStatus, setModelStatus] = useState<ModelsStatus | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const runIdRef = useRef<string | null>(null);
  const stopRequestedRef = useRef(false);

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
    setNotice(null);  // a manual refresh supersedes the "mission stopped" notice
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
    setNotice(null);  // opening a mission supersedes the "mission stopped" notice
    try {
      setDetail(await getMission(id));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  // Best-effort model-status chip (which local model is warm). Never surfaces an
  // error: the endpoint is informational and the studio works without it.
  const refreshModelStatus = useCallback(async () => {
    try {
      setModelStatus(await getModelsStatus());
    } catch {
      /* informational only — ignore */
    }
  }, []);

  useEffect(() => {
    void refreshModelStatus();
  }, [refreshModelStatus]);

  // A panel generated an asset: prepend it to the session gallery (newest first) and
  // refresh the warm-model chip (the generation just loaded/switched a model).
  const onGenerated = useCallback(
    (item: GalleryItem) => {
      setGallery((prev) => [item, ...prev]);
      void refreshModelStatus();
    },
    [refreshModelStatus],
  );

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
    runIdRef.current = null;
    stopRequestedRef.current = false;
    let completedId: string | null = null;
    let cancelled = false;
    try {
      await runMission(
        trimmed,
        (e) => {
          setEvents((prev) => [...prev, e]);
          if (e.phase === "run") runIdRef.current = e.run_id;
          if (e.phase === "done" && e.mission_id) completedId = e.mission_id;
          if (e.phase === "cancelled") cancelled = true;
        },
        { signal: ctrl.signal },
      );
      // The stream ended on a terminal frame. Always refresh first so a mission that
      // won the cancel race (finished before the stop landed) still shows in History.
      await refreshMissions();
      if (cancelled) {
        setNotice(STOPPED_NOTICE);
      } else if (completedId) {
        // A `done` despite a stop request means the run finished before the cancel
        // took effect — it was saved, so say so honestly rather than claim a stop.
        if (stopRequestedRef.current) {
          setNotice("Stop arrived too late — the mission finished and was saved.");
        }
        await openMission(completedId);
      }
    } catch (e) {
      if (ctrl.signal.aborted) {
        // Stop fell back to aborting the fetch (no run id yet, or the cancel call
        // failed). The server kills the in-flight subprocess before persistence, but
        // a run that had just finished may already be saved — refresh so History
        // reflects whichever actually happened, and don't over-promise "not saved".
        await refreshMissions();
        setNotice("Mission stopped. If it had already finished, it now appears in History.");
      } else {
        setError(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setRunning(false);
      abortRef.current = null;
      runIdRef.current = null;
      stopRequestedRef.current = false;
      // A mission run loads the LLM (which evicts any warm media model, per the
      // mutually-exclusive rule), so refresh the warm-model chip when it ends.
      void refreshModelStatus();
    }
  }, [goal, running, refreshMissions, openMission, refreshModelStatus]);

  // "Stop mission" cancels this exact run via the explicit endpoint (the server then
  // kills the in-flight engine subprocess before persistence). `cancelMission` is
  // time-bounded, so a wedged request can't strand the click; on no run id yet, a
  // failure, or a timeout it falls back to aborting the fetch — the server detects the
  // dropped connection and cancels the same way.
  const onStopMission = useCallback(async () => {
    stopRequestedRef.current = true;
    setNotice("Stopping…");
    const runId = runIdRef.current;
    if (runId && (await cancelMission(runId).catch(() => false))) return;
    abortRef.current?.abort();
  }, []);

  // Arrow-key roving across the tabs (the ARIA tab pattern: Left/Right move focus
  // + selection). Wraps around the ends.
  const onTabKeyDown = useCallback(
    (ev: KeyboardEvent<HTMLElement>) => {
      if (ev.key !== "ArrowRight" && ev.key !== "ArrowLeft") return;
      ev.preventDefault();
      setTab((current) => {
        const i = TABS.findIndex(([id]) => id === current);
        const next = ev.key === "ArrowRight" ? i + 1 : i - 1;
        return TABS[(next + TABS.length) % TABS.length][0];
      });
    },
    [],
  );

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

  const resident = modelStatus?.resident;

  return (
    <div className="app">
      <header className="topbar">
        <h1>Agency Studio</h1>
        <nav className="tabs" role="tablist" aria-label="Studio sections" onKeyDown={onTabKeyDown}>
          {TABS.map(([id, label]) => (
            <button
              key={id}
              id={`tab-${id}`}
              role="tab"
              aria-selected={tab === id}
              aria-controls={`panel-${id}`}
              tabIndex={tab === id ? 0 : -1}
              className={`tab ${tab === id ? "active" : ""}`}
              onClick={() => setTab(id)}
            >
              {label}
            </button>
          ))}
        </nav>
        {/* Global Stop: while a mission runs, keep cancellation reachable from every
            tab (the mission pane's own Stop is hidden when another tab is active). */}
        {running && tab !== "mission" && (
          <button className="ghost" onClick={onStopMission}>
            Stop mission ({elapsed}s)
          </button>
        )}
        <span className={`model-chip ${resident ? "warm" : ""}`} title="Local model currently loaded">
          {resident ? `${resident} warm` : "no model loaded"}
        </span>
      </header>

      {/* All three views stay mounted, toggled by `hidden`, so switching tabs keeps a
          running mission alive, preserves panel input, and lets an in-flight media
          request resolve onto a still-mounted panel. */}
      <main
        className="layout"
        id="panel-mission"
        role="tabpanel"
        aria-labelledby="tab-mission"
        hidden={tab !== "mission"}
      >
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
              <button className="ghost" onClick={onStopMission}>
                Stop mission
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

      <main
        className="studio-layout"
        id="panel-image"
        role="tabpanel"
        aria-labelledby="tab-image"
        hidden={tab !== "image"}
      >
        <ImagePanel onGenerated={onGenerated} />
        <section className="panel gallery-panel">
          <h2>Gallery</h2>
          <Gallery items={gallery.filter((g) => g.kind === "image")} />
        </section>
      </main>

      <main
        className="studio-layout"
        id="panel-voice"
        role="tabpanel"
        aria-labelledby="tab-voice"
        hidden={tab !== "voice"}
      >
        <VoicePanel onGenerated={onGenerated} />
        <section className="panel gallery-panel">
          <h2>Gallery</h2>
          <Gallery items={gallery.filter((g) => g.kind === "audio")} />
        </section>
      </main>
    </div>
  );
}
