import Link from "next/link";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { getWorkspace } from "@/lib/api";

import { MembersClient } from "./members-client";

export default async function WorkspaceMembersPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const workspace = await getWorkspace(id);
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-2">
            <h1 className="text-2xl font-semibold tracking-normal">Workspace members</h1>
            <p className="text-sm text-muted-foreground">{workspace.name}</p>
          </div>
          <Button asChild variant="outline">
            <Link href={`/workspaces/${workspace.id}`}>Back to workspace</Link>
          </Button>
        </div>
        <MembersClient workspace={workspace} />
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Members unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load members"}</AlertDescription>
      </Alert>
    );
  }
}
