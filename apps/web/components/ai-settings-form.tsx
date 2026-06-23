"use client";

import { FormEvent, useState } from "react";
import type { UserAiSettings } from "@chemvault-extract/schemas";
import { KeyRound, Save, TestTube2, Trash2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function AiSettingsForm({ initialSettings }: { initialSettings: UserAiSettings }) {
  const [settings, setSettings] = useState(initialSettings);
  const [useOwnApiKey, setUseOwnApiKey] = useState(initialSettings.useOwnApiKey);
  const [openaiApiKey, setOpenaiApiKey] = useState("");
  const [defaultModel, setDefaultModel] = useState(initialSettings.defaultModel);
  const [fallbackModel, setFallbackModel] = useState(initialSettings.fallbackModel);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const response = await fetch("/api/settings/ai", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          useOwnApiKey,
          openaiApiKey: openaiApiKey.trim() || null,
          defaultModel,
          fallbackModel,
        }),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail ?? "Unable to save AI settings");
      }
      setSettings(body as UserAiSettings);
      setOpenaiApiKey("");
      setMessage("AI settings saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save AI settings");
    } finally {
      setBusy(false);
    }
  }

  async function testKey() {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const response = await fetch("/api/settings/ai/test-openai-key", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ openaiApiKey: openaiApiKey.trim() || null }),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail ?? "OpenAI key test failed");
      }
      setMessage(body.message ?? "OpenAI key test completed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "OpenAI key test failed");
    } finally {
      setBusy(false);
    }
  }

  async function deleteKey() {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const response = await fetch("/api/settings/ai/openai-key", { method: "DELETE" });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail ?? "Unable to delete key");
      }
      setSettings(body as UserAiSettings);
      setUseOwnApiKey(false);
      setOpenaiApiKey("");
      setMessage("Saved OpenAI key deleted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete key");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,720px)_minmax(280px,1fr)]">
      <Card>
        <CardHeader>
          <CardTitle>AI settings</CardTitle>
          <CardDescription>Choose platform billing or your own OpenAI API key.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Settings update failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          {message ? (
            <Alert>
              <AlertTitle>Settings updated</AlertTitle>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          ) : null}
          <form className="flex flex-col gap-5" onSubmit={save}>
            <div className="flex items-center gap-3 rounded-md border p-3">
              <input
                id="useOwnApiKey"
                type="checkbox"
                className="size-4"
                checked={useOwnApiKey}
                disabled={!settings.allowUserOpenAiKeys || busy}
                onChange={(event) => setUseOwnApiKey(event.target.checked)}
              />
              <Label htmlFor="useOwnApiKey">Use my own OpenAI API key</Label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-2">
                <Label htmlFor="defaultModel">Default model</Label>
                <Input id="defaultModel" value={defaultModel} onChange={(event) => setDefaultModel(event.target.value)} />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="fallbackModel">Fallback model</Label>
                <Input id="fallbackModel" value={fallbackModel} onChange={(event) => setFallbackModel(event.target.value)} />
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="openaiApiKey">OpenAI API key</Label>
              <Input
                id="openaiApiKey"
                type="password"
                placeholder={settings.maskedOpenAiApiKey ?? "sk-..."}
                value={openaiApiKey}
                disabled={!settings.allowUserOpenAiKeys || busy}
                onChange={(event) => setOpenaiApiKey(event.target.value)}
              />
              <span className="text-xs text-muted-foreground">
                Saved key: {settings.maskedOpenAiApiKey ?? "No user key saved"}
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={busy}>
                <Save data-icon="inline-start" />
                Save
              </Button>
              <Button type="button" variant="outline" onClick={testKey} disabled={busy || (!openaiApiKey && !settings.hasOpenAiApiKey)}>
                <TestTube2 data-icon="inline-start" />
                Test key
              </Button>
              <Button type="button" variant="outline" onClick={deleteKey} disabled={busy || !settings.hasOpenAiApiKey}>
                <Trash2 data-icon="inline-start" />
                Delete key
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <KeyRound className="size-4" />
            Current provider
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm">
          <Detail label="Provider" value={settings.provider} />
          <Detail label="Key mode" value={useOwnApiKey ? "User key" : "Platform key"} />
          <Detail label="User keys enabled" value={settings.allowUserOpenAiKeys ? "Yes" : "No"} />
        </CardContent>
      </Card>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <span>{value}</span>
    </div>
  );
}
