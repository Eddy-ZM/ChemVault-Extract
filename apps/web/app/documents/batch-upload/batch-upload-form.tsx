"use client";

import { FormEvent, useRef, useState } from "react";
import Link from "next/link";
import type { BatchUploadResponse, Project } from "@chemvault-extract/schemas";
import { Loader2, UploadCloud } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function BatchUploadForm({ projects }: { projects: Project[] }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [result, setResult] = useState<BatchUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const files = Array.from(inputRef.current?.files ?? []);
    if (!projectId) {
      setError("Create or select a project before uploading.");
      return;
    }
    if (files.length === 0) {
      setError("Select at least one file.");
      return;
    }

    const formData = new FormData();
    formData.append("project_id", projectId);
    for (const file of files) formData.append("files", file);
    setIsUploading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/documents/batch-upload", { method: "POST", body: formData });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Batch upload failed");
      setResult(body as BatchUploadResponse);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,720px)_minmax(320px,1fr)]">
      <Card>
        <CardHeader>
          <CardTitle>Batch upload</CardTitle>
          <CardDescription>Each file creates a Document, parse job, and batch item.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-5">
          <Alert>
            <AlertTitle>AI data handling notice</AlertTitle>
            <AlertDescription>
              AI features may process submitted text, files, or extracted content through third-party AI services. Do not submit
              sensitive personal information, confidential data, or content you do not have permission to process. AI outputs may be
              inaccurate and should be reviewed before use. See the{" "}
              <Link className="underline" href="https://chemvault.science/privacy">
                Privacy Policy
              </Link>
              .
            </AlertDescription>
          </Alert>
          <form className="grid gap-5" onSubmit={onSubmit}>
            <div className="grid gap-2">
              <Label htmlFor="batch-project">Project</Label>
              <select
                id="batch-project"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
                disabled={isUploading}
                required
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                    {project.workspaceId ? " (workspace)" : " (personal)"}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="files">Source files</Label>
              <Input
                ref={inputRef}
                id="files"
                name="files"
                type="file"
                accept=".pdf,.docx,.csv,.xlsx,.txt,.md"
                multiple
                disabled={isUploading}
              />
            </div>
            <div className="flex flex-wrap gap-3">
              <Button type="submit" disabled={isUploading || projects.length === 0}>
                {isUploading ? <Loader2 data-icon="inline-start" className="animate-spin" /> : <UploadCloud data-icon="inline-start" />}
                {isUploading ? "Uploading" : "Upload batch"}
              </Button>
              <Button asChild type="button" variant="outline">
                <Link href="/batch">Batch jobs</Link>
              </Button>
              <Button asChild type="button" variant="ghost">
                <Link href="/projects/new">New project</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="grid gap-4">
        {error ? (
          <Alert variant="destructive">
            <AlertTitle>Batch upload rejected</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}
        {result ? (
          <Alert>
            <AlertTitle>Batch queued</AlertTitle>
            <AlertDescription>
              <div className="grid gap-3">
                <div className="text-sm">{result.documents} documents queued for parsing.</div>
                <dl className="grid gap-1 text-sm">
                  <dt className="text-muted-foreground">Batch job ID</dt>
                  <dd className="break-all font-mono text-xs">{result.batchJobId}</dd>
                </dl>
                <Button asChild size="sm">
                  <Link href={`/batch/${result.batchJobId}`}>Open batch job</Link>
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Batch policy</CardTitle>
              <CardDescription>Uploads are still checked against document and storage limits before files are accepted.</CardDescription>
            </CardHeader>
          </Card>
        )}
      </div>
    </div>
  );
}
