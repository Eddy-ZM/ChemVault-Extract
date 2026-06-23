import type { Metadata } from "next";

import { SectionHeader } from "@/components/product-ui";

import { ContactForm } from "./contact-form";

export const metadata: Metadata = {
  title: "Contact — ChemVault Extract",
  description: "Contact ChemVault Extract about scientific document extraction and research database workflows.",
};

export default function ContactPage() {
  return (
    <section className="marketing-container py-16 md:py-24">
      <SectionHeader
        title="Talk to us about scientific data extraction."
        description="Share your document workflow and what kind of structured research database you want to build."
        align="center"
      />
      <div className="mt-12">
        <ContactForm />
      </div>
    </section>
  );
}
