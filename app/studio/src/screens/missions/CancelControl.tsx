import { useState } from "react";
import { useI18n } from "../../i18n/I18nProvider";

export default function CancelControl({ status, onCancel }: { status: string; onCancel: () => Promise<unknown> }) {
  const { t } = useI18n();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  if (!["launching", "running"].includes(status)) return null;
  async function confirm() {
    if (busy) return;
    setBusy(true);
    await onCancel();
  }
  return (
    <div className="mission-stop">
      <button type="button" disabled={busy} onClick={() => setConfirming(true)}>{t("missions.stop.button")}</button>
      {confirming && (
        <div role="dialog" aria-modal="true" aria-labelledby="mission-stop-title" className="mission-dialog">
          <h2 id="mission-stop-title">{t("missions.stop.title")}</h2>
          <p>{t("missions.stop.body")}</p>
          <button type="button" disabled={busy} onClick={confirm}>{t("missions.stop.confirm")}</button>
          <button type="button" disabled={busy} onClick={() => setConfirming(false)}>{t("missions.stop.keep")}</button>
        </div>
      )}
    </div>
  );
}
