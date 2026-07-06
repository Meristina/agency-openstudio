import { useEffect, useState } from "react";
import { fetchCapabilities } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import type { CapabilityInventory } from "../../types";
import FamilyCard from "./FamilyCard";
import { toCapabilityViews } from "./capabilityModel";

export default function ModelsScreen() {
  const { t } = useI18n();
  const [inventory, setInventory] = useState<CapabilityInventory | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);

  async function load(refresh = false) {
    setBusy(true);
    setError(false);
    try {
      setInventory(await fetchCapabilities(refresh));
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void load();
    // load() is stable (module-local closure over setState setters); mount-once is intended.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section className="models-screen" aria-labelledby="models-title">
      <div className="row between models-head">
        <div>
          <h1 id="models-title">{t("models.title")}</h1>
          <p className="muted">{t("models.subtitle")}</p>
        </div>
        <button className="ghost" onClick={() => void load(true)} disabled={busy}>
          {busy ? t("models.rechecking") : t("models.recheck")}
        </button>
      </div>
      {error && (
        <section className="panel">
          <p className="error">{t("models.error")}</p>
          <button onClick={() => void load()}>{t("models.error.retry")}</button>
        </section>
      )}
      {!inventory && !error && <p className="muted">{t("state.loading")}</p>}
      {inventory && (
        <div className="model-family-grid">
          {toCapabilityViews(inventory).map((family) => (
            <FamilyCard key={family.family} family={family} busy={busy} onInventory={setInventory} />
          ))}
        </div>
      )}
    </section>
  );
}
