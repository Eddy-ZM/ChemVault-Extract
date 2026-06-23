import { WorkspaceCreateForm } from "./workspace-create-form";

export default function NewWorkspacePage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-normal">New workspace</h1>
        <p className="text-sm text-muted-foreground">Create a shared workspace for lab projects, documents, and batch jobs.</p>
      </div>
      <WorkspaceCreateForm />
    </div>
  );
}
