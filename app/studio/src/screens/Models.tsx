import Capabilities from "../components/Capabilities";
import { useI18n } from "../i18n/I18nProvider";

export default function Models() {
  const { t } = useI18n();
  return (
    <section className="models-screen">
      <h1>{t("models.title")}</h1>
      <Capabilities />
    </section>
  );
}
