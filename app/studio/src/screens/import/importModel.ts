import type { CatalogKey } from "../../i18n/catalog";
import type { DocMeta, VisualMeta } from "../../types";

export type MaterialKind = "document" | "image";

export interface ClientAssociation {
  client: string;
  project?: string;
  campaign?: string;
}

export type AssociationMap = Record<string, ClientAssociation>;

export interface ImportedMaterial {
  id: string;
  kind: MaterialKind;
  name: string;
  importedAt: number;
  association: ClientAssociation | null;
}

export interface CampaignShelf {
  campaign?: string;
  items: ImportedMaterial[];
}

export interface ProjectShelf {
  project?: string;
  campaigns: CampaignShelf[];
}

export interface ClientShelf {
  client: string;
  projects: ProjectShelf[];
}

export interface ImportModel {
  shelves: ClientShelf[];
  unassigned: ImportedMaterial[];
  total: number;
}

export interface ImportViewState {
  activeClientContext?: { client?: string | null; project?: string | null; campaign?: string | null };
}

export type BringInResult =
  | { status: "accepted"; kind: MaterialKind; reason: null; item: ImportedMaterial | null }
  | { status: "rejected"; kind: MaterialKind | "unsupported"; reason: CatalogKey; item: null }
  | { status: "capabilityAbsent"; kind: MaterialKind; reason: CatalogKey; item: null };

const badNames = new Set(["", "untitled", "document", "image"]);

function cleanName(meta: DocMeta | VisualMeta): string {
  const title = meta.title?.trim();
  if (title && !badNames.has(title.toLowerCase()) && title !== meta.id) return title;
  return meta.filename?.split(/[\\/]/).pop()?.trim() || "Imported material";
}

function byNewest(a: ImportedMaterial, b: ImportedMaterial): number {
  return b.importedAt - a.importedAt || b.name.localeCompare(a.name);
}

function material(meta: DocMeta | VisualMeta, kind: MaterialKind, assoc: AssociationMap): ImportedMaterial {
  return {
    id: meta.id,
    kind,
    name: cleanName(meta),
    importedAt: meta.created,
    association: assoc[meta.id] ?? null,
  };
}

function unique<T extends { id: string }>(items: T[]): T[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (seen.has(item.id)) return false;
    seen.add(item.id);
    return true;
  });
}

export function buildImportModel(
  docs: DocMeta[],
  visuals: VisualMeta[],
  assoc: AssociationMap,
  scope: { client?: string | null; project?: string | null; campaign?: string | null } = {},
): ImportModel {
  const all = [
    ...unique(docs).map((doc) => material(doc, "document", assoc)),
    ...unique(visuals).map((visual) => material(visual, "image", assoc)),
  ].sort(byNewest);
  const shelves: ClientShelf[] = [];
  const unassigned: ImportedMaterial[] = [];

  for (const item of all) {
    const a = item.association;
    if (!a || (scope.client && a.client !== scope.client) || (scope.project && a.project !== scope.project) || (scope.campaign && a.campaign !== scope.campaign)) {
      if (!scope.client && !a) unassigned.push(item);
      continue;
    }
    let shelf = shelves.find((candidate) => candidate.client === a.client);
    if (!shelf) shelves.push(shelf = { client: a.client, projects: [] });
    let project = shelf.projects.find((candidate) => candidate.project === a.project);
    if (!project) shelf.projects.push(project = { project: a.project, campaigns: [] });
    let campaign = project.campaigns.find((candidate) => candidate.campaign === a.campaign);
    if (!campaign) project.campaigns.push(campaign = { campaign: a.campaign, items: [] });
    campaign.items.push(item);
  }

  return { shelves, unassigned, total: shelves.reduce((n, s) => n + s.projects.reduce((p, pr) => p + pr.campaigns.reduce((c, ca) => c + ca.items.length, 0), 0), 0) + unassigned.length };
}

export function classifyFileKind(file: File): MaterialKind | "unsupported" {
  const name = file.name.toLowerCase();
  if (/\.(png|jpe?g|webp|gif|bmp|tiff?)$/.test(name) || file.type.startsWith("image/")) return "image";
  if (/\.(txt|md|pdf|docx?|pptx?|xlsx?|csv|rtf|odt)$/.test(name) || /^(text\/|application\/pdf)/.test(file.type)) return "document";
  return "unsupported";
}

export function classifyBringInError(error: unknown, kind: MaterialKind | "unsupported"): BringInResult {
  if (kind === "unsupported") return { status: "rejected", kind, reason: "import.reject.unsupportedKind", item: null };
  const message = error instanceof Error ? error.message : String(error);
  // Read the HTTP status from the `errorText` delimiter (`<label> → <status>[: …]`), never a bare
  // substring — an incidental "400 bytes" in a message must not be mistaken for a 400 rejection.
  const status = Number(message.match(/→\s*(\d{3})\b/)?.[1]);
  if (status === 501) return { status: "capabilityAbsent", kind, reason: "import.capabilityAbsent.hint", item: null };
  if (status === 413) return { status: "rejected", kind, reason: "import.reject.tooLarge", item: null };
  if (status === 400) return { status: "rejected", kind, reason: "import.reject.unreadable", item: null };
  return { status: "rejected", kind, reason: "import.reject.generic", item: null };
}
