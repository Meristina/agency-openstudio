import { useRef, useState } from "react";
import { ingestDoc, uploadVisual } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import { defaultOnAccept } from "./associationStore";
import { classifyBringInError, classifyFileKind, type BringInResult } from "./importModel";

export default function BringInPanel({ activeContext, onAccepted }: { activeContext: { client?: string | null; project?: string | null; campaign?: string | null }; onAccepted: () => void }) {
  const { t } = useI18n();
  const input = useRef<HTMLInputElement | null>(null);
  const [cloud, setCloud] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<BringInResult | null>(null);

  async function bring(files: FileList | File[]) {
    if (busy) return;   // ignore overlapping selections/drops so they can't race the shared result/busy state
    const list = Array.from(files);
    if (!list.length) return;
    setBusy(true);
    setResult(null);
    let accepted = false;
    let last: BringInResult | null = null;
    try {
      // Process every provided file (a multi-file drop must not silently discard the extras).
      for (const file of list) {
        const kind = classifyFileKind(file);
        if (kind === "unsupported") { last = classifyBringInError(null, kind); continue; }
        try {
          const meta = kind === "document" ? await ingestDoc(file) : await uploadVisual(file, { cloud });
          defaultOnAccept(meta.id, activeContext);
          last = { status: "accepted", kind, reason: null, item: null };
          accepted = true;
        } catch (error) {
          last = classifyBringInError(error, kind);
        }
      }
    } finally {
      setResult(last);
      setBusy(false);
      if (input.current) input.current.value = "";
    }
    if (accepted) onAccepted();
  }

  return (
    <section className="state-panel import-bring-in" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); void bring(event.dataTransfer.files); }}>
      <h2>{t("import.bringIn.cta")}</h2>
      <p>{t("import.bringIn.docHint")} {t("import.bringIn.imageHint")}</p>
      <input ref={input} type="file" aria-label={t("import.bringIn.cta")} disabled={busy} onChange={(event) => { if (event.target.files) void bring(event.target.files); }} />
      <label className="toggle">
        <input type="checkbox" checked={cloud} onChange={(event) => setCloud(event.target.checked)} />
        <span>{t("import.cloud.optInLabel")}</span>
      </label>
      {cloud && <p className="notice">{t("import.cloud.offMachineWarning")}</p>}
      {busy && <p role="status">{t("import.bringIn.progress")}</p>}
      {result?.status === "accepted" && <p role="status">{t("import.bringIn.accepted")}</p>}
      {result?.status === "rejected" && <p role="alert">{t(result.reason)}</p>}
      {result?.status === "capabilityAbsent" && (
        <p role="alert"><strong>{t("import.capabilityAbsent.title")}</strong> {t("import.capabilityAbsent.body")} {t(result.reason)}</p>
      )}
    </section>
  );
}
