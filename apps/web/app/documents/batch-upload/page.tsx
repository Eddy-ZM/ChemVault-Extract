import type { Project } from "@chemvault-extract/schemas";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { listProjects } from "@/lib/api";

import { BatchUploadForm } from "./batch-upload-form";

export default async function BatchUploadPage() {
  let projects: Project[] = [];
  let error: string | null = null;

  try {
    projects = await listProjects();
  } catch (err) {
    error = err instanceof Error ? err.message : "Unable to load projects";
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-normal">Batch upload</h1>
        <p className="text-sm text-muted-foreground">Upload multiple scientific files into one project and monitor parse progress.</p>
      </div>
      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Projects unavailable</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : (
        <BatchUploadForm projects={projects} />
      )}
    </div>
  );
}
