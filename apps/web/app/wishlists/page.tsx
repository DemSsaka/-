"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useLocale } from "@/components/locale-provider";
import { Skeleton } from "@/components/skeleton";
import { api } from "@/lib/api";
import { PublicWishlistSummary, WishlistSummary } from "@/lib/types";

type WishlistListRow = {
  public_id: string;
  title: string;
  author_name: string;
  currency: string;
  item_count: number;
  isMine: boolean;
  isPublic: boolean;
};

export default function PublicWishlistsPage() {
  const { locale, t } = useLocale();
  const [wishlists, setWishlists] = useState<WishlistListRow[]>([]);
  const [authorQuery, setAuthorQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      setLoading(true);
      setError("");

      const [publicResult, mineResult] = await Promise.allSettled([
        api.get<PublicWishlistSummary[]>("/api/public/wishlists"),
        api.get<WishlistSummary[]>("/api/wishlists")
      ]);

      const rows = new Map<string, WishlistListRow>();

      if (publicResult.status === "fulfilled") {
        for (const w of publicResult.value) {
          rows.set(w.public_id, {
            public_id: w.public_id,
            title: w.title,
            author_name: w.author_name,
            currency: w.currency,
            item_count: w.item_count,
            isMine: false,
            isPublic: true
          });
        }
      }

      if (mineResult.status === "fulfilled") {
        for (const w of mineResult.value) {
          const existing = rows.get(w.public_id);
          rows.set(w.public_id, {
            public_id: w.public_id,
            title: w.title,
            author_name: existing?.author_name || "You",
            currency: w.currency,
            item_count: w.item_count,
            isMine: true,
            isPublic: w.is_public || existing?.isPublic || false
          });
        }
      }

      if (publicResult.status === "rejected" && mineResult.status === "rejected") {
        setError(locale === "ru" ? "Не удалось загрузить вишлисты. Попробуй обновить страницу." : "Failed to load wishlists. Please refresh.");
      }

      setWishlists(Array.from(rows.values()));
      setLoading(false);
    })();
  }, [locale]);

  const filteredWishlists = wishlists.filter(w =>
    w.author_name.toLowerCase().includes(authorQuery.trim().toLowerCase())
  );

  return (
    <main className="mx-auto max-w-5xl space-y-5 px-4 py-8">
      <header className="flex items-center justify-between">
        <h1 className="text-3xl font-black">{locale === "ru" ? "Все публичные вишлисты" : "All public wishlists"}</h1>
      </header>
      <section className="card p-4">
        <input
          className="input"
          placeholder={t("searchByAuthor")}
          value={authorQuery}
          onChange={e => setAuthorQuery(e.target.value)}
        />
      </section>

      {loading ? (
        <Skeleton className="h-24" />
      ) : error ? (
        <section className="card p-8 text-center text-red-700">{error}</section>
      ) : filteredWishlists.length === 0 ? (
        <section className="card p-10 text-center">
          <h2 className="text-xl font-semibold">
            {authorQuery.trim()
              ? (locale === "ru" ? "Ничего не найдено" : "No matches found")
              : (locale === "ru" ? "Пока нет публичных вишлистов" : "No public wishlists yet")}
          </h2>
          <p className="mt-2 text-slate-600">
            {authorQuery.trim()
              ? (locale === "ru" ? "Попробуй другой ник автора." : "Try another author nickname.")
              : (locale === "ru" ? "Создай первый вишлист на странице “Мои вишлисты”." : "Create your first wishlist on the My Wishlists page.")}
          </p>
        </section>
      ) : (
        <section className="grid gap-3">
          {filteredWishlists.map(w => (
            <article key={w.public_id} className="card flex items-center justify-between p-4">
              <div>
                <h2 className="text-lg font-semibold">{w.title}</h2>
                <p className="text-sm text-slate-600">
                  {t("author")}: {w.author_name} •{" "}
                  {w.item_count} {locale === "ru" ? "тов." : "items"} • {w.currency}
                  {w.isMine ? (locale === "ru" ? " • Мой" : " • Mine") : ""}
                  {w.isPublic ? " • Public" : (locale === "ru" ? " • Приватный" : " • Private")}
                </p>
              </div>
              <Link className="btn-primary" href={`/w/${w.public_id}`}>{locale === "ru" ? "Открыть" : "Open"}</Link>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
