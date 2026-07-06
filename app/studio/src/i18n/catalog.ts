export type Locale = "en" | "fr";

export type CatalogKey =
  | "nav.home" | "nav.brief" | "nav.missions" | "nav.library" | "nav.import" | "nav.export" | "nav.models" | "nav.settings" | "nav.console"
  | "home.question" | "home.intentLabel" | "home.intentPlaceholder" | "home.start"
  | "state.loading" | "state.empty" | "state.error" | "state.comingSoon.title" | "state.comingSoon.body" | "state.backHome" | "state.notFound.title" | "state.notFound.body"
  | "conn.unreachable" | "conn.retrying"
  | "context.label" | "context.client" | "context.project" | "context.campaign" | "context.none" | "context.unassigned" | "context.clear" | "context.empty"
  | "lang.label" | "lang.en" | "lang.fr"
  | "models.title"
  | "brief.title" | "brief.progress" | "brief.back" | "brief.next" | "brief.start" | "brief.review" | "brief.launch"
  | "brief.skip" | "brief.useDefault" | "brief.edit" | "brief.review.sources" | "brief.review.sourcesValue" | "brief.launched.link"
  | "brief.review.on" | "brief.review.off" | "brief.question.sectorOther"
  | "brief.help.intent" | "brief.help.sector" | "brief.help.constraints" | "brief.help.research"
  | "brief.question.deliverableType" | "brief.question.sector" | "brief.question.constraints" | "brief.question.research" | "brief.question.deliverableLanguage"
  | "brief.question.attachment" | "brief.help.attachment" | "brief.attachment.unassigned" | "brief.attachment.newClient" | "brief.attachment.unavailable"
  | "brief.capability.video" | "brief.capability.videoLocal" | "brief.capability.videoPaid" | "brief.capability.blocked" | "brief.capability.unavailable" | "brief.capability.openModels" | "brief.capability.ackPaid"
  | "brief.draft.title" | "brief.draft.resume" | "brief.draft.discard"
  | "brief.question.researchAudience" | "brief.question.researchObjective" | "brief.question.strategyAudience" | "brief.question.strategyGoal" | "brief.question.videoAudience" | "brief.question.videoMessage"
  | "brief.choice.research" | "brief.choice.strategy" | "brief.choice.video"
  | "brief.sector.general" | "brief.sector.food" | "brief.sector.sport" | "brief.sector.events" | "brief.sector.other"
  | "brief.validation.required" | "brief.validation.tooLong" | "brief.validation.clientName" | "brief.error.launch" | "brief.state.launched"
  | "brief.comingSoon.title" | "brief.comingSoon.body"
  | "missions.comingSoon.title" | "missions.comingSoon.body"
  | "library.comingSoon.title" | "library.comingSoon.body"
  | "import.comingSoon.title" | "import.comingSoon.body"
  | "export.comingSoon.title" | "export.comingSoon.body"
  | "settings.comingSoon.title" | "settings.comingSoon.body";

export const PREFS_KEY = "agency-studio.prefs";
