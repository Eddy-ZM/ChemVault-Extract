import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { DocsShell } from "../docs-shell";
import { docsPages, getDocsPage } from "../docs-data";

export function generateStaticParams() {
  return docsPages.filter((page) => page.slug && !page.slug.includes("/")).map((page) => ({ slug: page.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const page = getDocsPage(slug);
  if (!page) return {};
  return {
    title: `${page.title} — ChemVault Extract Docs`,
    description: page.description,
  };
}

export default async function DocsSlugPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = getDocsPage(slug);
  if (!page) notFound();
  return <DocsShell page={page} />;
}
