import Link from "next/link";

import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate } from "@/lib/format";
import { getCurrentUser, getWorkspace } from "@/lib/api";

export default async function WorkspaceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const [workspace, user] = await Promise.all([getWorkspace(id), getCurrentUser()]);
    const myMember = workspace.members.find((member) => member.userId === user.id && member.status === "active");
    const canCreateProject = myMember ? ["owner", "admin"].includes(myMember.role) : false;
    const canManageMembers = myMember ? ["owner", "admin"].includes(myMember.role) : false;

    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-2">
            <h1 className="text-2xl font-semibold tracking-normal">{workspace.name}</h1>
            <p className="text-sm text-muted-foreground">
              {myMember ? `Your role: ${myMember.role}` : "Workspace membership"} · plan {workspace.plan}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {canCreateProject ? (
              <Button asChild>
                <Link href={`/projects/new?workspaceId=${workspace.id}`}>New project</Link>
              </Button>
            ) : null}
            {canManageMembers ? (
              <Button asChild variant="outline">
                <Link href={`/workspaces/${workspace.id}/members`}>Members</Link>
              </Button>
            ) : null}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Projects" value={workspace.projects.length.toString()} />
          <MetricCard label="Members" value={workspace.members.filter((member) => member.status === "active").length.toString()} />
          <MetricCard label="Created" value={formatDate(workspace.createdAt)} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Workspace projects</CardTitle>
            <CardDescription>Documents uploaded to these projects share workspace permissions.</CardDescription>
          </CardHeader>
          <CardContent>
            {workspace.projects.length === 0 ? (
              <div className="flex min-h-36 items-center justify-center rounded-md border border-dashed">
                <p className="text-sm text-muted-foreground">No projects in this workspace.</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Scope</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {workspace.projects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell className="font-medium">{project.name}</TableCell>
                      <TableCell>team</TableCell>
                      <TableCell>{formatDate(project.createdAt)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Members</CardTitle>
            <CardDescription>Viewer members can inspect data but cannot upload, extract, export, or review.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            {workspace.members.slice(0, 8).map((member) => (
              <div key={member.id} className="flex items-center justify-between gap-3 rounded-md border p-3 text-sm">
                <div className="min-w-0">
                  <div className="truncate font-medium">{member.invitedEmail ?? member.userId ?? "Unlinked user"}</div>
                  <div className="truncate text-xs text-muted-foreground">{member.role}</div>
                </div>
                <StatusBadge status={member.status} />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Workspace unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load workspace"}</AlertDescription>
      </Alert>
    );
  }
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold tracking-normal">{value}</div>
      </CardContent>
    </Card>
  );
}
