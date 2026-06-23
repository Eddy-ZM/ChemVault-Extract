import Link from "next/link";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/format";
import { getBillingOverview } from "@/lib/api";

import { ManageBillingButton } from "./billing-actions";

export default async function BillingPage() {
  try {
    const billing = await getBillingOverview();
    const subscription = billing.subscription;

    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-normal">Billing</h1>
          <p className="text-sm text-muted-foreground">Stripe is the source of truth for paid subscription status.</p>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <MetricCard label="Current plan" value={billing.usage.plan} />
          <MetricCard label="Subscription status" value={subscription?.status ?? "free"} />
          <MetricCard
            label="Period end"
            value={subscription?.currentPeriodEnd ? formatDate(subscription.currentPeriodEnd) : "No paid period"}
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Subscription</CardTitle>
            <CardDescription>
              {subscription?.cancelAtPeriodEnd ? "This subscription is set to cancel at period end." : "Manage payment methods and subscription changes in Stripe."}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-3 text-sm md:grid-cols-2">
              <Detail label="Billing interval" value={subscription?.billingInterval ?? "none"} />
              <Detail label="Stripe subscription" value={subscription?.stripeSubscriptionId ?? "none"} />
              <Detail label="Latest invoice" value={subscription?.latestInvoiceId ?? "none"} />
              <Detail label="Last payment" value={subscription?.lastPaymentStatus ?? "none"} />
            </div>
            <ManageBillingButton disabled={!subscription?.stripeCustomerId} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Current limits</CardTitle>
            <CardDescription>Usage is enforced by backend plan checks before uploads, AI extraction, and exports.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm md:grid-cols-2">
            <Detail label="AI files" value={`${billing.usage.filesUsed} / ${billing.usage.filesLimit}`} />
            <Detail label="Platform AI cost" value={`$${billing.usage.platformEstimatedCostUsedUsd.toFixed(2)} / $${billing.usage.costLimitUsd.toFixed(2)}`} />
            <Detail label="Projects" value={`${billing.usage.projectsUsed} / ${billing.usage.projectsLimit}`} />
            <Detail label="Documents" value={`${billing.usage.documentsUsed} / ${billing.usage.documentsLimit}`} />
            <Detail label="Storage" value={`${billing.usage.storageUsedMb.toFixed(2)} MB / ${billing.usage.storageLimitMb} MB`} />
            <Detail label="Batch extraction" value={billing.usage.canBatchExtract ? "enabled" : "disabled"} />
          </CardContent>
        </Card>

        {billing.usage.plan === "free" ? (
          <Alert>
            <AlertTitle>Upgrade available</AlertTitle>
            <AlertDescription>
              Paid plans increase extraction, storage, and project limits. <Link className="underline" href="/pricing">Open pricing</Link>.
            </AlertDescription>
          </Alert>
        ) : null}
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Billing unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load billing information."}</AlertDescription>
      </Alert>
    );
  }
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold tracking-normal">{value}</div>
      </CardContent>
    </Card>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border px-3 py-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="truncate font-medium">{value}</span>
    </div>
  );
}
