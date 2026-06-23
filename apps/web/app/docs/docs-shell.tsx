import Link from "next/link";
import { ArrowLeft, ArrowRight, Search } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

import { CodeCopyButton } from "./code-copy-button";
import { docsPages, type DocsPage } from "./docs-data";

export function DocsShell({ page }: { page: DocsPage }) {
  const index = docsPages.findIndex((item) => item.slug === page.slug);
  const previous = index > 0 ? docsPages[index - 1] : null;
  const next = index >= 0 && index < docsPages.length - 1 ? docsPages[index + 1] : null;

  return (
    <div className="marketing-container grid gap-8 py-10 lg:grid-cols-[250px_minmax(0,1fr)_210px]">
      <aside className="hidden lg:block">
        <div className="sticky top-20 grid gap-4">
          <div className="flex h-10 items-center gap-2 rounded-md border bg-background px-3 text-sm text-muted-foreground">
            <Search className="size-4" />
            Search docs
          </div>
          <nav className="grid gap-1">
            {docsPages.map((item) => {
              const href = item.slug ? `/docs/${item.slug}` : "/docs";
              const active = item.slug === page.slug;
              return (
                <Link
                  key={item.slug || "index"}
                  href={href}
                  className={cn(
                    "rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    active && "bg-accent text-accent-foreground",
                  )}
                >
                  {item.title}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      <article className="min-w-0">
        <div className="border-b pb-8">
          <p className="text-sm font-medium text-blue-600">ChemVault Extract docs</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-normal text-slate-950">{page.title}</h1>
          <p className="mt-4 max-w-3xl text-lg leading-8 text-muted-foreground">{page.description}</p>
        </div>

        <div className="grid gap-10 py-10">
          {page.sections.map((section) => (
            <section key={section.id} id={section.id} className="scroll-mt-24">
              <h2 className="text-2xl font-semibold tracking-normal">{section.title}</h2>
              <div className="mt-4 grid gap-4 text-base leading-7 text-muted-foreground">
                {section.body.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
              </div>
              {section.code ? (
                <Card className="mt-5 overflow-hidden bg-slate-950 text-slate-50">
                  <CardContent className="p-0">
                    <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
                      <span className="text-xs text-slate-300">{section.code.language}</span>
                      <CodeCopyButton value={section.code.value} />
                    </div>
                    <pre className="overflow-x-auto p-4 text-sm leading-6">
                      <code>{section.code.value}</code>
                    </pre>
                  </CardContent>
                </Card>
              ) : null}
            </section>
          ))}
        </div>

        <div className="grid gap-3 border-t pt-6 sm:grid-cols-2">
          {previous ? (
            <Button asChild variant="outline" className="justify-start">
              <Link href={previous.slug ? `/docs/${previous.slug}` : "/docs"}>
                <ArrowLeft data-icon="inline-start" />
                {previous.title}
              </Link>
            </Button>
          ) : (
            <div />
          )}
          {next ? (
            <Button asChild variant="outline" className="justify-end">
              <Link href={next.slug ? `/docs/${next.slug}` : "/docs"}>
                {next.title}
                <ArrowRight data-icon="inline-end" />
              </Link>
            </Button>
          ) : null}
        </div>
      </article>

      <aside className="hidden xl:block">
        <div className="sticky top-20">
          <div className="text-xs font-semibold uppercase text-muted-foreground">On this page</div>
          <nav className="mt-3 grid gap-2">
            {page.sections.map((section) => (
              <a key={section.id} href={`#${section.id}`} className="text-sm text-muted-foreground hover:text-foreground">
                {section.title}
              </a>
            ))}
          </nav>
        </div>
      </aside>
    </div>
  );
}
