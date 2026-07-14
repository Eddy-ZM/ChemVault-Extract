"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  CreditCard,
  Database,
  FileCheck2,
  FileUp,
  Files,
  FolderPlus,
  LayoutDashboard,
  Layers3,
  LogOut,
  Search,
  Settings,
  Tags,
  TerminalSquare,
  UploadCloud,
  User,
  Users,
  WalletCards,
} from "lucide-react";
import type { User as UserRecord } from "@chemvault-extract/schemas";

import { clearAuthSession, readStoredUser, storeUser } from "@/lib/auth-client";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { PublicFooter, PublicNav } from "@/components/marketing";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/workspaces", label: "Workspaces", icon: Users },
  { href: "/projects/new", label: "New Project", icon: FolderPlus },
  { href: "/documents", label: "Documents", icon: Files },
  { href: "/documents/upload", label: "Upload", icon: FileUp },
  { href: "/documents/batch-upload", label: "Batch Upload", icon: UploadCloud },
  { href: "/review", label: "Review", icon: FileCheck2 },
  { href: "/batch", label: "Batch Jobs", icon: Layers3 },
  { href: "/database", label: "Database", icon: Database },
  { href: "/search", label: "Search", icon: Search },
  { href: "/exports", label: "Exports", icon: CreditCard },
  { href: "/developers", label: "Developers", icon: TerminalSquare },
  { href: "/usage", label: "Usage", icon: WalletCards },
  { href: "/pricing", label: "Pricing", icon: Tags },
  { href: "/account/billing", label: "Billing", icon: CreditCard },
  { href: "/settings/ai", label: "AI Settings", icon: Settings },
  { href: "/account", label: "Account", icon: User },
];
const publicRoutes = new Set(["/", "/features", "/pricing", "/demo", "/use-cases", "/security", "/docs", "/contact", "/login", "/register"]);
const protectedPrefixes = [
  "/dashboard",
  "/documents",
  "/workspaces",
  "/projects",
  "/batch",
  "/database",
  "/search",
  "/review",
  "/exports",
  "/settings",
  "/developers",
  "/usage",
  "/account",
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<UserRecord | null>(null);
  const publicPath = publicRoutes.has(pathname) || pathname.startsWith("/docs/");
  const protectedPath = protectedPrefixes.some((prefix) => pathname.startsWith(prefix));

  useEffect(() => {
    const storedUser = readStoredUser();
    if (storedUser) {
      setUser(storedUser);
    }
    if (publicPath) {
      return;
    }

    let cancelled = false;
    fetch("/api/auth/me", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) {
          if (response.status === 401) {
            clearAuthSession();
            if (!cancelled) setUser(null);
          }
          if ((response.status === 401 || response.status === 500) && protectedPath) {
            router.push(`/login?next=${encodeURIComponent(pathname)}`);
          }
          return null;
        }
        return (await response.json()) as UserRecord;
      })
      .then((body) => {
        if (!cancelled && body) {
          storeUser(body);
          setUser(body);
        }
      })
      .catch(() => {
        if (!cancelled) setUser(null);
      });
    return () => {
      cancelled = true;
    };
  }, [pathname, protectedPath, publicPath, router]);

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" }).catch(() => null);
    clearAuthSession();
    setUser(null);
    router.push("/login");
    router.refresh();
  }

  if (publicPath) {
    return (
      <div className="min-h-screen bg-background">
        <PublicNav userEmail={user?.email} />
        <ProductTransitionNotice />
        <main>{children}</main>
        <PublicFooter />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="flex min-h-screen">
        <aside className="extract-sidebar hidden w-64 shrink-0 border-r backdrop-blur lg:block">
          <div className="extract-sidebar-brand flex h-16 items-center gap-3 border-b px-5">
            <div className="flex size-9 items-center justify-center overflow-hidden rounded-md border border-slate-200 bg-white p-1 shadow-sm">
              <img src="/assets/chemvault-logo-mark.png" alt="" className="size-full object-contain" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium">ChemVault Extract</span>
              <span className="text-xs text-muted-foreground">research workspace</span>
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
                    "flex h-9 items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
                    active && "bg-accent text-accent-foreground shadow-sm ring-1 ring-blue-100",
                  )}
                >
                  <Icon className="size-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </aside>
        <div className="extract-workspace flex min-w-0 flex-1 flex-col">
          <header className="extract-topbar sticky top-0 z-30 flex h-16 items-center justify-between border-b px-4 backdrop-blur lg:px-8">
            <Link href="/dashboard" className="flex items-center gap-3 lg:hidden">
              <div className="flex size-9 items-center justify-center overflow-hidden rounded-md border border-slate-200 bg-white p-1 shadow-sm">
                <img src="/assets/chemvault-logo-mark.png" alt="" className="size-full object-contain" />
              </div>
              <span className="text-sm font-medium">ChemVault Extract</span>
            </Link>
            <div className="hidden text-sm font-medium text-muted-foreground lg:block">
              Scientific document ingestion
            </div>
            <div className="flex items-center gap-2">
              {user ? (
                <>
                  <span className="hidden max-w-56 truncate text-sm text-muted-foreground md:inline">{user.email}</span>
                  <Button variant="outline" size="sm" onClick={logout}>
                    <LogOut data-icon="inline-start" />
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Button asChild variant="outline" size="sm">
                    <Link href="/login">Login</Link>
                  </Button>
                  <Button asChild size="sm">
                    <Link href="/register">Register</Link>
                  </Button>
                </>
              )}
            </div>
          </header>
          <ProductTransitionNotice />
          <main className="flex-1 px-4 py-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  );
}

function ProductTransitionNotice() {
  const productMode = process.env.NEXT_PUBLIC_PRODUCT_MODE || "sunset";
  if (productMode !== "sunset") return null;

  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-center text-sm text-amber-950">
      Extract is in maintenance mode. New laboratory analysis workflows are moving to{" "}
      <a
        className="font-semibold underline underline-offset-2"
        href={process.env.NEXT_PUBLIC_CHEMVAULT_LAB_URL || "https://lab.chemvault.science"}
      >
        ChemVault Lab
      </a>
      . Existing data and exports remain available during migration.
    </div>
  );
}
