import { useEffect, useMemo, useState } from "react";
import MissionDetail from "../../components/MissionDetail";
import { getMission, listMissions } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import { navigate } from "../../shell/router";
import { useClientContext } from "../../shell/ClientContext";
import type { Attribution, Dossier, MissionSummary } from "../../types";
import { ErrorState, Loading } from "../../ui/states";
import ShelfTree from "./ShelfTree";
import { buildLibraryModel, previewFromDossier } from "./libraryModel";
import type { DeliverablePreview, OutcomeFilter } from "./libraryModel";

function applyFiling(missions: MissionSummary[], filed: Record<string, Attribution | null>): MissionSummary[] {
  return missions.map((m) => {
    if (!(m.mission_id in filed)) return m;
    const next = filed[m.mission_id];
    return next ? { ...m, ...next, attribution: next } : { ...m, client: undefined, project: undefined, campaign: undefined, attribution: undefined };
  });
}

export default function DeliverableLibrary({ search = "" }: { search?: string }) {
  const { t } = useI18n();
  const context = useClientContext();
  const [missions, setMissions] = useState<MissionSummary[]>([]);
  const [filed, setFiled] = useState<Record<string, Attribution | null>>({});
  const [query, setQuery] = useState("");
  const [outcomeFilter, setOutcomeFilter] = useState<OutcomeFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [openDossier, setOpenDossier] = useState<Dossier | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [loadingPreviewId, setLoadingPreviewId] = useState<string | null>(null);
  const [previews, setPreviews] = useState<Record<string, DeliverablePreview>>({});
  const [previewErrors, setPreviewErrors] = useState<Set<string>>(() => new Set());
  const visibleMissions = useMemo(() => applyFiling(missions, filed), [missions, filed]);
  const model = useMemo(() => buildLibraryModel(
    visibleMissions,
    context.taxonomy,
    { client: context.client, project: context.project, campaign: context.campaign },
    { query, outcomeFilter },
  ), [visibleMissions, context.taxonomy, context.client, context.project, context.campaign, query, outcomeFilter]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(false);
    listMissions()
      .then((items) => { if (alive) setMissions(items); })
      .catch(() => { if (alive) setError(true); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  async function open(id: string) {
    setDetailLoading(true);
    try {
      setOpenDossier(await getMission(id));
    } finally {
      setDetailLoading(false);
    }
  }

  async function preview(id: string) {
    setPreviewId(id);
    if (previews[id]) return;
    setLoadingPreviewId(id);
    setPreviewErrors((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    try {
      const dossier = await getMission(id);
      setPreviews((prev) => ({ ...prev, [id]: previewFromDossier(dossier) }));
    } catch {
      setPreviewErrors((prev) => new Set(prev).add(id));
    } finally {
      setLoadingPreviewId(null);
    }
  }

  useEffect(() => {
    const id = new URLSearchParams(search).get("deliverable");
    if (!id || loading || !visibleMissions.some((m) => m.mission_id === id)) return;
    void open(id);
  }, [search, loading, visibleMissions]);

  function clearSearch() {
    setQuery("");
    setOutcomeFilter("all");
  }

  function onFiled(id: string, attribution: Attribution | null) {
    setFiled((prev) => ({ ...prev, [id]: attribution }));
  }

  if (loading) return <Loading />;
  if (error) return <ErrorState message={t("library.state.loadError")} />;

  return (
    <section className="library-screen">
      <header className="library-header">
        <div>
          <h1>{t("library.title")}</h1>
          <p>{t("library.subtitle")}</p>
        </div>
      </header>

      {model.isEmptyFirstRun ? (
        <section className="state-panel">
          <h1>{t("library.empty.firstRun.title")}</h1>
          <p>{t("library.empty.firstRun.body")}</p>
          <button type="button" onClick={() => navigate("#/brief")}>{t("library.empty.firstRun.cta")}</button>
        </section>
      ) : (
        <>
          <div className="library-controls">
            <input
              aria-label={t("library.search.placeholder")}
              placeholder={t("library.search.placeholder")}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <select aria-label={t("library.outcomeFilter.all")} value={outcomeFilter} onChange={(event) => setOutcomeFilter(event.target.value as OutcomeFilter)}>
              <option value="all">{t("library.outcomeFilter.all")}</option>
              <option value="successful">{t("library.outcomeFilter.successful")}</option>
              <option value="needs-attention">{t("library.outcomeFilter.needsAttention")}</option>
            </select>
            <button type="button" className="ghost" onClick={clearSearch}>{t("library.search.clear")}</button>
          </div>
          {model.isEmptyForContext && (
            <section className="state-panel">
              <h1>{t("library.empty.context.title")}</h1>
              <p>{t("library.empty.context.body")}</p>
            </section>
          )}
          {model.isEmptyForQuery && (
            <section className="state-panel">
              <h1>{t("library.search.noResults")}</h1>
              <button type="button" onClick={clearSearch}>{t("library.search.clear")}</button>
            </section>
          )}
          {model.total > 0 && (
            <ShelfTree
              model={model}
              taxonomy={context.taxonomy}
              previewId={previewId}
              previews={previews}
              loadingPreviewId={loadingPreviewId}
              previewErrors={previewErrors}
              onPreview={preview}
              onClosePreview={() => setPreviewId(null)}
              onOpen={open}
              onFiled={onFiled}
            />
          )}
          {(openDossier || detailLoading) && <MissionDetail dossier={openDossier} loading={detailLoading} />}
        </>
      )}
    </section>
  );
}
