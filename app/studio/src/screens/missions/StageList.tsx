import { useState } from "react";
import { useI18n } from "../../i18n/I18nProvider";
import type { CatalogKey } from "../../i18n/catalog";
import type { HumanStage } from "./humanStages";

export default function StageList({ stages }: { stages: HumanStage[] }) {
  const { t } = useI18n();
  const [open, setOpen] = useState<string | null>(null);
  return (
    <ol className="mission-stages">
      {stages.map((stage) => {
        const expanded = open === stage.key;
        const canExpand = stage.detail.length > 0 || (stage.iterations?.length ?? 0) > 0;
        return (
          <li key={stage.key} className={`mission-stage is-${stage.state}`}>
            <div className="mission-stage-row">
              <div>
                <h2>{t(stage.titleKey)}</h2>
                <p>{t(`missions.state.${stage.state}` as CatalogKey)}</p>
              </div>
              {canExpand && (
                <button type="button" aria-expanded={expanded} onClick={() => setOpen(expanded ? null : stage.key)}>
                  {expanded ? t("missions.detail.hide") : t("missions.detail.show")}
                </button>
              )}
            </div>
            {expanded && (
              <div className="mission-stage-detail">
                {stage.detail.map((detail, index) => (
                  <p key={`${detail.labelKey}-${index}`}>
                    <strong>{t(detail.labelKey, typeof detail.value === "number" ? { count: detail.value } : undefined)}</strong>
                    {typeof detail.value === "string" && detail.value.startsWith("missions.") ? `: ${t(detail.value as CatalogKey)}` : typeof detail.value === "string" ? `: ${detail.value}` : ""}
                    <span>{t(`missions.state.${detail.state}` as CatalogKey)}</span>
                  </p>
                ))}
                {stage.iterations?.map((iteration) => (
                  <p key={iteration.round}>
                    <strong>{t("missions.round", { count: iteration.round })}</strong>
                    <span>{iteration.verified ? t(iteration.verified.ok ? "missions.verify.ok" : "missions.verify.needsWork", { rate: iteration.verified.rate ?? 0 }) : t("missions.state.running")}</span>
                  </p>
                ))}
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );
}
