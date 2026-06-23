import Link from "next/link";
import { Users } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate } from "@/lib/format";
import { listWorkspaces } from "@/lib/api";

export default async function WorkspacesPage() {
  try {
    const workspaces = await listWorkspaces();
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-2">
            <h1 className="text-2xl font-semibold tracking-normal">Workspaces</h1>
            <p className="text-sm text-muted-foreground">Team-scoped projects, documents, usage, and batch jobs.</p>
          </div>
          <Button asChild>
            <Link href="/workspaces/new">
              <Users data-icon="inline-start" />
              New workspace
            </Link>
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>My workspaces</CardTitle>
            <CardDescription>{workspaces.length} active workspace memberships</CardDescription>
          </CardHeader>
          <CardContent>
            {workspaces.length === 0 ? (
              <div className="flex min-h-40 flex-col items-center justify-center gap-3 rounded-md border border-dashed">
                <p className="text-sm text-muted-foreground">No team workspaces yet.</p>
                <Button asChild size="sm">
                  <Link href="/workspaces/new">Create workspace</Link>
                </Button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Open</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {workspaces.map((workspace) => (
                    <TableRow key={workspace.id}>
                      <TableCell className="font-medium">{workspace.name}</TableCell>
                      <TableCell>{workspace.plan}</TableCell>
                      <TableCell>{formatDate(workspace.createdAt)}</TableCell>
                      <TableCell className="text-right">
                        <Button asChild size="sm" variant="outline">
                          <Link href={`/workspaces/${workspace.id}`}>View</Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Workspaces unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load workspaces"}</AlertDescription>
      </Alert>
    );
  }
}
