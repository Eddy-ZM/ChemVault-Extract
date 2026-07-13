export type DocsSection = {
  id: string;
  title: string;
  body: string[];
  code?: {
    language: string;
    value: string;
  };
};

export type DocsPage = {
  slug: string;
  title: string;
  description: string;
  sections: DocsSection[];
};

const retiredSections: DocsSection[] = [
  {
    id: "successor",
    title: "ChemVault Lab is the successor",
    body: [
      "ChemVault Extract is retired. Upload, analysis, review, search, export, Files writeback, and account-scoped history now live in ChemVault Lab.",
      "Open https://lab.chemvault.science and sign in with ChemVault User before selecting or uploading files.",
    ],
  },
  {
    id: "developer-api",
    title: "Hosted developer API retired",
    body: [
      "The former api.chemvault.science /v1 API and its API-key SDKs no longer have a hosted endpoint.",
      "Legacy SDKs require an explicit self-hosted base URL. They must not be pointed at ChemVault Lab because Lab uses an authenticated user-session contract.",
    ],
  },
];

const legacyPages = [
  "getting-started",
  "upload-documents",
  "ai-extraction",
  "review-workflow",
  "search",
  "export",
  "api",
  "api-authentication",
  "api-reference",
  "sdks",
  "sdks/javascript",
  "sdks/python",
];

export const docsPages: DocsPage[] = [
  {
    slug: "",
    title: "ChemVault Extract retirement",
    description: "ChemVault Extract documentation has moved to ChemVault Lab.",
    sections: retiredSections,
  },
  ...legacyPages.map((slug) => ({
    slug,
    title: "Documentation moved to ChemVault Lab",
    description: "This legacy ChemVault Extract guide is retired.",
    sections: retiredSections,
  })),
];

export function getDocsPage(slug: string) {
  return docsPages.find((page) => page.slug === slug) || docsPages[0];
}
