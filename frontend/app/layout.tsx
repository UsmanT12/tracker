import type { Metadata } from "next";
import Link from "next/link";
import { Activity } from "lucide-react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Baseline — WNBA Performance Explorer",
  description: "Explore every WNBA performance against a player's season average.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <Link className="brand" href="/">
            <span className="brand-mark"><Activity size={19} aria-hidden="true" /></span>
            <span>Baseline</span>
          </Link>
          <span className="header-kicker">WNBA performance explorer</span>
        </header>
        <main>{children}</main>
        <footer className="site-footer">
          Statistics sourced from locally imported WNBA box scores.
        </footer>
      </body>
    </html>
  );
}

