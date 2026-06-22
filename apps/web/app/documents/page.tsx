import type { Document } from "@chemvault-extract/schemas";

import { DocumentsTable } from "@/components/documents-table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { listDocuments } from "@/lib/api";

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
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-normal">Documents</h1>
        <p className="text-sm text-muted-foreground">Uploaded source files and their latest extraction jobs.</p>
      </div>

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
