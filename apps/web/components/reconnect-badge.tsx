export function ReconnectBadge({ connected }: { connected: boolean }) {
  if (connected) return null;
  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800" role="status" aria-live="polite">
      Reconnecting to live updates... fallback polling active.
    </div>
  );
}
