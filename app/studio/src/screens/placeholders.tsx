import type { CatalogKey } from "../i18n/catalog";
import { ComingSoon } from "../ui/states";
import type { RouteId } from "../shell/router";

const copy: Partial<Record<RouteId, { titleKey: CatalogKey; bodyKey: CatalogKey }>> = {
  missions: { titleKey: "missions.comingSoon.title", bodyKey: "missions.comingSoon.body" },
  library: { titleKey: "library.comingSoon.title", bodyKey: "library.comingSoon.body" },
  import: { titleKey: "import.comingSoon.title", bodyKey: "import.comingSoon.body" },
  export: { titleKey: "export.comingSoon.title", bodyKey: "export.comingSoon.body" },
  settings: { titleKey: "settings.comingSoon.title", bodyKey: "settings.comingSoon.body" },
};

export function PlaceholderScreen({ id }: { id: RouteId }) {
  const keys = copy[id];
  return keys ? <ComingSoon titleKey={keys.titleKey} bodyKey={keys.bodyKey} /> : null;
}
