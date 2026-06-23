import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const response = await fetch(apiUrl(`/settings/webhooks/${id}`), {
    headers: buildApiHeaders(request),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const response = await fetch(apiUrl(`/settings/webhooks/${id}`), {
    method: "PATCH",
    headers: buildApiHeaders(request, { "content-type": "application/json" }),
    body: await request.text(),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}

export async function DELETE(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const response = await fetch(apiUrl(`/settings/webhooks/${id}`), {
    method: "DELETE",
    headers: buildApiHeaders(request),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
