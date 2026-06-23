import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const response = await fetch(apiUrl("/settings/api-keys"), {
    headers: buildApiHeaders(request),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}

export async function POST(request: Request) {
  const response = await fetch(apiUrl("/settings/api-keys"), {
    method: "POST",
    headers: buildApiHeaders(request, { "content-type": "application/json" }),
    body: await request.text(),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
