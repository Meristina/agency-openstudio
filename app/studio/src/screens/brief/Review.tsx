import { useEffect, useState } from "react";
import { fetchCapabilities } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import type { CapabilityEntry } from "../../types";
import type { Answer, Brief, Question } from "./questionSets";
import { questionSets } from "./questionSets";

export default function Review({ brief, error, launching, readOnly, onEdit, onLaunch }: {
  brief: Brief;
  error?: string | null;
  launching?: boolean;
  readOnly?: boolean;
  onEdit?: (id: string) => void;
  onLaunch?: () => void;
}) {
  const { t } = useI18n();
  const [videoEntry, setVideoEntry] = useState<CapabilityEntry | null>(null);
  const [preflightError, setPreflightError] = useState("");
  const [ackPaid, setAckPaid] = useState(false);
  const questions = questionSets[brief.deliverableType].questions.filter(
    (question) => !["intent", "deliverableLanguage"].includes(question.id),
  );
  const needsVideo = brief.deliverableType === "video";
  const videoBlocked = needsVideo && (!videoEntry || videoEntry.availability !== "available");
  const videoPaid = needsVideo && videoEntry?.cost === "paid";

  useEffect(() => {
    if (!needsVideo) return;
    let alive = true;
    fetchCapabilities()
      .then((inventory) => {
        const family = inventory.families.find((candidate) => candidate.family === "video");
        const active = family?.entries.find((entry) => entry.id === family.active) ?? family?.entries[0] ?? null;
        if (alive) setVideoEntry(active);
      })
      .catch(() => { if (alive) setPreflightError(t("brief.capability.unavailable")); });
    return () => { alive = false; };
  }, [needsVideo, t]);

  function answerDisplay(question: Question, value: Answer): string {
    if (question.kind === "toggle") return t(value !== false ? "brief.review.on" : "brief.review.off");
    if (value && typeof value === "object" && "other" in value) return String(value.other);
    const id = typeof value === "string" ? value : value && typeof value === "object" && "id" in value ? String(value.id) : "";
    const choice = question.choices?.find((candidate) => candidate.id === id);
    return choice ? t(choice.labelKey) : String(value);
  }

  return (
    <section aria-labelledby="brief-review-title">
      <h1 id="brief-review-title">{t("brief.review")}</h1>
      <dl>
        <dt>{t("home.intentLabel")}</dt>
        <dd>{brief.intent}</dd>
        <dt>{t("brief.question.deliverableLanguage")}</dt>
        <dd>{brief.deliverableLanguage}</dd>
        <dt>{t("brief.review.sources")}</dt>
        <dd>{t("brief.review.sourcesValue")}</dd>
        {needsVideo && (
          <>
            <dt>{t("brief.capability.video")}</dt>
            <dd>{videoPaid ? t("brief.capability.videoPaid") : t("brief.capability.videoLocal")}</dd>
          </>
        )}
        {questions.map((question) => {
          const value = brief.answers[question.id];
          if (value === undefined || value === "") return null;
          return (
            <div key={question.id}>
              <dt>{t(question.labelKey)}</dt>
              <dd>{answerDisplay(question, value)}</dd>
              {!readOnly && onEdit && (
                <button type="button" onClick={() => onEdit(question.id)}>{t("brief.edit")}</button>
              )}
            </div>
          );
        })}
      </dl>
      {error && <p role="alert">{error}</p>}
      {(videoBlocked || preflightError) && (
        <p role="alert">
          {preflightError || videoEntry?.enablement || videoEntry?.reason || t("brief.capability.blocked")}{" "}
          <a href="#/models">{t("brief.capability.openModels")}</a>
        </p>
      )}
      {videoPaid && (
        <label>
          <input type="checkbox" checked={ackPaid} onChange={(event) => setAckPaid(event.target.checked)} />
          <span>{t("brief.capability.ackPaid")}</span>
        </label>
      )}
      {!readOnly && onLaunch && (
        <button
          type="button"
          disabled={launching || videoBlocked || (videoPaid && !ackPaid)}
          onClick={onLaunch}
        >{t("brief.launch")}</button>
      )}
    </section>
  );
}
