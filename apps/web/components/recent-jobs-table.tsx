import Link from "next/link";
import type { Document, ExtractionJob } from "@chemvault-extract/schemas";

import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate } from "@/lib/format";

type RecentJobRow = {
  document: Document;
  job: ExtractionJob;
};

export function RecentJobsTable({ documents }: { documents: Document[] }) {
  const rows = documents
    .flatMap((document): RecentJobRow[] => (document.latestJob ? [{ document, job: document.latestJob }] : []))
    .sort((a, b) => new Date(b.job.updatedAt).getTime() - new Date(a.job.updatedAt).getTime())
    .slice(0, 8);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent jobs</CardTitle>
        <CardDescription>{rows.length} latest extraction jobs</CardDescription>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <div className="flex min-h-36 items-center justify-center rounded-md border border-dashed">
            <p className="text-sm text-muted-foreground">No extraction jobs yet.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Document</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Updated</TableHead>
                <TableHead className="text-right">Open</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map(({ document, job }) => (
                <TableRow key={job.id}>
                  <TableCell className="max-w-80 font-medium">
                    <span className="block truncate">{document.originalFilename}</span>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={job.status} />
                  </TableCell>
                  <TableCell>{formatDate(job.updatedAt)}</TableCell>
                  <TableCell className="text-right">
                    <Button asChild variant="outline" size="sm">
                      <Link href={`/documents/${document.id}`}>View</Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
