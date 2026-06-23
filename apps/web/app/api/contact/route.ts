import { apiUrl, proxyApiResponse } from "@/lib/proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const response = await fetch(apiUrl("/contact"), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: await request.text(),
    cache: "no-store",
  });
  return proxyApiResponse(response);
}
