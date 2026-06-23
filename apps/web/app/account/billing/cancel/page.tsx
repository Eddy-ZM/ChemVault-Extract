import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function BillingCancelPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Checkout cancelled</CardTitle>
        <CardDescription>Your current plan has not changed.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        <Button asChild>
          <Link href="/pricing">Return to pricing</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/account/billing">Open billing</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
