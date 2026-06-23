import type { Metadata } from "next";

import { DocsShell } from "./docs-shell";
import { getDocsPage } from "./docs-data";

export const metadata: Metadata = {
  title: "Docs — ChemVault Extract",
  description: "Documentation for ChemVault Extract product workflows and developer API access.",
};

export default function DocsPage() {
  const page = getDocsPage("");
  if (!page) return null;
  return <DocsShell page={page} />;
}
