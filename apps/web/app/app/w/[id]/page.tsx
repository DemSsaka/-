"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ItemCard } from "@/components/item-card";
import { useLocale } from "@/components/locale-provider";
import { ReconnectBadge } from "@/components/reconnect-badge";
import { Skeleton } from "@/components/skeleton";
import { Toast } from "@/components/toast";
import { WishlistHeader } from "@/components/wishlist-header";
import { useWishlistRealtime } from "@/hooks/useWishlistRealtime";
import { api } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import { Item, Wishlist } from "@/lib/types";

type Currency = "USD" | "EUR" | "GBP" | "RUB";

type OgParseResponse = {
  title: string | null;
  image_url: string | null;
  price_cents: number | null;
  currency: string | null;
  cached: boolean;
  warning?: string | null;
};

function centsFromInput(value: string): number {
  return Math.round(Number(value || "0") * 100);
}

function inputFromCents(cents: number): string {
  return (cents / 100).toFixed(2);
}

export default function OwnerWishlistPage() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const { locale, t } = useLocale();

  const [toast, setToast] = useState("");
  const [origin, setOrigin] = useState("");
  const [showArchived, setShowArchived] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [currency, setCurrency] = useState<Currency>("USD");
  const [isPublic, setIsPublic] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);

  const [newItemName, setNewItemName] = useState("");
  const [newItemPrice, setNewItemPrice] = useState("99.00");
  const [newItemUrl, setNewItemUrl] = useState("");
  const [newItemImageUrl, setNewItemImageUrl] = useState("");
  const [newItemNotes, setNewItemNotes] = useState("");
  const [allowContrib, setAllowContrib] = useState(true);
  const [creatingItem, setCreatingItem] = useState(false);
  const [uploadingNewImage, setUploadingNewImage] = useState(false);
  const [autofillLoading, setAutofillLoading] = useState(false);
  const [autofillCurrencyHint, setAutofillCurrencyHint] = useState<string | null>(null);
  const [autofillCached, setAutofillCached] = useState(false);

  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editPrice, setEditPrice] = useState("0.00");
  const [editUrl, setEditUrl] = useState("");
  const [editImageUrl, setEditImageUrl] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editAllowContrib, setEditAllowContrib] = useState(true);
  const [savingItem, setSavingItem] = useState(false);
  const [uploadingEditImage, setUploadingEditImage] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setOrigin(window.location.origin);
    }
  }, []);

  const queryKey = useMemo(() => ["owner-wishlist", id], [id]);
  const { data, isLoading, refetch } = useQuery({
    queryKey,
    queryFn: () => api.get<Wishlist>(`/api/wishlists/${id}`)
  });

  useEffect(() => {
    if (!data) return;
    setTitle(data.title);
    setDescription(data.description ?? "");
    setCurrency(data.currency);
    setIsPublic(data.is_public);
  }, [data]);

  const { wsConnected } = useWishlistRealtime(data?.public_id ?? "", () => {
    void refetch();
  });

  const activeItems = useMemo(() => data?.items.filter(item => !item.is_archived) ?? [], [data]);
  const archivedItems = useMemo(() => data?.items.filter(item => item.is_archived) ?? [], [data]);

  async function saveWishlistSettings() {
    if (!data) return;
    setSavingSettings(true);
    try {
      await api.patch(`/api/wishlists/${data.id}`, {
        title,
        description,
        currency,
        is_public: isPublic
      });
      setToast(t("settingsSaved"));
      await refetch();
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      setSavingSettings(false);
    }
  }

  async function autofillFromUrl() {
    if (!newItemUrl.trim()) {
      setToast(t("pasteUrlFirst"));
      return;
    }

    setAutofillLoading(true);
    setAutofillCurrencyHint(null);
    setAutofillCached(false);

    try {
      const parsed = await api.post<OgParseResponse>("/api/og/parse", { url: newItemUrl.trim() });
      if (parsed.title) setNewItemName(parsed.title);
      if (parsed.image_url) setNewItemImageUrl(parsed.image_url);
      if (parsed.price_cents && parsed.price_cents > 0) setNewItemPrice(inputFromCents(parsed.price_cents));
      if (parsed.currency) setAutofillCurrencyHint(parsed.currency);
      setAutofillCached(Boolean(parsed.cached));
      if (parsed.warning) {
        setToast(parsed.warning);
      } else {
        setToast(parsed.cached ? t("autofillAppliedCached") : t("autofillApplied"));
      }
    } catch (e) {
      setToast(`${t("autofillFailed")}: ${(e as Error).message}`);
    } finally {
      setAutofillLoading(false);
    }
  }

  async function createItem() {
    if (!newItemName.trim()) {
      setToast(t("itemNameRequired"));
      return;
    }

    const priceCents = centsFromInput(newItemPrice);
    if (priceCents <= 0) {
      setToast(t("priceInvalid"));
      return;
    }

    setCreatingItem(true);
    try {
      await api.post(`/api/wishlists/${id}/items`, {
        name: newItemName,
        price_cents: priceCents,
        url: newItemUrl || null,
        image_url: newItemImageUrl || null,
        notes: newItemNotes || null,
        allow_contributions: allowContrib
      });
      setNewItemName("");
      setNewItemPrice("99.00");
      setNewItemUrl("");
      setNewItemImageUrl("");
      setNewItemNotes("");
      setAllowContrib(true);
      setAutofillCurrencyHint(null);
      setAutofillCached(false);
      setToast(t("itemAdded"));
      await refetch();
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      setCreatingItem(false);
    }
  }

  function startEditItem(item: Item) {
    setEditingItemId(item.id);
    setEditName(item.name);
    setEditPrice(inputFromCents(item.price_cents));
    setEditUrl(item.url ?? "");
    setEditImageUrl(item.image_url ?? "");
    setEditNotes(item.notes ?? "");
    setEditAllowContrib(item.allow_contributions);
  }

  async function saveItem() {
    if (!editingItemId) return;
    const priceCents = centsFromInput(editPrice);
    if (!editName.trim() || priceCents <= 0) {
      setToast(`${t("itemNameRequired")} / ${t("priceInvalid")}`);
      return;
    }

    setSavingItem(true);
    try {
      await api.patch(`/api/items/${editingItemId}`, {
        name: editName,
        price_cents: priceCents,
        url: editUrl || null,
        image_url: editImageUrl || null,
        notes: editNotes || null,
        allow_contributions: editAllowContrib
      });
      setToast(t("itemUpdated"));
      setEditingItemId(null);
      await refetch();
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      setSavingItem(false);
    }
  }

  async function archiveOrDeleteItem(itemId: number) {
    try {
      const result = await api.delete<{ message: string }>(`/api/items/${itemId}`);
      setToast(result.message);
      await refetch();
    } catch (e) {
      setToast((e as Error).message);
    }
  }

  async function restoreArchivedItem(itemId: number) {
    try {
      await api.patch(`/api/items/${itemId}`, { is_archived: false });
      setToast(t("itemRestored"));
      await refetch();
    } catch (e) {
      setToast((e as Error).message);
    }
  }

  async function reorderItem(itemId: number, direction: "up" | "down") {
    if (!data) return;

    const idx = activeItems.findIndex(item => item.id === itemId);
    if (idx === -1) return;

    const swapWith = direction === "up" ? idx - 1 : idx + 1;
    if (swapWith < 0 || swapWith >= activeItems.length) return;

    const reordered = [...activeItems];
    const tmp = reordered[idx];
    reordered[idx] = reordered[swapWith];
    reordered[swapWith] = tmp;

    const allIds = [...reordered.map(item => item.id), ...archivedItems.map(item => item.id)];

    try {
      await api.post(`/api/wishlists/${data.id}/items/reorder`, { item_ids: allIds });
      setToast(t("orderUpdated"));
      await refetch();
    } catch (e) {
      setToast((e as Error).message);
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
    return <main className="mx-auto max-w-5xl p-8">{t("wishlistNotFound")}</main>;
  }

  async function uploadNewItemImage(file: File) {
    setUploadingNewImage(true);
    try {
      const uploaded = await api.uploadImage(file);
      setNewItemImageUrl(uploaded.url);
      setToast(locale === "ru" ? "Изображение товара загружено" : "Item image uploaded");
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      setUploadingNewImage(false);
    }
  }

  async function uploadEditItemImage(file: File) {
    setUploadingEditImage(true);
    try {
      const uploaded = await api.uploadImage(file);
      setEditImageUrl(uploaded.url);
      setToast(locale === "ru" ? "Изображение товара загружено" : "Item image uploaded");
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      setUploadingEditImage(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl space-y-5 px-4 py-8">
      <div className="flex flex-wrap gap-2">
        <button className="btn-secondary" onClick={() => router.back()}>{t("back")}</button>
      </div>

      <WishlistHeader title={data.title} shareUrl={origin ? `${origin}/w/${data.public_id}` : undefined} />
      <ReconnectBadge connected={wsConnected} />

      <section className="card space-y-3 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{t("wishlistSettings")}</h2>
          <span className={isPublic ? "text-sm text-emerald-700" : "text-sm text-slate-600"}>
            {isPublic ? t("publicEnabled") : t("publicDisabled")}
          </span>
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          <input className="input" value={title} onChange={e => setTitle(e.target.value)} placeholder={locale === "ru" ? "Название" : "Title"} />
          <select className="input" value={currency} onChange={e => setCurrency(e.target.value as Currency)}>
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="GBP">GBP</option>
            <option value="RUB">RUB</option>
          </select>
          <textarea
            className="input sm:col-span-2 min-h-24"
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder={locale === "ru" ? "Описание" : "Description"}
          />
          <label className="sm:col-span-2 flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={isPublic} onChange={e => setIsPublic(e.target.checked)} />
            {locale === "ru" ? "Включить публичную ссылку" : "Enable public link"}
          </label>
        </div>
        <button className="btn-primary" onClick={saveWishlistSettings} disabled={savingSettings}>
          {savingSettings ? t("saving") : t("saveSettings")}
        </button>
      </section>

      <section className="card grid gap-2 p-4 sm:grid-cols-[1fr_140px_auto]">
        <input className="input" placeholder={t("itemNamePlaceholder")} value={newItemName} onChange={e => setNewItemName(e.target.value)} />
        <input className="input" placeholder={t("itemPricePlaceholder")} value={newItemPrice} onChange={e => setNewItemPrice(e.target.value)} />
        <button className="btn-primary" onClick={createItem} disabled={creatingItem}>
          {creatingItem ? t("adding") : t("addItem")}
        </button>

        <div className="sm:col-span-3 grid gap-2 sm:grid-cols-[1fr_auto]">
          <input
            className="input"
            placeholder={t("productLinkOptional")}
            value={newItemUrl}
            onChange={e => setNewItemUrl(e.target.value)}
          />
          <button className="btn-secondary" onClick={autofillFromUrl} disabled={autofillLoading}>
            {autofillLoading ? t("autofilling") : t("autofill")}
          </button>
        </div>
        <p className="sm:col-span-3 text-xs text-slate-500">{t("addByUrlHint")}</p>

        <input
          className="input sm:col-span-3"
          placeholder={t("imageUrlOptional")}
          value={newItemImageUrl}
          onChange={e => setNewItemImageUrl(e.target.value)}
        />
        <label className="btn-secondary inline-flex w-fit cursor-pointer" htmlFor="new-item-image-upload">
          {uploadingNewImage ? (locale === "ru" ? "Загрузка..." : "Uploading...") : t("uploadImage")}
        </label>
        <input
          id="new-item-image-upload"
          type="file"
          accept="image/*"
          className="hidden"
          onChange={e => {
            const file = e.target.files?.[0];
            if (file) void uploadNewItemImage(file);
          }}
        />
        <input
          className="input sm:col-span-3"
          placeholder={t("notesOptional")}
          value={newItemNotes}
          onChange={e => setNewItemNotes(e.target.value)}
        />
        <label className="sm:col-span-3 flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={allowContrib}
            onChange={e => setAllowContrib(e.target.checked)}
          />
          {t("allowContributions")}
        </label>

        {autofillCurrencyHint ? (
          <p className="sm:col-span-3 text-xs text-slate-600">
            {t("currencyHint")}: <b>{autofillCurrencyHint}</b> ({t("wishlistCurrencyFixed")} {currency})
            {autofillCached ? (locale === "ru" ? " • кеш" : " • cached") : ""}
          </p>
        ) : null}
      </section>

      {activeItems.length === 0 ? (
        <section className="card p-10 text-center">
          <h2 className="text-xl font-semibold">{locale === "ru" ? "Ваш вишлист пока пуст" : "Your wishlist is empty"}</h2>
          <p className="mt-2 text-slate-600">{locale === "ru" ? "Добавьте первый товар или вставьте ссылку для автозаполнения." : "Add your first item or paste a product link to auto-fill metadata."}</p>
        </section>
      ) : (
        <section className="grid gap-3">
          {activeItems.map((item, index) => (
            <div key={item.id} className="space-y-2">
              <ItemCard
                item={item}
                currency={data.currency}
                actions={
                  <div className="flex flex-wrap gap-2">
                    <button className="btn-secondary" onClick={() => reorderItem(item.id, "up")} disabled={index === 0}>{t("moveUp")}</button>
                    <button className="btn-secondary" onClick={() => reorderItem(item.id, "down")} disabled={index === activeItems.length - 1}>{t("moveDown")}</button>
                    <button className="btn-secondary" onClick={() => startEditItem(item)}>{t("edit")}</button>
                    <button className="btn-secondary" onClick={() => archiveOrDeleteItem(item.id)}>{t("archiveDelete")}</button>
                  </div>
                }
              />

              {editingItemId === item.id ? (
                <section className="card grid gap-2 p-4 sm:grid-cols-2">
                  <input className="input" value={editName} onChange={e => setEditName(e.target.value)} placeholder={locale === "ru" ? "Название" : "Name"} />
                  <input className="input" value={editPrice} onChange={e => setEditPrice(e.target.value)} placeholder={locale === "ru" ? "Цена" : "Price"} />
                  <input className="input sm:col-span-2" value={editUrl} onChange={e => setEditUrl(e.target.value)} placeholder={locale === "ru" ? "Ссылка" : "URL"} />
                  <input className="input sm:col-span-2" value={editImageUrl} onChange={e => setEditImageUrl(e.target.value)} placeholder={t("imageUrlOptional")} />
                  <label className="btn-secondary inline-flex w-fit cursor-pointer sm:col-span-2" htmlFor={`edit-item-image-upload-${item.id}`}>
                    {uploadingEditImage ? (locale === "ru" ? "Загрузка..." : "Uploading...") : t("uploadImage")}
                  </label>
                  <input
                    id={`edit-item-image-upload-${item.id}`}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={e => {
                      const file = e.target.files?.[0];
                      if (file) void uploadEditItemImage(file);
                    }}
                  />
                  <input className="input sm:col-span-2" value={editNotes} onChange={e => setEditNotes(e.target.value)} placeholder={t("notesPlaceholder")} />
                  <label className="sm:col-span-2 flex items-center gap-2 text-sm text-slate-700">
                    <input type="checkbox" checked={editAllowContrib} onChange={e => setEditAllowContrib(e.target.checked)} />
                    {t("allowContributions")}
                  </label>
                  <div className="sm:col-span-2 flex gap-2">
                    <button className="btn-primary" onClick={saveItem} disabled={savingItem}>{savingItem ? t("saving") : t("saveItem")}</button>
                    <button className="btn-secondary" onClick={() => setEditingItemId(null)}>{t("cancel")}</button>
                  </div>
                </section>
              ) : null}
            </div>
          ))}
        </section>
      )}

      <section className="card p-4">
        <button className="btn-secondary" onClick={() => setShowArchived(v => !v)}>
          {showArchived ? t("hideArchived") : `${t("showArchived")} (${archivedItems.length})`}
        </button>

        {showArchived ? (
          <div className="mt-3 grid gap-3">
            {archivedItems.length === 0 ? (
              <p className="text-sm text-slate-600">{t("noArchived")}</p>
            ) : (
              archivedItems.map(item => (
                <div key={item.id} className="space-y-2">
                  <ItemCard
                    item={item}
                    currency={data.currency}
                    actions={
                      <div className="flex flex-wrap gap-2">
                        <button className="btn-secondary" onClick={() => restoreArchivedItem(item.id)}>{t("restore")}</button>
                        <span className="text-xs text-slate-500 self-center">
                          {t("archivedCollected")} {formatMoney(item.collected_cents, data.currency)}
                        </span>
                      </div>
                    }
                  />
                </div>
              ))
            )}
          </div>
        ) : null}
      </section>

      {toast ? <Toast message={toast} onDone={() => setToast("")} /> : null}
    </main>
  );
}
