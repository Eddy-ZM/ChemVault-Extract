"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { RotateCcw, StopCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export function BatchActions({ batchJobId }: { batchJobId: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  async function mutate(path: string) {
    setIsBusy(true);
    setError(null);
    try {
      const response = await fetch(path, { method: "POST" });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail ?? "Batch update failed");
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch update failed");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="grid gap-3">
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" disabled={isBusy} onClick={() => mutate(`/api/batch/jobs/${batchJobId}/cancel`)}>
          <StopCircle data-icon="inline-start" />
          Cancel queued
        </Button>
        <Button variant="outline" disabled={isBusy} onClick={() => mutate(`/api/batch/jobs/${batchJobId}/retry-failed`)}>
          <RotateCcw data-icon="inline-start" />
          Retry failed
        </Button>
      </div>
      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Batch action failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}
