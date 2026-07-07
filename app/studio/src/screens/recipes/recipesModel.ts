import type { CatalogKey } from "../../i18n/catalog";
import type { Recipe } from "./recipesApi";

export function catalogView(recipes: Recipe[], t: (key: CatalogKey) => string) {
  return recipes.map((recipe) => ({
    id: recipe.id,
    kind: recipe.kind,
    name: t(recipe.name_key as CatalogKey),
    description: t(recipe.desc_key as CatalogKey),
    tiers: stageTierBadges(recipe),
  }));
}

export function stageTierBadges(recipe: Recipe) {
  return recipe.stages.map((stage) => ({ labelKey: stage.label_key as CatalogKey, tier: stage.tier, kind: stage.kind }));
}
