"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Copy, KeyRound, RotateCcw, ShieldOff } from "lucide-react";
import type { ApiKey, ApiKeyCreateResponse, ApiKeyScope } from "@chemvault-extract/schemas";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const scopes: Array<{ value: ApiKeyScope; label: string }> = [
  { value: "projects:read", label: "Read projects" },
  { value: "projects:write", label: "Write projects" },
  { value: "documents:read", label: "Read documents" },
  { value: "documents:write", label: "Upload documents" },
  { value: "extractions:read", label: "Read extraction jobs" },
  { value: "extractions:write", label: "Run extraction" },
  { value: "records:read", label: "Read records" },
  { value: "exports:read", label: "Read exports" },
  { value: "exports:write", label: "Create exports" },
];

export function ApiKeyManager({ initialKeys }: { initialKeys: ApiKey[] }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [selectedScopes, setSelectedScopes] = useState<ApiKeyScope[]>(["projects:read", "documents:read"]);
  const [expiresInDays, setExpiresInDays] = useState("365");
  const [createdKey, setCreatedKey] = useState<ApiKeyCreateResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const activeKeys = useMemo(() => initialKeys.filter((key) => !key.revokedAt), [initialKeys]);

  async function createKey() {
    setBusy(true);
    setError(null);
    setCopied(false);
    try {
      const response = await fetch("/api/settings/api-keys", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          name,
          scopes: selectedScopes,
          expiresInDays: expiresInDays === "never" ? null : Number(expiresInDays),
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      const body = (await response.json()) as ApiKeyCreateResponse;
      setCreatedKey(body);
      setName("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create API key.");
    } finally {
      setBusy(false);
    }
  }

  async function revokeKey(id: string) {
    setError(null);
    const response = await fetch(`/api/settings/api-keys/${id}/revoke`, { method: "POST" });
    if (!response.ok) {
      setError(await response.text());
      return;
    }
    router.refresh();
  }

  async function copyKey() {
    if (!createdKey) return;
    await navigator.clipboard.writeText(createdKey.plainKey);
    setCopied(true);
  }

  function toggleScope(scope: ApiKeyScope) {
    setSelectedScopes((current) =>
      current.includes(scope) ? current.filter((item) => item !== scope) : [...current, scope],
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="size-5 text-amber-500" />
            Create API key
          </CardTitle>
          <CardDescription>Raw keys are shown once. Store them in your own secret manager.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-2">
            <Label htmlFor="api-key-name">Name</Label>
            <Input id="api-key-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Lab pipeline" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="api-key-expiry">Expiry</Label>
            <select
              id="api-key-expiry"
              className="h-10 rounded-md border bg-background px-3 text-sm"
              value={expiresInDays}
              onChange={(event) => setExpiresInDays(event.target.value)}
            >
              <option value="30">30 days</option>
              <option value="90">90 days</option>
              <option value="365">1 year</option>
              <option value="never">No expiry</option>
            </select>
          </div>
          <div className="grid gap-3">
            <Label>Scopes</Label>
            <div className="grid gap-2">
              {scopes.map((scope) => (
                <label key={scope.value} className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedScopes.includes(scope.value)}
                    onChange={() => toggleScope(scope.value)}
                  />
                  <span>{scope.label}</span>
                  <code className="ml-auto text-xs text-muted-foreground">{scope.value}</code>
                </label>
              ))}
            </div>
          </div>
          {error ? <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
          <Button onClick={createKey} disabled={busy || !name.trim() || selectedScopes.length === 0}>
            {busy ? "Creating..." : "Create key"}
          </Button>
          {createdKey ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
              <p className="text-sm font-medium text-amber-950">Copy this key now. It will not be shown again.</p>
              <div className="mt-3 flex items-center gap-2 rounded-md bg-white p-2">
                <code className="min-w-0 flex-1 truncate text-xs">{createdKey.plainKey}</code>
                <Button variant="outline" size="sm" onClick={copyKey}>
                  {copied ? <Check data-icon="inline-start" /> : <Copy data-icon="inline-start" />}
                  {copied ? "Copied" : "Copy"}
                </Button>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Existing keys</CardTitle>
          <CardDescription>{activeKeys.length} active API keys.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {initialKeys.length === 0 ? (
            <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">Create an API key to start integrating ChemVault Extract.</div>
          ) : (
            initialKeys.map((key) => (
              <div key={key.id} className="rounded-md border p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="font-medium">{key.name}</div>
                    <div className="mt-1 font-mono text-xs text-muted-foreground">{key.maskedKey}</div>
                  </div>
                  <Badge variant={key.revokedAt ? "secondary" : "outline"}>{key.revokedAt ? "revoked" : "active"}</Badge>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {key.scopes.map((scope) => (
                    <Badge key={scope} variant="secondary">
                      {scope}
                    </Badge>
                  ))}
                </div>
                <div className="mt-3 grid gap-1 text-xs text-muted-foreground sm:grid-cols-2">
                  <span>Last used: {key.lastUsedAt ? new Date(key.lastUsedAt).toLocaleString() : "Never"}</span>
                  <span>Expires: {key.expiresAt ? new Date(key.expiresAt).toLocaleDateString() : "No expiry"}</span>
                </div>
                {!key.revokedAt ? (
                  <Button className="mt-4" variant="outline" size="sm" onClick={() => revokeKey(key.id)}>
                    <ShieldOff data-icon="inline-start" />
                    Revoke
                  </Button>
                ) : (
                  <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                    <RotateCcw className="size-3" />
                    Revoked at {new Date(key.revokedAt).toLocaleString()}
                  </div>
                )}
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
