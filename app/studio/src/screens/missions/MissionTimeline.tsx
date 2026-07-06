import { useEffect, useMemo, useState } from "react";
import { useI18n } from "../../i18n/I18nProvider";
import type { CatalogKey } from "../../i18n/catalog";
import { navigate } from "../../shell/router";
import { Empty, ErrorState, Loading } from "../../ui/states";
import { groupTimeline, type Terminal } from "../../timeline";
import { missionSession } from "../session/missionSession";
import CancelControl from "./CancelControl";
import { clear, read, record, type FollowPointer } from "./followPointer";
import { humanStages, type HumanStage } from "./humanStages";
import StageList from "./StageList";
import TerminalPanel from "./TerminalPanel";

function pointerFromTerminal(runId: string, terminal: Terminal): Omit<FollowPointer, "updatedAt"> {
  if (terminal.kind === "done") return { runId, status: "done", missionId: terminal.missionId };
  if (terminal.kind === "error") return { runId, status: "error", resumable: terminal.resumable, checkpoint: terminal.checkpoint };
  return { runId, status: "cancelled" };
}

export default function MissionTimeline() {
  const { t } = useI18n();
  const [session, setSession] = useState(missionSession.snapshot());
  const [pointer, setPointer] = useState<FollowPointer | null>(() => read());
  const [lastStages, setLastStages] = useState<HumanStage[]>([]);
  const model = useMemo(() => groupTimeline(session.events), [session.events]);
  const stages = useMemo(() => humanStages(model), [model]);
  const terminal = model.terminal;
  const stageAnnouncement = stages.map((stage) => `${t(stage.titleKey)} ${t(`missions.state.${stage.state}` as CatalogKey)}`).join(", ");

  useEffect(() => missionSession.subscribe(setSession), []);

  useEffect(() => {
    if (stages.length) setLastStages(stages);
  }, [stages]);

  useEffect(() => {
    if (!session.runId) return;
    if (terminal) setPointer(record(pointerFromTerminal(session.runId, terminal)));
    else if (session.status === "running" || session.status === "launching") setPointer(record({ runId: session.runId, status: "running" }));
  }, [session.runId, session.status, terminal]);

  if (session.status === "launching") return <Loading />;

  if (session.status === "idle") {
    if (pointer?.status === "done" || (pointer?.status === "error" && pointer.resumable)) {
      return (
        <section className="mission-screen">
          <TerminalPanel terminal={null} pointer={pointer} />
          <button type="button" onClick={() => { clear(); setPointer(null); }}>{t("missions.resume.dismiss")}</button>
        </section>
      );
    }
    return (
      <section className="state-panel">
        <h1>{t("missions.title")}</h1>
        <p>{t("missions.empty.body")}</p>
        <button type="button" onClick={() => navigate("#/brief")}>{t("missions.empty.cta")}</button>
      </section>
    );
  }

  if (session.status === "failed" && !terminal) {
    // A failure before the run ever streamed (no run id) is a launch/resume rejection — show a
    // plain error with a way forward. A failure after streaming began is a transport drop — show
    // a calm connection-lost state that keeps the stages already rendered. We key off runId (not
    // the raw message) so no machinery term (e.g. the engine/kit name in a server reason) leaks.
    const startedStreaming = Boolean(session.runId);
    return (
      <section className="mission-screen">
        <ErrorState message={t(startedStreaming ? "missions.connection.body" : "missions.terminal.error.body")} />
        {!startedStreaming && (
          <button type="button" onClick={() => navigate("#/brief")}>{t("missions.terminal.retry")}</button>
        )}
        {lastStages.length > 0 && <StageList stages={lastStages} />}
      </section>
    );
  }

  if (session.status === "done" || session.status === "failed" || session.status === "cancelled") {
    return (
      <section className="mission-screen">
        <p className="sr-only" aria-live="polite">{stageAnnouncement}</p>
        <TerminalPanel terminal={terminal ?? (session.status === "cancelled" ? { kind: "cancelled" } : null)} pointer={pointer} />
        {lastStages.length > 0 && <StageList stages={lastStages} />}
      </section>
    );
  }

  if (!stages.length && !session.runId) return <Empty />;

  return (
    <section className="mission-screen" aria-labelledby="mission-title">
      <div className="mission-header">
        <div>
          <h1 id="mission-title">{t("missions.title")}</h1>
          {session.runId && <p>{t("missions.running", { id: session.runId })}</p>}
        </div>
        <CancelControl status={session.status} onCancel={() => missionSession.cancel()} />
      </div>
      <p className="sr-only" aria-live="polite">{stageAnnouncement}</p>
      <StageList stages={stages} />
    </section>
  );
}
