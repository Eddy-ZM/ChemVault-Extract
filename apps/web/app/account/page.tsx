import Link from "next/link";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getCurrentUser } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default async function AccountPage() {
  try {
    const user = await getCurrentUser();
    return (
      <div className="flex max-w-3xl flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-normal">Account</h1>
          <p className="text-sm text-muted-foreground">User identity, plan, and monthly AI extraction limits.</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>{user.email}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Detail label="Name" value={user.name || "-"} />
            <Detail label="Role" value={user.role} />
            <Detail label="Plan" value={user.plan} />
            <Detail label="Created" value={formatDate(user.createdAt)} />
            <Detail label="Monthly file limit" value={String(user.monthlyAiFileLimit)} />
            <Detail label="Monthly cost limit" value={`$${user.monthlyAiCostLimitUsd.toFixed(2)}`} />
            <Detail label="Plan override" value={user.planOverride || "-"} />
          </CardContent>
        </Card>
        <div className="flex flex-wrap gap-2">
          <Button asChild>
            <Link href="/account/billing">Manage billing</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/settings/ai">AI key settings</Link>
          </Button>
        </div>
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Account unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load account"}</AlertDescription>
      </Alert>
    );
  }
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <span className="text-sm">{value}</span>
    </div>
  );
}
