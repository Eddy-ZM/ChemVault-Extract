"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { Document } from "@chemvault-extract/schemas";
import { RefreshCw } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate, statusLabel } from "@/lib/format";

const visiblePipeline = ["queued", "parsing", "chunking", "review_ready"];

export function DocumentDetailClient({ initialDocument }: { initialDocument: Document }) {
  const [document, setDocument] = useState(initialDocument);
  const [error, setError] = useState<string | null>(null);
  const latestJob = document.latestJob;
  const currentIndex = useMemo(
    () => visiblePipeline.findIndex((status) => status === latestJob?.status),
    [latestJob?.status],
  );

  useEffect(() => {
    if (latestJob?.status === "review_ready" || latestJob?.status === "failed") return;

    const interval = window.setInterval(async () => {
      try {
        const response = await fetch(`/api/documents/${document.id}`);
        const body = await response.json();
        if (!response.ok) {
          throw new Error(body.detail ?? "Unable to refresh document");
        }
        setDocument(body as Document);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to refresh document");
      }
    }, 2000);

    return () => window.clearInterval(interval);
  }, [document.id, latestJob?.status]);

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
      <Card>
        <CardHeader>
          <CardTitle>{document.originalFilename}</CardTitle>
          <CardDescription>Document ID: {document.id}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <DetailItem label="Stored filename" value={document.filename} />
          <DetailItem label="File type" value={document.fileType.toUpperCase()} />
          <DetailItem label="MIME type" value={document.mimeType} />
          <DetailItem label="Uploaded" value={formatDate(document.createdAt)} />
          <div className="flex flex-col gap-2">
            <span className="text-xs font-medium text-muted-foreground">Upload status</span>
            <StatusBadge status={document.status} />
          </div>
          <DetailItem label="Storage key" value={document.storageKey} mono />
        </CardContent>
      </Card>

      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-3 text-base">
              Extraction job
              <StatusBadge status={latestJob?.status} />
            </CardTitle>
            <CardDescription>{latestJob ? `Job ID: ${latestJob.id}` : "No extraction job"}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {latestJob ? (
              <>
                <div className="flex flex-col gap-3">
                  {visiblePipeline.map((status, index) => {
                    const complete = latestJob.status === "review_ready" || index <= currentIndex;
                    return (
                      <div key={status} className="flex items-center gap-3">
                        <div
                          className={
                            complete
                              ? "size-2.5 rounded-full bg-primary"
                              : "size-2.5 rounded-full border border-border bg-background"
                          }
                        />
                        <span className={complete ? "text-sm" : "text-sm text-muted-foreground"}>{statusLabel(status)}</span>
                      </div>
                    );
                  })}
                </div>
                {latestJob.error ? (
                  <Alert variant="destructive">
                    <AlertTitle>Job failed</AlertTitle>
                    <AlertDescription>{latestJob.error}</AlertDescription>
                  </Alert>
                ) : null}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No job has been created for this document.</p>
            )}
            <div className="flex gap-2">
              <Button asChild variant="outline" size="sm">
                <Link href="/documents">Documents</Link>
              </Button>
              <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                <RefreshCw data-icon="inline-start" />
                Refresh
              </Button>
            </div>
          </CardContent>
        </Card>
        {error ? (
          <Alert variant="destructive">
            <AlertTitle>Refresh failed</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}
      </div>
    </div>
  );
}

function DetailItem({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <span className={mono ? "break-all font-mono text-xs" : "break-words text-sm"}>{value}</span>
    </div>
  );
}
