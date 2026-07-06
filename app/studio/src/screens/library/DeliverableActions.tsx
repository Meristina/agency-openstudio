import { useState } from "react";
import { fetchMissionPdf } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import type { Attribution, TaxonomyTree } from "../../types";
import type { Deliverable } from "./libraryModel";
import FilingControl from "./FilingControl";

export default function DeliverableActions({
  deliverable,
  taxonomy,
  onOpen,
  onFiled,
}: {
  deliverable: Deliverable;
  taxonomy: TaxonomyTree;
  onOpen: (id: string) => void;
  onFiled: (id: string, attribution: Attribution | null) => void;
}) {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);

  async function download() {
    setBusy(true);
    setError(false);
    // Bound the request so a wedged connection can't leave the button disabled
    // forever with no retry path; abort after 30s and surface the failure.
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 30_000);
    try {
      const blob = await fetchMissionPdf(deliverable.id, controller.signal);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${deliverable.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10_000);
    } catch {
      setError(true);
    } finally {
      clearTimeout(timer);
      setBusy(false);
    }
  }

  return (
    <div className="library-actions">
      <button type="button" onClick={() => onOpen(deliverable.id)}>{t("library.action.open")}</button>
      <button type="button" disabled={busy} onClick={download}>
        {busy ? t("library.pdf.inProgress") : t("library.action.downloadPdf")}
      </button>
      {error && <p className="error-text" role="alert">{t("library.pdf.failed")} {t("library.pdf.hint")}</p>}
      <FilingControl deliverable={deliverable} taxonomy={taxonomy} onFiled={onFiled} />
    </div>
  );
}
