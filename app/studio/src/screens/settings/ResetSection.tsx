import { useState } from "react";
import { defaultLocale, useI18n } from "../../i18n/I18nProvider";
import { useClientContext } from "../../shell/ClientContext";
import { clearLocalPreferences } from "./settingsModel";

export default function ResetSection() {
  const { t, setLocale } = useI18n();
  const ctx = useClientContext();
  const [confirming, setConfirming] = useState(false);
  const [done, setDone] = useState(false);

  const reset = () => {
    clearLocalPreferences(window.localStorage);
    // Also return the live app to defaults so the reset is visible without a reload:
    // language and default context both revert in-session (setClient(null) cascades).
    setLocale(defaultLocale());
    ctx.setClient(null);
    setConfirming(false);
    setDone(true);
  };

  return (
    <section aria-labelledby="settings-reset">
      <h2 id="settings-reset">{t("settings.section.reset")}</h2>
      <h3>{t("settings.reset.title")}</h3>
      <p>{t("settings.reset.body")}</p>
      {confirming ? (
        <div className="actions">
          <button onClick={reset}>{t("settings.reset.confirm")}</button>
          <button className="ghost" onClick={() => setConfirming(false)}>{t("settings.reset.cancel")}</button>
        </div>
      ) : (
        <button onClick={() => setConfirming(true)}>{t("settings.reset.confirm")}</button>
      )}
      {done && <p role="status">{t("settings.reset.done")}</p>}
    </section>
  );
}
