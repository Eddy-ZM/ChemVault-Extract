import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-normal">Settings</h1>
        <p className="text-sm text-muted-foreground">Workspace configuration and API key management.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>AI extraction</CardTitle>
            <CardDescription>Manage AI provider model settings and API key mode.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href="/settings/ai">Open AI settings</Link>
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Developer API keys</CardTitle>
            <CardDescription>Create scoped keys for uploads, extraction, records, and exports.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline">
              <Link href="/settings/api-keys">Manage API keys</Link>
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Webhooks</CardTitle>
            <CardDescription>Configure signed delivery endpoints for workflow events.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline">
              <Link href="/settings/webhooks">Manage webhooks</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
