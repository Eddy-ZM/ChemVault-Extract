import Link from "next/link";
import { AlertTriangle, Download, FileJson, FileSpreadsheet, Table2, type LucideIcon } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState, PageHeader } from "@/components/product-ui";
import { formatDate } from "@/lib/format";
import { listExports, listProjects } from "@/lib/api";

import { ExportCreateForm } from "./export-create-form";

export default async function ExportsPage() {
  try {
    const [exports, projects] = await Promise.all([listExports(), listProjects()]);
    return (
      <div className="flex flex-col gap-6">
        <PageHeader
          title="Exports"
          description="Create export jobs for reviewed scientific data and inspect export history."
        />
        <div className="grid gap-4 md:grid-cols-3">
          <FormatCard icon={Table2} title="CSV" description="Spreadsheet-friendly records for downstream analysis." />
          <FormatCard icon={FileJson} title="JSON" description="Structured payloads with evidence and normalized fields." />
          <FormatCard icon={FileSpreadsheet} title="XLSX" description="Workbook exports for review and sharing." />
        </div>
        <Alert>
          <AlertTriangle className="size-4" />
          <AlertTitle>Review before exporting</AlertTitle>
          <AlertDescription>Exports may include records that are pending review. Check review status before sharing final datasets.</AlertDescription>
        </Alert>
        <Card>
          <CardHeader>
            <CardTitle>Create export</CardTitle>
            <CardDescription>Exports are checked against project permissions and plan export capability.</CardDescription>
          </CardHeader>
          <CardContent>
            <ExportCreateForm projects={projects} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Export history</CardTitle>
            <CardDescription>{exports.length} export jobs</CardDescription>
          </CardHeader>
          <CardContent>
            {exports.length === 0 ? (
              <EmptyState title="No exports yet" description="Create an export after records have been extracted and reviewed." />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Format</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Storage</TableHead>
                    <TableHead className="text-right">Download</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {exports.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="uppercase">{item.exportFormat}</TableCell>
                      <TableCell>
                        <StatusBadge status={item.status} />
                      </TableCell>
                      <TableCell>{formatDate(item.createdAt)}</TableCell>
                      <TableCell className="max-w-80 truncate font-mono text-xs text-muted-foreground">{item.storageKey ?? item.error ?? "Queued"}</TableCell>
                      <TableCell className="text-right">
                        {item.storageKey ? (
                          <Button asChild size="sm" variant="outline">
                            <Link href={item.storageKey}>
                              <Download data-icon="inline-start" />
                              Download
                            </Link>
                          </Button>
                        ) : (
                          <Button size="sm" variant="outline" disabled>
                            <Download data-icon="inline-start" />
                            Download
                          </Button>
                        )}
                      </TableCell>
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
        <AlertTitle>Exports unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load exports"}</AlertDescription>
      </Alert>
    );
  }
}

function FormatCard({ icon: Icon, title, description }: { icon: LucideIcon; title: string; description: string }) {
  return (
    <Card className="shadow-none">
      <CardHeader>
        <div className="flex size-10 items-center justify-center rounded-md bg-amber-100 text-slate-950">
          <Icon className="size-5" />
        </div>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
    </Card>
  );
}
