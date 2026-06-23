import Link from "next/link";
import type { Document } from "@chemvault-extract/schemas";
import { FileSpreadsheet, FileText, FileType, FileUp } from "lucide-react";

import { EmptyState } from "@/components/product-ui";
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
          <EmptyState
            icon={FileUp}
            title="No documents yet"
            description="Upload your first scientific document to start building your research database."
            actionHref="/documents/upload"
            actionLabel="Upload a file"
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Project</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Parsing</TableHead>
                <TableHead>Extraction</TableHead>
                <TableHead>Review</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.map((document) => {
                const Icon = fileIcon(document.fileType);
                const parsingStatus = document.status === "parsed" || document.status === "review_ready" ? "parsed" : document.latestJob?.status;
                const extractionStatus = document.latestJob?.jobType === "ai_extraction" ? document.latestJob.status : "not started";
                const reviewStatus = document.status === "review_ready" ? "review_ready" : "pending";
                return (
                  <TableRow key={document.id}>
                    <TableCell className="max-w-80 font-medium">
                      <div className="flex items-center gap-3">
                        <div className="flex size-9 items-center justify-center rounded-md bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                          <Icon className="size-4" />
                        </div>
                        <span className="block truncate">{document.originalFilename}</span>
                      </div>
                    </TableCell>
                    <TableCell className="max-w-40">
                      <span className="block truncate font-mono text-xs text-muted-foreground">{document.projectId}</span>
                    </TableCell>
                    <TableCell className="uppercase">{document.fileType}</TableCell>
                    <TableCell>
                      <StatusBadge status={parsingStatus} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={extractionStatus} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={reviewStatus} />
                    </TableCell>
                    <TableCell>{formatDate(document.createdAt)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button asChild variant="outline" size="sm">
                          <Link href={`/documents/${document.id}`}>View</Link>
                        </Button>
                        <Button asChild variant="outline" size="sm">
                          <Link href={`/documents/${document.id}/review`}>Review</Link>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function fileIcon(fileType: string) {
  if (["csv", "xlsx"].includes(fileType.toLowerCase())) return FileSpreadsheet;
  if (["txt", "md", "docx"].includes(fileType.toLowerCase())) return FileText;
  return FileType;
}
