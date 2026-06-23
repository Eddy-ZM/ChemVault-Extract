import Link from "next/link";

import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate } from "@/lib/format";
import { getBatchJob } from "@/lib/api";

import { BatchActions } from "./batch-actions";

export default async function BatchJobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const batch = await getBatchJob(id);
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-2">
            <h1 className="text-2xl font-semibold tracking-normal">Batch job</h1>
            <p className="break-all text-sm text-muted-foreground">{batch.id}</p>
          </div>
          <Button asChild variant="outline">
            <Link href="/batch">Back to batch jobs</Link>
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard label="Status" value={batch.status.replaceAll("_", " ")} />
          <MetricCard label="Progress" value={`${Math.round(batch.progress)}%`} />
          <MetricCard label="Completed" value={`${batch.completedItems} / ${batch.totalItems}`} />
          <MetricCard label="Failed" value={batch.failedItems.toString()} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Controls</CardTitle>
            <CardDescription>Cancel only skips queued items. Running worker tasks are allowed to finish.</CardDescription>
          </CardHeader>
          <CardContent>
            <BatchActions batchJobId={batch.id} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Items</CardTitle>
            <CardDescription>{batch.items.length} document-level jobs</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Document</TableHead>
                  <TableHead>Job</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Error</TableHead>
                  <TableHead>Updated</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {batch.items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="max-w-72">
                      {item.documentId ? (
                        <Link className="truncate underline-offset-4 hover:underline" href={`/documents/${item.documentId}`}>
                          {item.documentId}
                        </Link>
                      ) : (
                        "No document"
                      )}
                    </TableCell>
                    <TableCell className="max-w-72 truncate">{item.extractionJobId ?? "not queued"}</TableCell>
                    <TableCell>
                      <StatusBadge status={item.status} />
                    </TableCell>
                    <TableCell className="max-w-80 truncate text-sm text-muted-foreground">{item.error ?? ""}</TableCell>
                    <TableCell>{formatDate(item.updatedAt)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Batch job unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load batch job"}</AlertDescription>
      </Alert>
    );
  }
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold tracking-normal">{value}</div>
      </CardContent>
    </Card>
  );
}
