import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader, StatCard } from "@/components/product-ui";
import { getDeveloperUsage } from "@/lib/api";

export default async function DeveloperUsagePage() {
  try {
    const usage = await getDeveloperUsage();
    return (
      <div className="flex flex-col gap-6">
        <PageHeader title="Developer API usage" description="API requests, API-created extraction jobs, estimated AI cost, and current rate limits." />
        <div className="grid gap-4 md:grid-cols-4">
          <StatCard label="Requests this month" value={usage.requestsThisMonth.toLocaleString()} />
          <StatCard label="Active API keys" value={usage.apiKeysActive.toLocaleString()} />
          <StatCard label="API extraction jobs" value={usage.extractionJobsCreatedByApi.toLocaleString()} />
          <StatCard label="Estimated AI cost" value={`$${usage.estimatedAiCostUsd.toFixed(4)}`} />
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Rate limits</CardTitle>
            <CardDescription>Limits are enforced by plan and keyed by user or API key.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
            <div className="rounded-md border p-4">
              <div className="text-muted-foreground">Requests per minute</div>
              <div className="mt-1 text-2xl font-semibold">{usage.rateLimit.per_minute.toLocaleString()}</div>
            </div>
            <div className="rounded-md border p-4">
              <div className="text-muted-foreground">Requests per day</div>
              <div className="mt-1 text-2xl font-semibold">{usage.rateLimit.per_day.toLocaleString()}</div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Developer usage unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load developer API usage."}</AlertDescription>
      </Alert>
    );
  }
}
