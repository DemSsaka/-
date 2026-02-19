"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useLocale } from "@/components/locale-provider";
import { Toast } from "@/components/toast";
import { api } from "@/lib/api";
import { WishlistSummary } from "@/lib/types";

export default function DashboardPage() {
  const [wishlists, setWishlists] = useState<WishlistSummary[]>([]);
  const [title, setTitle] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [toast, setToast] = useState("");
  const { locale, t } = useLocale();

  async function load() {
    try {
      const data = await api.get<WishlistSummary[]>("/api/wishlists");
      setWishlists(data);
    } catch {
      window.location.href = "/";
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function createWishlist() {
    try {
      await api.post("/api/wishlists", { title, currency, is_public: true });
      setTitle("");
      setToast(locale === "ru" ? "Вишлист создан" : "Wishlist created");
      await load();
    } catch (e) {
      setToast((e as Error).message);
    }
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-5xl font-black tracking-tight">{t("yourWishlists")}</h1>
      </header>

      <section className="card grid gap-3 p-4 sm:grid-cols-[1fr_140px_auto]">
        <input className="input" placeholder={locale === "ru" ? "Вишлист на день рождения" : "Birthday wishlist"} value={title} onChange={e => setTitle(e.target.value)} />
        <select className="input" value={currency} onChange={e => setCurrency(e.target.value)}>
          <option value="USD">USD</option>
          <option value="EUR">EUR</option>
          <option value="GBP">GBP</option>
          <option value="RUB">RUB</option>
        </select>
        <button className="btn-primary" onClick={createWishlist}>{t("createWishlist")}</button>
      </section>

      {wishlists.length === 0 ? (
        <section className="card p-10 text-center">
          <h2 className="text-xl font-semibold">{t("noWishlists")}</h2>
          <p className="mt-2 text-slate-600">{locale === "ru" ? "Создайте первый вишлист, чтобы делиться подарками." : "Create your first wishlist to start sharing gifts with friends."}</p>
        </section>
      ) : (
        <section className="grid gap-3">
          {wishlists.map(w => (
            <article key={w.id} className="card flex items-center justify-between p-4">
              <div>
                <h3 className="text-lg font-semibold">{w.title}</h3>
                <p className="text-sm text-slate-600">{w.item_count} {locale === "ru" ? "тов." : `item${w.item_count === 1 ? "" : "s"}`} • {w.currency} • {w.is_public ? (locale === "ru" ? "Публичный" : "Public") : (locale === "ru" ? "Приватный" : "Private")}</p>
              </div>
              <div className="flex gap-2">
                <Link className="btn-secondary" href={`/w/${w.public_id}`}>{t("publicView")}</Link>
                <Link className="btn-primary" href={`/app/w/${w.id}`}>{t("manage")}</Link>
              </div>
            </article>
          ))}
        </section>
      )}

      {toast ? <Toast message={toast} onDone={() => setToast("")} /> : null}
    </main>
  );
}
