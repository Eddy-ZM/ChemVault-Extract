import type { Metadata } from "next";
import { CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/product-ui";

import { SubscribeButtons } from "./pricing-actions";

export const metadata: Metadata = {
  title: "Pricing - ChemVault Extract",
  description: "Plans for AI scientific data extraction, evidence-backed records, team workspaces, and batch extraction.",
};

const plans = [
  {
    name: "Free",
    plan: "free",
    price: "$0",
    description: "Start building a personal research database.",
    limits: [
      "10 AI extractions / month",
      "2 projects",
      "50 documents",
      "500 MB storage",
      "CSV / JSON export",
      "Supported user key option",
    ],
    highlight: false,
  },
  {
    name: "Student",
    plan: "student",
    price: "Contact us",
    description: "For thesis, coursework, and individual literature review workflows.",
    limits: [
      "100 AI extractions / month",
      "10 projects",
      "1,000 documents",
      "5 GB storage",
      "Structured extraction",
      "Export",
      "Supported user key option",
    ],
    highlight: false,
  },
  {
    name: "Researcher",
    plan: "researcher",
    price: "Contact us",
    description: "For active scientific extraction and repeated review workflows.",
    limits: [
      "500 AI extractions / month",
      "50 projects",
      "10,000 documents",
      "50 GB storage",
      "Batch extraction",
      "Advanced export",
      "Supported user key option",
    ],
    highlight: true,
  },
  {
    name: "Lab",
    plan: "lab",
    price: "Contact us",
    description: "For teams building shared evidence-backed scientific databases.",
    limits: [
      "3,000 AI extractions / month",
      "Team workspace",
      "10 team members",
      "Batch upload",
      "Batch extraction",
      "500 GB storage",
      "Team database",
    ],
    highlight: false,
  },
];

export default function PricingPage() {
  return (
    <section className="marketing-container py-16 md:py-24">
      <SectionHeader
        title="Choose a plan for your research workflow."
        description="Stripe manages paid subscriptions. Plan changes are applied after Stripe webhook confirmation."
        align="center"
      />

      <div className="mt-12 grid gap-4 lg:grid-cols-4">
        {plans.map((item) => (
          <Card key={item.plan} className={item.highlight ? "flex flex-col border-slate-950 shadow-xl shadow-slate-950/10" : "flex flex-col shadow-none"}>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <CardTitle>{item.name}</CardTitle>
                {item.highlight ? <Badge>Popular</Badge> : null}
              </div>
              <CardDescription className="min-h-12 leading-6">{item.description}</CardDescription>
              <div className="text-2xl font-semibold tracking-normal">{item.price}</div>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col gap-5">
              <div className="grid flex-1 gap-2 text-sm">
                {item.limits.map((limit) => (
                  <div key={limit} className="flex items-start gap-2">
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-blue-600" />
                    <span>{limit}</span>
                  </div>
                ))}
              </div>
              {item.plan === "free" ? (
                <Button variant="outline" disabled>
                  Current free tier
                </Button>
              ) : (
                <SubscribeButtons plan={item.plan} />
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="mt-8 shadow-none">
        <CardContent className="p-5 text-sm leading-6 text-muted-foreground">
          AI provider costs may apply depending on whether you use ChemVault hosted credits or a supported user-provided key.
          User-provided keys can reduce platform AI cost usage, but file, storage, project, workspace, and batch limits still apply.
        </CardContent>
      </Card>
    </section>
  );
}
