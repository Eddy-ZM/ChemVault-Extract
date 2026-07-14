import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import "./globals.css";
import "./exhibition-theme.css";

export const metadata: Metadata = {
  title: "ChemVault Extract — AI Scientific Data Extraction",
  description: "Turn scientific papers, lab reports, and instrument exports into structured, evidence-backed research databases.",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/assets/favicon-192.png", type: "image/png", sizes: "192x192" },
      { url: "/assets/favicon.svg", type: "image/svg+xml" },
    ],
    apple: "/assets/chemvault-apple-touch-icon.png",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
