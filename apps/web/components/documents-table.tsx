import Link from "next/link";
import type { Document } from "@chemvault-extract/schemas";

import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate } from "@/lib/format";

export function DocumentsTable({ documents, title = "Documents" }: { documents: Document[]; title?: string }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <CardTitle>{title}</CardTitle>
          <CardDescription>{documents.length} files in the current project</CardDescription>
        </div>
        <Button asChild size="sm">
          <Link href="/documents/upload">Upload</Link>
        </Button>
      </CardHeader>
      <CardContent>
        {documents.length === 0 ? (
          <div className="flex min-h-40 flex-col items-center justify-center gap-3 rounded-md border border-dashed">
            <p className="text-sm text-muted-foreground">No documents yet.</p>
            <Button asChild size="sm">
              <Link href="/documents/upload">Upload a file</Link>
            </Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Upload</TableHead>
                <TableHead>Job</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Open</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.map((document) => (
                <TableRow key={document.id}>
                  <TableCell className="max-w-80 font-medium">
                    <span className="block truncate">{document.originalFilename}</span>
                  </TableCell>
                  <TableCell className="uppercase">{document.fileType}</TableCell>
                  <TableCell>
                    <StatusBadge status={document.status} />
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={document.latestJob?.status} />
                  </TableCell>
                  <TableCell>{formatDate(document.createdAt)}</TableCell>
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
