import { useEffect, useRef, useState } from "react";
import { useI18n } from "../../i18n/I18nProvider";

export default function CancelControl({ status, onCancel }: { status: string; onCancel: () => Promise<unknown> }) {
  const { t } = useI18n();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const confirmRef = useRef<HTMLButtonElement>(null);
  // Move focus into the dialog when it opens so keyboard users land on the
  // primary action rather than having to tab in from the page.
  useEffect(() => {
    if (confirming) confirmRef.current?.focus();
  }, [confirming]);
  if (!["launching", "running"].includes(status)) return null;
  async function confirm() {
    if (busy) return;
    setBusy(true);
    try {
      await onCancel();
    } catch {
      // Cancel failed — re-enable the control so the user can retry instead of
      // being locked out on a wedged/failed cancel.
      setBusy(false);
    }
  }
  return (
    <div className="mission-stop">
      <button type="button" disabled={busy} onClick={() => setConfirming(true)}>{t("missions.stop.button")}</button>
      {confirming && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="mission-stop-title"
          className="mission-dialog"
          onKeyDown={(event) => { if (event.key === "Escape" && !busy) setConfirming(false); }}
        >
          <h2 id="mission-stop-title">{t("missions.stop.title")}</h2>
          <p>{t("missions.stop.body")}</p>
          <button ref={confirmRef} type="button" disabled={busy} onClick={confirm}>{t("missions.stop.confirm")}</button>
          <button type="button" disabled={busy} onClick={() => setConfirming(false)}>{t("missions.stop.keep")}</button>
        </div>
      )}
    </div>
  );
}
