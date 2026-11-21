import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "Baseline — WNBA Stats",
  description: "Explore every WNBA performance against a player's season average.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <Link className="brand" href="/">
            <span className="brand-mark" aria-hidden="true" />
            <span>Baseline</span>
          </Link>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}

