import { API_BASE_URL } from "@/lib/api";

export const runtime = "nodejs";

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const response = await fetch(`${API_BASE_URL}/review-items/${id}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: await request.text(),
    cache: "no-store",
  });
  const body = await response.text();
  return new Response(body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
  });
}
