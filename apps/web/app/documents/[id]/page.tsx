import { DocumentDetailClient } from "@/app/documents/[id]/document-detail-client";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getDocument } from "@/lib/api";

export default async function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  try {
    const document = await getDocument(id);
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-normal">Document detail</h1>
          <p className="text-sm text-muted-foreground">Uploaded file metadata and extraction job status.</p>
        </div>
        <DocumentDetailClient initialDocument={document} />
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Document unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load document"}</AlertDescription>
      </Alert>
    );
  }
}
