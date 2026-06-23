"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Users } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function WorkspaceCreateForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    try {
      const response = await fetch("/api/workspaces", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to create workspace");
      router.push(`/workspaces/${body.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create workspace");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>Create workspace</CardTitle>
        <CardDescription>Team workspaces are available on Lab or admin plans.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-5" onSubmit={onSubmit}>
          <div className="grid gap-2">
            <Label htmlFor="workspace-name">Workspace name</Label>
            <Input
              id="workspace-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Synthesis Lab"
              disabled={isSaving}
              required
            />
          </div>
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Workspace not created</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          <Button className="w-fit" type="submit" disabled={isSaving}>
            {isSaving ? <Loader2 data-icon="inline-start" className="animate-spin" /> : <Users data-icon="inline-start" />}
            {isSaving ? "Creating" : "Create workspace"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
