"use client";

import { useState } from "react";
import Link from "next/link";
import { ExternalLink, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";

export function ManageBillingButton({ disabled }: { disabled?: boolean }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function openPortal() {
    setLoading(true);
    setError(null);
    const response = await fetch("/api/billing/create-portal-session", { method: "POST" }).catch(() => null);
    if (!response) {
      setError("Unable to reach billing API.");
      setLoading(false);
      return;
    }
    if (!response.ok) {
      const body = await response.text();
      setError(body || "Unable to create portal session.");
      setLoading(false);
      return;
    }
    const body = (await response.json()) as { portalUrl: string };
    window.location.href = body.portalUrl;
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        <Button onClick={openPortal} disabled={disabled || loading}>
          {loading ? <Loader2 data-icon="inline-start" className="animate-spin" /> : <ExternalLink data-icon="inline-start" />}
          Manage billing
        </Button>
        <Button asChild variant="outline">
          <Link href="/pricing">Compare plans</Link>
        </Button>
      </div>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
