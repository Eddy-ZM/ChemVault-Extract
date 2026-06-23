"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import type { BatchExtractAIResponse, Document, Project } from "@chemvault-extract/schemas";
import { Loader2, Sparkles } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

export function BatchExtractForm({ projects, documents }: { projects: Project[]; documents: Document[] }) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [mode, setMode] = useState("selected_documents");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [result, setResult] = useState<BatchExtractAIResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const projectDocuments = useMemo(() => documents.filter((document) => document.projectId === projectId), [documents, projectId]);

  function toggleDocument(documentId: string) {
    setSelectedIds((current) =>
      current.includes(documentId) ? current.filter((id) => id !== documentId) : [...current, documentId],
    );
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectId) {
      setError("Select a project first.");
      return;
    }
    if (mode === "selected_documents" && selectedIds.length === 0) {
      setError("Select at least one document.");
      return;
    }
    setIsRunning(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch("/api/batch/extract-ai", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ project_id: projectId, document_ids: selectedIds, mode }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Batch extraction failed");
      setResult(body as BatchExtractAIResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch extraction failed");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Run batch AI extraction</CardTitle>
        <CardDescription>Available to Researcher, Lab, and admin plans. Backend enforces plan and role checks.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-5" onSubmit={onSubmit}>
          <div className="grid gap-2">
            <Label htmlFor="batch-project">Project</Label>
            <select
              id="batch-project"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={projectId}
              onChange={(event) => {
                setProjectId(event.target.value);
                setSelectedIds([]);
              }}
              disabled={isRunning}
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
            <Label htmlFor="batch-mode">Mode</Label>
            <select
              id="batch-mode"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={mode}
              onChange={(event) => setMode(event.target.value)}
              disabled={isRunning}
            >
              <option value="selected_documents">Selected documents</option>
              <option value="all_unprocessed_documents">All unprocessed documents</option>
            </select>
          </div>
          {mode === "selected_documents" ? (
            <div className="grid gap-2">
              <Label>Documents</Label>
              <div className="max-h-64 overflow-auto rounded-md border">
                {projectDocuments.length === 0 ? (
                  <div className="p-4 text-sm text-muted-foreground">No documents in this project.</div>
                ) : (
                  projectDocuments.map((document) => (
                    <label key={document.id} className="flex cursor-pointer items-center gap-3 border-b p-3 text-sm last:border-b-0">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(document.id)}
                        onChange={() => toggleDocument(document.id)}
                        disabled={isRunning}
                      />
                      <span className="min-w-0 flex-1 truncate">{document.originalFilename}</span>
                      <span className="text-xs uppercase text-muted-foreground">{document.fileType}</span>
                    </label>
                  ))
                )}
              </div>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={isRunning || projects.length === 0}>
              {isRunning ? <Loader2 data-icon="inline-start" className="animate-spin" /> : <Sparkles data-icon="inline-start" />}
              {isRunning ? "Queueing" : "Queue batch extraction"}
            </Button>
            <Button asChild type="button" variant="outline">
              <Link href="/usage">View usage</Link>
            </Button>
          </div>
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Batch extraction rejected</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          {result ? (
            <Alert>
              <AlertTitle>Batch extraction queued</AlertTitle>
              <AlertDescription>
                <div className="grid gap-2">
                  <div>
                    {result.documents} documents · ${result.estimatedTotalCostUsd.toFixed(4)} estimated ·{" "}
                    {result.estimatedInputTokens} input tokens estimated
                  </div>
                  <Button asChild size="sm" className="w-fit">
                    <Link href={`/batch/${result.batchJobId}`}>Open batch job</Link>
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          ) : null}
        </form>
      </CardContent>
    </Card>
  );
}
