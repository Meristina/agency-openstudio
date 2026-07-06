import type { AssetManifestItem, Dossier } from "../../types";
import type { CatalogKey } from "../../i18n/catalog";

export type ExportFormat = "document" | "mediaPack" | "fullBundle";
export type FormatState = "available" | "unavailable-here" | "no-media-to-pack";

export interface ExportDeliverable {
  id: string;
  title: string;
  dossier?: Dossier;
}

export interface FormatView {
  id: ExportFormat;
  nameKey: CatalogKey;
  contentsKey: CatalogKey;
  state: FormatState;
}

export function hasMedia(dossier?: Pick<Dossier, "assets">): boolean {
  return !!dossier?.assets?.some((item: AssetManifestItem) => item.status === "ok" && !!item.url);
}

export function availableFormats({ hasMedia: withMedia, pdfCapable = true }: { hasMedia: boolean; pdfCapable?: boolean }): FormatView[] {
  const pdfState = pdfCapable ? "available" : "unavailable-here";
  return [
    { id: "document", nameKey: "export.format.document", contentsKey: "export.contents.document", state: pdfState },
    { id: "mediaPack", nameKey: "export.format.mediaPack", contentsKey: "export.contents.mediaPack", state: withMedia ? "available" : "no-media-to-pack" },
    { id: "fullBundle", nameKey: "export.format.fullBundle", contentsKey: "export.contents.fullBundle", state: pdfState },
  ];
}

function slug(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 80) || "deliverable";
}

export function friendlyFilename(deliverable: Pick<ExportDeliverable, "title">, format: ExportFormat): string {
  const suffix = format === "document" ? "document.pdf" : format === "mediaPack" ? "media.zip" : "bundle.zip";
  return `${slug(deliverable.title)}-${suffix}`;
}
