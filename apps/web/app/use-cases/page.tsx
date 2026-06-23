import type { Metadata } from "next";
import { BookOpen, FlaskConical, GraduationCap, RadioTower } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/product-ui";

export const metadata: Metadata = {
  title: "Use Cases — ChemVault Extract",
  description: "Use ChemVault Extract for literature extraction, lab report digitisation, instrument data consolidation, and research knowledge bases.",
};

const useCases = [
  {
    icon: FlaskConical,
    title: "Organic Chemistry Literature Extraction",
    description: "Extract reaction conditions, reagents, solvents, yields, and characterisation data from chemistry papers.",
    input: "PDF papers, supporting information, experimental sections",
    extracted: "Reactants, products, reagents, solvents, yields, NMR/IR/MS records",
    output: "Evidence-backed reaction and measurement database",
    plan: "Researcher",
  },
  {
    icon: GraduationCap,
    title: "Teaching Lab Report Digitisation",
    description: "Turn student lab reports into structured records for marking, feedback, and data reuse.",
    input: "DOCX, PDF, TXT, Markdown lab reports",
    extracted: "Procedures, yields, observations, measurements, evidence quotes",
    output: "Reviewable class dataset for feedback and analysis",
    plan: "Student",
  },
  {
    icon: RadioTower,
    title: "Instrument Data Consolidation",
    description: "Import HPLC, NMR, IR, UV-vis, and other exported files into searchable datasets.",
    input: "CSV, XLSX, TXT exports and report attachments",
    extracted: "Retention times, peaks, raw text, conditions, units",
    output: "Searchable measurement tables with source links",
    plan: "Researcher",
  },
  {
    icon: BookOpen,
    title: "Research Team Knowledge Base",
    description: "Build a shared, evidence-backed database from papers and internal reports.",
    input: "Team papers, internal reports, experimental notebooks",
    extracted: "Chemicals, reactions, measurements, metadata, evidence",
    output: "Team-reviewed database with roles and export history",
    plan: "Lab",
  },
];

export default function UseCasesPage() {
  return (
    <section className="marketing-container py-16 md:py-24">
      <SectionHeader
        title="Use ChemVault Extract where scientific evidence needs structure."
        description="Each use case starts with unstructured scientific files and ends with reviewable database records."
        align="center"
      />
      <div className="mt-12 grid gap-5 lg:grid-cols-2">
        {useCases.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.title} className="shadow-none">
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex size-11 items-center justify-center rounded-md bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                    <Icon className="size-5" />
                  </div>
                  <Badge>{item.plan}</Badge>
                </div>
                <CardTitle>{item.title}</CardTitle>
                <CardDescription className="leading-6">{item.description}</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm">
                <UseCaseRow label="Input documents" value={item.input} />
                <UseCaseRow label="Extracted data" value={item.extracted} />
                <UseCaseRow label="Output database" value={item.output} />
                <UseCaseRow label="Best-fit plan" value={item.plan} />
              </CardContent>
            </Card>
          );
        })}
      </div>
    </section>
  );
}

function UseCaseRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-white p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-1 leading-6">{value}</div>
    </div>
  );
}
