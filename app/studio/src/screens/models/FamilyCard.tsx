import { useState } from "react";
import { clearCapability, fetchCapabilities, selectCapability } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import type { CapabilityInventory, Family } from "../../types";
import type { CapabilityView } from "./capabilityModel";
import ModelOption from "./ModelOption";

interface Props {
  family: CapabilityView;
  busy?: boolean;
  onInventory: (inventory: CapabilityInventory) => void;
}

export default function FamilyCard({ family, busy = false, onInventory }: Props) {
  const { t } = useI18n();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const disabled = busy || saving;
  const active = family.options.find((option) => option.id === family.activeOptionId);
  const inForceLabel = active?.label ?? t("models.choose.builtinDefault");

  async function reread() {
    onInventory(await fetchCapabilities());
  }

  async function choose(id: string) {
    await save(async (familyId: Family) => {
      await selectCapability(familyId, id);
    });
  }

  async function revert() {
    await save(async (familyId: Family) => {
      await clearCapability(familyId);
    });
  }

  async function save(action: (familyId: Family) => Promise<void>) {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await action(family.family);
      await reread();
      // Under an env override the saved selection does not take effect — say so honestly.
      setMessage(
        family.isEnvOverridden && family.envVarName
          ? t("models.override.saved", { var: family.envVarName })
          : t("models.applies.nextProduction"),
      );
    } catch {
      setError(t("models.error"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="panel model-family" aria-labelledby={`models-${family.family}`}>
      <div className="row between">
        <div>
          <h2 id={`models-${family.family}`}>{t(family.nameKey)}</h2>
          <p className="muted">{t(family.descriptionKey)}</p>
        </div>
        <span className={family.status.kind === "not_available" ? "badge warn" : "badge ok"}>{t(family.status.labelKey)}</span>
      </div>
      {family.status.enablementHintKey && (
        <p className="hint">
          {family.status.envVarName ? t("models.key.setToEnable", { var: family.status.envVarName }) : t(family.status.enablementHintKey)}
        </p>
      )}
      {family.isEnvOverridden && family.envVarName && (
        <p className="hint">{t("models.override.note", { var: family.envVarName, model: inForceLabel })}</p>
      )}
      {family.isStale && <p className="hint">{t("models.stale.note", { model: inForceLabel })}</p>}
      {error && (
        <p className="error">
          {error} <button className="link-button" onClick={() => void reread()}>{t("models.error.retry")}</button>
        </p>
      )}
      {message && <p className="hint">{message}</p>}
      <div className="model-options">
        {family.displayKind === "chooser" && (
          <button
            type="button"
            className="model-option model-option-button"
            onClick={() => void revert()}
            disabled={disabled || family.selectedId == null}
          >
            <span>
              <strong>{t("models.choose.builtinDefault")}</strong>
              <span className="hint">{t("models.choose.revert")}</span>
            </span>
            {family.selectedId == null && <span className="badge ok">{t("models.choose.default")}</span>}
          </button>
        )}
        {family.options.map((option) => (
          <ModelOption
            key={option.id}
            option={option}
            name={`models-${family.family}`}
            checked={family.selectedId === option.id}
            disabled={disabled}
            selectable={family.displayKind === "chooser"}
            onChoose={(id) => void choose(id)}
          />
        ))}
      </div>
    </section>
  );
}
