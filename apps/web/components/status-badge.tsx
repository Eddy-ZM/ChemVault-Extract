import { Badge } from "@/components/ui/badge";
import { statusLabel } from "@/lib/format";

type StatusValue = string | undefined | null;

export function StatusBadge({ status }: { status: StatusValue }) {
  if (status === "failed" || status === "rejected") {
    return <Badge variant="destructive">{statusLabel(status)}</Badge>;
  }

  if (status === "review_ready" || status === "approved") {
    return <Badge>{statusLabel(status)}</Badge>;
  }

  if (status === "queued" || status === "uploaded" || status === "pending") {
    return <Badge variant="secondary">{statusLabel(status)}</Badge>;
  }

  if (status === "parsed" || status === "needs_review") {
    return <Badge variant="outline">{statusLabel(status)}</Badge>;
  }

  return <Badge variant="outline">{statusLabel(status)}</Badge>;
}
