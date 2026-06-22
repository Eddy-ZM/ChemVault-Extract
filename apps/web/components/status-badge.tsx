import type { ExtractionJob } from "@chemvault-extract/schemas";

import { Badge } from "@/components/ui/badge";
import { statusLabel } from "@/lib/format";

type StatusValue = ExtractionJob["status"] | "uploaded" | "parsed" | undefined | null;

export function StatusBadge({ status }: { status: StatusValue }) {
  if (status === "failed") {
    return <Badge variant="destructive">{statusLabel(status)}</Badge>;
  }

  if (status === "review_ready") {
    return <Badge>{statusLabel(status)}</Badge>;
  }

  if (status === "queued" || status === "uploaded") {
    return <Badge variant="secondary">{statusLabel(status)}</Badge>;
  }

  if (status === "parsed") {
    return <Badge variant="outline">{statusLabel(status)}</Badge>;
  }

  return <Badge variant="outline">{statusLabel(status)}</Badge>;
}
