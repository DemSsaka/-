"use client";

import { useEffect, useRef, useState } from "react";

export function useWishlistRealtime(publicId: string, onEvent: () => void): { wsConnected: boolean } {
  const [wsConnected, setWsConnected] = useState(false);
  const attemptsRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    if (!publicId) {
      setWsConnected(false);
      return;
    }

    let stopped = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      if (stopped) return;
      const base = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(
        /^http/,
        "ws"
      );
      const ws = new WebSocket(`${base}/ws/wishlist/${publicId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        attemptsRef.current = 0;
        setWsConnected(true);
      };

      ws.onmessage = () => {
        onEventRef.current();
      };

      ws.onclose = () => {
        setWsConnected(false);
        if (stopped) return;
        attemptsRef.current += 1;
        const baseDelay = Math.min(30000, Math.pow(2, attemptsRef.current) * 1000);
        const jitter = Math.floor(Math.random() * 400);
        reconnectTimer = setTimeout(connect, baseDelay + jitter);
      };

      ws.onerror = () => ws.close();
    };

    connect();

    return () => {
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [publicId]);

  return { wsConnected };
}
