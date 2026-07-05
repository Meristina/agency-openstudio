import { useI18n } from "../i18n/I18nProvider";
import type { Locale } from "../i18n/catalog";

export default function LanguageSwitch() {
  const { locale, setLocale, t } = useI18n();
  return (
    <label className="language-switch">
      <span>{t("lang.label")}</span>
      <select aria-label={t("lang.label")} value={locale} onChange={(event) => setLocale(event.target.value as Locale)}>
        <option value="en">{t("lang.en")}</option>
        <option value="fr">{t("lang.fr")}</option>
      </select>
    </label>
  );
}
