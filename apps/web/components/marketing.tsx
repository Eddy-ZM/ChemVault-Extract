import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";

const primaryLinks = [
  { href: "/", label: "Home" },
  { href: "/features", label: "Features" },
  { href: "/use-cases", label: "Use cases" },
  { href: "/pricing", label: "Pricing" },
  { href: "/demo", label: "Demo" },
  { href: "https://docs.chemvault.science/manual/extract/", label: "Docs" },
];

const moreLinks = [
  { href: "/security", label: "Security" },
  { href: "/developers", label: "Developers" },
  { href: "/contact", label: "Contact" },
];

export function PublicNav({ userEmail }: { userEmail?: string | null }) {
  return (
    <header className="site-header">
      <div className="marketing-container nav-shell">
        <Link href="/" className="brand" aria-label="ChemVault Extract home">
          <span className="brand-mark" aria-hidden="true">
            <img src="/assets/chemvault-logo-mark.png" alt="" />
          </span>
          <span>
            <strong>ChemVault Extract</strong>
            <small>scientific extraction platform</small>
          </span>
        </Link>
        <nav className="site-nav" aria-label="Main navigation">
          {primaryLinks.map((link) => (
            <SmartLink key={link.href} href={link.href}>{link.label}</SmartLink>
          ))}
          <details className="nav-more">
            <summary>More</summary>
            <div className="nav-more-menu">
              {moreLinks.map((link) => (
                <SmartLink key={link.href} href={link.href}>{link.label}</SmartLink>
              ))}
            </div>
          </details>
        </nav>
        <div className="header-actions">
          {userEmail ? (
            <Button asChild size="sm" variant="outline" className="site-action-button">
              <Link href="/dashboard">Dashboard</Link>
            </Button>
          ) : (
            <Button asChild size="sm" variant="outline" className="site-action-button">
              <Link href="/login">Login</Link>
            </Button>
          )}
          <Button asChild size="sm" className="site-action-button">
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
    <footer className="site-footer" aria-label="ChemVault Extract footer">
      <div className="footer-panel">
        <div className="footer-ambient" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div className="marketing-container footer-grid">
          <div className="footer-brand-block">
            <Link className="footer-brand" href="/">
              <span className="footer-brand-mark" aria-hidden="true">
                <img src="/assets/chemvault-logo-mark.png" alt="" />
              </span>
              <span>
                <strong>ChemVault Extract</strong>
                <small>Scientific data extraction</small>
              </span>
            </Link>
            <p>
              AI-powered scientific data extraction for papers, lab reports, and instrument exports. Every record is
              designed to stay tied to evidence, review state, and source provenance.
            </p>
            <div className="footer-social-row" aria-label="Quick footer actions">
              <Link className="footer-social" href="/documents/upload">
                Upload document
              </Link>
              <Link className="footer-social" href="/demo">
                Product demo
              </Link>
              <Link className="footer-social" href="/docs/api">
                API docs
              </Link>
            </div>
          </div>
          <div className="footer-link-groups">
            <FooterGroup title="Product" links={[["Features", "/features"], ["Demo", "/demo"], ["Pricing", "/pricing"], ["Security", "/security"]]} />
            <FooterGroup title="Workflows" links={[["Upload", "/documents/upload"], ["Review", "/review"], ["Search", "/search"], ["Exports", "/exports"]]} />
            <FooterGroup title="Developers" links={[["Docs", "https://docs.chemvault.science/manual/extract/"], ["API", "/docs/api"], ["SDKs", "/docs/sdks"], ["Webhooks", "/docs/webhooks"]]} />
            <FooterGroup title="Account" links={[["Login", "/login"], ["Register", "/register"], ["Usage", "/usage"], ["Contact", "/contact"]]} />
          </div>
        </div>
        <div className="marketing-container footer-bottom">
          <p>© 2026 ChemVault. All rights reserved.</p>
          <div className="footer-bottom-meta">
            <p>Research-oriented reference. Verify primary literature before applying chemical information.</p>
            <span className="footer-version">ChemVault Extract MVP</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

function FooterGroup({ title, links }: { title: string; links: Array<[string, string]> }) {
  return (
    <div className="footer-column">
      <span className="footer-heading">{title}</span>
      {links.map(([label, href]) => (
        <SmartLink key={href} href={href}>{label}</SmartLink>
      ))}
    </div>
  );
}

function SmartLink({ href, children, className }: { href: string; children: ReactNode; className?: string }) {
  if (/^https?:\/\//i.test(href)) {
    return (
      <a className={className} href={href} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    );
  }

  return (
    <Link className={className} href={href}>
      {children}
    </Link>
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
          <div className="rounded-md bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 ring-1 ring-blue-100">
            review ready
          </div>
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
              <div className="rounded-md bg-blue-50 p-3 text-sm leading-6 text-blue-950">
                “The product was obtained as a white solid in 82% yield.”
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <div className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white">Approve</div>
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
