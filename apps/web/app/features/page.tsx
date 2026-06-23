import type { Metadata } from "next";
import {
  Beaker,
  CheckCircle2,
  Database,
  FileText,
  Search,
  ShieldCheck,
  Table2,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { FeatureCard, SectionHeader } from "@/components/product-ui";

export const metadata: Metadata = {
  title: "Features — ChemVault Extract",
  description: "Scientific ingestion, structured extraction, evidence validation, normalization, review, search, export, and team workspaces.",
};

const ingestionFormats = ["PDF", "DOCX", "CSV", "XLSX", "TXT", "Markdown"];
const modules = [
  {
    icon: FileText,
    title: "Scientific document ingestion",
    description: "Upload chemistry papers, lab reports, instrument exports, text notes, spreadsheets, and Markdown files.",
    tags: ingestionFormats,
  },
  {
    icon: Beaker,
    title: "AI structured extraction",
    description: "Extract chemical entities, reaction records, measurement records, and paper metadata through structured outputs.",
    tags: ["chemical entities", "reactions", "measurements", "metadata"],
  },
  {
    icon: ShieldCheck,
    title: "Evidence-backed records",
    description: "Each record keeps source document, page, section, quote, confidence, and review status.",
    tags: ["page", "section", "quote", "source document"],
  },
  {
    icon: CheckCircle2,
    title: "Scientific normalization",
    description: "Normalize common scientific language and units before records enter review.",
    tags: ["EtOH -> ethanol", "NaOCl -> sodium hypochlorite", "rt -> room temperature", "yield standardization"],
  },
  {
    icon: Table2,
    title: "Human review workflow",
    description: "Approve, edit, or reject extracted records with validation warnings and raw vs normalized values side by side.",
    tags: ["approve", "edit", "reject", "warnings"],
  },
  {
    icon: Search,
    title: "Search and export",
    description: "Search parsed chunks and extracted records, then export evidence-included CSV, JSON, or XLSX datasets.",
    tags: ["CSV", "JSON", "XLSX", "filtering"],
  },
  {
    icon: Users,
    title: "Team workspace",
    description: "Workspaces support roles, permissions, batch upload, and batch extraction for shared research databases.",
    tags: ["roles", "permissions", "batch upload", "batch extraction"],
  },
  {
    icon: Database,
    title: "Research database foundation",
    description: "Build a structured database that can later connect to normalization, PubChem/RDKit enrichment, search, and exports.",
    tags: ["records", "evidence", "review", "export"],
  },
];

export default function FeaturesPage() {
  return (
    <div className="bg-white">
      <section className="marketing-container py-16 md:py-24">
        <SectionHeader
          title="A scientific extraction workflow from upload to reviewed database."
          description="ChemVault Extract combines document parsing, AI structured extraction, evidence validation, scientific normalization, review, search, export, and team workflows."
          align="center"
        />
        <div className="mt-12 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {modules.map((module) => (
            <FeatureCard key={module.title} icon={module.icon} title={module.title} description={module.description}>
              <div className="flex flex-wrap gap-2">
                {module.tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
              </div>
            </FeatureCard>
          ))}
        </div>
      </section>
    </div>
  );
}
