import Link from "next/link";
import { BookOpen, KeyRound, TerminalSquare } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/product-ui";

const baseUrl = "https://api.chemvault.science";

export default function DevelopersPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Developers"
        description="Use the ChemVault API to upload scientific documents, run extraction, query reviewed records, and create exports."
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TerminalSquare className="size-5 text-amber-500" />
              Base URL
            </CardTitle>
            <CardDescription>Use API keys for server-side integrations.</CardDescription>
          </CardHeader>
          <CardContent>
            <code className="rounded-md bg-muted px-2 py-1 text-sm">{baseUrl}</code>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KeyRound className="size-5 text-amber-500" />
              API keys
            </CardTitle>
            <CardDescription>Create scoped keys and revoke them any time.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href="/settings/api-keys">Create API key</Link>
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="size-5 text-amber-500" />
              API docs
            </CardTitle>
            <CardDescription>Endpoint reference with curl and Python examples.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline">
              <Link href="/docs/api-reference">Open reference</Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick start</CardTitle>
          <CardDescription>Upload a document with a key that has documents:write scope.</CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="overflow-x-auto rounded-md bg-slate-950 p-4 text-xs text-slate-50">
{`curl -X POST ${baseUrl}/v1/documents \\
  -H "Authorization: Bearer cv_live_xxxxx" \\
  -F "project_id=proj_123" \\
  -F "file=@paper.pdf"`}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
