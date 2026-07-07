"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import type { WorkspaceDetail } from "@chemvault-extract/schemas";
import { Loader2, Send, Trash2 } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function MembersClient({ workspace }: { workspace: WorkspaceDetail }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function invite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setMessage(null);
    setError(null);
    try {
      const response = await fetch(`/api/workspaces/${workspace.id}/invites`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, role }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Invite failed");
      setEmail("");
      setMessage(`Invite created for ${body.invitedEmail}. Email is sent when SMTP is configured. Token: ${body.inviteToken}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invite failed");
    } finally {
      setIsSaving(false);
    }
  }

  async function updateRole(memberId: string, nextRole: string) {
    setError(null);
    const response = await fetch(`/api/workspaces/${workspace.id}/members/${memberId}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ role: nextRole }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      setError(body.detail ?? "Unable to update member role");
      return;
    }
    router.refresh();
  }

  async function removeMember(memberId: string) {
    setError(null);
    const response = await fetch(`/api/workspaces/${workspace.id}/members/${memberId}`, { method: "DELETE" });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      setError(body.detail ?? "Unable to remove member");
      return;
    }
    router.refresh();
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,520px)_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Invite member</CardTitle>
          <CardDescription>Invites are stored in the API. Email is sent automatically when SMTP is configured.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4" onSubmit={invite}>
            <div className="grid gap-2">
              <Label htmlFor="member-email">Email</Label>
              <Input
                id="member-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                disabled={isSaving}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="member-role">Role</Label>
              <select
                id="member-role"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={role}
                onChange={(event) => setRole(event.target.value)}
                disabled={isSaving}
              >
                <option value="admin">Admin</option>
                <option value="member">Member</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>
            <Button className="w-fit" type="submit" disabled={isSaving}>
              {isSaving ? <Loader2 data-icon="inline-start" className="animate-spin" /> : <Send data-icon="inline-start" />}
              {isSaving ? "Inviting" : "Create invite"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Members</CardTitle>
          <CardDescription>{workspace.members.length} active or invited member records</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Member update failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          {message ? (
            <Alert>
              <AlertTitle>Invite ready</AlertTitle>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          ) : null}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {workspace.members.map((member) => (
                <TableRow key={member.id}>
                  <TableCell className="max-w-72">
                    <span className="block truncate">{member.invitedEmail ?? member.userId ?? "Unlinked user"}</span>
                  </TableCell>
                  <TableCell>
                    {member.role === "owner" ? (
                      "owner"
                    ) : (
                      <select
                        className="h-9 rounded-md border border-input bg-background px-2 text-sm"
                        value={member.role}
                        onChange={(event) => updateRole(member.id, event.target.value)}
                        disabled={member.status === "removed"}
                      >
                        <option value="admin">Admin</option>
                        <option value="member">Member</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    )}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={member.status} />
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={member.role === "owner" || member.status === "removed"}
                      onClick={() => removeMember(member.id)}
                    >
                      <Trash2 data-icon="inline-start" />
                      Remove
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
