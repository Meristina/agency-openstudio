import { useEffect, useState } from "react";
import { fetchTaxonomy } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import type { TaxonomyTree } from "../../types";
import type { Answer, ClientAttachment, Question } from "./questionSets";

type Props = {
  question: Question;
  value: Answer | undefined;
  error?: string;
  onAnswer: (value: Answer) => void;
  onDefault: () => void;
  onSkip: () => void;
};

export default function FlowStep({ question, value, error, onAnswer, onDefault, onSkip }: Props) {
  const { t } = useI18n();
  const [taxonomy, setTaxonomy] = useState<TaxonomyTree>({ clients: [] });
  const [taxonomyFailed, setTaxonomyFailed] = useState(false);
  const text = typeof value === "string" ? value : "";
  const otherText = value && typeof value === "object" && "other" in value ? String(value.other) : null;
  const selectedId = otherText !== null ? "other" : typeof value === "string" ? value : undefined;
  const attachment = value && typeof value === "object" && "client" in value ? value as ClientAttachment : null;
  const selectedClient = taxonomy.clients.find((client) => client.name === attachment?.client);
  const selectedProject = selectedClient?.projects.find((project) => project.name === attachment?.project);

  useEffect(() => {
    if (question.kind !== "attachment") return;
    let alive = true;
    fetchTaxonomy()
      .then((next) => { if (alive) setTaxonomy(next); })
      .catch(() => { if (alive) setTaxonomyFailed(true); });
    return () => { alive = false; };
  }, [question.kind]);

  function setAttachment(next: ClientAttachment) {
    onAnswer(next);
  }
  return (
    <div className="intent-form">
      {question.kind === "longText" && (
        <label>
          <span>{t(question.labelKey)}</span>
          <textarea value={text} onChange={(event) => onAnswer(event.target.value)} rows={4} />
        </label>
      )}
      {question.kind === "shortText" && (
        <label>
          <span>{t(question.labelKey)}</span>
          <input value={text} onChange={(event) => onAnswer(event.target.value)} />
        </label>
      )}
      {(question.kind === "choice" || question.kind === "language" || question.kind === "sector") && (
        <fieldset>
          <legend>{t(question.labelKey)}</legend>
          {question.choices?.map((choice) => (
            <label key={choice.id}>
              <input
                type="radio"
                name={question.id}
                checked={selectedId === choice.id}
                onChange={() => onAnswer(question.kind === "sector" && choice.id === "other" ? { other: "" } : choice.id)}
              />
              <span>{t(choice.labelKey)}</span>
            </label>
          ))}
          {question.kind === "sector" && otherText !== null && (
            <label>
              <span>{t("brief.question.sectorOther")}</span>
              <input value={otherText} onChange={(event) => onAnswer({ other: event.target.value })} />
            </label>
          )}
        </fieldset>
      )}
      {question.kind === "toggle" && (
        <label>
          <input
            type="checkbox"
            checked={typeof value === "boolean" ? value : question.defaultValue !== false}
            onChange={(event) => onAnswer(event.target.checked)}
          />
          <span>{t(question.labelKey)}</span>
        </label>
      )}
      {question.kind === "attachment" && (
        <fieldset>
          <legend>{t(question.labelKey)}</legend>
          {taxonomyFailed && <p>{t("brief.attachment.unavailable")}</p>}
          <label>
            <span>{t("context.client")}</span>
            <select value={selectedClient?.name ?? ""} onChange={(event) => setAttachment({ client: event.target.value, project: null, campaign: null })}>
              <option value="">{t("brief.attachment.unassigned")}</option>
              {taxonomy.clients.map((client) => <option key={client.name} value={client.name}>{client.name}</option>)}
            </select>
          </label>
          <label>
            <span>{t("context.project")}</span>
            <select value={selectedProject?.name ?? ""} disabled={!selectedClient} onChange={(event) => setAttachment({ client: selectedClient?.name ?? "", project: event.target.value || null, campaign: null })}>
              <option value="">{t("context.none")}</option>
              {selectedClient?.projects.map((project) => <option key={project.name} value={project.name}>{project.name}</option>)}
            </select>
          </label>
          <label>
            <span>{t("context.campaign")}</span>
            <select value={attachment?.campaign ?? ""} disabled={!selectedProject} onChange={(event) => setAttachment({ client: selectedClient?.name ?? "", project: selectedProject?.name ?? null, campaign: event.target.value || null })}>
              <option value="">{t("context.none")}</option>
              {selectedProject?.campaigns.map((campaign) => <option key={campaign.name} value={campaign.name}>{campaign.name}</option>)}
            </select>
          </label>
          <label>
            <span>{t("brief.attachment.newClient")}</span>
            <input value={selectedClient ? "" : attachment?.client ?? ""} onChange={(event) => setAttachment({ client: event.target.value, project: null, campaign: null })} />
          </label>
        </fieldset>
      )}
      {question.helpKey && <p>{t(question.helpKey)}</p>}
      {error && <p role="alert">{error}</p>}
      <div className="brief-step-actions">
        {question.defaultValue !== undefined && <button type="button" onClick={onDefault}>{t("brief.useDefault")}</button>}
        {question.skippable && <button type="button" onClick={onSkip}>{t("brief.skip")}</button>}
      </div>
    </div>
  );
}
