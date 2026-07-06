import type { CatalogKey } from "../i18n/catalog";
import { ComingSoon } from "../ui/states";
import type { RouteId } from "../shell/router";

const copy: Partial<Record<RouteId, { titleKey: CatalogKey; bodyKey: CatalogKey }>> = {
  settings: { titleKey: "settings.comingSoon.title", bodyKey: "settings.comingSoon.body" },
};

export function PlaceholderScreen({ id }: { id: RouteId }) {
  const keys = copy[id];
  return keys ? <ComingSoon titleKey={keys.titleKey} bodyKey={keys.bodyKey} /> : null;
}
