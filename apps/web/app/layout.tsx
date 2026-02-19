import "./globals.css";

import type { Metadata } from "next";
import Script from "next/script";

import { FallingPresents } from "@/components/falling-presents";
import { Providers } from "@/components/providers";
import { TopNav } from "@/components/top-nav";

export const metadata: Metadata = {
  title: "Social Wishlist",
  description: "Realtime social wishlist with reservations and contributions"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning data-theme="light">
      <head>
        <Script id="theme-init" strategy="beforeInteractive">
          {`
            (function () {
              try {
                var theme = localStorage.getItem("wishlist_theme") || "light";
                document.documentElement.setAttribute("data-theme", theme);
              } catch (e) {}
            })();
          `}
        </Script>
      </head>
      <body suppressHydrationWarning>
        <Providers>
          <FallingPresents />
          <TopNav />
          <div className="relative z-10 pt-24">{children}</div>
        </Providers>
      </body>
    </html>
  );
}
