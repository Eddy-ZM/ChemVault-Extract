import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function DELETE(request: Request) {
  const response = await fetch(apiUrl("/settings/ai/openai-key"), {
    method: "DELETE",
    headers: buildApiHeaders(request),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
