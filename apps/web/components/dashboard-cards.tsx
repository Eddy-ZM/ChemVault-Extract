import type { Document } from "@chemvault-extract/schemas";
import { AlertTriangle, CheckCircle2, Clock3, Files } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function getDashboardStats(documents: Document[]) {
  return {
    totalDocuments: documents.length,
    queuedJobs: documents.filter((document) => document.latestJob?.status === "queued").length,
    failedJobs: documents.filter((document) => document.latestJob?.status === "failed").length,
    reviewReadyJobs: documents.filter((document) => document.latestJob?.status === "review_ready").length,
  };
}

export function DashboardCards({ documents }: { documents: Document[] }) {
  const stats = getDashboardStats(documents);
  const cards = [
    { label: "Total documents", value: stats.totalDocuments, icon: Files },
    { label: "Queued jobs", value: stats.queuedJobs, icon: Clock3 },
    { label: "Failed jobs", value: stats.failedJobs, icon: AlertTriangle },
    { label: "Review ready", value: stats.reviewReadyJobs, icon: CheckCircle2 },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.label}>
            <CardHeader className="flex flex-row items-center justify-between gap-4 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{card.label}</CardTitle>
              <Icon className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold tracking-normal">{card.value}</div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
