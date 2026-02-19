"use client";

import { useEffect, useMemo, useState } from "react";

import { useTheme } from "@/components/theme-provider";

type FallingItem = {
  id: number;
  src: string;
  left: number;
  size: number;
  duration: number;
  delay: number;
  rotateDuration: number;
  opacity: number;
};

const LIGHT_ICONS = ["/assets/Light.png", "/assets/Light-present.png"];
const DARK_ICONS = ["/assets/Dark.png", "/assets/Dark-present.png"];

function randomFromSeed(seed: number) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

export function FallingPresents() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const items = useMemo<FallingItem[]>(() => {
    if (!mounted) return [];
    const nowSeed = Math.floor(Date.now() / 1000);
    const plainIcon = theme === "dark" ? DARK_ICONS[0] : LIGHT_ICONS[0];
    const presentIcon = theme === "dark" ? DARK_ICONS[1] : LIGHT_ICONS[1];
    return Array.from({ length: 24 }, (_, idx) => {
      const base = nowSeed + idx * 137;
      const src = idx % 4 === 0 ? plainIcon : presentIcon;
      const baseSize = 48 + Math.floor(randomFromSeed(base + 3) * 64);
      return {
        id: idx,
        src,
        left: Math.floor(randomFromSeed(base + 2) * 100),
        size: Math.round(baseSize * 1.3),
        duration: 22 + Math.floor(randomFromSeed(base + 4) * 24),
        delay: -Math.floor(randomFromSeed(base + 5) * 30),
        rotateDuration: 18 + Math.floor(randomFromSeed(base + 6) * 24),
        opacity: theme === "dark" ? 0.14 + randomFromSeed(base + 7) * 0.12 : 0.18 + randomFromSeed(base + 7) * 0.14,
      };
    });
  }, [mounted, theme]);

  if (!mounted) return null;

  return (
    <div aria-hidden className="falling-bg">
      {items.map(item => (
        <div
          key={item.id}
          className="falling-wrap"
          style={{
            left: `${item.left}%`,
            width: item.size,
            height: item.size,
            animationDuration: `${item.duration}s`,
            animationDelay: `${item.delay}s`,
            opacity: item.opacity,
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={item.src}
            alt=""
            className="falling-icon"
            style={{ animationDuration: `${item.rotateDuration}s` }}
          />
        </div>
      ))}
    </div>
  );
}
