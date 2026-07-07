import { useI18n } from "../../i18n/I18nProvider";
import { useClientContext } from "../../shell/ClientContext";
import { contextLabelView } from "./homeModel";

export default function ContextLabel() {
  const { t } = useI18n();
  const ctx = useClientContext();
  const view = contextLabelView(ctx);
  return (
    <section className="home-context" aria-label={t("context.label")}>
      <strong>{t("home.context.scopedTo")}</strong>
      <span>{view.text ?? t("home.context.none")}</span>
    </section>
  );
}
