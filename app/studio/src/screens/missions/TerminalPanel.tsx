import { fetchMissionPdf } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import { navigate } from "../../shell/router";
import type { Terminal } from "../../timeline";
import { clear, type FollowPointer } from "./followPointer";
import { missionSession } from "../session/missionSession";

export default function TerminalPanel({ terminal, pointer }: { terminal: Terminal | null; pointer?: FollowPointer | null }) {
  const { t } = useI18n();
  const kind = terminal?.kind ?? (pointer?.status === "done" ? "done" : pointer?.status === "error" ? "error" : pointer?.status === "cancelled" ? "cancelled" : null);
  const missionId = terminal?.kind === "done" ? terminal.missionId : pointer?.missionId ?? null;
  const resumable = terminal?.kind === "error" ? terminal.resumable : pointer?.resumable;
  const checkpoint = terminal?.kind === "error" ? terminal.checkpoint : pointer?.checkpoint;
  if (!kind) return null;

  function openDetails() {
    if (missionId) navigate(`#/library?deliverable=${encodeURIComponent(missionId)}`);
  }
  async function downloadPdf() {
    if (!missionId) return;
    // Fetch → blob download (mirrors MissionDetail's export): a plain <a href> can't carry the
    // fetch's error handling, and the blob must actually reach the user, not be discarded.
    const blob = await fetchMissionPdf(missionId);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${missionId}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
  }
  async function resume() {
    if (pointer?.runId) {
      clear();
      await missionSession.resume(pointer.runId);
    }
  }

  if (kind === "done") {
    return (
      <section className="state-panel mission-terminal">
        <h1>{t("missions.terminal.finished.title")}</h1>
        <p>{t("missions.terminal.finished.body")}</p>
        {missionId && <p>{t("missions.terminal.mission", { id: missionId })}</p>}
        <button type="button" disabled={!missionId} onClick={openDetails}>{t("missions.terminal.openDetails")}</button>
        <button type="button" disabled={!missionId} onClick={downloadPdf}>{t("missions.terminal.downloadPdf")}</button>
        <button type="button" onClick={() => navigate("#/brief")}>{t("missions.terminal.startAnother")}</button>
      </section>
    );
  }
  if (kind === "error") {
    return (
      <section className="state-panel mission-terminal">
        <h1>{t(resumable && checkpoint ? "missions.terminal.error.resumeTitle" : "missions.terminal.error.title")}</h1>
        <p>{t("missions.terminal.error.body")}</p>
        {resumable && checkpoint && <button type="button" onClick={resume}>{t("missions.resume.button")}</button>}
        <button type="button" onClick={() => navigate("#/brief")}>{t("missions.terminal.retry")}</button>
      </section>
    );
  }
  return (
    <section className="state-panel mission-terminal">
      <h1>{t("missions.terminal.stopped.title")}</h1>
      <p>{t("missions.terminal.stopped.body")}</p>
      <button type="button" onClick={() => navigate("#/brief")}>{t("missions.terminal.startAnother")}</button>
    </section>
  );
}
