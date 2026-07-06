import AssetGallery from "../../components/AssetGallery";
import { useI18n } from "../../i18n/I18nProvider";
import { isSafeHttpUrl } from "../../types";
import type { DeliverablePreview as PreviewModel } from "./libraryModel";

function source(url: string) {
  if (!isSafeHttpUrl(url)) return url;
  return <a href={url} target="_blank" rel="noopener noreferrer">{url}</a>;
}

export default function DeliverablePreview({
  preview,
  loading,
  error,
  onClose,
}: {
  preview: PreviewModel | null;
  loading?: boolean;
  error?: boolean;
  onClose: () => void;
}) {
  const { t } = useI18n();
  return (
    <section className="library-preview" aria-label={t("library.preview.title")} aria-live="polite">
      <div className="row between">
        <h4>{t("library.preview.title")}</h4>
        <button type="button" className="ghost" onClick={onClose}>{t("library.preview.close")}</button>
      </div>
      {loading && <p className="muted">{t("library.preview.loading")}</p>}
      {error && <p className="error-text" role="alert">{t("library.preview.failed")}</p>}
      {preview && (
        <>
          <p>{preview.headline}</p>
          {preview.keySources.length > 0 && (
            <section>
              <h5>{t("library.preview.sources")}</h5>
              <ul>{preview.keySources.map((item, i) => <li key={`${item}-${i}`}>{source(item)}</li>)}</ul>
            </section>
          )}
          {preview.keyDecisions.length > 0 && (
            <section>
              <h5>{t("library.preview.decisions")}</h5>
              <ul>{preview.keyDecisions.map((item, i) => <li key={`${item}-${i}`}>{item}</li>)}</ul>
            </section>
          )}
          <AssetGallery items={preview.media} />
        </>
      )}
    </section>
  );
}
