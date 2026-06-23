import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { PageHeader } from "@/components/product-ui";
import { listApiKeys } from "@/lib/api";

import { ApiKeyManager } from "./api-key-manager";

export default async function ApiKeysPage() {
  try {
    const keys = await listApiKeys();
    return (
      <div className="flex flex-col gap-6">
        <PageHeader
          title="API keys"
          description="Create scoped developer API keys for document upload, extraction, search, records, and export workflows."
        />
        <ApiKeyManager initialKeys={keys} />
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>API keys unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load API keys."}</AlertDescription>
      </Alert>
    );
  }
}
