import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getDocument } from "@/lib/api";

import { ReviewItemsClient } from "./review-items-client";

export default async function DocumentReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  try {
    const document = await getDocument(id);

    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-normal">Extraction review</h1>
          <p className="text-sm text-muted-foreground">{document.originalFilename}</p>
        </div>
        <ReviewItemsClient documentId={document.id} />
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Review unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load review workspace"}</AlertDescription>
      </Alert>
    );
  }
}
