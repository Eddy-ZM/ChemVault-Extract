"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Check, Loader2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function InviteAcceptClient({ inviteId }: { inviteId: string }) {
  const [state, setState] = useState<"loading" | "accepted" | "failed">("loading");
  const [message, setMessage] = useState("Accepting workspace invite...");

  useEffect(() => {
    let cancelled = false;
    async function acceptInvite() {
      try {
        const response = await fetch(`/api/workspaces/invites/${inviteId}/accept`, { method: "POST" });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(body.detail ?? "Unable to accept invite");
        if (!cancelled) {
          setState("accepted");
          setMessage(`You joined ${body.workspace?.name ?? "the workspace"}.`);
        }
      } catch (err) {
        if (!cancelled) {
          setState("failed");
          setMessage(err instanceof Error ? err.message : "Unable to accept invite");
        }
      }
    }
    acceptInvite();
    return () => {
      cancelled = true;
    };
  }, [inviteId]);

  return (
    <div className="mx-auto flex min-h-[60vh] w-full max-w-xl items-center px-6">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Workspace invite</CardTitle>
          <CardDescription>Accept your ChemVault Extract workspace invitation.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {state === "loading" ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              {message}
            </div>
          ) : null}
          {state === "accepted" ? (
            <Alert>
              <Check className="size-4" />
              <AlertTitle>Invite accepted</AlertTitle>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          ) : null}
          {state === "failed" ? (
            <Alert variant="destructive">
              <AlertTitle>Invite could not be accepted</AlertTitle>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          ) : null}
          <div className="flex gap-2">
            <Button asChild>
              <Link href="/workspaces">Open workspaces</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/dashboard">Dashboard</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
