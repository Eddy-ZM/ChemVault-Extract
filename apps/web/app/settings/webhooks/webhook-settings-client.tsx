"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Copy, PlugZap, RotateCcw, Send, PowerOff, Power } from "lucide-react";
import type {
  WebhookDelivery,
  WebhookEndpoint,
  WebhookEndpointCreateResponse,
  WebhookSecretRotateResponse,
} from "@chemvault-extract/schemas";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const webhookEvents = [
  "document.uploaded",
  "document.parsed",
  "document.parse_failed",
  "extraction.started",
  "extraction.completed",
  "extraction.failed",
  "normalization.completed",
  "normalization.failed",
  "review.item_created",
  "review.item_approved",
  "review.item_rejected",
  "export.completed",
  "export.failed",
  "batch.completed",
  "batch.partial_failed",
  "batch.failed",
];

export function WebhookSettingsClient({ endpoints }: { endpoints: WebhookEndpoint[] }) {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [events, setEvents] = useState<string[]>(["document.parsed", "extraction.completed", "extraction.failed"]);
  const [selectedEndpoint, setSelectedEndpoint] = useState<WebhookEndpoint | null>(endpoints[0] ?? null);
  const [editUrl, setEditUrl] = useState(selectedEndpoint?.url ?? "");
  const [editEvents, setEditEvents] = useState<string[]>(selectedEndpoint?.events ?? []);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [secret, setSecret] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function selectEndpoint(endpoint: WebhookEndpoint) {
    setSelectedEndpoint(endpoint);
    setEditUrl(endpoint.url);
    setEditEvents(endpoint.events);
    setDeliveries([]);
    setError(null);
  }

  function toggleEvent(event: string) {
    setEvents((current) => (current.includes(event) ? current.filter((item) => item !== event) : [...current, event]));
  }

  function toggleEditEvent(event: string) {
    setEditEvents((current) => (current.includes(event) ? current.filter((item) => item !== event) : [...current, event]));
  }

  async function createEndpoint() {
    setBusy(true);
    setError(null);
    setCopied(false);
    try {
      const response = await fetch("/api/settings/webhooks", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ url, events }),
      });
      if (!response.ok) throw new Error(await response.text());
      const body = (await response.json()) as WebhookEndpointCreateResponse;
      setSecret(body.signingSecret);
      setUrl("");
      setSelectedEndpoint(body);
      setEditUrl(body.url);
      setEditEvents(body.events);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save webhook endpoint.");
    } finally {
      setBusy(false);
    }
  }

  async function saveEndpoint() {
    if (!selectedEndpoint) return;
    setError(null);
    const response = await fetch(`/api/settings/webhooks/${selectedEndpoint.id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ url: editUrl, events: editEvents, isActive: selectedEndpoint.isActive }),
    });
    if (!response.ok) {
      setError(await response.text());
      return;
    }
    router.refresh();
  }

  async function setActive(isActive: boolean) {
    if (!selectedEndpoint) return;
    setError(null);
    const response = await fetch(`/api/settings/webhooks/${selectedEndpoint.id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ isActive }),
    });
    if (!response.ok) {
      setError(await response.text());
      return;
    }
    setSelectedEndpoint({ ...selectedEndpoint, isActive });
    router.refresh();
  }

  async function rotateSecret() {
    if (!selectedEndpoint) return;
    setError(null);
    setCopied(false);
    const response = await fetch(`/api/settings/webhooks/${selectedEndpoint.id}/rotate-secret`, { method: "POST" });
    if (!response.ok) {
      setError(await response.text());
      return;
    }
    const body = (await response.json()) as WebhookSecretRotateResponse;
    setSecret(body.signingSecret);
    setSelectedEndpoint({ ...selectedEndpoint, secretPreview: body.secretPreview });
    router.refresh();
  }

  async function sendTest() {
    if (!selectedEndpoint) return;
    setError(null);
    const response = await fetch(`/api/settings/webhooks/${selectedEndpoint.id}/test`, { method: "POST" });
    if (!response.ok) {
      setError(await response.text());
      return;
    }
    await loadDeliveries(selectedEndpoint.id);
  }

  async function loadDeliveries(endpointId = selectedEndpoint?.id) {
    if (!endpointId) return;
    const response = await fetch(`/api/settings/webhooks/${endpointId}/deliveries`, { cache: "no-store" });
    if (!response.ok) {
      setError(await response.text());
      return;
    }
    setDeliveries((await response.json()) as WebhookDelivery[]);
  }

  async function copySecret() {
    if (!secret) return;
    await navigator.clipboard.writeText(secret);
    setCopied(true);
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PlugZap className="size-5 text-amber-500" />
              Add endpoint
            </CardTitle>
            <CardDescription>Secrets are shown once. Store them with the receiving service.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-2">
              <Label htmlFor="webhook-url">Endpoint URL</Label>
              <Input
                id="webhook-url"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://example.com/chemvault-webhook"
              />
            </div>
            <EventSelector events={events} toggleEvent={toggleEvent} />
            {error ? <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
            <Button onClick={createEndpoint} disabled={busy || !url.trim() || events.length === 0}>
              {busy ? "Saving..." : "Save endpoint"}
            </Button>
            {secret ? (
              <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
                <p className="text-sm font-medium text-amber-950">Copy this webhook signing secret now. It will not be shown again.</p>
                <div className="mt-3 flex items-center gap-2 rounded-md bg-white p-2">
                  <code className="min-w-0 flex-1 truncate text-xs">{secret}</code>
                  <Button variant="outline" size="sm" onClick={copySecret}>
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
            <CardTitle>Configured endpoints</CardTitle>
            <CardDescription>{endpoints.length} webhook endpoints.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {endpoints.length === 0 ? (
              <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">No webhook endpoints configured.</div>
            ) : (
              endpoints.map((endpoint) => (
                <button
                  key={endpoint.id}
                  type="button"
                  onClick={() => selectEndpoint(endpoint)}
                  className="w-full rounded-md border p-4 text-left transition-colors hover:border-amber-300"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate font-mono text-sm">{endpoint.url}</div>
                      <div className="mt-1 text-xs text-muted-foreground">{endpoint.secretPreview ?? "whsec_****"}</div>
                    </div>
                    <Badge variant={endpoint.isActive ? "outline" : "secondary"}>{endpoint.isActive ? "active" : "inactive"}</Badge>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {endpoint.events.slice(0, 4).map((event) => (
                      <Badge key={event} variant="secondary">
                        {event}
                      </Badge>
                    ))}
                    {endpoint.events.length > 4 ? <Badge variant="secondary">+{endpoint.events.length - 4}</Badge> : null}
                  </div>
                </button>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Endpoint details</CardTitle>
          <CardDescription>Edit endpoint settings and inspect recent delivery attempts.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {!selectedEndpoint ? (
            <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">Select an endpoint to manage delivery settings.</div>
          ) : (
            <>
              <div className="grid gap-2">
                <Label htmlFor="edit-webhook-url">Endpoint URL</Label>
                <Input id="edit-webhook-url" value={editUrl} onChange={(event) => setEditUrl(event.target.value)} />
              </div>
              <EventSelector events={editEvents} toggleEvent={toggleEditEvent} compact />
              <div className="flex flex-wrap gap-2">
                <Button onClick={saveEndpoint}>Save changes</Button>
                <Button variant="outline" onClick={() => setActive(!selectedEndpoint.isActive)}>
                  {selectedEndpoint.isActive ? <PowerOff data-icon="inline-start" /> : <Power data-icon="inline-start" />}
                  {selectedEndpoint.isActive ? "Deactivate" : "Activate"}
                </Button>
                <Button variant="outline" onClick={rotateSecret}>
                  <RotateCcw data-icon="inline-start" />
                  Rotate secret
                </Button>
                <Button variant="outline" onClick={sendTest}>
                  <Send data-icon="inline-start" />
                  Send test
                </Button>
              </div>
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="text-sm font-semibold">Recent deliveries</h3>
                  <Button variant="outline" size="sm" onClick={() => loadDeliveries()}>
                    Refresh
                  </Button>
                </div>
                <DeliveryTable deliveries={deliveries} />
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function EventSelector({
  events,
  toggleEvent,
  compact = false,
}: {
  events: string[];
  toggleEvent: (event: string) => void;
  compact?: boolean;
}) {
  return (
    <div className="grid gap-2">
      <Label>Events</Label>
      <div className={compact ? "grid max-h-64 gap-2 overflow-auto rounded-md border p-2" : "grid gap-2"}>
        {webhookEvents.map((event) => (
          <label key={event} className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
            <input type="checkbox" checked={events.includes(event)} onChange={() => toggleEvent(event)} />
            <span>{event}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function DeliveryTable({ deliveries }: { deliveries: WebhookDelivery[] }) {
  if (deliveries.length === 0) {
    return <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">No delivery attempts loaded.</div>;
  }
  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="border-b bg-muted/40 text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Event</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Attempts</th>
            <th className="px-3 py-2">Response</th>
            <th className="px-3 py-2">Created</th>
            <th className="px-3 py-2">Delivered</th>
          </tr>
        </thead>
        <tbody>
          {deliveries.map((delivery) => (
            <tr key={delivery.id} className="border-b last:border-0">
              <td className="px-3 py-3 font-mono text-xs">{delivery.eventType}</td>
              <td className="px-3 py-3">
                <Badge variant={delivery.status === "delivered" ? "outline" : delivery.status === "failed" ? "destructive" : "secondary"}>
                  {delivery.status}
                </Badge>
              </td>
              <td className="px-3 py-3">
                {delivery.attemptCount}/{delivery.maxAttempts}
              </td>
              <td className="px-3 py-3">{delivery.responseStatusCode ?? delivery.error ?? "-"}</td>
              <td className="px-3 py-3">{new Date(delivery.createdAt).toLocaleString()}</td>
              <td className="px-3 py-3">{delivery.deliveredAt ? new Date(delivery.deliveredAt).toLocaleString() : "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
