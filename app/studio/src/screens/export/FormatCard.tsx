import { useI18n } from "../../i18n/I18nProvider";
import type { FormatView } from "./exportModel";

export default function FormatCard({
  format,
  busy,
  message,
  onProduce,
}: {
  format: FormatView;
  busy: boolean;
  message: string | null;
  onProduce: () => void;
}) {
  const { t } = useI18n();
  const disabled = busy || format.state !== "available";
  const unavailable = format.state === "unavailable-here"
    ? t("export.capabilityAbsent")
    : format.state === "no-media-to-pack"
      ? t("export.noMedia")
      : null;
  const name = t(format.nameKey);
  return (
    <article className="deliverable-card">
      <div className="deliverable-card-head">
        <h4>{name}</h4>
      </div>
      <p>{t(format.contentsKey)}</p>
      {unavailable && <p className="muted">{unavailable}</p>}
      {message && message !== unavailable && <p className={message === t("export.failed") ? "error-text" : "muted"} role={message === t("export.failed") ? "alert" : "status"}>{message}</p>}
      <button type="button" disabled={disabled} onClick={onProduce} aria-label={`${t("export.produce")} ${name}`}>
        {busy ? t("export.progress") : t("export.produce")}
      </button>
    </article>
  );
}
