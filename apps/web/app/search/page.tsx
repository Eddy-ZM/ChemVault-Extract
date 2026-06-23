import Link from "next/link";
import type { Project, Workspace } from "@chemvault-extract/schemas";
import { Download, FileText, Search as SearchIcon, Table2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState, PageHeader } from "@/components/product-ui";
import { listProjects, listWorkspaces, searchScientificData } from "@/lib/api";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; workspace_id?: string; project_id?: string }>;
}) {
  const params = await searchParams;
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.workspace_id) query.set("workspace_id", params.workspace_id);
  if (params.project_id) query.set("project_id", params.project_id);
  const queryString = query.toString() ? `?${query.toString()}` : "";

  try {
    const [results, projects, workspaces] = await Promise.all([
      searchScientificData(queryString),
      listProjects(),
      listWorkspaces(),
    ]);
    return (
      <div className="flex flex-col gap-6">
        <PageHeader
          title="Search"
          description="Search accessible documents and parsed chunks with project and workspace filters."
          actions={
            <Button asChild variant="outline">
              <Link href="/exports">
                <Download data-icon="inline-start" />
                Export current results
              </Link>
            </Button>
          }
        />
        <div className="grid gap-6 xl:grid-cols-[300px_1fr]">
          <SearchFilters projects={projects} workspaces={workspaces} params={params} />
          <div className="grid gap-6">
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{results.documents.length + results.chunks.length} results</Badge>
              <Badge variant="outline">Documents {results.documents.length}</Badge>
              <Badge variant="outline">Parsed chunks {results.chunks.length}</Badge>
              <Badge variant="secondary">Evidence preview</Badge>
            </div>
            <Card>
              <CardHeader>
                <CardTitle>Documents</CardTitle>
                <CardDescription>{results.documents.length} matching documents</CardDescription>
              </CardHeader>
              <CardContent>
                {results.documents.length === 0 ? (
                  <EmptyState title="No matching documents" description="Try another search term or clear filters." />
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Filename</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Open</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {results.documents.map((document) => (
                        <TableRow key={document.id}>
                          <TableCell>{document.filename}</TableCell>
                          <TableCell className="uppercase">{document.fileType}</TableCell>
                          <TableCell>{document.status}</TableCell>
                          <TableCell className="text-right">
                            <Link className="text-sm underline-offset-4 hover:underline" href={`/documents/${document.id}`}>
                              View
                            </Link>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Parsed chunks</CardTitle>
                <CardDescription>{results.chunks.length} matching chunks with evidence previews</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3">
                {results.chunks.map((chunk) => (
                  <Link key={chunk.id} href={`/documents/${chunk.documentId}`} className="rounded-md border bg-white p-4 hover:bg-accent">
                    <div className="flex flex-wrap items-center gap-2 text-sm font-medium">
                      <Badge variant="outline">{chunk.section ?? "Unsectioned"}</Badge>
                      <span>pages {chunk.pageStart ?? "?"}-{chunk.pageEnd ?? "?"}</span>
                    </div>
                    <p className="mt-3 line-clamp-4 border-l-4 border-amber-300 pl-3 text-sm leading-6 text-muted-foreground">
                      {chunk.text}
                    </p>
                  </Link>
                ))}
                {results.chunks.length === 0 ? (
                  <EmptyState title="No parsed chunks matched" description="Parsed evidence previews appear after documents are processed by the worker." />
                ) : null}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Search unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to search"}</AlertDescription>
      </Alert>
    );
  }
}

function SearchFilters({
  projects,
  workspaces,
  params,
}: {
  projects: Project[];
  workspaces: Workspace[];
  params: { q?: string; workspace_id?: string; project_id?: string };
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Filters</CardTitle>
        <CardDescription>Search parsed text, filenames, file types, and accessible project scopes.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4" action="/search">
          <div className="grid gap-2">
            <label className="text-xs font-medium text-muted-foreground" htmlFor="q">Global search</label>
          <input
            id="q"
            name="q"
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            defaultValue={params.q ?? ""}
            placeholder="yield, HPLC, ethanol..."
          />
          </div>
          <div className="grid gap-2">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="workspace_id">Workspace</label>
          <select id="workspace_id" name="workspace_id" className="h-10 rounded-md border border-input bg-background px-3 text-sm" defaultValue={params.workspace_id ?? ""}>
            <option value="">All workspaces</option>
            {workspaces.map((workspace) => (
              <option key={workspace.id} value={workspace.id}>
                {workspace.name}
              </option>
            ))}
          </select>
          </div>
          <div className="grid gap-2">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="project_id">Project</label>
          <select id="project_id" name="project_id" className="h-10 rounded-md border border-input bg-background px-3 text-sm" defaultValue={params.project_id ?? ""}>
            <option value="">All projects</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
          </div>
          <div className="grid gap-2">
            <span className="text-xs font-medium text-muted-foreground">Record type</span>
            <div className="grid gap-2 text-sm">
              <div className="flex items-center gap-2 rounded-md border p-2"><FileText className="size-4" /> Documents</div>
              <div className="flex items-center gap-2 rounded-md border p-2"><Table2 className="size-4" /> Parsed chunks</div>
              <div className="flex items-center gap-2 rounded-md border p-2 text-muted-foreground"><SearchIcon className="size-4" /> Extracted records next</div>
            </div>
          </div>
          <button className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground" type="submit">
            Search
          </button>
        </form>
      </CardContent>
    </Card>
  );
}
