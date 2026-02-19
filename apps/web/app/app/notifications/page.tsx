"use client";

import { useEffect, useState } from "react";

import { useLocale } from "@/components/locale-provider";
import { api } from "@/lib/api";
import { NotificationItem } from "@/lib/types";

export default function NotificationsPage() {
  const { locale, t } = useLocale();
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    try {
      setError("");
      const data = await api.get<NotificationItem[]>("/api/notifications");
      setItems(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void (async () => {
      await api.post("/api/notifications/read-all", {});
      window.dispatchEvent(new CustomEvent("profile:refresh"));
      await load();
    })();
  }, []);

  useEffect(() => {
    const wsBase = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace("http", "ws");
    let socket: WebSocket | null = null;
    let retryTimer: number | null = null;

    const connect = () => {
      socket = new WebSocket(`${wsBase}/ws/notifications`);
      socket.onmessage = () => {
        void load();
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
  }, []);

  async function clearAll() {
    try {
      await api.delete("/api/notifications");
      setItems([]);
      window.dispatchEvent(new CustomEvent("profile:refresh"));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <main className="mx-auto max-w-4xl space-y-5 px-4 py-8">
      <header className="flex items-center justify-between">
        <h1 className="text-3xl font-black">{t("notificationsPage")}</h1>
        {items.length > 0 ? (
          <button className="btn-secondary" type="button" onClick={clearAll}>
            {t("clearNotifications")}
          </button>
        ) : null}
      </header>
      {loading ? <section className="card p-6">{t("loading")}</section> : null}
      {error ? <section className="card p-6 text-red-600">{error}</section> : null}
      {!loading && !error && items.length === 0 ? <section className="card p-6">{t("noNotifications")}</section> : null}
      {!loading && !error && items.length > 0 ? (
        <section className="space-y-3">
          {items.map(item => (
            <article key={item.id} className="card p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold">{item.title}</h2>
                  <p className="mt-1 text-sm">{item.body ?? (locale === "ru" ? "Без комментария" : "No comment")}</p>
                </div>
                {!item.read_at ? (
                  <span className="rounded-full bg-brand-100 px-2 py-1 text-xs font-semibold text-brand-900">
                    {locale === "ru" ? "Новое" : "New"}
                  </span>
                ) : null}
              </div>
            </article>
          ))}
        </section>
      ) : null}
    </main>
  );
}
