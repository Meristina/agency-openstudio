import { useState } from "react";
import { deleteDoc, deleteVisual } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import type { TaxonomyTree } from "../../types";
import { clearAssociation } from "./associationStore";
import AssociateControl from "./AssociateControl";
import type { ImportedMaterial } from "./importModel";

export default function MaterialCard({ item, taxonomy, onChanged }: { item: ImportedMaterial; taxonomy: TaxonomyTree; onChanged: () => void }) {
  const { t } = useI18n();
  const [message, setMessage] = useState("");
  const date = new Date(item.importedAt * 1000).toLocaleDateString();

  async function remove() {
    if (!window.confirm(t("import.remove.confirm"))) return;
    try {
      if (item.kind === "document") await deleteDoc(item.id);
      else await deleteVisual(item.id);
      clearAssociation(item.id);
      setMessage(t("import.remove.success"));
      onChanged();
    } catch {
      setMessage(t("import.remove.failed"));
    }
  }

  return (
    <article className="deliverable-card">
      <div className="deliverable-card-head">
        <div>
          <h4>{item.name}</h4>
          <p className="muted">{t(`import.kind.${item.kind}`)} · {t("import.card.importedOn", { date })}</p>
        </div>
        <span className="badge pending">{t(`import.kind.${item.kind}`)}</span>
      </div>
      <AssociateControl item={item} taxonomy={taxonomy} onAssociated={onChanged} />
      <button type="button" className="ghost" onClick={remove}>{t("import.card.remove")}</button>
      {message && <p className="muted" role="status">{message}</p>}
    </article>
  );
}
