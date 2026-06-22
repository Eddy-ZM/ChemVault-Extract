import Link from "next/link";
import type { Document } from "@chemvault-extract/schemas";
import { Database, FileUp } from "lucide-react";

import { DashboardCards } from "@/components/dashboard-cards";
import { DocumentsTable } from "@/components/documents-table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { listDocuments } from "@/lib/api";

export default async function HomePage() {
  let documents: Document[] = [];
  let error: string | null = null;

  try {
    documents = await listDocuments();
  } catch (err) {
    error = err instanceof Error ? err.message : "Unable to reach API";
  }

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="flex max-w-3xl flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-normal">ChemVault Extract</h1>
          <p className="text-sm text-muted-foreground">
            Upload chemistry papers, lab reports, and instrument exports into an evidence-backed ingestion pipeline.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild>
            <Link href="/documents/upload">
              <FileUp data-icon="inline-start" />
              Upload
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/documents">
              <Database data-icon="inline-start" />
              Documents
            </Link>
          </Button>
        </div>
      </section>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>API unavailable</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : (
        <>
          <DashboardCards documents={documents} />
          <DocumentsTable documents={documents.slice(0, 5)} title="Recent documents" />
        </>
      )}
    </div>
  );
}
