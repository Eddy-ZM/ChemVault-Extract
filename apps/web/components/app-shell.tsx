"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileUp, Files, FlaskConical, LayoutDashboard } from "lucide-react";

import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Home", icon: FlaskConical },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", label: "Documents", icon: Files },
  { href: "/documents/upload", label: "Upload", icon: FileUp },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r bg-card lg:block">
          <div className="flex h-16 items-center gap-3 border-b px-5">
            <div className="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <FlaskConical className="size-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold">ChemVault Extract</span>
              <span className="text-xs text-muted-foreground">MVP workspace</span>
            </div>
          </div>
          <nav className="flex flex-col gap-1 p-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active =
                item.href === "/" ? pathname === "/" : pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex h-9 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
                    active && "bg-accent text-accent-foreground",
                  )}
                >
                  <Icon className="size-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </aside>
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-16 items-center justify-between border-b bg-card px-4 lg:px-8">
            <Link href="/" className="flex items-center gap-3 lg:hidden">
              <div className="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <FlaskConical className="size-4" />
              </div>
              <span className="text-sm font-semibold">ChemVault Extract</span>
            </Link>
            <div className="hidden text-sm text-muted-foreground lg:block">Scientific document ingestion</div>
            <Link
              href="/documents/upload"
              className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
            >
              Upload
            </Link>
          </header>
          <main className="flex-1 px-4 py-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
