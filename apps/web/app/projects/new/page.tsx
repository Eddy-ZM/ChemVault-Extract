import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { listWorkspaces } from "@/lib/api";

import { ProjectCreateForm } from "./project-create-form";

export default async function NewProjectPage({
  searchParams,
}: {
  searchParams: Promise<{ workspaceId?: string; workspace_id?: string }>;
}) {
  const params = await searchParams;
  try {
    const workspaces = await listWorkspaces();
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-normal">New project</h1>
          <p className="text-sm text-muted-foreground">Create a personal or team-scoped project before uploading documents.</p>
        </div>
        <ProjectCreateForm workspaces={workspaces} initialWorkspaceId={params.workspaceId ?? params.workspace_id ?? ""} />
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Projects unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load workspace list"}</AlertDescription>
      </Alert>
    );
  }
}
