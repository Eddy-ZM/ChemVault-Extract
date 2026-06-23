import { NextResponse } from "next/server";

import { apiUrl, setAuthCookie } from "@/lib/proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const response = await fetch(apiUrl("/auth/register"), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: await request.text(),
    cache: "no-store",
  });
  const body = await response.json();
  const nextResponse = NextResponse.json(body, { status: response.status });
  if (response.ok && typeof body.accessToken === "string") {
    setAuthCookie(nextResponse, body.accessToken);
  }
  return nextResponse;
}
