"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import type { Workspace } from "@chemvault-extract/schemas";
import { FolderPlus, Loader2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function ProjectCreateForm({ workspaces, initialWorkspaceId = "" }: { workspaces: Workspace[]; initialWorkspaceId?: string }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [workspaceId, setWorkspaceId] = useState(initialWorkspaceId);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    try {
      const payload: { name: string; workspace_id?: string } = { name };
      if (workspaceId) payload.workspace_id = workspaceId;
      const response = await fetch("/api/projects", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to create project");
      router.push(workspaceId ? `/workspaces/${workspaceId}` : "/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>Create project</CardTitle>
        <CardDescription>Personal projects stay private. Workspace projects inherit team permissions.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-5" onSubmit={onSubmit}>
          <div className="grid gap-2">
            <Label htmlFor="project-name">Project name</Label>
            <Input
              id="project-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Photocatalysis screening"
              disabled={isSaving}
              required
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="project-workspace">Owner</Label>
            <select
              id="project-workspace"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={workspaceId}
              onChange={(event) => setWorkspaceId(event.target.value)}
              disabled={isSaving}
            >
              <option value="">Personal project</option>
              {workspaces.map((workspace) => (
                <option key={workspace.id} value={workspace.id}>
                  {workspace.name}
                </option>
              ))}
            </select>
          </div>
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Project not created</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          <Button className="w-fit" type="submit" disabled={isSaving}>
            {isSaving ? <Loader2 data-icon="inline-start" className="animate-spin" /> : <FolderPlus data-icon="inline-start" />}
            {isSaving ? "Creating" : "Create project"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
