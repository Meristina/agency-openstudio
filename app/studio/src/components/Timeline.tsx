// Structured live timeline: renders the folded TimelineModel as ordered phase
// rows (route → departments → synthesis → inspect → terminal), each reflecting
// the agency-kit mission loop. The veto loop shows as multiple synth/inspect
// iterations — never collapsed, so a VETO→retry is visible (Constitution Art. IX).

import { useMemo } from "react";
import { groupTimeline } from "../timeline";
import { verdictClass } from "../types";
import type { MissionEvent } from "../types";

function Verdict({ verdict }: { verdict: string | null }) {
  if (!verdict) return <span className="badge pending">…</span>;
  return <span className={`badge ${verdictClass(verdict)}`}>{verdict}</span>;
}

export default function Timeline({ events }: { events: MissionEvent[] }) {
  // Re-fold only when the event list itself changes — not on the per-second
  // `elapsed`-tick re-renders App fires during a run.
  const model = useMemo(() => groupTimeline(events), [events]);
  const empty = !model.route && model.depts.length === 0 && !model.terminal;

  if (empty) return <p className="muted">No events yet — run a mission to see the live timeline.</p>;

  return (
    <div className="timeline-grid">
      {model.route && (
        <section className="phase">
          <h4>Route</h4>
          <div className="chips">
            {model.route.map((d) => (
              <span key={d} className="chip">{d}</span>
            ))}
          </div>
        </section>
      )}

      {model.depts.length > 0 && (
        <section className="phase">
          <h4>Departments</h4>
          <ul className="steps">
            {model.depts.map((d) => (
              <li key={d.dept} className={d.done ? "step done" : "step active"}>
                <span className="step-dot" /> {d.dept}
                <span className="step-state">{d.done ? "done" : "running…"}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {model.synth.length > 0 && (
        <section className="phase">
          <h4>Synthesis</h4>
          <ul className="steps">
            {model.synth.map((s) => (
              <li key={s.iteration} className={s.done ? "step done" : "step active"}>
                <span className="step-dot" /> iteration {s.iteration}
                <span className="step-state">{s.done ? "done" : "running…"}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {model.inspect.length > 0 && (
        <section className="phase">
          <h4>Inspect</h4>
          <ul className="steps">
            {model.inspect.map((i) => (
              <li key={i.iteration} className="step">
                <span className="step-dot" /> iteration {i.iteration}
                <Verdict verdict={i.verdict} />
              </li>
            ))}
          </ul>
        </section>
      )}

      {model.terminal?.kind === "done" && (
        <section className="phase terminal">
          <h4>Done</h4>
          <p>
            verdict <Verdict verdict={model.terminal.verdict} />
            {model.terminal.missionId && <> · <code>{model.terminal.missionId}</code></>}
          </p>
          {model.terminal.residualRisk && (
            <p className="residual">residual risk: {model.terminal.residualRisk}</p>
          )}
        </section>
      )}

      {model.terminal?.kind === "error" && (
        <section className="phase terminal">
          <h4>Error</h4>
          <p className="error">{model.terminal.message}</p>
        </section>
      )}

      {model.terminal?.kind === "cancelled" && (
        <section className="phase terminal">
          <h4>Stopped</h4>
          <p className="muted">Mission cancelled — it was stopped before saving.</p>
        </section>
      )}
    </div>
  );
}
