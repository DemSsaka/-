"use client";

import { useEffect } from "react";

export function Toast({ message, onDone }: { message: string; onDone: () => void }) {
  useEffect(() => {
    const id = setTimeout(onDone, 2200);
    return () => clearTimeout(id);
  }, [onDone]);

  return <div className="fixed bottom-4 right-4 rounded-xl bg-slatex px-4 py-2 text-sm text-white">{message}</div>;
}
