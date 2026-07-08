import { useEffect, useState } from "react";
import { deleteMission, listMissions } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import { navigate } from "../../shell/router";
import { loadBriefDraft } from "../brief/briefDraft";
import { clear as clearFollowPointer, read as readFollowPointer } from "../missions/followPointer";
import { hasResumableDraft, recentMissionsView } from "./homeModel";
import type { RecentMissionItem } from "./homeModel";

type LoadState = "loading" | "ready" | "error";

export default function ResumeSection() {
  const { t } = useI18n();
  const [items, setItems] = useState<RecentMissionItem[]>([]);
  const [state, setState] = useState<LoadState>("loading");
  // Which item is showing its delete confirmation, and which failed to delete (both keyed by
  // mission id). Only one confirmation is open at a time; an error is per-item.
  const [confirmingKey, setConfirmingKey] = useState<string | null>(null);
  const [errorKey, setErrorKey] = useState<string | null>(null);
  const canResume = hasResumableDraft(loadBriefDraft());

  useEffect(() => {
    let alive = true;
    listMissions()
      .then((missions) => {
        if (!alive) return;
        setItems(recentMissionsView(missions, readFollowPointer()));
        setState("ready");
      })
      .catch(() => {
        if (alive) setState("error");
      });
    return () => {
      alive = false;
    };
  }, []);

  async function confirmDelete(key: string) {
    try {
      await deleteMission(key);
      setItems((prev) => prev.filter((i) => i.key !== key));
      // If the resume/follow pointer referenced the deleted mission, clear it so no stale
      // "resume" is offered for a mission that no longer exists (FR-007).
      const pointer = readFollowPointer();
      if (pointer && (pointer.runId === key || pointer.missionId === key)) clearFollowPointer();
      setConfirmingKey(null);
      setErrorKey(null);
    } catch {
      // Leave the item in place and surface an error — never show it as removed when it wasn't.
      setConfirmingKey(null);
      setErrorKey(key);
    }
  }

  const empty = state === "ready" && !canResume && items.length === 0;
  return (
    <section className="home-panel" aria-labelledby="home-resume-title">
      <h2 id="home-resume-title">{t("home.resume.title")}</h2>
      {canResume && <button type="button" onClick={() => navigate("#/brief")}>{t("home.resume.draft")}</button>}
      <h3>{t("home.resume.recentTitle")}</h3>
      {state === "loading" && <p>{t("state.loading")}</p>}
      {state === "error" && <p role="status">{t("home.recent.loadError")}</p>}
      {empty && <p>{t("home.recent.empty")}</p>}
      {items.length > 0 && (
        <ul className="home-recent-list">
          {items.map((item) => {
            const label = item.untitled ? t("home.recent.untitled") : item.label;
            return (
              <li key={item.key}>
                <button type="button" onClick={() => navigate(item.target)}>
                  <span>{label}</span>
                  <small>{t(item.statusKey)}</small>
                </button>
                {item.deletable && confirmingKey !== item.key && (
                  <button
                    type="button"
                    className="recent-delete"
                    aria-label={`${t("home.recent.delete")} — ${label}`}
                    onClick={() => { setErrorKey(null); setConfirmingKey(item.key); }}
                  >
                    {t("home.recent.delete")}
                  </button>
                )}
                {confirmingKey === item.key && (
                  <span
                    className="recent-delete-confirm"
                    role="group"
                    aria-label={t("home.recent.deleteConfirm")}
                    onKeyDown={(e) => { if (e.key === "Escape") setConfirmingKey(null); }}
                  >
                    <span>{t("home.recent.deleteConfirm")}</span>
                    <button type="button" onClick={() => confirmDelete(item.key)}>{t("home.recent.deleteConfirmYes")}</button>
                    <button type="button" onClick={() => setConfirmingKey(null)}>{t("home.recent.deleteConfirmCancel")}</button>
                  </span>
                )}
                {errorKey === item.key && (
                  <span className="error-text" role="alert">{t("home.recent.deleteError")}</span>
                )}
              </li>
            );
          })}
        </ul>
      )}
      <button className="ghost" type="button" onClick={() => navigate("#/library")}>{t("home.recent.seeAll")}</button>
    </section>
  );
}
