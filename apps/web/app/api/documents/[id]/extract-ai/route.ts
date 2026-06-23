import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const response = await fetch(apiUrl(`/documents/${id}/extract-ai`), {
    method: "POST",
    headers: buildApiHeaders(request),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
