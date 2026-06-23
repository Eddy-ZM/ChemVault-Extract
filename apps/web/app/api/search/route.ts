import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const incomingUrl = new URL(request.url);
  const response = await fetch(apiUrl(`/search${incomingUrl.search}`), {
    headers: buildApiHeaders(request),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
