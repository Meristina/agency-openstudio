import { useI18n } from "../../i18n/I18nProvider";
import type { Locale } from "../../i18n/catalog";
import { ClientContextSelector } from "../../shell/ClientContext";

export default function PreferencesSection() {
  const { locale, setLocale, t } = useI18n();
  return (
    <section aria-labelledby="settings-preferences">
      <h2 id="settings-preferences">{t("settings.section.preferences")}</h2>
      <label>
        <span>{t("lang.label")}</span>
        <select value={locale} onChange={(event) => setLocale(event.target.value as Locale)}>
          <option value="en">{t("lang.en")}</option>
          <option value="fr">{t("lang.fr")}</option>
        </select>
      </label>
      {/* Same component as the top bar — one source of truth for the default context. */}
      <ClientContextSelector />
      <p className="muted">{t("settings.network.perMissionNote")}</p>
    </section>
  );
}
