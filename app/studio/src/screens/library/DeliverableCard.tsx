import { useI18n } from "../../i18n/I18nProvider";
import type { Attribution, TaxonomyTree } from "../../types";
import type { Deliverable, DeliverablePreview as PreviewModel } from "./libraryModel";
import DeliverableActions from "./DeliverableActions";
import DeliverablePreview from "./DeliverablePreview";

export default function DeliverableCard({
  deliverable,
  taxonomy,
  preview,
  previewOpen,
  previewLoading,
  previewError,
  onPreview,
  onClosePreview,
  onOpen,
  onFiled,
}: {
  deliverable: Deliverable;
  taxonomy: TaxonomyTree;
  preview: PreviewModel | null;
  previewOpen: boolean;
  previewLoading: boolean;
  previewError: boolean;
  onPreview: (id: string) => void;
  onClosePreview: () => void;
  onOpen: (id: string) => void;
  onFiled: (id: string, attribution: Attribution | null) => void;
}) {
  const { t } = useI18n();
  const outcomeKey = deliverable.outcome === "successful" ? "library.outcome.successful" : "library.outcome.needsAttention";
  return (
    <article className="deliverable-card">
      <div className="deliverable-card-head">
        <h4>{deliverable.title || t("library.card.untitled")}</h4>
        <span className={`badge ${deliverable.outcome === "successful" ? "ok" : "warn"}`}>{t(outcomeKey)}</span>
      </div>
      {deliverable.producedAt && <p className="muted">{t("library.card.producedOn", { date: deliverable.producedAt })}</p>}
      <div className="row">
        <button type="button" onClick={() => onPreview(deliverable.id)}>{t("library.card.preview")}</button>
        <button type="button" onClick={() => onOpen(deliverable.id)}>{t("library.card.open")}</button>
      </div>
      {previewOpen && (
        <DeliverablePreview
          preview={preview}
          loading={previewLoading}
          error={previewError}
          onClose={onClosePreview}
        />
      )}
      <DeliverableActions deliverable={deliverable} taxonomy={taxonomy} onOpen={onOpen} onFiled={onFiled} />
    </article>
  );
}
