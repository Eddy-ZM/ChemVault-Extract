import Link from "next/link";
import type { BatchJob, Document, Project } from "@chemvault-extract/schemas";

import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate } from "@/lib/format";
import { listBatchJobs, listDocuments, listProjects } from "@/lib/api";

import { BatchExtractForm } from "./batch-extract-form";

export default async function BatchJobsPage() {
  let jobs: BatchJob[] = [];
  let documents: Document[] = [];
  let projects: Project[] = [];
  let error: string | null = null;

  try {
    [jobs, documents, projects] = await Promise.all([listBatchJobs(), listDocuments(), listProjects()]);
  } catch (err) {
    error = err instanceof Error ? err.message : "Unable to load batch jobs";
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-normal">Batch jobs</h1>
          <p className="text-sm text-muted-foreground">Monitor batch uploads and batch AI extraction work.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/documents/batch-upload">Batch upload</Link>
        </Button>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Batch jobs unavailable</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : (
        <>
          <BatchExtractForm projects={projects} documents={documents} />
          <Card>
            <CardHeader>
              <CardTitle>Recent batch jobs</CardTitle>
              <CardDescription>{jobs.length} latest jobs</CardDescription>
            </CardHeader>
            <CardContent>
              {jobs.length === 0 ? (
                <div className="flex min-h-36 items-center justify-center rounded-md border border-dashed">
                  <p className="text-sm text-muted-foreground">No batch jobs yet.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Progress</TableHead>
                      <TableHead>Cost</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Open</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobs.map((job) => (
                      <TableRow key={job.id}>
                        <TableCell>{job.type.replaceAll("_", " ")}</TableCell>
                        <TableCell>
                          <StatusBadge status={job.status} />
                        </TableCell>
                        <TableCell>
                          {job.completedItems}/{job.totalItems} complete · {job.failedItems} failed
                        </TableCell>
                        <TableCell>${job.estimatedTotalCostUsd.toFixed(4)}</TableCell>
                        <TableCell>{formatDate(job.createdAt)}</TableCell>
                        <TableCell className="text-right">
                          <Button asChild size="sm" variant="outline">
                            <Link href={`/batch/${job.id}`}>View</Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
