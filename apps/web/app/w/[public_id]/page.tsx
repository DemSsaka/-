"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ContributionPanel } from "@/components/contribution-panel";
import { ItemCard } from "@/components/item-card";
import { useLocale } from "@/components/locale-provider";
import { ReconnectBadge } from "@/components/reconnect-badge";
import { ReserveButton } from "@/components/reserve-button";
import { Skeleton } from "@/components/skeleton";
import { Toast } from "@/components/toast";
import { WishlistHeader } from "@/components/wishlist-header";
import { useWishlistRealtime } from "@/hooks/useWishlistRealtime";
import { api } from "@/lib/api";
import { getViewerToken } from "@/lib/viewer-token";
import { Wishlist } from "@/lib/types";

export default function PublicWishlistPage() {
  const router = useRouter();
  const { public_id } = useParams<{ public_id: string }>();
  const { locale, t } = useLocale();
  const [toast, setToast] = useState("");
  const [busyMap, setBusyMap] = useState<Record<number, boolean>>({});
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    getViewerToken();
  }, []);

  const queryKey = useMemo(() => ["public-wishlist", public_id], [public_id]);
  const { data, isLoading, refetch } = useQuery({
    queryKey,
    queryFn: () => api.get<Wishlist>(`/api/public/w/${public_id}`, true)
  });

  useEffect(() => {
    void api
      .get("/api/auth/me")
      .then(() => setIsAuthed(true))
      .catch(() => setIsAuthed(false));
  }, []);

  const { wsConnected } = useWishlistRealtime(public_id, () => {
    void refetch();
  });

  useEffect(() => {
    if (wsConnected) return;
    const timer = setInterval(() => {
      void refetch();
    }, 10000);
    return () => clearInterval(timer);
  }, [refetch, wsConnected]);

  async function reserve(itemId: number) {
    setBusyMap(s => ({ ...s, [itemId]: true }));
    try {
      await api.post(`/api/public/items/${itemId}/reserve`, { honeypot: "" }, true);
      setToast(locale === "ru" ? "Товар зарезервирован" : "Item reserved");
      await refetch();
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      setBusyMap(s => ({ ...s, [itemId]: false }));
    }
  }

  async function unreserve(itemId: number) {
    setBusyMap(s => ({ ...s, [itemId]: true }));
    try {
      await api.post(`/api/public/items/${itemId}/unreserve`, {}, true);
      setToast(locale === "ru" ? "Резерв снят" : "Reservation removed");
      await refetch();
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      setBusyMap(s => ({ ...s, [itemId]: false }));
    }
  }

  async function contribute(itemId: number, amountCents: number, message: string) {
    setBusyMap(s => ({ ...s, [itemId]: true }));
    try {
      await api.post(
        `/api/public/items/${itemId}/contribute`,
        { amount_cents: amountCents, message, honeypot: "" },
        true
      );
      setToast(locale === "ru" ? "Вклад добавлен" : "Contribution added");
      window.dispatchEvent(new CustomEvent("profile:refresh"));
      await refetch();
    } catch (e) {
      const msg = (e as Error).message;
      if (msg.toLowerCase().includes("not authenticated")) {
        setToast(t("signInToContribute"));
        setTimeout(() => {
          window.location.href = "/";
        }, 800);
      } else {
        setToast(msg);
      }
    } finally {
      setBusyMap(s => ({ ...s, [itemId]: false }));
    }
  }

  if (isLoading) {
    return (
      <main className="mx-auto max-w-5xl space-y-4 px-4 py-8">
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-44" />
      </main>
    );
  }

  if (!data) {
    return <main className="p-8">{t("wishlistNotFound")}</main>;
  }

  return (
    <main className="mx-auto max-w-5xl space-y-5 px-4 py-8">
      <button className="btn-secondary" onClick={() => router.back()}>{t("back")}</button>
      <WishlistHeader title={data.title} />
      <ReconnectBadge connected={wsConnected} />

      {data.items.length === 0 ? (
        <section className="card p-10 text-center">
          <h2 className="text-xl font-semibold">{t("noItemsYet")}</h2>
          <p className="mt-2 text-slate-600">{t("checkLater")}</p>
        </section>
      ) : (
        <section className="grid gap-3">
          {data.items
            .filter(item => !item.is_archived)
            .map(item => (
              <ItemCard
                key={item.id}
                item={item}
                currency={data.currency}
                publicMode
                actions={
                  <div className="space-y-2">
                    <ReserveButton
                      reserved={item.reserved}
                      canUnreserve={item.reserved_by_me}
                      onReserve={() => reserve(item.id)}
                      onUnreserve={() => unreserve(item.id)}
                      busy={Boolean(busyMap[item.id])}
                    />
                    {item.allow_contributions ? (
                      <ContributionPanel
                        onSubmit={(amount, msg) => contribute(item.id, amount, msg)}
                        busy={Boolean(busyMap[item.id])}
                        disabled={!isAuthed || item.collected_cents >= item.price_cents}
                      />
                    ) : null}
                    {!isAuthed && item.allow_contributions ? (
                      <p className="text-xs text-slate-500">{t("signInToContribute")}</p>
                    ) : null}
                  </div>
                }
              />
            ))}
        </section>
      )}

      {toast ? <Toast message={toast} onDone={() => setToast("")} /> : null}
    </main>
  );
}
