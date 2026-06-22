"use client";

import { FormEvent, useRef, useState } from "react";
import Link from "next/link";
import type { UploadDocumentResponse } from "@chemvault-extract/schemas";
import { FileUp, Loader2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function UploadForm() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<UploadDocumentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = inputRef.current?.files?.[0];
    if (!file) {
      setError("Select a file before uploading.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setIsUploading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData,
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail ?? "Upload failed");
      }
      setResult(body as UploadDocumentResponse);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,720px)_minmax(320px,1fr)]">
      <Card>
        <CardHeader>
          <CardTitle>Upload document</CardTitle>
          <CardDescription>Accepted formats: PDF, DOCX, CSV, XLSX, TXT, MD</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-5" onSubmit={onSubmit}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="file">Source file</Label>
              <Input
                ref={inputRef}
                id="file"
                name="file"
                type="file"
                accept=".pdf,.docx,.csv,.xlsx,.txt,.md"
                disabled={isUploading}
              />
            </div>
            <div className="flex items-center gap-3">
              <Button type="submit" disabled={isUploading}>
                {isUploading ? <Loader2 data-icon="inline-start" className="animate-spin" /> : <FileUp data-icon="inline-start" />}
                {isUploading ? "Uploading" : "Upload"}
              </Button>
              <Button asChild type="button" variant="outline">
                <Link href="/documents">Documents</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="flex flex-col gap-4">
        {error ? (
          <Alert variant="destructive">
            <AlertTitle>Upload rejected</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        {result ? (
          <Alert>
            <AlertTitle>Upload queued</AlertTitle>
            <AlertDescription>
              <div className="flex flex-col gap-3">
                <dl className="grid gap-2 text-sm">
                  <div className="grid gap-1">
                    <dt className="text-muted-foreground">Document ID</dt>
                    <dd className="break-all font-mono text-xs">{result.document.id}</dd>
                  </div>
                  <div className="grid gap-1">
                    <dt className="text-muted-foreground">Job ID</dt>
                    <dd className="break-all font-mono text-xs">{result.job.id}</dd>
                  </div>
                </dl>
                <Button asChild size="sm">
                  <Link href={`/documents/${result.document.id}`}>Open document</Link>
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Pipeline status</CardTitle>
              <CardDescription>Uploaded files are stored in MinIO, then a queued job is pushed to Redis.</CardDescription>
            </CardHeader>
          </Card>
        )}
      </div>
    </div>
  );
}
