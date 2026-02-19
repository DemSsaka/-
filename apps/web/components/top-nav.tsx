"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { api } from "@/lib/api";
import { Currency, UserProfile } from "@/lib/types";
import { useTheme } from "@/components/theme-provider";
import { formatMoney } from "@/lib/format";
import { Toast } from "@/components/toast";
import { useLocale } from "@/components/locale-provider";

type AuthState = "loading" | "authed" | "guest";

export function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [authState, setAuthState] = useState<AuthState>("loading");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [toast, setToast] = useState("");
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [balanceCurrency, setBalanceCurrency] = useState<Currency>("USD");
  const [rates, setRates] = useState<Record<string, number>>({ USD: 1 });
  const menuRef = useRef<HTMLDivElement | null>(null);
  const { theme, setTheme } = useTheme();
  const { locale, setLocale, t } = useLocale();

  const refreshProfile = useCallback(async () => {
    try {
      const me = await api.get<UserProfile>("/api/auth/me");
      setUser(me);
      setAuthState("authed");
      if (me.theme === "dark" || me.theme === "light") {
        setTheme(me.theme);
      }
      return me;
    } catch {
      setUser(null);
      setAuthState("guest");
      return null;
    }
  }, [setTheme]);

  useEffect(() => {
    void refreshProfile();
  }, [pathname, refreshProfile]);

  useEffect(() => {
    if (authState !== "authed") return;
    const handler = () => {
      void refreshProfile();
      void api
        .get<{ unread: number }>("/api/notifications/unread-count")
        .then(data => setUnreadNotifications(data.unread))
        .catch(() => setUnreadNotifications(0));
    };
    window.addEventListener("profile:refresh", handler as EventListener);
    const timer = window.setInterval(() => {
      void refreshProfile();
    }, 10000);
    return () => {
      window.removeEventListener("profile:refresh", handler as EventListener);
      window.clearInterval(timer);
    };
  }, [authState, refreshProfile]);

  useEffect(() => {
    if (authState !== "authed") {
      setUnreadNotifications(0);
      return;
    }
    let active = true;
    api
      .get<{ unread: number }>("/api/notifications/unread-count")
      .then(data => {
        if (active) setUnreadNotifications(data.unread);
      })
      .catch(() => {
        if (active) setUnreadNotifications(0);
      });
    return () => {
      active = false;
    };
  }, [authState, pathname]);

  useEffect(() => {
    if (authState !== "authed") return;
    const wsBase = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace("http", "ws");
    let socket: WebSocket | null = null;
    let retryTimer: number | null = null;

    const connect = () => {
      socket = new WebSocket(`${wsBase}/ws/notifications`);
      socket.onmessage = () => {
        void refreshProfile();
        void api
          .get<{ unread: number }>("/api/notifications/unread-count")
          .then(data => setUnreadNotifications(data.unread))
          .catch(() => setUnreadNotifications(0));
      };
      socket.onclose = () => {
        retryTimer = window.setTimeout(connect, 3000);
      };
    };

    connect();
    return () => {
      if (retryTimer) window.clearTimeout(retryTimer);
      socket?.close();
    };
  }, [authState, refreshProfile]);

  useEffect(() => {
    const stored = localStorage.getItem("wishlist_balance_currency");
    if (stored === "USD" || stored === "EUR" || stored === "GBP" || stored === "RUB") {
      setBalanceCurrency(stored);
    }
  }, []);

  useEffect(() => {
    if (authState !== "authed") return;
    api
      .get<{ base: string; rates: Record<string, number> }>("/api/fx/rates")
      .then(data => {
        setRates(data.rates || { USD: 1 });
      })
      .catch(() => {
        setRates({ USD: 1, EUR: 0.92, GBP: 0.79, RUB: 76.6 });
      });
  }, [authState, pathname]);

  useEffect(() => {
    if (!menuOpen) return;
    function handleOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    window.addEventListener("mousedown", handleOutside);
    return () => window.removeEventListener("mousedown", handleOutside);
  }, [menuOpen]);

  const avatarLabel = useMemo(() => {
    if (!user) return "U";
    return (user.nickname || user.email).trim().charAt(0).toUpperCase();
  }, [user]);

  const isAuthPage = pathname === "/";
  const isAllWishlistsPage = pathname === "/wishlists";
  const localeFlag = locale === "ru" ? "🇷🇺" : "🇬🇧";

  const convertedBalanceCents = useMemo(() => {
    const usdCents = user?.balance_cents ?? 0;
    if (balanceCurrency === "USD") return usdCents;
    const rate = rates[balanceCurrency];
    if (!rate) return usdCents;
    return Math.round((usdCents / 100) * rate * 100);
  }, [balanceCurrency, rates, user?.balance_cents]);

  async function logout() {
    try {
      await api.post("/api/auth/logout", {});
    } catch {
      // ignore
    } finally {
      setMenuOpen(false);
      router.push("/");
      router.refresh();
    }
  }

  return (
    <nav className="top-nav-light fixed inset-x-0 top-0 z-50 border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-4">
        {isAuthPage ? (
          <div className="flex items-center gap-2 text-xl font-semibold text-slate-900">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-slate-950 text-sm font-black text-white">
              S
            </span>
            <span>Social Wishlist</span>
          </div>
        ) : (
          <button
            type="button"
            className="flex items-center gap-2 text-xl font-semibold text-slate-900"
            onClick={() => router.push(authState === "authed" ? "/app" : "/")}
          >
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-slate-950 text-sm font-black text-white">
              S
            </span>
            <span>Social Wishlist</span>
          </button>
        )}
        <div className="flex flex-wrap items-center gap-2">
          {isAuthPage ? (
            <button
              className="btn-secondary"
              type="button"
              onClick={() => setLocale(locale === "ru" ? "en" : "ru")}
            >
              {t("language")}: {locale === "ru" ? "RU" : "EN"} {localeFlag}
            </button>
          ) : null}
          {!isAuthPage && !isAllWishlistsPage ? (
            <Link className="btn-secondary" href="/wishlists">
              {t("allWishlists")}
            </Link>
          ) : null}
          {authState === "guest" && !isAuthPage ? (
            <Link className="btn-primary" href="/">
              {t("signIn")}
            </Link>
          ) : null}
          {authState === "authed" && !isAuthPage ? (
            <div className="relative" ref={menuRef}>
              <button
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-300 bg-white text-sm font-bold text-slate-700 hover:bg-slate-50"
                onClick={() => setMenuOpen(v => !v)}
              >
                {user?.avatar_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={user.avatar_url} alt="Avatar" className="h-full w-full rounded-full object-cover" />
                ) : (
                  avatarLabel
                )}
              </button>
              {menuOpen ? (
                <div className="absolute right-0 mt-2 w-64 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl">
                  <div className="mb-2 border-b border-slate-200 pb-2">
                    <p className="text-sm font-semibold text-slate-900">{user?.nickname || user?.email}</p>
                    <p className="text-xs text-slate-500">{user?.email}</p>
                  </div>
                  <div className="grid gap-2 text-sm">
                    <Link className="btn-secondary text-left" href="/app">
                      {t("myWishlists")}
                    </Link>
                    <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 font-medium text-slate-700">
                      <button
                        type="button"
                        className="w-full text-left"
                        onClick={() => {
                          const order: Currency[] = ["USD", "EUR", "GBP", "RUB"];
                          const idx = order.indexOf(balanceCurrency);
                          const next = order[(idx + 1) % order.length];
                          setBalanceCurrency(next);
                          localStorage.setItem("wishlist_balance_currency", next);
                        }}
                      >
                        {t("balance")}: {formatMoney(convertedBalanceCents, balanceCurrency)} ({balanceCurrency})
                      </button>
                    </div>
                    <Link className="btn-secondary text-left" href="/app/notifications">
                      {t("notifications")} {unreadNotifications > 0 ? `(${unreadNotifications})` : ""}
                    </Link>
                    <button
                      className="btn-secondary text-left"
                      type="button"
                      onClick={() => setToast(t("topUpSoon"))}
                    >
                      {t("topUp")}
                    </button>
                    <button
                      className="btn-secondary text-left"
                      type="button"
                      onClick={() => setToast(t("withdrawSoon"))}
                    >
                      {locale === "ru" ? "Вывести деньги" : "Withdraw"}
                    </button>
                    <Link className="btn-secondary text-left" href="/app/settings">
                      {t("settings")}
                    </Link>
                    <button
                      className="btn-secondary text-left"
                      type="button"
                      onClick={async () => {
                        const nextTheme = theme === "dark" ? "light" : "dark";
                        setTheme(nextTheme);
                        try {
                          await api.patch<UserProfile>("/api/profile/me", { theme: nextTheme });
                          setToast(nextTheme === "dark" ? `${t("themeDark")} ON` : `${t("themeLight")} ON`);
                        } catch {
                          setToast("Theme save failed");
                        }
                      }}
                    >
                      {t("themeLabel")}: {theme === "dark" ? t("themeDark") : t("themeLight")}
                    </button>
                    <button
                      className="btn-secondary text-left"
                      type="button"
                      onClick={() => setLocale(locale === "ru" ? "en" : "ru")}
                    >
                      {t("language")}: {locale === "ru" ? "RU" : "EN"} {localeFlag}
                    </button>
                    <button className="btn-secondary text-left" type="button" onClick={logout}>
                      {t("logout")}
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
      {toast ? <Toast message={toast} onDone={() => setToast("")} /> : null}
    </nav>
  );
}
