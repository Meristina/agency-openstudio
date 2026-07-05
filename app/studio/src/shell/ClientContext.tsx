import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { fetchTaxonomy } from "../api";
import { readPrefs, writePrefs, useI18n } from "../i18n/I18nProvider";
import type { TaxonomyTree } from "../types";

export interface ClientContextValue {
  client: string | null;
  project: string | null;
  campaign: string | null;
  taxonomy: TaxonomyTree;
  setClient: (value: string | null) => void;
  setProject: (value: string | null) => void;
  setCampaign: (value: string | null) => void;
  refresh: () => Promise<void>;
}

const Context = createContext<ClientContextValue | null>(null);
const emptyTaxonomy: TaxonomyTree = { clients: [] };

export function ClientContextProvider({ children }: { children: ReactNode }) {
  // One-shot lazy read: prefs only seed the initial selection.
  const [initialPrefs] = useState(() => readPrefs().clientContext ?? {});
  const [taxonomy, setTaxonomy] = useState<TaxonomyTree>(emptyTaxonomy);
  // Validation and persistence stay gated until the first successful taxonomy load:
  // running them against the initial empty taxonomy would wipe a valid persisted
  // selection (and save the nulls back) before fetchTaxonomy() resolves.
  const [loaded, setLoaded] = useState(false);
  const [client, setClientState] = useState<string | null>(initialPrefs.client ?? null);
  const [project, setProjectState] = useState<string | null>(initialPrefs.project ?? null);
  const [campaign, setCampaignState] = useState<string | null>(initialPrefs.campaign ?? null);

  const persist = useCallback((next: { client: string | null; project: string | null; campaign: string | null }) => {
    writePrefs({ clientContext: { client: next.client ?? undefined, project: next.project ?? undefined, campaign: next.campaign ?? undefined } });
  }, []);

  const refresh = useCallback(async () => {
    const next = await fetchTaxonomy();
    setTaxonomy(next);
    setLoaded(true);
  }, []);

  useEffect(() => {
    void refresh().catch(() => {});
  }, [refresh]);

  // Single place that drops whatever the loaded taxonomy no longer contains,
  // clearing the whole hierarchy below the first stale level.
  useEffect(() => {
    if (!loaded || !client) return;
    const selectedClient = taxonomy.clients.find((item) => item.name === client);
    if (!selectedClient) {
      setClientState(null);
      setProjectState(null);
      setCampaignState(null);
      return;
    }
    if (!project) return;
    const selectedProject = selectedClient.projects.find((item) => item.name === project);
    if (!selectedProject) {
      setProjectState(null);
      setCampaignState(null);
      return;
    }
    if (campaign && !selectedProject.campaigns.some((item) => item.name === campaign)) setCampaignState(null);
  }, [loaded, taxonomy, client, project, campaign]);

  useEffect(() => {
    if (!loaded) return;
    persist({ client, project, campaign });
  }, [loaded, client, project, campaign, persist]);

  const value = useMemo<ClientContextValue>(() => ({
    client,
    project,
    campaign,
    taxonomy,
    refresh,
    setClient(value) {
      setClientState(value);
      setProjectState(null);
      setCampaignState(null);
    },
    setProject(value) {
      setProjectState(value);
      setCampaignState(null);
    },
    setCampaign: setCampaignState,
  }), [client, project, campaign, taxonomy, refresh]);

  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useClientContext(): ClientContextValue {
  const value = useContext(Context);
  if (!value) throw new Error("useClientContext must be used inside ClientContextProvider");
  return value;
}

export function ClientContextSelector() {
  const { t } = useI18n();
  const ctx = useClientContext();
  const selectedClient = ctx.taxonomy.clients.find((item) => item.name === ctx.client);
  const selectedProject = selectedClient?.projects.find((item) => item.name === ctx.project);
  return (
    <section className="client-context" aria-label={t("context.label")}>
      <label>
        <span>{t("context.client")}</span>
        <select value={ctx.client ?? ""} onChange={(event) => ctx.setClient(event.target.value || null)}>
          <option value="">{ctx.taxonomy.clients.length ? t("context.none") : t("context.empty")}</option>
          {ctx.taxonomy.clients.map((client) => <option key={client.name} value={client.name}>{client.name}</option>)}
        </select>
      </label>
      <label>
        <span>{t("context.project")}</span>
        <select value={ctx.project ?? ""} disabled={!selectedClient} onChange={(event) => ctx.setProject(event.target.value || null)}>
          <option value="">{t("context.none")}</option>
          {selectedClient?.projects.map((project) => <option key={project.name} value={project.name}>{project.name}</option>)}
        </select>
      </label>
      <label>
        <span>{t("context.campaign")}</span>
        <select value={ctx.campaign ?? ""} disabled={!selectedProject} onChange={(event) => ctx.setCampaign(event.target.value || null)}>
          <option value="">{t("context.none")}</option>
          {selectedProject?.campaigns.map((campaign) => <option key={campaign.name} value={campaign.name}>{campaign.name}</option>)}
        </select>
      </label>
      <button className="ghost" onClick={() => ctx.setClient(null)}>{t("context.clear")}</button>
    </section>
  );
}
