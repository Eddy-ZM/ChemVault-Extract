import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function POST(request: Request, { params }: { params: Promise<{ type: string; id: string }> }) {
  const { type, id } = await params;
  const response = await fetch(apiUrl(`/records/${type}/${id}/renormalize`), {
    method: "POST",
    headers: buildApiHeaders(request, { "content-type": "application/json" }),
    body: await request.text(),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
