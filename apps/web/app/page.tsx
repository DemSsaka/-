"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Toast } from "@/components/toast";
import { api } from "@/lib/api";
import { useLocale } from "@/components/locale-provider";

export default function HomePage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [toast, setToast] = useState("");
  const [busy, setBusy] = useState(false);
  const { locale } = useLocale();
  const googleUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/auth/google/start`;

  useEffect(() => {
    if (typeof window === "undefined") return;
    const search = new URLSearchParams(window.location.search);
    const oauthError = search.get("oauth_error");
    if (!oauthError) return;
    if (oauthError === "google_not_configured") {
      setToast(locale === "ru" ? "Google OAuth не настроен на сервере" : "Google OAuth is not configured on server");
      return;
    }
    setToast(locale === "ru" ? "Ошибка входа через Google" : "Google sign-in failed");
  }, [locale]);

  async function submit() {
    setBusy(true);
    try {
      await api.post(`/api/auth/${mode}`, { email, password });
      setToast(mode === "login" ? (locale === "ru" ? "С возвращением" : "Welcome back") : (locale === "ru" ? "Аккаунт создан" : "Account created"));
      window.location.href = "/app";
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto grid min-h-screen max-w-6xl grid-cols-1 gap-8 px-4 py-10 lg:grid-cols-2 lg:items-center">
      <section className="space-y-5">
        <p className="inline-flex rounded-full bg-brand-100 px-4 py-1 text-sm font-semibold text-brand-900">
          {locale === "ru" ? "Готово к использованию" : "Production-ready gifting"}
        </p>
        <h1 className="text-5xl font-black leading-tight text-[var(--text)]">Social Wishlist</h1>
        <p className="max-w-lg text-lg text-slate-700">
          {locale === "ru"
            ? "Создавайте вишлисты, делитесь одной публичной ссылкой, избегайте дублей подарков и собирайте деньги вместе в реальном времени."
            : "Build curated wishlists, share one public link, avoid duplicate gifts with reservation, and fund big-ticket gifts together in real time."}
        </p>
        <div className="grid gap-3 text-sm text-slate-700 sm:grid-cols-2">
          <div className="card p-3">{locale === "ru" ? "Реалтайм обновления брони" : "Realtime reservation updates"}</div>
          <div className="card p-3">{locale === "ru" ? "Анонимные взносы" : "Anonymous contribution privacy"}</div>
          <div className="card p-3">{locale === "ru" ? "Публичная ссылка без регистрации" : "Public link without registration"}</div>
          <div className="card p-3">{locale === "ru" ? "Адаптивный интерфейс" : "Mobile-first and accessible UX"}</div>
        </div>
      </section>

      <section className="card p-6">
        <div className="mb-5 flex gap-2">
          <button className={mode === "login" ? "btn-primary" : "btn-secondary"} onClick={() => setMode("login")}>{locale === "ru" ? "Вход" : "Login"}</button>
          <button className={mode === "register" ? "btn-primary" : "btn-secondary"} onClick={() => setMode("register")}>{locale === "ru" ? "Регистрация" : "Register"}</button>
        </div>

        <div className="space-y-3">
          <label className="block text-sm font-medium">Email</label>
          <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} />
          <label className="block text-sm font-medium">{locale === "ru" ? "Пароль" : "Password"}</label>
          <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} />
          <button className="btn-primary w-full" disabled={busy} onClick={submit}>
            {busy ? (locale === "ru" ? "Подождите..." : "Please wait...") : mode === "login" ? (locale === "ru" ? "Войти" : "Sign in") : (locale === "ru" ? "Создать аккаунт" : "Create account")}
          </button>
          <a className="btn-secondary block text-center" href={googleUrl}>
            {locale === "ru" ? "Войти через Google" : "Continue with Google"}
          </a>
          <p className="text-xs text-slate-500">{locale === "ru" ? "Безопасная cookie авторизация с refresh flow и CSRF." : "Secure cookie auth with refresh flow and CSRF token support."}</p>
          <p className="text-xs text-slate-500">
            {locale === "ru" ? "Пример публичной ссылки: " : "Demo public view route pattern: "}<Link href="/w/example" className="underline">/w/&lt;public_id&gt;</Link>
          </p>
        </div>
      </section>

      {toast ? <Toast message={toast} onDone={() => setToast("")} /> : null}
    </main>
  );
}
