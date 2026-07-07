import PreferencesSection from "./PreferencesSection";
import ResetSection from "./ResetSection";
import SystemStatusSection from "./SystemStatusSection";
import { useI18n } from "../../i18n/I18nProvider";

export default function SettingsScreen() {
  const { t } = useI18n();
  return (
    <div className="screen settings-screen">
      <h1>{t("settings.title")}</h1>
      <PreferencesSection />
      <SystemStatusSection />
      <ResetSection />
    </div>
  );
}
