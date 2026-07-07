import type { Metadata } from "next";
import { Check, Download, FileUp, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/product-ui";

export const metadata: Metadata = {
  title: "Demo - ChemVault Extract",
  description: "See a sample ChemVault Extract workflow with clearly labelled sample data.",
};

const reaction = {
  product: "benzyl alcohol derivative",
  reagent: "sodium hypochlorite",
  solvent: "acetic acid",
  temperature: "room temperature",
  yield: "82%",
  evidence: "The product was obtained as a white solid in 82% yield.",
};

export default function DemoPage() {
  return (
    <section className="marketing-container py-16 md:py-24">
      <SectionHeader
        title="Product demo using sample data."
        description="This is a static workflow preview. It does not call the API and does not represent a real extraction run."
        align="center"
      />
      <div className="mt-10 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <Card className="shadow-none">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileUp className="size-5" />
              1. Upload sample paper
            </CardTitle>
            <CardDescription>Sample input: sample_paper_like.txt with abstract, experimental section, results, and table text.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            {["Abstract", "Experimental", "Results", "Tables"].map((section, index) => (
              <div key={section} className="rounded-md border bg-white p-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{section}</span>
                  <span className="text-muted-foreground">parsed section {index + 1}</span>
                </div>
                <div className="mt-3 h-2 rounded-full bg-muted" />
                <div className="mt-2 h-2 w-2/3 rounded-full bg-muted" />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="shadow-none">
          <CardHeader>
            <CardTitle>2. Extracted reaction example</CardTitle>
            <CardDescription>Structured sample JSON with an evidence quote copied from the sample source.</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-6 text-slate-100">
              {JSON.stringify(reaction, null, 2)}
            </pre>
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card className="shadow-none">
          <CardHeader>
            <CardTitle>3. Review card</CardTitle>
            <CardDescription>Raw value, normalized value, evidence, and actions are visible before approval.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <DemoField label="Raw value" value="NaOCl" />
              <DemoField label="Normalized value" value="sodium hypochlorite" />
              <DemoField label="Raw temperature" value="rt" />
              <DemoField label="Normalized temperature" value="room temperature" />
            </div>
            <blockquote className="rounded-md border-l-4 border-blue-400 bg-blue-50 p-4 text-sm leading-6 text-blue-950">
              "The product was obtained as a white solid in 82% yield."
            </blockquote>
            <div className="flex flex-wrap gap-2">
              <Button size="sm">
                <Check data-icon="inline-start" />
                Approve
              </Button>
              <Button size="sm" variant="outline">
                Edit
              </Button>
              <Button size="sm" variant="outline">
                Reject
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-none">
          <CardHeader>
            <CardTitle>4. Search and export preview</CardTitle>
            <CardDescription>Search by reagent, inspect evidence, and export CSV when records are ready.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="flex items-center gap-2 rounded-md border bg-white p-3 text-sm">
              <Search className="size-4 text-muted-foreground" />
              sodium hypochlorite
            </div>
            <div className="rounded-md border bg-white p-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="font-medium">Reaction record</div>
                  <div className="text-sm text-muted-foreground">Experimental - page 4</div>
                </div>
                <Badge>evidence linked</Badge>
              </div>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">{reaction.evidence}</p>
            </div>
            <Button variant="outline" className="w-fit">
              <Download data-icon="inline-start" />
              Export CSV
            </Button>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function DemoField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-white p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm font-medium">{value}</div>
    </div>
  );
}
