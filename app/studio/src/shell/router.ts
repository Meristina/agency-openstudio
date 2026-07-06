import { useEffect, useState } from "react";
import type { CatalogKey } from "../i18n/catalog";

export type RouteId = "home" | "brief" | "missions" | "library" | "import" | "export" | "models" | "settings" | "console";

export interface Route {
  id: RouteId;
  hash: string;
  titleKey: CatalogKey;
  status: "shipped" | "placeholder";
  taxonomyScoped: boolean;
}

export const routes: Route[] = [
  { id: "home", hash: "#/", titleKey: "nav.home", status: "shipped", taxonomyScoped: false },
  { id: "brief", hash: "#/brief", titleKey: "nav.brief", status: "shipped", taxonomyScoped: false },
  { id: "missions", hash: "#/missions", titleKey: "nav.missions", status: "shipped", taxonomyScoped: true },
  { id: "library", hash: "#/library", titleKey: "nav.library", status: "shipped", taxonomyScoped: true },
  { id: "import", hash: "#/import", titleKey: "nav.import", status: "shipped", taxonomyScoped: true },
  { id: "export", hash: "#/export", titleKey: "nav.export", status: "shipped", taxonomyScoped: true },
  { id: "models", hash: "#/models", titleKey: "nav.models", status: "shipped", taxonomyScoped: false },
  { id: "settings", hash: "#/settings", titleKey: "nav.settings", status: "placeholder", taxonomyScoped: false },
  { id: "console", hash: "#/console", titleKey: "nav.console", status: "shipped", taxonomyScoped: false },
];

export interface RouteMatch {
  route: Route | null;
  search: string;
  notFound: boolean;
}

export function parseHash(hash = window.location.hash): RouteMatch {
  if (!hash || hash === "#") return { route: routes[0], search: "", notFound: false };
  const [path, search = ""] = hash.split("?", 2);
  const route = routes.find((candidate) => candidate.hash === path);
  return route ? { route, search, notFound: false } : { route: null, search, notFound: true };
}

export function navigate(hash: string): void {
  const changed = window.location.hash !== hash;
  window.location.hash = hash;
  // A real change fires the native hashchange; only same-hash re-navigation
  // needs a synthetic one (so useRoute still resyncs) without double-firing.
  if (!changed) window.dispatchEvent(new Event("hashchange"));
}

export function useRoute(): RouteMatch {
  const [match, setMatch] = useState(parseHash);
  useEffect(() => {
    const onHashChange = () => setMatch(parseHash());
    window.addEventListener("hashchange", onHashChange);
    onHashChange();
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);
  return match;
}
