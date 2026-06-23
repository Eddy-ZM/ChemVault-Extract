import type { ChemicalEntity, MeasurementRecord, Project, ReactionRecord, Workspace } from "@chemvault-extract/schemas";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getScientificDatabase, listProjects, listWorkspaces } from "@/lib/api";

export default async function DatabasePage({
  searchParams,
}: {
  searchParams: Promise<{ workspace_id?: string; project_id?: string }>;
}) {
  const params = await searchParams;
  const query = new URLSearchParams();
  if (params.workspace_id) query.set("workspace_id", params.workspace_id);
  if (params.project_id) query.set("project_id", params.project_id);
  const queryString = query.toString() ? `?${query.toString()}` : "";

  try {
    const [database, projects, workspaces] = await Promise.all([
      getScientificDatabase(queryString),
      listProjects(),
      listWorkspaces(),
    ]);
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-normal">Scientific database</h1>
          <p className="text-sm text-muted-foreground">Normalized extracted records scoped to projects and workspaces you can access.</p>
        </div>
        <DatabaseFilters projects={projects} workspaces={workspaces} selectedProject={params.project_id} selectedWorkspace={params.workspace_id} />
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Chemical entities" value={database.chemicalEntities.length.toString()} />
          <MetricCard label="Reactions" value={database.reactions.length.toString()} />
          <MetricCard label="Measurements" value={database.measurements.length.toString()} />
        </div>
        <ChemicalTable rows={database.chemicalEntities} />
        <ReactionTable rows={database.reactions} />
        <MeasurementTable rows={database.measurements} />
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Database unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load database records"}</AlertDescription>
      </Alert>
    );
  }
}

function DatabaseFilters({
  projects,
  workspaces,
  selectedProject,
  selectedWorkspace,
}: {
  projects: Project[];
  workspaces: Workspace[];
  selectedProject?: string;
  selectedWorkspace?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Filters</CardTitle>
        <CardDescription>Leave blank to show all accessible records.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-[1fr_1fr_auto]" action="/database">
          <select name="workspace_id" className="h-10 rounded-md border border-input bg-background px-3 text-sm" defaultValue={selectedWorkspace ?? ""}>
            <option value="">All workspaces</option>
            {workspaces.map((workspace) => (
              <option key={workspace.id} value={workspace.id}>
                {workspace.name}
              </option>
            ))}
          </select>
          <select name="project_id" className="h-10 rounded-md border border-input bg-background px-3 text-sm" defaultValue={selectedProject ?? ""}>
            <option value="">All projects</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
          <button className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground" type="submit">
            Apply
          </button>
        </form>
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

function ChemicalTable({ rows }: { rows: ChemicalEntity[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Chemical entities</CardTitle>
        <CardDescription>Raw and normalized compound records.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Normalized</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Formula</TableHead>
              <TableHead>PubChem</TableHead>
              <TableHead>Validation</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.slice(0, 50).map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.rawName ?? row.name ?? "Untitled"}</TableCell>
                <TableCell>{row.normalizedName ?? ""}</TableCell>
                <TableCell>{row.normalizedRole ?? row.role ?? ""}</TableCell>
                <TableCell>{row.normalizedFormula ?? row.formula ?? ""}</TableCell>
                <TableCell>{row.pubchemCid ?? ""}</TableCell>
                <TableCell>{row.validationStatus ?? ""}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function ReactionTable({ rows }: { rows: ReactionRecord[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Reactions</CardTitle>
        <CardDescription>Evidence-backed reaction records awaiting review.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Yield</TableHead>
              <TableHead>Temperature</TableHead>
              <TableHead>Time</TableHead>
              <TableHead>Validation</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.slice(0, 50).map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.reactionName ?? "Reaction"}</TableCell>
                <TableCell>
                  {row.normalizedYieldValue ?? row.rawYieldValue ?? ""}
                  {row.normalizedYieldUnit ?? row.rawYieldUnit ?? ""}
                </TableCell>
                <TableCell>{row.normalizedTemperature ?? row.rawTemperature ?? ""}</TableCell>
                <TableCell>{row.normalizedTime ?? row.rawTime ?? ""}</TableCell>
                <TableCell>{row.validationStatus ?? ""}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function MeasurementTable({ rows }: { rows: MeasurementRecord[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Measurements</CardTitle>
        <CardDescription>Analytical and experimental measurement records.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>Value</TableHead>
              <TableHead>Unit</TableHead>
              <TableHead>Validation</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.slice(0, 50).map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.normalizedMeasurementType ?? row.measurementType}</TableCell>
                <TableCell>{row.subject ?? ""}</TableCell>
                <TableCell>{row.normalizedValue ?? row.rawValue ?? ""}</TableCell>
                <TableCell>{row.normalizedUnit ?? row.rawUnit ?? ""}</TableCell>
                <TableCell>{row.validationStatus ?? ""}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
