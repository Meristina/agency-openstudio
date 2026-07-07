import { useEffect, useState } from "react";
import { fetchCapabilities, getSystemInfo } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import type { CapabilityInventory, SystemInfo } from "../../types";
import { deriveSystemView } from "./settingsModel";

const connectionKeys = {
  connected: "settings.system.connected",
  offline: "settings.system.offline",
  unknown: "settings.system.unknown",
} as const;

export default function SystemStatusSection() {
  const { t } = useI18n();
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [capabilities, setCapabilities] = useState<CapabilityInventory | null>(null);
  const [reachable, setReachable] = useState<boolean | null>(null);
  const view = deriveSystemView(info, capabilities, reachable);

  useEffect(() => {
    let cancelled = false;
    // /api/system is the reachability signal; capabilities is best-effort for the
    // model summary. Loading them independently means a capabilities failure never
    // masks a reachable server or the version it returned.
    getSystemInfo()
      .then((system) => { if (!cancelled) { setInfo(system); setReachable(true); } })
      .catch(() => { if (!cancelled) setReachable(false); });
    fetchCapabilities()
      .then((inventory) => { if (!cancelled) setCapabilities(inventory); })
      .catch(() => { /* model summary stays empty; connection state is unaffected */ });
    return () => { cancelled = true; };
  }, []);

  return (
    <section aria-labelledby="settings-system">
      <h2 id="settings-system">{t("settings.section.system")}</h2>
      <dl className="settings-facts">
        <dt>{t("settings.system.connection")}</dt>
        <dd>{t(connectionKeys[view.connection])}</dd>
        <dt>{t("settings.system.version")}</dt>
        <dd>{view.version ?? t("settings.system.unknown")}</dd>
        <dt>{t("settings.system.dataLocation")}</dt>
        <dd>{view.dataLocation ?? t("settings.system.unknown")}</dd>
      </dl>
      <p>{t("settings.system.localFirst")}</p>
      <h3>{t("settings.system.modelSummary")}</h3>
      {view.modelSummary.length ? (
        <ul>
          {view.modelSummary.map((item) => <li key={item.familyKey}>{t(item.familyKey)}: {item.choiceLabel}</li>)}
        </ul>
      ) : <p>{t("settings.system.unknown")}</p>}
      <a href="#/models">{t("settings.system.modelLink")}</a>
    </section>
  );
}
