import { FormEvent, useState } from "react";
import { useI18n } from "../../i18n/I18nProvider";
import { navigate } from "../../shell/router";

export default function StartSection() {
  const { t } = useI18n();
  const [intent, setIntent] = useState("");
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const qs = intent.trim() ? `?intent=${encodeURIComponent(intent.trim())}` : "";
    navigate(`#/brief${qs}`);
  };
  return (
    <section className="home-start" aria-labelledby="home-start-title">
      <h1 id="home-start-title">{t("home.question")}</h1>
      <form className="intent-form" onSubmit={submit}>
        <label>
          <span>{t("home.intentLabel")}</span>
          <textarea value={intent} onChange={(event) => setIntent(event.target.value)} placeholder={t("home.intentPlaceholder")} rows={4} />
        </label>
        <button type="submit">{t("home.start")}</button>
      </form>
    </section>
  );
}
