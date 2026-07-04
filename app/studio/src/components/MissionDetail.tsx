// Renders one saved/just-completed dossier: the structured header (goal, route,
// verdict, residual risk) plus the deliverable as Markdown. react-markdown is
// used WITHOUT rehype-raw, so agency-authored Markdown can never inject raw HTML.

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { isSafeHttpUrl, lastVerdict, verdictClass } from "../types";
import type { Dossier } from "../types";
import type { ReactNode } from "react";
import AssetGallery from "./AssetGallery";
import { fetchMissionPdf } from "../api";

function List({
  title,
  items,
  renderItem,
}: {
  title: string;
  items?: string[];
  renderItem?: (item: string) => ReactNode;
}) {
  if (!items || items.length === 0) return null;
  return (
    <section className="detail-list">
      <h4>{title}</h4>
      <ul>
        {items.map((it, i) => (
          <li key={`${it}-${i}`}>{renderItem ? renderItem(it) : it}</li>
        ))}
      </ul>
    </section>
  );
}

/**
 * `_extract_sources` (cli_engine.py) populates `sources` with bare http(s) URLs,
 * so each renders as a real link — opened in a new tab and isolated with
 * `rel="noopener noreferrer"` (no opener access, no referrer leak), matching the
 * studio's security ethos. A non-URL string degrades to plain text.
 */
function sourceItem(url: string): ReactNode {
  if (!isSafeHttpUrl(url)) return url;
  return (
    <a className="source-link" href={url} target="_blank" rel="noopener noreferrer">
      {url}
    </a>
  );
}

function pct(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

export default function MissionDetail({ dossier, loading }: { dossier: Dossier | null; loading?: boolean }) {
  const [pdfBusy, setPdfBusy] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  // Export via fetch → blob download rather than an <a href> navigation: a failed export
  // (501 without the [pdf] extra, 404, 500) is shown inline instead of replacing the SPA
  // with raw JSON, and a running mission's SSE stream is never torn down by a page unload.
  async function exportPdf(missionId: string) {
    setPdfBusy(true);
    setPdfError(null);
    try {
      const blob = await fetchMissionPdf(missionId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${missionId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      // Defer the revoke: revoking in the same tick as click() can cancel the download before
      // the browser starts streaming it (Firefox/Safari).
      setTimeout(() => URL.revokeObjectURL(url), 10_000);
    } catch (e) {
      setPdfError(e instanceof Error ? e.message : "PDF export failed");
    } finally {
      setPdfBusy(false);
    }
  }

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
            <button
              type="button"
              className="pdf-link"
              disabled={pdfBusy}
              onClick={() => exportPdf(dossier.mission_id!)}
            >
              {pdfBusy ? "Exporting…" : "Export PDF"}
            </button>
          )}
        </div>
        {pdfError && <p className="error-text" role="alert">PDF export failed: {pdfError}</p>}
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

      <AssetGallery items={dossier.assets} />

      {dossier.verification?.final && (
        <section className="detail-list">
          <h4>Source verification</h4>
          <p>
            {/* final.resolve (the cycle that produced this rate) drives the copy —
                not the mission-level config — so the message describes what actually
                happened in the delivered cycle. */}
            {dossier.verification.final.rate === null
              ? `unverified — ${dossier.verification.final.resolve ? "network unavailable or no checkable sources" : "resolution not enabled"}`
              : `Verified-source rate: ${pct(dossier.verification.final.rate)}`}
          </p>
          {Object.keys(dossier.verification.final.per_dept).length > 0 && (
            <table>
              <thead>
                <tr><th>Department</th><th>Counted</th><th>Min</th><th>OK</th></tr>
              </thead>
              <tbody>
                {Object.entries(dossier.verification.final.per_dept).map(([dept, item]) => (
                  <tr key={dept}>
                    <td>{dept}</td>
                    <td>{item.counted}</td>
                    <td>{item.min}</td>
                    <td>{item.ok ? "yes" : "no"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {dossier.verification.final.sources.length > 0 && (
            <ul>
              {dossier.verification.final.sources.map((s) => (
                <li key={s.url}>
                  {sourceItem(s.url)} — {s.status}{s.detail ? ` (${s.detail})` : ""}
                </li>
              ))}
            </ul>
          )}
          {dossier.verification.final.missing.length > 0 && (
            <List title="Missing sources" items={dossier.verification.final.missing} />
          )}
          {dossier.verification.final.truncated > 0 && (
            <p>{dossier.verification.final.truncated} source{dossier.verification.final.truncated === 1 ? "" : "s"} not checked — cap reached</p>
          )}
        </section>
      )}

      <List title="Decisions" items={dossier.decisions} />
      <List title="Sources" items={dossier.sources} renderItem={sourceItem} />
      <List title="Open to verify" items={dossier.open_to_verify} />
    </article>
  );
}
