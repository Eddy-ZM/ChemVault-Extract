import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function BillingSuccessPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Subscription successful</CardTitle>
        <CardDescription>Your plan will update shortly after the Stripe webhook is processed.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        <Button asChild>
          <Link href="/account/billing">Refresh billing</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/dashboard">Open dashboard</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
