import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const response = await fetch(apiUrl("/settings/ai/test-openai-key"), {
    method: "POST",
    headers: buildApiHeaders(request, { "content-type": "application/json" }),
    body: await request.text(),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
