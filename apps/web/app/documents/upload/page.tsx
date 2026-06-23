import { UploadForm } from "@/app/documents/upload/upload-form";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { listProjects } from "@/lib/api";
import type { Project } from "@chemvault-extract/schemas";

export default async function UploadPage() {
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
        <h1 className="text-2xl font-semibold tracking-normal">Upload</h1>
        <p className="text-sm text-muted-foreground">Create a document record and queue the first extraction job.</p>
      </div>
      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Projects unavailable</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : (
        <UploadForm projects={projects} />
      )}
    </div>
  );
}
