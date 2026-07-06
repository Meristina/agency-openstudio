import { summaryVerdictClass } from "../../types";
import type { AssetManifestItem, Dossier, MissionSummary, TaxonomyTree } from "../../types";

export type Outcome = "successful" | "needs-attention";
export type OutcomeFilter = "all" | Outcome;

export interface TaxonomyPlacement {
  kind: "filed" | "unassigned" | "orphaned";
  client: string | null;
  project: string | null;
  campaign: string | null;
}

export interface DeliverablePreview {
  headline: string;
  outcome: Outcome;
  keySources: string[];
  keyDecisions: string[];
  media: AssetManifestItem[];
}

export interface Deliverable {
  id: string;
  title: string;
  producedAt: string | null;
  outcome: Outcome;
  placement: TaxonomyPlacement;
  preview: DeliverablePreview | null;
}

export interface CampaignShelf {
  campaign: string | null;
  deliverables: Deliverable[];
}

export interface ProjectShelf {
  project: string | null;
  campaigns: CampaignShelf[];
}

export interface Shelf {
  client: string;
  projects: ProjectShelf[];
}

export interface LibraryViewState {
  query: string;
  outcomeFilter: OutcomeFilter;
  previewId?: string | null;
  openId?: string | null;
}

export interface LibraryScope {
  client: string | null;
  project: string | null;
  campaign: string | null;
}

export interface LibraryModel {
  shelves: Shelf[];
  unassigned: Deliverable[];
  total: number;
  isEmptyFirstRun: boolean;
  isEmptyForContext: boolean;
  isEmptyForQuery: boolean;
}

const emptyView: LibraryViewState = { query: "", outcomeFilter: "all" };

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function attribution(m: MissionSummary): { client: string | null; project: string | null; campaign: string | null } {
  const nested = m.attribution && typeof m.attribution === "object" ? m.attribution as Record<string, unknown> : {};
  return {
    client: text(m.client) ?? text(nested.client),
    project: text(m.project) ?? text(nested.project),
    campaign: text(m.campaign) ?? text(nested.campaign),
  };
}

export function placementOf(m: MissionSummary, taxonomy: TaxonomyTree): TaxonomyPlacement {
  const a = attribution(m);
  if (!a.client) return { kind: "unassigned", ...a };
  const client = taxonomy.clients.find((item) => item.name === a.client);
  const project = a.project ? client?.projects.find((item) => item.name === a.project) : undefined;
  const campaignOk = a.campaign ? project?.campaigns.some((item) => item.name === a.campaign) : true;
  const resolved = client && (!a.project || project) && campaignOk;
  return { kind: resolved ? "filed" : "orphaned", ...a };
}

export function classifyOutcome(m: MissionSummary | Dossier): Outcome {
  const verdicts = (m as Dossier).verdicts;
  const verdict = "verdict" in m ? (m as MissionSummary).verdict : verdicts?.[verdicts.length - 1]?.verdict;
  return m.delivered && summaryVerdictClass(verdict) === "ok" ? "successful" : "needs-attention";
}

function producedAt(id: string): string | null {
  const match = id.match(/^(\d{4})[-_]?(\d{2})[-_]?(\d{2})/);
  return match ? `${match[1]}-${match[2]}-${match[3]}` : null;
}

function byNewest(a: Deliverable, b: Deliverable): number {
  return (b.producedAt ?? b.id).localeCompare(a.producedAt ?? a.id);
}

function makeDeliverable(m: MissionSummary, taxonomy: TaxonomyTree): Deliverable {
  const title = text(m.goal) ?? "";
  return {
    id: m.mission_id,
    title,
    producedAt: producedAt(m.mission_id),
    outcome: classifyOutcome(m),
    placement: placementOf(m, taxonomy),
    preview: null,
  };
}

function inScope(d: Deliverable, scope: LibraryScope): boolean {
  if (!scope.client) return true;
  if (d.placement.kind !== "filed" || d.placement.client !== scope.client) return false;
  if (scope.project && d.placement.project !== scope.project) return false;
  return !scope.campaign || d.placement.campaign === scope.campaign;
}

function matches(d: Deliverable, view: LibraryViewState): boolean {
  if (view.outcomeFilter !== "all" && d.outcome !== view.outcomeFilter) return false;
  const q = view.query.trim().toLowerCase();
  if (!q) return true;
  return [d.title, d.placement.client, d.placement.project, d.placement.campaign]
    .filter(Boolean)
    .join(" ")
    .toLowerCase()
    .includes(q);
}

export function buildLibraryModel(
  missions: MissionSummary[],
  taxonomy: TaxonomyTree,
  scope: LibraryScope = { client: null, project: null, campaign: null },
  view: LibraryViewState = emptyView,
): LibraryModel {
  const seen = new Set<string>();
  const all = missions
    .filter((m) => {
      if (!m.mission_id || seen.has(m.mission_id)) return false;
      seen.add(m.mission_id);
      return true;
    })
    .map((m) => makeDeliverable(m, taxonomy));
  const scoped = all.filter((d) => inScope(d, scope));
  const visible = scoped.filter((d) => matches(d, view)).sort(byNewest);
  const shelves: Shelf[] = [];
  const unassigned: Deliverable[] = [];

  for (const d of visible) {
    if (d.placement.kind !== "filed" || !d.placement.client) {
      unassigned.push(d);
      continue;
    }
    let shelf = shelves.find((item) => item.client === d.placement.client);
    if (!shelf) shelves.push(shelf = { client: d.placement.client, projects: [] });
    let project = shelf.projects.find((item) => item.project === d.placement.project);
    if (!project) shelf.projects.push(project = { project: d.placement.project, campaigns: [] });
    let campaign = project.campaigns.find((item) => item.campaign === d.placement.campaign);
    if (!campaign) project.campaigns.push(campaign = { campaign: d.placement.campaign, deliverables: [] });
    campaign.deliverables.push(d);
  }

  const total = visible.length;
  const scopeEmpty = scoped.length === 0;
  const filtered = view.query.trim() || view.outcomeFilter !== "all";
  return {
    shelves,
    unassigned,
    total,
    isEmptyFirstRun: missions.length === 0,
    isEmptyForContext: missions.length > 0 && scopeEmpty,
    isEmptyForQuery: missions.length > 0 && !scopeEmpty && total === 0 && !!filtered,
  };
}

export function previewFromDossier(dossier: Dossier): DeliverablePreview {
  return {
    headline: dossier.goal || "",
    outcome: classifyOutcome(dossier),
    keySources: (dossier.sources ?? []).slice(0, 4),
    keyDecisions: (dossier.decisions ?? []).slice(0, 4),
    media: dossier.assets ?? [],
  };
}
