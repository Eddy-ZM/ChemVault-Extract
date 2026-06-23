import { apiUrl, buildApiHeaders, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const formData = await request.formData();
  const response = await fetch(apiUrl("/documents/upload"), {
    method: "POST",
    headers: buildApiHeaders(request),
    body: formData,
  });
  return proxyApiResponse(response);
}
