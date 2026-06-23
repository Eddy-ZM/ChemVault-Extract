import type { Document } from "@chemvault-extract/schemas";

import { DocumentsTable } from "@/components/documents-table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { PageHeader } from "@/components/product-ui";
import { Button } from "@/components/ui/button";
import { listDocuments } from "@/lib/api";
import Link from "next/link";

export default async function DocumentsPage() {
  let documents: Document[] = [];
  let error: string | null = null;

  try {
    documents = await listDocuments();
  } catch (err) {
    error = err instanceof Error ? err.message : "Unable to reach API";
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Documents"
        description="Uploaded source files, parsing status, extraction status, review readiness, and project scope."
        actions={
          <>
            <Button asChild>
              <Link href="/documents/upload">Upload</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/documents/batch-upload">Batch upload</Link>
            </Button>
          </>
        }
      />

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>API unavailable</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : (
        <DocumentsTable documents={documents} />
      )}
    </div>
  );
}
