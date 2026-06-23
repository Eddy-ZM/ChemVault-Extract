import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function POST(request: Request, { params }: { params: Promise<{ inviteId: string }> }) {
  const { inviteId } = await params;
  const response = await fetch(apiUrl(`/workspaces/invites/${inviteId}/accept`), {
    method: "POST",
    headers: buildApiHeaders(request),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
