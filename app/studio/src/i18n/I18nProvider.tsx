import { createContext, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { en } from "./en";
import { fr } from "./fr";
import { PREFS_KEY } from "./catalog";
import type { CatalogKey, Locale } from "./catalog";

interface UserPrefs {
  locale?: Locale;
  clientContext?: { client?: string; project?: string; campaign?: string };
}

interface I18nValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: CatalogKey, params?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nValue | null>(null);
const catalogs: Record<Locale, Record<CatalogKey, string>> = { en, fr };

export function readPrefs(): UserPrefs {
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return {};
    return parsed as UserPrefs;
  } catch {
    return {};
  }
}

export function writePrefs(next: UserPrefs): void {
  localStorage.setItem(PREFS_KEY, JSON.stringify({ ...readPrefs(), ...next }));
}

function defaultLocale(): Locale {
  const saved = readPrefs().locale;
  if (saved === "en" || saved === "fr") return saved;
  return navigator.language.toLowerCase().startsWith("fr") ? "fr" : "en";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);
  const value = useMemo<I18nValue>(() => ({
    locale,
    setLocale(next) {
      setLocaleState(next);
      writePrefs({ locale: next });
    },
    t(key, params) {
      const template = catalogs[locale][key] || en[key];
      return Object.entries(params ?? {}).reduce((text, [name, value]) => text.replaceAll(`{${name}}`, String(value)), template);
    },
  }), [locale]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n must be used inside I18nProvider");
  return value;
}
