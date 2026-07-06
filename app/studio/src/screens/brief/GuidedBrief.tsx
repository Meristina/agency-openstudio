import { useEffect, useMemo, useState } from "react";
import { listDocs, listVisual } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import { useClientContext } from "../../shell/ClientContext";
import FlowStep from "./FlowStep";
import Review from "./Review";
import { discardBriefDraft, loadBriefDraft, saveBriefDraft } from "./briefDraft";
import { composeMission } from "./composeMission";
import { missionSession } from "../session/missionSession";
import { questionSets, type Answer, type Brief, type DeliverableType, type Question } from "./questionSets";

type GuidedBriefState = "resumePrompt" | "flow" | "review" | "launching" | "launched" | "failed";

// Generous cap on free-text answers (spec edge case: over-limit input is
// flagged in plain language, never silently truncated).
const ANSWER_LIMIT = 4000;

function initialIntent(search: string): string {
  return (new URLSearchParams(search).get("intent") ?? "").trim();
}

export default function GuidedBrief({ search = "" }: { search?: string }) {
  const { locale, t } = useI18n();
  const clientContext = useClientContext();
  const seededIntent = useMemo(() => initialIntent(search), [search]);
  const [draft, setDraft] = useState(() => loadBriefDraft());
  const [answers, setAnswers] = useState<Record<string, Answer>>({
    intent: seededIntent,
    deliverableType: "research",
    deliverableLanguage: locale,
  });
  const [useImportedMaterial, setUseImportedMaterialState] = useState(draft?.useImportedMaterial ?? false);
  const [importedPresence, setImportedPresence] = useState({ documents: false, images: false });
  const [stepIndex, setStepIndex] = useState(0);
  const [state, setState] = useState<GuidedBriefState>(draft ? "resumePrompt" : "flow");
  const [error, setError] = useState("");
  // Only a brief the operator actually progressed is worth persisting: saving the
  // untouched seeded state would turn every visit into a phantom resume prompt
  // and make "discard" immediately recreate what it just removed (FR-021).
  const [dirty, setDirty] = useState(false);
  const [session, setSession] = useState(missionSession.snapshot());
  const activeType = (answers.deliverableType as DeliverableType) || "research";
  const questions = questionSets[activeType].questions.filter((question) => !question.relevant || question.relevant({ answers, deliverableType: activeType }));
  const question = questions[stepIndex];
  const contextAttachment: Answer | undefined = clientContext.client ? {
    client: clientContext.client,
    project: clientContext.project,
    campaign: clientContext.campaign,
  } : undefined;
  // The value the step displays when unanswered — the same value next() commits,
  // so what the operator sees pre-selected is exactly what launches (US3).
  function fallbackFor(target: Question): Answer | undefined {
    return target.kind === "attachment" ? contextAttachment ?? target.defaultValue : target.defaultValue;
  }
  const value = question ? answers[question.id] ?? fallbackFor(question) : undefined;

  useEffect(() => missionSession.subscribe(setSession), []);

  useEffect(() => {
    let alive = true;
    Promise.all([listDocs(), listVisual()])
      .then(([docs, visuals]) => { if (alive) setImportedPresence({ documents: docs.length > 0, images: visuals.length > 0 }); })
      .catch(() => { if (alive) setImportedPresence({ documents: false, images: false }); });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if ((state === "flow" || state === "review") && dirty) saveBriefDraft(answers, stepIndex, localStorage, useImportedMaterial);
  }, [answers, stepIndex, state, dirty, useImportedMaterial]);

  // Launch handoff: the session owns the SSE stream, so the screen leaves
  // "launching" as soon as the run is announced — not when the mission ends.
  useEffect(() => {
    if (state !== "launching" && state !== "launched") return;
    if (session.status === "running" || session.status === "done") {
      discardBriefDraft();
      setState("launched");
    } else if (session.status === "cancelled") {
      setState("review");
    } else if (session.status === "failed") {
      if (session.runId) {
        setState("failed");
      } else {
        setError(session.error ?? t("brief.error.launch"));
        setState("review");
      }
    }
  }, [session, state, t]);

  function setAnswer(id: string, nextValue: Answer) {
    setAnswers((current) => ({ ...current, [id]: nextValue }));
    setDirty(true);
    setError("");
  }

  function acceptDefault() {
    if (question?.defaultValue !== undefined) setAnswer(question.id, question.defaultValue);
  }

  function skip() {
    if (question?.skippable) setAnswer(question.id, "");
  }

  function next() {
    if (!question) return;
    const nextValue = answers[question.id] ?? fallbackFor(question);
    if ((nextValue === undefined || nextValue === "") && !question.skippable) {
      setError(t("brief.validation.required"));
      return;
    }
    if (typeof nextValue === "string" && nextValue.length > ANSWER_LIMIT) {
      setError(t("brief.validation.tooLong"));
      return;
    }
    if (question.kind === "attachment" && nextValue && typeof nextValue === "object" && "client" in nextValue) {
      const name = String(nextValue.client).trim();
      if (name && (name.length > 80 || /[<>]/.test(name))) {
        setError(t("brief.validation.clientName"));
        return;
      }
    }
    if (nextValue !== undefined && answers[question.id] === undefined) setAnswer(question.id, nextValue);
    if (stepIndex >= questions.length - 1) setState("review");
    else setStepIndex((index) => index + 1);
  }

  function back() {
    setError("");
    setStepIndex((index) => Math.max(0, index - 1));
  }

  function currentBrief(): Brief {
    const sector = answers.sector;
    return {
      intent: String(answers.intent ?? ""),
      deliverableType: activeType,
      sector: typeof sector === "string" ? { id: sector }
        : sector && typeof sector === "object" && "other" in sector ? { other: String(sector.other) }
        : null,
      answers,
      deliverableLanguage: String(answers.deliverableLanguage ?? locale),
      research: answers.research !== false,
      attachment: answers.attachment && typeof answers.attachment === "object" && "client" in answers.attachment && answers.attachment.client.trim()
        ? {
          client: answers.attachment.client.trim(),
          project: answers.attachment.project || null,
          campaign: answers.attachment.campaign || null,
        }
        : null,
      options: [],
      useImportedMaterial,
    };
  }

  function setUseImportedMaterial(enabled: boolean) {
    setUseImportedMaterialState(enabled);
    setDirty(true);
  }

  function edit(id: string) {
    const index = questions.findIndex((candidate) => candidate.id === id);
    if (index !== -1) {
      setStepIndex(index);
      setState("flow");
    }
  }

  function launch() {
    setState("launching");
    void missionSession.launch(composeMission(currentBrief(), importedPresence));
  }

  function resumeDraft() {
    if (!draft) return;
    setAnswers(draft.answers);
    setStepIndex(draft.stepIndex);
    setUseImportedMaterialState(draft.useImportedMaterial ?? false);
    setDirty(true);
    setState("flow");
  }

  function discardDraft() {
    discardBriefDraft();
    setDraft(null);
    setDirty(false);
    setState("flow");
  }

  return (
    <section className="state-panel" aria-labelledby="guided-brief-title">
      <h1 id="guided-brief-title">{t("brief.title")}</h1>
      {state === "resumePrompt" && (
        <section>
          <h1>{t("brief.draft.title")}</h1>
          <button type="button" onClick={resumeDraft}>{t("brief.draft.resume")}</button>
          <button type="button" onClick={discardDraft}>{t("brief.draft.discard")}</button>
        </section>
      )}
      {state === "flow" && (
        <form className="intent-form" onSubmit={(event) => event.preventDefault()}>
          <p>{t("brief.progress", { current: stepIndex + 1, total: questions.length })}</p>
          {question && (
            <FlowStep
              question={question}
              value={value}
              error={error}
              onAnswer={(nextValue) => setAnswer(question.id, nextValue)}
              onDefault={acceptDefault}
              onSkip={skip}
            />
          )}
          <div className="brief-step-actions">
            {stepIndex > 0 && <button type="button" onClick={back}>{t("brief.back")}</button>}
            <button type="button" onClick={next}>{t("brief.next")}</button>
          </div>
        </form>
      )}
      {state === "review" && <Review brief={currentBrief()} error={error} onEdit={edit} onUseImportedMaterial={setUseImportedMaterial} onLaunch={launch} />}
      {state === "launching" && <p>{t("state.loading")}</p>}
      {(state === "launched" || state === "failed") && (
        <>
          {state === "launched" && (
            <p>
              {t("brief.state.launched")}{session.runId ? ` (${session.runId})` : ""}{" "}
              <a href="#/missions">{t("brief.launched.link")}</a>
            </p>
          )}
          {state === "failed" && <p role="alert">{session.error ?? t("brief.error.launch")}</p>}
          {/* FR-018: the launched brief stays consultable */}
          <Review brief={currentBrief()} readOnly />
        </>
      )}
    </section>
  );
}
