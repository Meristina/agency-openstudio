export type Locale = "en" | "fr";

export type CatalogKey =
  | "nav.home" | "nav.brief" | "nav.missions" | "nav.library" | "nav.import" | "nav.export" | "nav.models" | "nav.settings" | "nav.console"
  | "home.question" | "home.intentLabel" | "home.intentPlaceholder" | "home.start"
  | "state.loading" | "state.empty" | "state.error" | "state.comingSoon.title" | "state.comingSoon.body" | "state.backHome" | "state.notFound.title" | "state.notFound.body"
  | "conn.unreachable" | "conn.retrying"
  | "context.label" | "context.client" | "context.project" | "context.campaign" | "context.none" | "context.unassigned" | "context.clear" | "context.empty"
  | "lang.label" | "lang.en" | "lang.fr"
  | "models.title"
  | "brief.comingSoon.title" | "brief.comingSoon.body"
  | "missions.comingSoon.title" | "missions.comingSoon.body"
  | "library.comingSoon.title" | "library.comingSoon.body"
  | "import.comingSoon.title" | "import.comingSoon.body"
  | "export.comingSoon.title" | "export.comingSoon.body"
  | "settings.comingSoon.title" | "settings.comingSoon.body";

export const PREFS_KEY = "agency-studio.prefs";
