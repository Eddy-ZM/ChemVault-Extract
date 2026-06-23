"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import type { Project } from "@chemvault-extract/schemas";
import { Download, Loader2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export function ExportCreateForm({ projects }: { projects: Project[] }) {
  const router = useRouter();
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [exportFormat, setExportFormat] = useState("json");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    try {
      const response = await fetch("/api/exports", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ projectId, exportFormat }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to create export");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create export");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="grid gap-4 md:grid-cols-[1fr_180px_auto]" onSubmit={onSubmit}>
      <select
        className="h-10 rounded-md border border-input bg-background px-3 text-sm"
        value={projectId}
        onChange={(event) => setProjectId(event.target.value)}
        disabled={isSaving}
        required
      >
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
            {project.workspaceId ? " (workspace)" : " (personal)"}
          </option>
        ))}
      </select>
      <select
        className="h-10 rounded-md border border-input bg-background px-3 text-sm"
        value={exportFormat}
        onChange={(event) => setExportFormat(event.target.value)}
        disabled={isSaving}
      >
        <option value="csv">CSV</option>
        <option value="json">JSON</option>
        <option value="xlsx">XLSX</option>
      </select>
      <Button type="submit" disabled={isSaving || projects.length === 0}>
        {isSaving ? <Loader2 data-icon="inline-start" className="animate-spin" /> : <Download data-icon="inline-start" />}
        Create export
      </Button>
      {error ? (
        <Alert variant="destructive" className="md:col-span-3">
          <AlertTitle>Export failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}
    </form>
  );
}
