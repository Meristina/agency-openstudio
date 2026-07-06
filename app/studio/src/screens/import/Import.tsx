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
  const [failed, setFailed] = useState(false);
  const [version, setVersion] = useState(0);

  // No `t` dependency: a language switch must not refetch/re-prune the list — the error is stored
  // as a flag and translated at render time instead.
  const load = useCallback(async () => {
    setLoading(true);
    setFailed(false);
    try {
      const [nextDocs, nextVisuals] = await Promise.all([listDocs(), listVisual()]);
      pruneAssociations([...nextDocs, ...nextVisuals].map((item) => item.id));
      setDocs(nextDocs);
      setVisuals(nextVisuals);
      setVersion((n) => n + 1);
    } catch {
      setFailed(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const model = useMemo(() => buildImportModel(docs, visuals, getAssociations(), {
    client: context.client,
    project: context.project,
    campaign: context.campaign,
  }), [docs, visuals, context.client, context.project, context.campaign, version]);
  const allTotal = docs.length + visuals.length;

  if (loading) return <Loading />;
  if (failed) return <ErrorState message={t("import.state.loadError")} />;

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
