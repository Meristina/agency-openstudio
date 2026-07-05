import type { ReactNode } from "react";
import { useI18n } from "../i18n/I18nProvider";
import type { CatalogKey } from "../i18n/catalog";
import { navigate } from "../shell/router";

function State({ title, body, action }: { title: ReactNode; body?: ReactNode; action?: ReactNode }) {
  return (
    <section className="state-panel">
      <h1>{title}</h1>
      {body && <p>{body}</p>}
      {action}
    </section>
  );
}

export function Loading() {
  const { t } = useI18n();
  return <State title={t("state.loading")} />;
}

export function Empty() {
  const { t } = useI18n();
  return <State title={t("state.empty")} />;
}

export function ErrorState({ message }: { message?: string }) {
  const { t } = useI18n();
  return <State title={t("state.error")} body={message} />;
}

export function ComingSoon({ titleKey, bodyKey }: { titleKey: CatalogKey; bodyKey?: CatalogKey }) {
  const { t } = useI18n();
  const title = t(titleKey);
  return (
    <State
      title={t("state.comingSoon.title", { title })}
      body={bodyKey ? t(bodyKey) : t("state.comingSoon.body")}
      action={<button onClick={() => navigate("#/")}>{t("state.backHome")}</button>}
    />
  );
}

export function NotFound() {
  const { t } = useI18n();
  return (
    <State
      title={t("state.notFound.title")}
      body={t("state.notFound.body")}
      action={<button onClick={() => navigate("#/")}>{t("state.backHome")}</button>}
    />
  );
}
