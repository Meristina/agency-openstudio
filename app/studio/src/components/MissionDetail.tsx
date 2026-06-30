// Renders one saved/just-completed dossier: the structured header (goal, route,
// verdict, residual risk) plus the deliverable as Markdown. react-markdown is
// used WITHOUT rehype-raw, so agency-authored Markdown can never inject raw HTML.

import ReactMarkdown from "react-markdown";
import { lastVerdict, verdictClass } from "../types";
import type { Dossier } from "../types";

function List({ title, items }: { title: string; items?: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <section className="detail-list">
      <h4>{title}</h4>
      <ul>
        {items.map((it, i) => (
          <li key={i}>{it}</li>
        ))}
      </ul>
    </section>
  );
}

export default function MissionDetail({ dossier, loading }: { dossier: Dossier | null; loading?: boolean }) {
  if (loading) return <p className="muted">Loading dossier…</p>;
  if (!dossier) return <p className="muted">Select a mission, or run one, to see its dossier.</p>;

  const verdict = lastVerdict(dossier);
  return (
    <article className="detail">
      <header className="detail-head">
        <h3>{dossier.goal || "(untitled mission)"}</h3>
        <div className="detail-meta">
          {dossier.mission_id && <code>{dossier.mission_id}</code>}
          {verdict && <span className={`badge ${verdictClass(verdict)}`}>{verdict}</span>}
          {dossier.mission_id && (
            <a className="pdf-link" href={`/api/mission/${encodeURIComponent(dossier.mission_id)}/pdf`}>
              Export PDF
            </a>
          )}
        </div>
        {dossier.route && dossier.route.length > 0 && (
          <div className="chips">
            {dossier.route.map((d) => (
              <span key={d} className="chip">{d}</span>
            ))}
          </div>
        )}
      </header>

      {dossier.residual_risk && <p className="residual">Residual risk: {dossier.residual_risk}</p>}

      <section className="deliverable">
        <h4>Deliverable</h4>
        {dossier.delivered
          ? <div className="markdown"><ReactMarkdown>{dossier.delivered}</ReactMarkdown></div>
          : <p className="muted">No deliverable recorded.</p>}
      </section>

      <List title="Decisions" items={dossier.decisions} />
      <List title="Sources" items={dossier.sources} />
      <List title="Open to verify" items={dossier.open_to_verify} />
    </article>
  );
}
