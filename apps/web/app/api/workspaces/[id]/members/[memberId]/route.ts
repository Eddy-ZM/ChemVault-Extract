import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string; memberId: string }> }) {
  const { id, memberId } = await params;
  const response = await fetch(apiUrl(`/workspaces/${id}/members/${memberId}`), {
    method: "PATCH",
    headers: buildApiHeaders(request, { "content-type": "application/json" }),
    body: await request.text(),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}

export async function DELETE(request: Request, { params }: { params: Promise<{ id: string; memberId: string }> }) {
  const { id, memberId } = await params;
  const response = await fetch(apiUrl(`/workspaces/${id}/members/${memberId}`), {
    method: "DELETE",
    headers: buildApiHeaders(request),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
