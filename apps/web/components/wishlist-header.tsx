"use client";

import { useState } from "react";

export function WishlistHeader({ title, shareUrl }: { title: string; shareUrl?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    if (!shareUrl) return;
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  }

  return (
    <header className="flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-2xl font-bold tracking-tight text-slatex">{title}</h1>
      {shareUrl ? (
        <button className="btn-secondary" onClick={copy}>
          {copied ? "Link copied" : "Copy share link"}
        </button>
      ) : null}
    </header>
  );
}
