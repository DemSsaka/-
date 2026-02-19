"use client";

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";

import { Locale, messages } from "@/lib/i18n";

type LocaleCtx = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: keyof (typeof messages)["ru"]) => string;
};

const LocaleContext = createContext<LocaleCtx | null>(null);
const STORAGE_KEY = "wishlist_locale";

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("ru");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "ru" || stored === "en") {
      setLocaleState(stored);
      return;
    }
    setLocaleState(navigator.language.toLowerCase().startsWith("ru") ? "ru" : "en");
  }, []);

  const setLocale = (next: Locale) => {
    setLocaleState(next);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, next);
      document.documentElement.setAttribute("data-locale-switch", "1");
      window.setTimeout(() => {
        document.documentElement.removeAttribute("data-locale-switch");
      }, 280);
    }
  };

  const value = useMemo<LocaleCtx>(() => {
    return {
      locale,
      setLocale,
      t: key => messages[locale][key]
    };
  }, [locale]);

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale() {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error("useLocale must be used within LocaleProvider");
  return ctx;
}
