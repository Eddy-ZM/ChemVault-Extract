import Link from "next/link";
import type {
  BatchJob,
  BillingOverview,
  CurrentMonthUsage,
  Document,
  ExportJob,
  Project,
  ReviewItem,
  User,
  Workspace,
} from "@chemvault-extract/schemas";
import {
  Database,
  Download,
  FileCheck2,
  FileUp,
  Search,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import { DashboardCards } from "@/components/dashboard-cards";
import { DocumentsTable } from "@/components/documents-table";
import { RecentJobsTable } from "@/components/recent-jobs-table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import {
  getBillingOverview,
  getCurrentMonthUsage,
  getCurrentUser,
  listDocuments,
  listBatchJobs,
  listExports,
  listProjects,
  listReviewItems,
  listWorkspaces,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { EmptyState, PageHeader } from "@/components/product-ui";

export default async function DashboardPage() {
  let documents: Document[] = [];
  let projects: Project[] = [];
  let usage: CurrentMonthUsage | null = null;
  let billing: BillingOverview | null = null;
  let user: User | null = null;
  let reviewItems: ReviewItem[] = [];
  let exports: ExportJob[] = [];
  let workspaces: Workspace[] = [];
  let batchJobs: BatchJob[] = [];
  let error: string | null = null;

  try {
    [user, documents, projects, usage, billing, reviewItems, exports, workspaces, batchJobs] = await Promise.all([
      getCurrentUser(),
      listDocuments(),
      listProjects(),
      getCurrentMonthUsage(),
      getBillingOverview(),
      listReviewItems(),
      listExports(),
      listWorkspaces(),
      listBatchJobs(),
    ]);
  } catch (err) {
    error = err instanceof Error ? err.message : "Unable to reach API";
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Dashboard"
        description={user ? `${user.email} workspace activity and AI usage.` : "Current ingestion volume and extraction queue status."}
        actions={
          <>
            <Button asChild>
              <Link href="/documents/upload">
                <FileUp data-icon="inline-start" />
                Upload document
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/batch">
                <Sparkles data-icon="inline-start" />
                Run batch extraction
              </Link>
            </Button>
          </>
        }
      />

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>API unavailable</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : (
        <>
          <DashboardCards documents={documents} />
          {usage ? (
            <div className="grid gap-4 md:grid-cols-3">
              <MetricCard label="Plan" value={usage.plan} />
              <MetricCard label="Remaining AI files" value={`${usage.remainingFiles} / ${usage.filesLimit}`} />
              <MetricCard label="Remaining AI cost" value={`$${usage.remainingCostUsd.toFixed(2)}`} />
              <MetricCard label="Projects" value={`${projects.length} / ${usage.projectsLimit}`} />
              <MetricCard label="Workspaces" value={workspaces.length.toString()} />
              <MetricCard label="Storage used" value={`${usage.storageUsedMb.toFixed(1)} MB / ${usage.storageLimitMb} MB`} />
              <MetricCard label="Subscription" value={billing?.subscription?.status ?? "free"} />
            </div>
          ) : null}
          <Card>
            <CardHeader>
              <CardTitle>Quick actions</CardTitle>
              <CardDescription>Common paths for building and maintaining your research database.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-5">
              <QuickAction href="/documents/upload" icon={FileUp} label="Upload document" />
              <QuickAction href="/batch" icon={Sparkles} label="Run batch extraction" />
              <QuickAction href="/review" icon={FileCheck2} label="Review records" />
              <QuickAction href="/search" icon={Search} label="Search database" />
              <QuickAction href="/exports" icon={Download} label="Export data" />
            </CardContent>
          </Card>
          {documents.length === 0 ? (
            <EmptyState
              icon={Database}
              title="Upload your first scientific document"
              description="Upload your first scientific document to start building your research database."
              actionHref="/documents/upload"
              actionLabel="Upload document"
            />
          ) : null}
          {usage?.plan === "free" ? (
            <Card>
              <CardHeader>
                <CardTitle>Upgrade plan</CardTitle>
                <CardDescription>Increase monthly AI extraction, storage, and project limits through Stripe billing.</CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild>
                  <Link href="/pricing">View pricing</Link>
                </Button>
              </CardContent>
            </Card>
          ) : null}
          <div className="grid gap-6 xl:grid-cols-2">
            <DocumentsTable documents={documents.slice(0, 8)} title="Latest documents" />
            <RecentJobsTable documents={documents} />
            <ReviewItemsPreview items={reviewItems.slice(0, 6)} />
            <ExportsPreview exports={exports.slice(0, 6)} />
            <BatchJobsPreview jobs={batchJobs.slice(0, 6)} />
          </div>
        </>
      )}
    </div>
  );
}

function QuickAction({ href, icon: Icon, label }: { href: string; icon: LucideIcon; label: string }) {
  return (
    <Link href={href} className="flex items-center gap-3 rounded-md border bg-white p-3 text-sm font-medium hover:bg-accent">
      <Icon className="size-4 text-muted-foreground" />
      {label}
    </Link>
  );
}

function BatchJobsPreview({ jobs }: { jobs: BatchJob[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent batch jobs</CardTitle>
        <CardDescription>{jobs.length} upload or extraction batches</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3">
        {jobs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No batch jobs yet.</p>
        ) : (
          jobs.map((item) => (
            <Link key={item.id} href={`/batch/${item.id}`} className="flex items-center justify-between gap-3 rounded-md border p-3 text-sm hover:bg-accent">
              <div className="min-w-0">
                <div className="truncate font-medium">{item.type.replaceAll("_", " ")}</div>
                <div className="truncate text-xs text-muted-foreground">
                  {item.completedItems}/{item.totalItems} complete · {item.failedItems} failed
                </div>
              </div>
              <StatusBadge status={item.status} />
            </Link>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
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

function ReviewItemsPreview({ items }: { items: ReviewItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent review items</CardTitle>
        <CardDescription>{items.length} latest records requiring review</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No review items yet.</p>
        ) : (
          items.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-3 rounded-md border p-3 text-sm">
              <div className="min-w-0">
                <div className="truncate font-medium">{item.recordType}</div>
                <div className="truncate text-xs text-muted-foreground">{item.message || item.id}</div>
              </div>
              <StatusBadge status={item.status} />
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function ExportsPreview({ exports }: { exports: ExportJob[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent exports</CardTitle>
        <CardDescription>{exports.length} export jobs</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3">
        {exports.length === 0 ? (
          <p className="text-sm text-muted-foreground">No exports yet.</p>
        ) : (
          exports.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-3 rounded-md border p-3 text-sm">
              <div className="min-w-0">
                <div className="truncate font-medium">{item.exportFormat}</div>
                <div className="truncate text-xs text-muted-foreground">{item.storageKey || item.id}</div>
              </div>
              <StatusBadge status={item.status} />
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
