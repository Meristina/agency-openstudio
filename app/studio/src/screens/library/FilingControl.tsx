import { useMemo, useState } from "react";
import { assignMission } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import type { Attribution, TaxonomyTree } from "../../types";
import type { Deliverable } from "./libraryModel";

export default function FilingControl({
  deliverable,
  taxonomy,
  onFiled,
}: {
  deliverable: Deliverable;
  taxonomy: TaxonomyTree;
  onFiled: (id: string, attribution: Attribution | null) => void;
}) {
  const { t } = useI18n();
  const [client, setClient] = useState(deliverable.placement.client ?? "");
  const [project, setProject] = useState(deliverable.placement.project ?? "");
  const [campaign, setCampaign] = useState(deliverable.placement.campaign ?? "");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const selectedClient = taxonomy.clients.find((item) => item.name === client);
  const selectedProject = selectedClient?.projects.find((item) => item.name === project);
  const canFile = !!client;
  const actionLabel = deliverable.placement.kind === "unassigned" ? t("library.filing.attach") : t("library.filing.move");
  const fields = useMemo(() => ({
    client,
    project: project || undefined,
    campaign: campaign || undefined,
  }), [client, project, campaign]);

  async function file() {
    if (!canFile) return;
    setBusy(true);
    setMessage(null);
    try {
      const next = await assignMission(deliverable.id, fields);
      onFiled(deliverable.id, next);
      setMessage(t("library.filing.success"));
    } catch {
      setMessage(t("library.filing.failed"));
    } finally {
      setBusy(false);
    }
  }

  async function unassign() {
    setBusy(true);
    setMessage(null);
    try {
      await assignMission(deliverable.id, { clear: true });
      onFiled(deliverable.id, null);
      setClient("");
      setProject("");
      setCampaign("");
      setMessage(t("library.filing.success"));
    } catch {
      setMessage(t("library.filing.failed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="library-filing">
      <label>
        <span>{t("library.filing.pickClient")}</span>
        <select value={client} onChange={(event) => { setClient(event.target.value); setProject(""); setCampaign(""); }}>
          <option value="">{t("library.shelf.unassigned")}</option>
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
      <button type="button" disabled={busy || !canFile} onClick={file}>{actionLabel}</button>
      <button type="button" className="ghost" disabled={busy} onClick={unassign}>{t("library.filing.unassign")}</button>
      {message && <p className="muted" role="status">{message}</p>}
    </div>
  );
}
