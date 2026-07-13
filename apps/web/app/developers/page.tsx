import Link from "next/link";
import { Archive, ExternalLink, ShieldX } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/product-ui";

const labUrl = "https://lab.chemvault.science";

export default function DevelopersPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Extract API retired"
        description="The hosted Extract API and API-key SDKs have been retired. ChemVault Lab is the supported home for authenticated laboratory workflows."
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldX className="size-5 text-amber-600" />
              Hosted endpoint
            </CardTitle>
            <CardDescription>Former Extract API requests return HTTP 410 and are never sent to the frozen backend.</CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ExternalLink className="size-5 text-blue-600" />
              Supported successor
            </CardTitle>
            <CardDescription>Use ChemVault Lab for upload, analysis, review, search, and export.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href={labUrl}>Open ChemVault Lab</Link>
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Archive className="size-5 text-slate-600" />
              Recovery only
            </CardTitle>
            <CardDescription>The legacy SDKs require an explicit self-hosted base URL and are retained only for controlled recovery work.</CardDescription>
          </CardHeader>
        </Card>
      </div>
    </div>
  );
}
