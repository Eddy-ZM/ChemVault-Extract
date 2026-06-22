import type { Document } from "@chemvault-extract/schemas";

import { DashboardCards } from "@/components/dashboard-cards";
import { DocumentsTable } from "@/components/documents-table";
import { RecentJobsTable } from "@/components/recent-jobs-table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { listDocuments } from "@/lib/api";

export default async function DashboardPage() {
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
        <h1 className="text-2xl font-semibold tracking-normal">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Current ingestion volume and extraction queue status.</p>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>API unavailable</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : (
        <>
          <DashboardCards documents={documents} />
          <div className="grid gap-6 xl:grid-cols-2">
            <DocumentsTable documents={documents.slice(0, 8)} title="Latest documents" />
            <RecentJobsTable documents={documents} />
          </div>
        </>
      )}
    </div>
  );
}
