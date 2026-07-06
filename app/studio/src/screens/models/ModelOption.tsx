import { useI18n } from "../../i18n/I18nProvider";
import type { ModelOptionView } from "./capabilityModel";

const costKeys = {
  free_local: "models.cost.freeLocal",
  paid_cloud: "models.cost.paidCloud",
  free_or_paid: "models.cost.freeOrPaid",
} as const;

interface Props {
  option: ModelOptionView;
  name?: string;
  checked?: boolean;
  disabled?: boolean;
  selectable?: boolean;
  onChoose?: (id: string) => void;
}

export default function ModelOption({ option, name, checked = false, disabled = false, selectable = false, onChoose }: Props) {
  const { t } = useI18n();
  const detail = option.available
    ? option.keyConfigured === true ? t("models.key.configured") : null
    : option.envVarName ? t("models.key.setToEnable", { var: option.envVarName }) : option.enablementHintKey ? t(option.enablementHintKey) : null;
  const content = (
    <>
      <span className="model-option-main">
        <strong>{option.label}</strong>
        <span className="model-option-badges">
          <span className="badge">{t(costKeys[option.costKind])}</span>
          {option.isDefault && <span className="badge ok">{t("models.choose.default")}</span>}
          {!option.available && <span className="badge warn">{t("models.choose.unavailableOption")}</span>}
        </span>
      </span>
      {detail && <span className={option.available ? "hint" : "error"}>{detail}</span>}
    </>
  );

  if (!selectable || !option.available) return <div className={`model-option ${!option.available ? "is-disabled" : ""}`}>{content}</div>;

  return (
    <label className="model-option">
      <input
        type="radio"
        name={name}
        aria-label={option.label}
        checked={checked}
        disabled={disabled}
        onChange={() => onChoose?.(option.id)}
      />
      <span>{content}</span>
    </label>
  );
}
