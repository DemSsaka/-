import Image from "next/image";

import { formatMoney } from "@/lib/format";
import { Currency, Item } from "@/lib/types";
import { ProgressBar } from "./progress-bar";

export function ItemCard({
  item,
  currency,
  actions,
  publicMode = false
}: {
  item: Item;
  currency: Currency;
  actions?: React.ReactNode;
  publicMode?: boolean;
}) {
  const pct = item.price_cents > 0 ? Math.round((item.collected_cents / item.price_cents) * 100) : 0;
  return (
    <article className="card overflow-hidden">
      <div className="grid grid-cols-1 gap-4 p-4 sm:grid-cols-[96px_1fr]">
        <div className="relative h-24 overflow-hidden rounded-xl bg-slate-100">
          {item.image_url ? (
            <Image src={item.image_url} alt={item.name} fill className="object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center text-xs text-slate-500">No image</div>
          )}
        </div>
        <div className="space-y-2">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <h3 className="text-lg font-semibold">{item.name}</h3>
            <span className="price-chip">
              {formatMoney(item.price_cents, currency)}
            </span>
          </div>

          {item.notes ? <p className="text-sm text-slate-600">{item.notes}</p> : null}

          {item.reserved ? (
            <p className="text-sm font-medium text-amber-700">
              {publicMode && item.reserved_by_me ? "Reserved by you" : "Reserved by someone"}
            </p>
          ) : (
            <p className="text-sm text-emerald-700">Available</p>
          )}

          {item.allow_contributions ? (
            <div className="space-y-1">
              <ProgressBar value={item.collected_cents} max={item.price_cents} />
              <p className="text-xs text-slate-600">
                Collected {formatMoney(item.collected_cents, currency)} of {formatMoney(item.price_cents, currency)} ({pct}%)
              </p>
              {publicMode && item.my_contribution_cents ? (
                <p className="text-xs text-brand-700">
                  You contributed {formatMoney(item.my_contribution_cents, currency)}
                </p>
              ) : null}
            </div>
          ) : null}

          {actions}
        </div>
      </div>
    </article>
  );
}
