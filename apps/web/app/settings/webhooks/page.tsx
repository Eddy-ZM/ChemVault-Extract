import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { PageHeader } from "@/components/product-ui";
import { listWebhookEndpoints } from "@/lib/api";

import { WebhookSettingsClient } from "./webhook-settings-client";

export default async function WebhooksPage() {
  try {
    const endpoints = await listWebhookEndpoints();
    return (
      <div className="flex flex-col gap-6">
        <PageHeader
          title="Webhooks"
          description="Register signed webhook endpoints, send test events, rotate secrets, and inspect delivery history."
        />
        <WebhookSettingsClient endpoints={endpoints} />
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Webhooks unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load webhook settings."}</AlertDescription>
      </Alert>
    );
  }
}
