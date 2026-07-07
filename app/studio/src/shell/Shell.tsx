import { useCallback } from "react";
import ConnectionBanner from "./ConnectionBanner";
import { ClientContextProvider, ClientContextSelector, useClientContext } from "./ClientContext";
import LanguageSwitch from "./LanguageSwitch";
import Nav from "./Nav";
import { useRoute } from "./router";
import Home from "../screens/Home";
import Console from "../screens/Console";
import Models from "../screens/Models";
import SettingsScreen from "../screens/settings/SettingsScreen";
import GuidedBrief from "../screens/brief/GuidedBrief";
import Import from "../screens/import/Import";
import Export from "../screens/export/Export";
import DeliverableLibrary from "../screens/library/DeliverableLibrary";
import MissionTimeline from "../screens/missions/MissionTimeline";
import { PlaceholderScreen } from "../screens/placeholders";
import { NotFound } from "../ui/states";
import { useI18n } from "../i18n/I18nProvider";

function Outlet() {
  const match = useRoute();
  const { t } = useI18n();
  const context = useClientContext();
  if (match.notFound || !match.route) return <NotFound />;
  if (match.route.id === "home") return <Home />;
  if (match.route.id === "brief") return <GuidedBrief search={match.search} />;
  if (match.route.id === "missions") return <MissionTimeline />;
  if (match.route.id === "library") return <DeliverableLibrary search={match.search} />;
  if (match.route.id === "import") return <Import />;
  if (match.route.id === "export") return <Export />;
  if (match.route.id === "console") return <Console />;
  if (match.route.id === "models") return <Models />;
  if (match.route.id === "settings") return <SettingsScreen />;
  return (
    <>
      {match.route.taxonomyScoped && (
        <p className="scope-note">
          {context.client ? [context.client, context.project, context.campaign].filter(Boolean).join(" / ") : t("context.none")} - {t("context.unassigned")}
        </p>
      )}
      <PlaceholderScreen id={match.route.id} />
    </>
  );
}

function ShellFrame() {
  const match = useRoute();
  const { refresh } = useClientContext();
  const onReachable = useCallback(() => { void refresh().catch(() => {}); }, [refresh]);
  return (
    <div className="shell">
      <header className="shell-topbar">
        <strong>Agency OpenStudio</strong>
        <LanguageSwitch />
      </header>
      <ConnectionBanner onReachable={onReachable} />
      <div className="shell-body">
        <aside className="shell-sidebar">
          <Nav activeId={match.route?.id ?? null} />
          <ClientContextSelector />
        </aside>
        <main className="shell-outlet">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default function Shell() {
  return (
    <ClientContextProvider>
      <ShellFrame />
    </ClientContextProvider>
  );
}
