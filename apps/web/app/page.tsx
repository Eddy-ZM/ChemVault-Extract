import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Database,
  FileText,
  FlaskConical,
  Search,
  ShieldCheck,
  Table2,
  Users,
} from "lucide-react";

import { ProductMockup } from "@/components/marketing";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EvidenceCard, FeatureCard, SectionHeader, WorkflowStep } from "@/components/product-ui";

export const metadata: Metadata = {
  title: "ChemVault Extract — AI Scientific Data Extraction",
  description:
    "Turn scientific papers, lab reports, and instrument exports into structured, evidence-backed research databases.",
};

const painPoints = [
  "Experimental data is trapped in PDFs.",
  "Tables, yields, spectra, and conditions are hard to reuse.",
  "Manual extraction is slow and error-prone.",
  "Generic PDF chat tools do not produce reliable structured databases.",
];

const workflow = [
  ["Upload documents", "Add papers, lab reports, CSV/XLSX instrument exports, TXT, Markdown, and DOCX files."],
  ["Parse pages, blocks, tables, and chunks", "The worker creates structured document objects that can be reviewed and reused."],
  ["Extract chemicals, reactions, and measurements", "OpenAI structured outputs target scientific records from selected chunks only."],
  ["Validate evidence and normalize data", "Quotes are checked against source chunks while units, roles, names, and measurements are normalized."],
  ["Human review", "Approve, edit, or reject every record before it becomes trusted research data."],
  ["Search and export database", "Filter evidence-backed records and export CSV, JSON, or XLSX datasets."],
];

const useCases = [
  { title: "Organic synthesis data extraction", icon: FlaskConical },
  { title: "Lab report digitisation", icon: FileText },
  { title: "HPLC / NMR / IR data extraction", icon: Table2 },
  { title: "Literature review database building", icon: Search },
  { title: "Team research knowledge base", icon: Users },
  { title: "Teaching lab report analysis", icon: Database },
];

export default function HomePage() {
  return (
    <div className="bg-white">
      <section className="marketing-container grid min-h-[calc(100vh-4rem)] items-center gap-10 py-14 lg:grid-cols-[0.95fr_1.05fr] lg:py-20">
        <div className="max-w-3xl">
          <h1 className="text-balance text-4xl font-semibold tracking-normal text-slate-950 md:text-6xl">
            Turn scientific documents into structured research databases.
          </h1>
          <p className="mt-6 text-lg leading-8 text-muted-foreground">
            Upload papers, lab reports, and instrument exports. ChemVault Extract parses them, extracts scientific data
            with AI, links every record to evidence, and lets your team review, search, and export reliable datasets.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link href="/register">
                Get started
                <ArrowRight data-icon="inline-end" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/demo">View demo</Link>
            </Button>
          </div>
        </div>
        <ProductMockup />
      </section>

      <section className="border-y bg-slate-50">
        <div className="marketing-container py-16">
          <SectionHeader
            title="Scientific data is still locked inside unstructured files."
            description="Chemistry teams need database-ready records, not another chat transcript or a copied PDF paragraph."
          />
          <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {painPoints.map((point) => (
              <Card key={point} className="shadow-none">
                <CardContent className="flex gap-3 p-5">
                  <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-amber-500" />
                  <p className="text-sm leading-6">{point}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="marketing-container py-20">
        <SectionHeader title="A workflow built for evidence-backed scientific databases." />
        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workflow.map(([title, description], index) => (
            <WorkflowStep key={title} index={index + 1} title={title} description={description} />
          ))}
        </div>
      </section>

      <section className="bg-slate-950 text-white">
        <div className="marketing-container grid gap-10 py-20 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <SectionHeader
              title="Every extracted record stays tied to evidence."
              description="ChemVault Extract is designed around traceability: source document, page, section, quote, confidence, and review status travel with every record."
            />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <EvidenceCard label="source document" value="paper_oxidation_study.pdf" />
            <EvidenceCard label="page number" value="4" />
            <EvidenceCard label="section" value="Experimental" />
            <EvidenceCard label="confidence" value="0.87" />
            <div className="sm:col-span-2">
              <EvidenceCard
                label="evidence quote"
                value="The product was obtained as a white solid in 82% yield."
              />
            </div>
            <EvidenceCard label="review status" value="pending human review" />
            <EvidenceCard label="record type" value="reaction" />
          </div>
        </div>
      </section>

      <section className="marketing-container py-20">
        <SectionHeader title="Built for chemistry documents and research teams." align="center" />
        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {useCases.map((item) => (
            <FeatureCard key={item.title} icon={item.icon} title={item.title} description="Extract structured, reviewable records from source files while preserving source evidence." />
          ))}
        </div>
      </section>

      <section className="marketing-container pb-20">
        <div className="rounded-2xl border bg-amber-50 p-8 md:p-12">
          <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <h2 className="text-3xl font-semibold tracking-normal text-balance">Start building a reliable research database.</h2>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
                Upload your first scientific document, review extracted evidence, and export structured data when it is ready.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/documents/upload">Start extracting data</Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/register">Create free account</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
