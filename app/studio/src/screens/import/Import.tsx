import { useCallback, useEffect, useMemo, useState } from "react";
import { listDocs, listVisual } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import { navigate } from "../../shell/router";
import { useClientContext } from "../../shell/ClientContext";
import type { DocMeta, VisualMeta } from "../../types";
import { Empty, ErrorState, Loading } from "../../ui/states";
import { getAssociations, pruneAssociations } from "./associationStore";
import BringInPanel from "./BringInPanel";
import MaterialShelf from "./MaterialShelf";
import { buildImportModel } from "./importModel";

export default function Import() {
  const { t } = useI18n();
  const context = useClientContext();
  const [docs, setDocs] = useState<DocMeta[]>([]);
  const [visuals, setVisuals] = useState<VisualMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [nextDocs, nextVisuals] = await Promise.all([listDocs(), listVisual()]);
      pruneAssociations([...nextDocs, ...nextVisuals].map((item) => item.id));
      setDocs(nextDocs);
      setVisuals(nextVisuals);
      setVersion((n) => n + 1);
    } catch {
      setError(t("import.state.loadError"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { void load(); }, [load]);

  const model = useMemo(() => buildImportModel(docs, visuals, getAssociations(), {
    client: context.client,
    project: context.project,
    campaign: context.campaign,
  }), [docs, visuals, context.client, context.project, context.campaign, version]);
  const allTotal = docs.length + visuals.length;

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} />;

  return (
    <section className="library-screen" aria-labelledby="import-title">
      <header className="library-header">
        <h1 id="import-title">{t("import.title")}</h1>
        <p>{t("import.subtitle")}</p>
      </header>
      <BringInPanel activeContext={context} onAccepted={load} />
      {allTotal > 0 && <button type="button" onClick={() => navigate("#/brief")}>{t("import.brief.startWithMaterial")}</button>}
      {allTotal === 0 ? (
        <section className="state-panel">
          <h2>{t("import.empty.firstRun.title")}</h2>
          <p>{t("import.empty.firstRun.body")}</p>
        </section>
      ) : model.total === 0 ? (
        <Empty />
      ) : (
        <MaterialShelf model={model} taxonomy={context.taxonomy} onChanged={load} />
      )}
    </section>
  );
}
