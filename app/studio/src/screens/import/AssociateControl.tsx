import { useState } from "react";
import { useI18n } from "../../i18n/I18nProvider";
import type { TaxonomyTree } from "../../types";
import { clearAssociation, setAssociation } from "./associationStore";
import type { ImportedMaterial } from "./importModel";

export default function AssociateControl({ item, taxonomy, onAssociated }: { item: ImportedMaterial; taxonomy: TaxonomyTree; onAssociated: () => void }) {
  const { t } = useI18n();
  const [client, setClient] = useState(item.association?.client ?? "");
  const [project, setProject] = useState(item.association?.project ?? "");
  const [campaign, setCampaign] = useState(item.association?.campaign ?? "");
  const [message, setMessage] = useState("");
  const selectedClient = taxonomy.clients.find((candidate) => candidate.name === client);
  const selectedProject = selectedClient?.projects.find((candidate) => candidate.name === project);

  function file() {
    if (!client) return;
    try {
      setAssociation(item.id, { client, ...(project ? { project } : {}), ...(campaign ? { campaign } : {}) });
      setMessage(t("import.associate.success"));
      onAssociated();
    } catch {
      setMessage(t("import.associate.failed"));
    }
  }

  function unassign() {
    try {
      clearAssociation(item.id);
      setClient("");
      setProject("");
      setCampaign("");
      setMessage(t("import.associate.success"));
      onAssociated();
    } catch {
      setMessage(t("import.associate.failed"));
    }
  }

  return (
    <div className="library-filing">
      <label>
        <span>{t("library.filing.pickClient")}</span>
        <select value={client} onChange={(event) => { setClient(event.target.value); setProject(""); setCampaign(""); }}>
          <option value="">{t("import.shelf.unassigned")}</option>
          {taxonomy.clients.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
        </select>
      </label>
      <label>
        <span>{t("library.filing.pickProject")}</span>
        <select value={project} disabled={!selectedClient} onChange={(event) => { setProject(event.target.value); setCampaign(""); }}>
          <option value=""></option>
          {selectedClient?.projects.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
        </select>
      </label>
      <label>
        <span>{t("library.filing.pickCampaign")}</span>
        <select value={campaign} disabled={!selectedProject} onChange={(event) => setCampaign(event.target.value)}>
          <option value=""></option>
          {selectedProject?.campaigns.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
        </select>
      </label>
      <button type="button" disabled={!client} onClick={file}>{item.association ? t("import.associate.move") : t("import.associate.attach")}</button>
      <button type="button" className="ghost" onClick={unassign}>{t("import.associate.unassign")}</button>
      {message && <p className="muted" role="status">{message}</p>}
    </div>
  );
}
