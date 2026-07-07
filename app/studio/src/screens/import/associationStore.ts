import { PREFS_KEY } from "../../i18n/catalog";
import type { AssociationMap, ClientAssociation } from "./importModel";

export const ASSOCIATION_KEY = `${PREFS_KEY}.importAssociations`;

function read(): AssociationMap {
  try {
    const parsed = JSON.parse(localStorage.getItem(ASSOCIATION_KEY) || "{}") as unknown;
    return parsed && typeof parsed === "object" ? parsed as AssociationMap : {};
  } catch {
    return {};
  }
}

function write(map: AssociationMap): void {
  try {
    localStorage.setItem(ASSOCIATION_KEY, JSON.stringify(map));
  } catch {
    // localStorage may be disabled; the import view simply behaves as unassigned.
  }
}

export function getAssociation(id: string): ClientAssociation | null {
  return read()[id] ?? null;
}

export function getAssociations(): AssociationMap {
  return read();
}

export function setAssociation(id: string, assoc: ClientAssociation): void {
  write({ ...read(), [id]: assoc });
}

export function clearAssociation(id: string): void {
  const next = read();
  delete next[id];
  write(next);
}

export function pruneAssociations(knownIds: string[]): void {
  const keep = new Set(knownIds);
  const next = Object.fromEntries(Object.entries(read()).filter(([id]) => keep.has(id)));
  write(next);
}

export function defaultOnAccept(id: string, activeContext: { client?: string | null; project?: string | null; campaign?: string | null }): void {
  if (!activeContext.client) return;
  setAssociation(id, {
    client: activeContext.client,
    ...(activeContext.project ? { project: activeContext.project } : {}),
    ...(activeContext.campaign ? { campaign: activeContext.campaign } : {}),
  });
}
