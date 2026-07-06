import type { CatalogKey } from "../../i18n/catalog";

export type DeliverableType = "research" | "strategy" | "video";

export type Answer =
  | string
  | boolean
  | { id: string }
  | { other: string }
  | ClientAttachment
  | ProductionOption[];

export type QuestionKind = "choice" | "shortText" | "longText" | "language" | "sector" | "toggle" | "attachment";

export type ClientAttachment = {
  client: string;
  project?: string | null;
  campaign?: string | null;
};

export type ProductionOption = {
  id: string;
  labelKey: CatalogKey;
  valueKey: CatalogKey;
  paidOffMachine: boolean;
};

export type Brief = {
  intent: string;
  deliverableType: DeliverableType;
  sector: { id: string } | { other: string } | null;
  answers: Record<string, Answer>;
  deliverableLanguage: string;
  research: boolean;
  attachment: ClientAttachment | null;
  options: ProductionOption[];
  useImportedMaterial?: boolean;
};

export type PartialBrief = Partial<Brief> & {
  answers?: Record<string, Answer>;
};

export type ComposeRule =
  | { kind: "line"; labelKey: CatalogKey }
  | { kind: "flag"; field: "web_search" | "video" | "assets" };

export type QuestionChoice = {
  id: string;
  labelKey: CatalogKey;
};

export type Question = {
  id: string;
  kind: QuestionKind;
  labelKey: CatalogKey;
  helpKey?: CatalogKey;
  choices?: QuestionChoice[];
  relevant?: (brief: PartialBrief) => boolean;
  defaultValue?: Answer;
  skippable?: boolean;
  compose: ComposeRule;
};

export type QuestionSet = {
  type: DeliverableType;
  questions: Question[];
};

const deliverableType: Question = {
  id: "deliverableType",
  kind: "choice",
  labelKey: "brief.question.deliverableType",
  choices: [
    { id: "research", labelKey: "brief.choice.research" },
    { id: "strategy", labelKey: "brief.choice.strategy" },
    { id: "video", labelKey: "brief.choice.video" },
  ],
  compose: { kind: "line", labelKey: "brief.question.deliverableType" },
};

const commonOpening: Question[] = [
  {
    id: "intent",
    kind: "longText",
    labelKey: "home.intentLabel",
    helpKey: "brief.help.intent",
    compose: { kind: "line", labelKey: "home.intentLabel" },
  },
  deliverableType,
  {
    id: "sector",
    kind: "sector",
    labelKey: "brief.question.sector",
    helpKey: "brief.help.sector",
    defaultValue: "general",
    choices: [
      { id: "general", labelKey: "brief.sector.general" },
      { id: "food", labelKey: "brief.sector.food" },
      { id: "sport", labelKey: "brief.sector.sport" },
      { id: "events", labelKey: "brief.sector.events" },
      { id: "other", labelKey: "brief.sector.other" },
    ],
    compose: { kind: "line", labelKey: "brief.question.sector" },
  },
];

const commonClosing: Question[] = [
  {
    id: "constraints",
    kind: "longText",
    labelKey: "brief.question.constraints",
    helpKey: "brief.help.constraints",
    skippable: true,
    compose: { kind: "line", labelKey: "brief.question.constraints" },
  },
  {
    id: "research",
    kind: "toggle",
    labelKey: "brief.question.research",
    helpKey: "brief.help.research",
    defaultValue: true,
    compose: { kind: "flag", field: "web_search" },
  },
  {
    id: "attachment",
    kind: "attachment",
    labelKey: "brief.question.attachment",
    helpKey: "brief.help.attachment",
    skippable: true,
    compose: { kind: "line", labelKey: "brief.question.attachment" },
  },
  {
    id: "deliverableLanguage",
    kind: "language",
    labelKey: "brief.question.deliverableLanguage",
    choices: [
      { id: "en", labelKey: "lang.en" },
      { id: "fr", labelKey: "lang.fr" },
    ],
    compose: { kind: "line", labelKey: "brief.question.deliverableLanguage" },
  },
];

export const questionSets: Record<DeliverableType, QuestionSet> = {
  research: {
    type: "research",
    questions: [
      ...commonOpening,
      {
        id: "researchAudience",
        kind: "shortText",
        labelKey: "brief.question.researchAudience",
        defaultValue: "Decision makers",
        compose: { kind: "line", labelKey: "brief.question.researchAudience" },
      },
      {
        id: "researchObjective",
        kind: "shortText",
        labelKey: "brief.question.researchObjective",
        defaultValue: "Understand the opportunity",
        compose: { kind: "line", labelKey: "brief.question.researchObjective" },
      },
      ...commonClosing,
    ],
  },
  strategy: {
    type: "strategy",
    questions: [
      ...commonOpening,
      {
        id: "strategyAudience",
        kind: "shortText",
        labelKey: "brief.question.strategyAudience",
        defaultValue: "The leadership team",
        compose: { kind: "line", labelKey: "brief.question.strategyAudience" },
      },
      {
        id: "strategyGoal",
        kind: "shortText",
        labelKey: "brief.question.strategyGoal",
        defaultValue: "Choose the next move",
        compose: { kind: "line", labelKey: "brief.question.strategyGoal" },
      },
      ...commonClosing,
    ],
  },
  video: {
    type: "video",
    questions: [
      ...commonOpening,
      {
        id: "videoAudience",
        kind: "shortText",
        labelKey: "brief.question.videoAudience",
        defaultValue: "Customers",
        compose: { kind: "line", labelKey: "brief.question.videoAudience" },
      },
      {
        id: "videoMessage",
        kind: "shortText",
        labelKey: "brief.question.videoMessage",
        defaultValue: "Present the offer clearly",
        compose: { kind: "line", labelKey: "brief.question.videoMessage" },
      },
      ...commonClosing,
    ],
  },
};
