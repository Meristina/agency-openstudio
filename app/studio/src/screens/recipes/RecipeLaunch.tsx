import { useMemo, useState } from "react";
import { useI18n } from "../../i18n/I18nProvider";
import { navigate } from "../../shell/router";
import { missionSession } from "../session/missionSession";
import type { Recipe } from "./recipesApi";
import { stageTierBadges } from "./recipesModel";

export default function RecipeLaunch({ recipe }: { recipe: Recipe }) {
  const { t } = useI18n();
  const [subject, setSubject] = useState("");
  const [cloudOptins, setCloudOptins] = useState<string[]>([]);
  const tiers = useMemo(() => stageTierBadges(recipe), [recipe]);
  function launch() {
    if (!subject.trim()) return;
    // Kick off the run (missionSession publishes live state) and go straight to the unified
    // timeline so the user follows the whole run there — don't block until the stream ends.
    void missionSession.launchRecipe(recipe.id, subject.trim(), cloudOptins);
    navigate("#/missions");
  }
  return (
    <section className="recipes-screen" aria-labelledby="recipe-launch-title">
      <h1 id="recipe-launch-title">{t(recipe.name_key)}</h1>
      <label className="recipes-subject">
        <span>{t("recipes.input.subject")}</span>
        <textarea value={subject} onChange={(event) => setSubject(event.target.value)} rows={4} />
      </label>
      {tiers.map((tier) => (
        <label key={tier.kind} className="recipes-optin">
          <input
            type="checkbox"
            checked={cloudOptins.includes(tier.kind)}
            disabled={tier.tier !== "cloud"}
            onChange={(event) => setCloudOptins((items) => event.target.checked ? [...items, tier.kind] : items.filter((item) => item !== tier.kind))}
          />
          <span>{t(tier.labelKey)}: {t(tier.tier === "cloud" ? "recipes.tier.cloud" : "recipes.tier.local")}</span>
        </label>
      ))}
      <button type="button" onClick={launch}>{t("recipes.launch")}</button>
    </section>
  );
}
