import Link from "next/link";

import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState, PageHeader } from "@/components/product-ui";
import { listReviewItems } from "@/lib/api";

export default async function ReviewPage() {
  try {
    const items = await listReviewItems();
    const pending = items.filter((item) => item.status === "pending" || item.status === "needs_review");
    return (
      <div className="flex flex-col gap-6">
        <PageHeader
          title="Review"
          description="Review extracted records before approval. Individual document review pages provide edit, approve, and reject actions."
        />
        <Card>
          <CardHeader>
            <CardTitle>Pending review items</CardTitle>
            <CardDescription>{pending.length} items awaiting decision across accessible documents</CardDescription>
          </CardHeader>
          <CardContent>
            {pending.length === 0 ? (
              <EmptyState
                title="No pending review items"
                description="Run AI extraction on a parsed document to create evidence-backed review items."
                actionHref="/documents"
                actionLabel="Open documents"
              />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Record type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Evidence</TableHead>
                    <TableHead className="text-right">Open</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pending.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.recordType}</TableCell>
                      <TableCell>
                        <StatusBadge status={item.status} />
                      </TableCell>
                      <TableCell>{item.confidence != null ? item.confidence.toFixed(2) : "-"}</TableCell>
                      <TableCell className="max-w-[520px]">
                        <span className="line-clamp-2 text-sm text-muted-foreground">
                          {typeof item.evidence?.quote === "string" ? item.evidence.quote : "No evidence quote."}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button asChild size="sm" variant="outline">
                          <Link href={`/documents/${item.documentId}/review`}>Review</Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Review unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load review items"}</AlertDescription>
      </Alert>
    );
  }
}
