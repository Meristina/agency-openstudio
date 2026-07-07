import { useEffect, useMemo, useState } from "react";
import { useI18n } from "../../i18n/I18nProvider";
import { ErrorState, Loading } from "../../ui/states";
import { listRecipes, type Recipe } from "./recipesApi";
import { catalogView } from "./recipesModel";
import RecipeLaunch from "./RecipeLaunch";

export default function RecipeCatalog() {
  const { t } = useI18n();
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [selected, setSelected] = useState<Recipe | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const rows = useMemo(() => catalogView(recipes, t), [recipes, t]);

  useEffect(() => {
    void listRecipes().then((items) => { setRecipes(items); setState("ready"); }).catch(() => setState("error"));
  }, []);

  if (state === "loading") return <Loading />;
  if (state === "error") return <ErrorState message={t("recipes.error.load")} />;
  if (selected) return <RecipeLaunch recipe={selected} />;
  return (
    <section className="recipes-screen" aria-labelledby="recipes-title">
      <h1 id="recipes-title">{t("recipes.title")}</h1>
      <div className="recipe-list">
        {rows.map((row) => (
          <article className="recipe-card" key={row.id}>
            <h2>{row.name}</h2>
            <p>{row.description}</p>
            <div className="recipe-badges">
              {row.tiers.map((tier) => <span key={`${row.id}-${tier.kind}`}>{t(tier.labelKey)}: {t(tier.tier === "cloud" ? "recipes.tier.cloud" : "recipes.tier.local")}</span>)}
            </div>
            <button type="button" onClick={() => setSelected(recipes.find((recipe) => recipe.id === row.id) ?? null)}>{t("recipes.launch")}</button>
          </article>
        ))}
      </div>
    </section>
  );
}
