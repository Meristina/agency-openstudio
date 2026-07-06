import { useEffect, useMemo, useState } from "react";
import { getMission, listMissions } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import { navigate } from "../../shell/router";
import { useClientContext } from "../../shell/ClientContext";
import type { Dossier, MissionSummary } from "../../types";
import { ErrorState, Loading } from "../../ui/states";
import ExportPanel from "./ExportPanel";
import type { ExportDeliverable } from "./exportModel";

function titleOf(m: MissionSummary): string {
  return typeof m.goal === "string" && m.goal.trim() ? m.goal.trim() : "Untitled deliverable";
}

export default function Export() {
  const { t } = useI18n();
  const context = useClientContext();
  const [missions, setMissions] = useState<MissionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<ExportDeliverable | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(false);
    listMissions({ client: context.client ?? undefined, project: context.project ?? undefined, campaign: context.campaign ?? undefined })
      .then((items) => { if (alive) setMissions(items); })
      .catch(() => { if (alive) setError(true); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [context.client, context.project, context.campaign]);

  const finished = useMemo(() => missions.filter((m) => !!m.delivered), [missions]);

  async function choose(m: MissionSummary) {
    let dossier: Dossier | undefined;
    try {
      dossier = await getMission(m.mission_id);
    } catch {
      dossier = undefined;
    }
    setSelected({ id: m.mission_id, title: titleOf(m), dossier });
  }

  if (loading) return <Loading />;
  if (error) return <ErrorState message={t("export.connectionLost")} />;

  return (
    <section className="library-screen" aria-labelledby="export-title">
      <header className="library-header">
        <h1 id="export-title">{t("export.title")}</h1>
        <p>{t("export.subtitle")}</p>
      </header>
      {missions.length === 0 ? (
        <section className="state-panel">
          <h1>{t("export.empty.title")}</h1>
          <p>{t("export.empty.body")}</p>
          <button type="button" onClick={() => navigate("#/brief")}>{t("export.empty.cta")}</button>
        </section>
      ) : finished.length === 0 ? (
        <section className="state-panel">
          <h1>{t("export.empty.context.title")}</h1>
          <p>{t("export.onlyFinished")}</p>
        </section>
      ) : (
        <>
          <div className="deliverable-grid" role="list" aria-label={t("export.deliverables")}>
            {finished.map((m) => (
              <div key={m.mission_id} role="listitem">
                <button type="button" className="deliverable-card" onClick={() => void choose(m)}>
                  <strong>{titleOf(m)}</strong>
                </button>
              </div>
            ))}
          </div>
          {selected && <ExportPanel key={selected.id} deliverable={selected} />}
        </>
      )}
    </section>
  );
}
