import { useI18n } from "../../i18n/I18nProvider";
import { navigate } from "../../shell/router";

export default function ShortcutsSection() {
  const { t } = useI18n();
  const shortcuts = [
    ["#/library", "home.shortcuts.library"],
    ["#/import", "home.shortcuts.import"],
    ["#/models", "home.shortcuts.models"],
  ] as const;
  return (
    <section className="home-panel" aria-labelledby="home-shortcuts-title">
      <h2 id="home-shortcuts-title">{t("home.shortcuts.title")}</h2>
      <div className="home-shortcuts">
        {shortcuts.map(([target, label]) => (
          <button key={target} type="button" onClick={() => navigate(target)}>{t(label)}</button>
        ))}
      </div>
    </section>
  );
}
