import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const formData = await request.formData();
  const response = await fetch(apiUrl("/documents/batch-upload"), {
    method: "POST",
    headers: buildApiHeaders(request),
    body: formData,
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
