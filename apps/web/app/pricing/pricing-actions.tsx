"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";

export function SubscribeButtons({ plan }: { plan: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState<"monthly" | "yearly" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function subscribe(interval: "monthly" | "yearly") {
    setLoading(interval);
    setError(null);
    const response = await fetch("/api/billing/create-checkout-session", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ plan, billing_interval: interval }),
    }).catch(() => null);
    if (!response) {
      setError("Unable to reach billing API.");
      setLoading(null);
      return;
    }
    if (response.status === 401) {
      router.push(`/login?next=${encodeURIComponent("/pricing")}`);
      return;
    }
    if (!response.ok) {
      const body = await response.text();
      setError(body || "Unable to create checkout session.");
      setLoading(null);
      return;
    }
    const body = (await response.json()) as { checkoutUrl: string };
    window.location.href = body.checkoutUrl;
  }

  return (
    <div className="grid gap-2">
      <Button onClick={() => subscribe("monthly")} disabled={loading !== null}>
        {loading === "monthly" ? <Loader2 data-icon="inline-start" className="animate-spin" /> : null}
        Subscribe monthly
      </Button>
      <Button variant="outline" onClick={() => subscribe("yearly")} disabled={loading !== null}>
        {loading === "yearly" ? <Loader2 data-icon="inline-start" className="animate-spin" /> : null}
        Subscribe yearly
      </Button>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
