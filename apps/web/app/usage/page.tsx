import { WalletCards } from "lucide-react";
import Link from "next/link";

import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate } from "@/lib/format";
import { getCurrentMonthUsage } from "@/lib/api";

export default async function UsagePage() {
  try {
    const usage = await getCurrentMonthUsage();
    const filesPercent = usage.filesLimit > 0 ? Math.min((usage.filesUsed / usage.filesLimit) * 100, 100) : 0;
    const costPercent = usage.costLimitUsd > 0 ? Math.min((usage.estimatedCostUsedUsd / usage.costLimitUsd) * 100, 100) : 0;
    const storagePercent = usage.storageLimitMb > 0 ? Math.min((usage.storageUsedMb / usage.storageLimitMb) * 100, 100) : 0;

    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-normal">Usage</h1>
          <p className="text-sm text-muted-foreground">Current month AI extraction quota and cost usage.</p>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <UsageCard label="Plan" value={usage.plan} />
          <UsageCard label="Remaining files" value={`${usage.remainingFiles} / ${usage.filesLimit}`} />
          <UsageCard label="Remaining cost" value={`$${usage.remainingCostUsd.toFixed(2)} / $${usage.costLimitUsd.toFixed(2)}`} />
          <UsageCard label="Remaining storage" value={`${usage.remainingStorageMb.toFixed(1)} MB`} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <WalletCards className="size-5" />
              Monthly limits
            </CardTitle>
            <CardDescription>AI extraction is blocked when either limit is reached.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5">
            <ProgressRow label="Files used" value={`${usage.filesUsed} of ${usage.filesLimit}`} percent={filesPercent} />
            <ProgressRow
              label="Platform AI cost used"
              value={`$${usage.platformEstimatedCostUsedUsd.toFixed(4)} of $${usage.costLimitUsd.toFixed(2)}`}
              percent={costPercent}
            />
            <ProgressRow
              label="Storage used"
              value={`${usage.storageUsedMb.toFixed(2)} MB of ${usage.storageLimitMb} MB`}
              percent={storagePercent}
            />
            <div className="rounded-md border p-3 text-sm">
              <div className="font-medium">Own OpenAI key usage</div>
              <p className="text-muted-foreground">
                Estimated OpenAI cost paid directly by user key: ${usage.ownKeyEstimatedCostUsedUsd.toFixed(4)}. These files still count toward monthly file, document, project, and storage limits.
              </p>
            </div>
            <div className="grid gap-2 text-sm md:grid-cols-3">
              <Capability label="Projects" value={`${usage.projectsUsed} / ${usage.projectsLimit}`} />
              <Capability label="Documents" value={`${usage.documentsUsed} / ${usage.documentsLimit}`} />
              <Capability label="Batch extraction" value={usage.canBatchExtract ? "enabled" : "disabled"} />
            </div>
            {usage.plan === "free" ? (
              <Button asChild className="w-fit">
                <Link href="/pricing">Upgrade plan</Link>
              </Button>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent AI usage records</CardTitle>
            <CardDescription>{usage.recentRecords.length} records this month</CardDescription>
          </CardHeader>
          <CardContent>
            {usage.recentRecords.length === 0 ? (
              <div className="flex min-h-36 items-center justify-center rounded-md border border-dashed">
                <p className="text-sm text-muted-foreground">No AI extraction usage this month.</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Model</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Input</TableHead>
                    <TableHead>Output</TableHead>
                    <TableHead>Estimated cost</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {usage.recentRecords.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>{record.model}</TableCell>
                      <TableCell>
                        <StatusBadge status={record.status} />
                      </TableCell>
                      <TableCell>{record.inputTokensEstimated}</TableCell>
                      <TableCell>{record.outputTokensEstimated}</TableCell>
                      <TableCell>
                        ${record.estimatedCostUsd.toFixed(4)}
                        {record.usedOwnApiKey ? <span className="ml-2 text-xs text-muted-foreground">own key</span> : null}
                      </TableCell>
                      <TableCell>{formatDate(record.createdAt)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Usage unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load usage"}</AlertDescription>
      </Alert>
    );
  }
}

function UsageCard({ label, value }: { label: string; value: string }) {
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

function ProgressRow({ label, value, percent }: { label: string; value: string; percent: number }) {
  return (
    <div className="grid gap-2">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground">{value}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function Capability({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3">
      <div className="text-muted-foreground">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}
