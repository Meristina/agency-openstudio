import { useMemo, useState } from "react";
import { fetchMissionBundle, fetchMissionMediaZip, fetchMissionPdf } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import { availableFormats, friendlyFilename, hasMedia } from "./exportModel";
import type { ExportDeliverable, ExportFormat, FormatView } from "./exportModel";
import { downloadBlob } from "./download";
import FormatCard from "./FormatCard";

export default function ExportPanel({ deliverable }: { deliverable: ExportDeliverable }) {
  const { t } = useI18n();
  // Per-format, not a single lock: two formats can download concurrently, so each must
  // track its own in-flight state — a shared value would let one finishing clear another's.
  const [busy, setBusy] = useState<Set<ExportFormat>>(new Set());
  // The document and full bundle both render server-side PDF: one 501 proves the
  // capability is absent for both, so track it once rather than per-format.
  const [pdfCapable, setPdfCapable] = useState(true);
  // The button gates on the persisted manifest, but the media may have been pruned from
  // disk since production. A media-pack 404 is that discovery: flip both the availability
  // and the reassurance note so the operator isn't sent to retry a permanent dead end.
  const [mediaGone, setMediaGone] = useState(false);
  const [messages, setMessages] = useState<Partial<Record<ExportFormat, string>>>({});
  const media = hasMedia(deliverable.dossier) && !mediaGone;
  const formats = useMemo(() => availableFormats({ hasMedia: media, pdfCapable }), [media, pdfCapable]);

  async function produce(format: FormatView) {
    if (format.state !== "available") return;
    setBusy((prev) => new Set(prev).add(format.id));
    setMessages((prev) => ({ ...prev, [format.id]: t("export.progress") }));
    const controller = new AbortController();
    // Generous ceiling: a media-heavy bundle can legitimately take a while to assemble
    // server-side; this only guards against a truly hung request, not a slow one.
    const timer = setTimeout(() => controller.abort(), 120_000);
    try {
      const blob = format.id === "document"
        ? await fetchMissionPdf(deliverable.id, controller.signal)
        : format.id === "mediaPack"
          ? await fetchMissionMediaZip(deliverable.id, controller.signal)
          : await fetchMissionBundle(deliverable.id, controller.signal);
      downloadBlob(blob, friendlyFilename(deliverable, format.id));
      setMessages((prev) => ({ ...prev, [format.id]: t("export.ready") }));
    } catch (err) {
      const text = err instanceof Error ? err.message : "";
      // errorText() formats the status as `<label> → <status>[: …]`, so match the status
      // in that position rather than a bare code that could appear anywhere in the body.
      if (/→\s*501\b/.test(text)) {
        setPdfCapable(false);
        setMessages((prev) => ({ ...prev, [format.id]: t("export.capabilityAbsent") }));
      } else if (format.id === "mediaPack" && /→\s*404\b/.test(text)) {
        setMediaGone(true);
        setMessages((prev) => ({ ...prev, [format.id]: "" }));
      } else {
        setMessages((prev) => ({ ...prev, [format.id]: t("export.failed") }));
      }
    } finally {
      clearTimeout(timer);
      setBusy((prev) => {
        const next = new Set(prev);
        next.delete(format.id);
        return next;
      });
    }
  }

  return (
    <section className="library-preview" aria-labelledby="export-panel-title">
      <h2 id="export-panel-title">{deliverable.title}</h2>
      <div className="deliverable-grid">
        {formats.map((format) => (
          <FormatCard key={format.id} format={format} busy={busy.has(format.id)} message={messages[format.id] || null} onProduce={() => void produce(format)} />
        ))}
      </div>
      {mediaGone && <p className="muted">{t("export.mediaPruned")}</p>}
    </section>
  );
}
