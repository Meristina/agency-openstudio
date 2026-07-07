import { useEffect, useState } from "react";
import { listMissions } from "../../api";
import { useI18n } from "../../i18n/I18nProvider";
import { navigate } from "../../shell/router";
import { loadBriefDraft } from "../brief/briefDraft";
import { read as readFollowPointer } from "../missions/followPointer";
import { hasResumableDraft, recentMissionsView } from "./homeModel";
import type { RecentMissionItem } from "./homeModel";

type LoadState = "loading" | "ready" | "error";

export default function ResumeSection() {
  const { t } = useI18n();
  const [items, setItems] = useState<RecentMissionItem[]>([]);
  const [state, setState] = useState<LoadState>("loading");
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
          {items.map((item) => (
            <li key={item.key}>
              <button type="button" onClick={() => navigate(item.target)}>
                <span>{item.label}</span>
                <small>{t(item.statusKey)}</small>
              </button>
            </li>
          ))}
        </ul>
      )}
      <button className="ghost" type="button" onClick={() => navigate("#/library")}>{t("home.recent.seeAll")}</button>
    </section>
  );
}
