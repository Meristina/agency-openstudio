import { useState } from "react";
import { summaryVerdictClass } from "../types";
import type { MissionSummary, TaxonomyTree } from "../types";

export default function TaxonomyBrowser({
  taxonomy,
  missions,
  selectedId,
  onFilter,
  onOpen,
  onClear,
  onAssign,
}: {
  taxonomy: TaxonomyTree;
  missions: MissionSummary[];
  selectedId: string | null;
  onFilter: (filters: { client?: string; project?: string; campaign?: string }) => void;
  onOpen: (id: string) => void;
  onClear: () => void;
  onAssign: (id: string, fields: { client?: string; project?: string; campaign?: string } | { clear: true }) => void;
}) {
  const [client, setClient] = useState("");
  const [project, setProject] = useState("");
  const [campaign, setCampaign] = useState("");
  const campaigns = taxonomy.clients.flatMap((c) =>
    c.projects.flatMap((p) => p.campaigns.map((k) => ({ client: c.name, project: p.name, campaign: k.name, missions: k.missions }))),
  );
  return (
    <div className="taxonomy-browser">
      <div className="taxonomy-tree" aria-label="Taxonomy groups">
        {taxonomy.clients.length === 0 && <p className="muted">No saved missions.</p>}
        {taxonomy.clients.map((client) => (
          <details key={client.name} open>
            <summary>
              <button className="link-button" onClick={() => onFilter({ client: client.name })}>{client.name}</button>
              <span className="muted">{client.missions}</span>
            </summary>
            {client.projects.map((project) => (
              <div className="taxonomy-project" key={project.name}>
                <button className="link-button" onClick={() => onFilter({ client: client.name, project: project.name })}>{project.name}</button>
                <span className="muted">{project.missions}</span>
                {project.campaigns.map((campaign) => (
                  <button
                    key={campaign.name}
                    className="taxonomy-campaign"
                    onClick={() => onFilter({ client: client.name, project: project.name, campaign: campaign.name })}
                  >
                    {campaign.name} <span>{campaign.missions}</span>
                  </button>
                ))}
              </div>
            ))}
          </details>
        ))}
        {campaigns.length > 0 && (
          <details>
            <summary>Campaigns</summary>
            {campaigns.map((c) => (
              <button key={`${c.client}/${c.project}/${c.campaign}`} className="taxonomy-campaign" onClick={() => onFilter(c)}>
                {c.campaign} <span>{c.missions}</span>
              </button>
            ))}
          </details>
        )}
      </div>
      <div className="row between">
        <h3>Filtered missions</h3>
        <button className="ghost" onClick={onClear}>All</button>
      </div>
      <ul className="missions">
        {missions.length === 0 && <li className="muted">No matching missions.</li>}
        {missions.map((m) => (
          <li key={m.mission_id}>
            <button className={`mission-item ${selectedId === m.mission_id ? "selected" : ""}`} onClick={() => onOpen(m.mission_id)}>
              <span className="mission-item-head">
                <code>{m.mission_id}</code>
                {m.verdict && <span className={`badge ${summaryVerdictClass(m.verdict)}`}>{m.verdict}</span>}
              </span>
              {m.goal ? <span className="goal-text">{m.goal}</span> : null}
            </button>
          </li>
        ))}
      </ul>
      {selectedId && (
        <div className="assign-box" aria-label="Assign mission">
          <input aria-label="Assign client" placeholder="Client" value={client} onChange={(ev) => setClient(ev.target.value)} />
          <input aria-label="Assign project" placeholder="Project" value={project} onChange={(ev) => setProject(ev.target.value)} />
          <input aria-label="Assign campaign" placeholder="Campaign" value={campaign} onChange={(ev) => setCampaign(ev.target.value)} />
          <button onClick={() => onAssign(selectedId, { client: client || undefined, project: project || undefined, campaign: campaign || undefined })}>Assign</button>
          <button className="ghost" onClick={() => onAssign(selectedId, { clear: true })}>Clear</button>
        </div>
      )}
    </div>
  );
}
