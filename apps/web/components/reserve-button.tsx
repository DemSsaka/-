"use client";

export function ReserveButton({
  reserved,
  canUnreserve,
  onReserve,
  onUnreserve,
  busy
}: {
  reserved: boolean;
  canUnreserve: boolean;
  onReserve: () => void;
  onUnreserve: () => void;
  busy: boolean;
}) {
  if (reserved) {
    return (
      <button className="btn-secondary" disabled={!canUnreserve || busy} onClick={onUnreserve}>
        {busy ? "Working..." : canUnreserve ? "Unreserve" : "Reserved"}
      </button>
    );
  }
  return (
    <button className="btn-primary" disabled={busy} onClick={onReserve}>
      {busy ? "Reserving..." : "Reserve"}
    </button>
  );
}
