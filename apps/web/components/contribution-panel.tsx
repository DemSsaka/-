"use client";

import { useState } from "react";

export function ContributionPanel({
  onSubmit,
  busy,
  disabled
}: {
  onSubmit: (amountCents: number, message: string) => void;
  busy: boolean;
  disabled: boolean;
}) {
  const [amount, setAmount] = useState("10.00");
  const [message, setMessage] = useState("");

  function submit() {
    const parsed = Math.round(Number(amount) * 100);
    if (!Number.isFinite(parsed) || parsed <= 0) return;
    onSubmit(parsed, message);
  }

  return (
    <div className="mt-2 grid gap-2 sm:grid-cols-[120px_1fr_auto]">
      <input
        className="input"
        value={amount}
        onChange={e => setAmount(e.target.value)}
        placeholder="10.00"
        inputMode="decimal"
        aria-label="Contribution amount"
        disabled={disabled}
      />
      <input
        className="input"
        value={message}
        onChange={e => setMessage(e.target.value)}
        placeholder="Short message (optional)"
        maxLength={280}
        aria-label="Contribution message"
        disabled={disabled}
      />
      <button className="btn-secondary" onClick={submit} disabled={busy || disabled}>
        {busy ? "Sending..." : "Contribute"}
      </button>
    </div>
  );
}
