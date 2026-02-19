import { Currency } from "./types";

export function formatMoney(cents: number, currency: Currency): string {
  const locale = currency === "RUB" ? "ru-RU" : "en-US";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2
  }).format(cents / 100);
}

export function formatMoneyByLocale(cents: number, currency: Currency, locale: "ru" | "en"): string {
  const intlLocale = locale === "ru" ? "ru-RU" : "en-US";
  return new Intl.NumberFormat(intlLocale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2
  }).format(cents / 100);
}
