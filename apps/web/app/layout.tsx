import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChemVault Extract — AI Scientific Data Extraction",
  description: "Turn scientific papers, lab reports, and instrument exports into structured, evidence-backed research databases.",
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
