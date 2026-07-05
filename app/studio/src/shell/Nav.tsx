import type { KeyboardEvent } from "react";
import { useI18n } from "../i18n/I18nProvider";
import { navigate, routes } from "./router";
import type { RouteId } from "./router";

export default function Nav({ activeId }: { activeId: RouteId | null }) {
  const { t } = useI18n();
  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    event.preventDefault();
    const links = Array.from(event.currentTarget.querySelectorAll<HTMLAnchorElement>("a"));
    const i = links.findIndex((link) => link === document.activeElement);
    const next = event.key === "ArrowRight" ? i + 1 : i - 1;
    links[(next + links.length) % links.length]?.focus();
  };
  return (
    <nav className="shell-nav" aria-label="Studio" onKeyDown={onKeyDown}>
      {routes.map((route, index) => (
        <a
          key={route.id}
          href={route.hash}
          aria-current={activeId === route.id ? "page" : undefined}
          // Roving tabindex; when no route is active (not-found), the first link keeps
          // the tab stop so the nav never becomes keyboard-unreachable.
          tabIndex={activeId === route.id || (activeId === null && index === 0) ? 0 : -1}
          onClick={(event) => {
            // Respect modified clicks (new tab/window) — only plain left clicks route in-app.
            if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
            event.preventDefault();
            navigate(route.hash);
          }}
        >
          {t(route.titleKey)}
        </a>
      ))}
    </nav>
  );
}
