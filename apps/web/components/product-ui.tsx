import Link from "next/link";
import type React from "react";
import type { LucideIcon } from "lucide-react";
import { AlertCircle, Inbox, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div className="max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-normal md:text-3xl">{title}</h1>
        {description ? <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function SectionHeader({
  title,
  description,
  align = "left",
}: {
  title: string;
  description?: string;
  align?: "left" | "center";
}) {
  return (
    <div className={cn("max-w-3xl", align === "center" && "mx-auto text-center")}>
      <h2 className="text-2xl font-semibold tracking-normal text-balance md:text-4xl">{title}</h2>
      {description ? <p className="mt-4 text-base leading-7 text-muted-foreground">{description}</p> : null}
    </div>
  );
}

export function FeatureCard({
  icon: Icon,
  title,
  description,
  children,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <Card className="h-full border-slate-200 shadow-none">
      <CardHeader>
        <div className="flex size-10 items-center justify-center rounded-md bg-blue-50 text-blue-700 ring-1 ring-blue-100">
          <Icon className="size-5" />
        </div>
        <CardTitle>{title}</CardTitle>
        <CardDescription className="leading-6">{description}</CardDescription>
      </CardHeader>
      {children ? <CardContent>{children}</CardContent> : null}
    </Card>
  );
}

export function EvidenceCard({
  label,
  value,
  muted,
}: {
  label: string;
  value: string;
  muted?: boolean;
}) {
  return (
    <div className="rounded-md border bg-white p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={cn("mt-1 text-sm font-medium text-slate-950", muted && "text-slate-500")}>{value}</div>
    </div>
  );
}

export function WorkflowStep({
  index,
  title,
  description,
}: {
  index: number;
  title: string;
  description: string;
}) {
  return (
    <div className="relative rounded-lg border bg-white p-5 shadow-sm">
      <div className="mb-4 flex size-9 items-center justify-center rounded-md bg-blue-600 text-sm font-semibold text-white shadow-sm">
        {index}
      </div>
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
    </div>
  );
}

export function StatCard({ label, value, icon: Icon }: { label: string; value: string; icon?: LucideIcon }) {
  return (
    <Card className="shadow-none">
      <CardHeader className="flex flex-row items-center justify-between gap-4 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        {Icon ? <Icon className="size-4 text-muted-foreground" /> : null}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold tracking-normal">{value}</div>
      </CardContent>
    </Card>
  );
}

export function EmptyState({
  title,
  description,
  actionHref,
  actionLabel,
  icon: Icon = Inbox,
}: {
  title: string;
  description: string;
  actionHref?: string;
  actionLabel?: string;
  icon?: LucideIcon;
}) {
  return (
    <div className="flex min-h-44 flex-col items-center justify-center gap-3 rounded-lg border border-dashed bg-white p-8 text-center">
      <div className="flex size-11 items-center justify-center rounded-md bg-blue-50 text-blue-700 ring-1 ring-blue-100">
        <Icon className="size-5" />
      </div>
      <div>
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="mt-1 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      {actionHref && actionLabel ? (
        <Button asChild size="sm">
          <Link href={actionHref}>{actionLabel}</Link>
        </Button>
      ) : null}
    </div>
  );
}

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="grid gap-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        {label}
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <div key={item} className="h-28 animate-pulse rounded-lg border bg-muted" />
        ))}
      </div>
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description,
  retryHref,
}: {
  title?: string;
  description: string;
  retryHref?: string;
}) {
  return (
    <div className="flex min-h-44 flex-col items-center justify-center gap-3 rounded-lg border bg-white p-8 text-center">
      <div className="flex size-11 items-center justify-center rounded-md bg-destructive/10 text-destructive">
        <AlertCircle className="size-5" />
      </div>
      <div>
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="mt-1 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      {retryHref ? (
        <Button asChild size="sm" variant="outline">
          <Link href={retryHref}>Retry</Link>
        </Button>
      ) : null}
    </div>
  );
}
