import Link from "next/link";
import { ArrowRight, FlaskConical } from "lucide-react";

import { Button } from "@/components/ui/button";

export function PublicNav({ userEmail }: { userEmail?: string | null }) {
  const links = [
    { href: "/features", label: "Features" },
    { href: "/use-cases", label: "Use cases" },
    { href: "/pricing", label: "Pricing" },
    { href: "/demo", label: "Demo" },
    { href: "/docs", label: "Docs" },
  ];

  return (
    <header className="sticky top-0 z-40 border-b bg-white/90 backdrop-blur">
      <div className="marketing-container flex h-16 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-md bg-slate-950 text-amber-300">
            <FlaskConical className="size-4" />
          </div>
          <span className="text-sm font-semibold tracking-normal">ChemVault Extract</span>
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-muted-foreground lg:flex">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className="hover:text-foreground">
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {userEmail ? (
            <Button asChild size="sm" variant="outline">
              <Link href="/dashboard">Dashboard</Link>
            </Button>
          ) : (
            <Button asChild size="sm" variant="outline">
              <Link href="/login">Login</Link>
            </Button>
          )}
          <Button asChild size="sm">
            <Link href={userEmail ? "/documents/upload" : "/register"}>
              Get started
              <ArrowRight data-icon="inline-end" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}

export function PublicFooter() {
  return (
    <footer className="border-t bg-white">
      <div className="marketing-container grid gap-8 py-10 md:grid-cols-[1.2fr_2fr]">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-md bg-slate-950 text-amber-300">
              <FlaskConical className="size-4" />
            </div>
            <span className="text-sm font-semibold">ChemVault Extract</span>
          </div>
          <p className="mt-3 max-w-md text-sm leading-6 text-muted-foreground">
            AI-powered scientific data extraction for evidence-backed research databases.
          </p>
        </div>
        <div className="grid gap-6 text-sm sm:grid-cols-3">
          <FooterGroup title="Product" links={[["Features", "/features"], ["Demo", "/demo"], ["Pricing", "/pricing"]]} />
          <FooterGroup title="Resources" links={[["Docs", "/docs"], ["Use cases", "/use-cases"], ["Security", "/security"]]} />
          <FooterGroup title="Account" links={[["Login", "/login"], ["Register", "/register"], ["Contact", "/contact"]]} />
        </div>
      </div>
    </footer>
  );
}

function FooterGroup({ title, links }: { title: string; links: Array<[string, string]> }) {
  return (
    <div>
      <h3 className="font-medium">{title}</h3>
      <div className="mt-3 grid gap-2 text-muted-foreground">
        {links.map(([label, href]) => (
          <Link key={href} href={href} className="hover:text-foreground">
            {label}
          </Link>
        ))}
      </div>
    </div>
  );
}

export function ProductMockup() {
  return (
    <div className="rounded-2xl border bg-white p-3 shadow-2xl shadow-slate-950/10">
      <div className="rounded-xl border bg-slate-50 p-4">
        <div className="mb-4 flex items-center justify-between border-b pb-3">
          <div>
            <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Document workflow</div>
            <div className="text-sm font-semibold">paper_oxidation_study.pdf</div>
          </div>
          <div className="rounded-md bg-amber-100 px-2.5 py-1 text-xs font-medium text-slate-950">review ready</div>
        </div>
        <div className="grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="grid gap-2">
            {["Abstract", "Experimental", "Results", "Tables"].map((section, index) => (
              <div key={section} className="rounded-md border bg-white p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{section}</span>
                  <span className="text-xs text-muted-foreground">page {index + 1}</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-200" />
                <div className="mt-1 h-2 w-2/3 rounded-full bg-slate-200" />
              </div>
            ))}
          </div>
          <div className="rounded-lg border bg-white p-4">
            <div className="mb-3 text-sm font-semibold">Evidence-backed reaction record</div>
            <div className="grid gap-2 text-sm">
              <MockRow label="Product" value="benzyl alcohol derivative" />
              <MockRow label="Reagent" value="sodium hypochlorite" />
              <MockRow label="Solvent" value="acetic acid" />
              <MockRow label="Yield" value="82%" />
              <div className="rounded-md bg-amber-50 p-3 text-sm leading-6">
                “The product was obtained as a white solid in 82% yield.”
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <div className="rounded-md bg-slate-950 px-3 py-1.5 text-xs font-medium text-white">Approve</div>
              <div className="rounded-md border px-3 py-1.5 text-xs font-medium">Edit</div>
              <div className="rounded-md border px-3 py-1.5 text-xs font-medium">Reject</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MockRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border p-2">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
