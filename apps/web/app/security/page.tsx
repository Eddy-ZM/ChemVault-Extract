import type { Metadata } from "next";
import { KeyRound, Lock, ShieldCheck } from "lucide-react";

import { FeatureCard, SectionHeader } from "@/components/product-ui";

export const metadata: Metadata = {
  title: "Security - ChemVault Extract",
  description: "How ChemVault Extract protects private files, projects, API keys, and billing data.",
};

const securityPoints = [
  ["Files are private by default.", "Uploaded documents are scoped to authenticated users and project permissions."],
  ["User projects are isolated.", "Document, record, review, export, and usage APIs enforce project ownership."],
  ["Team permissions control access.", "Workspace roles decide who can view, upload, extract, review, export, or manage members."],
  ["AI extraction sends selected chunks only.", "The pipeline does not send the full raw PDF file to the configured AI provider; references are excluded from extraction selection."],
  ["Evidence quotes allow verification.", "Every record can point back to a source quote, page, section, and document."],
  ["User provider keys are encrypted.", "Supported user-provided API keys are encrypted server-side and never returned in full."],
  ["API keys are masked in the UI.", "Settings pages show only masked key fragments such as sk-****abcd."],
  ["Stripe handles billing.", "Checkout, subscription management, and billing details are handled by Stripe-hosted flows."],
  ["Users can export data.", "Records can be exported by the user according to plan and project permissions."],
];

export default function SecurityPage() {
  return (
    <section className="marketing-container py-16 md:py-24">
      <SectionHeader
        title="Security choices for a scientific SaaS MVP."
        description="ChemVault Extract avoids overstated compliance claims. The current system focuses on privacy defaults, project isolation, encrypted provider keys, evidence verification, and Stripe-hosted billing."
        align="center"
      />
      <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {securityPoints.map(([title, description], index) => (
          <FeatureCard
            key={title}
            icon={index % 3 === 0 ? ShieldCheck : index % 3 === 1 ? Lock : KeyRound}
            title={title}
            description={description}
          />
        ))}
      </div>
    </section>
  );
}
