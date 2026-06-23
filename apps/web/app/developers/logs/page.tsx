import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/product-ui";
import { listApiRequestLogs } from "@/lib/api";

export default async function DeveloperLogsPage() {
  try {
    const logs = await listApiRequestLogs();
    return (
      <div className="flex flex-col gap-6">
        <PageHeader title="API request logs" description="Recent /v1 API calls with request ids for debugging." />
        <Card>
          <CardHeader>
            <CardTitle>Recent requests</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            {logs.length === 0 ? (
              <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">No API requests logged yet.</div>
            ) : (
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="border-b text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="py-2 pr-4">Method</th>
                    <th className="py-2 pr-4">Path</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2 pr-4">Latency</th>
                    <th className="py-2 pr-4">Request id</th>
                    <th className="py-2">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-b last:border-0">
                      <td className="py-3 pr-4 font-mono text-xs">{log.method}</td>
                      <td className="py-3 pr-4 font-mono text-xs">{log.path}</td>
                      <td className="py-3 pr-4">
                        <Badge variant={log.statusCode >= 400 ? "destructive" : "outline"}>{log.statusCode}</Badge>
                      </td>
                      <td className="py-3 pr-4">{log.latencyMs} ms</td>
                      <td className="py-3 pr-4 font-mono text-xs">{log.requestId}</td>
                      <td className="py-3">{new Date(log.createdAt).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Logs unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load API logs."}</AlertDescription>
      </Alert>
    );
  }
}
