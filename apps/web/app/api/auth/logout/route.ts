import { NextResponse } from "next/server";

import { apiUrl, buildApiHeaders, clearAuthCookie } from "@/lib/proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  await fetch(apiUrl("/auth/logout"), {
    method: "POST",
    headers: buildApiHeaders(request),
    cache: "no-store",
  }).catch(() => null);
  return clearAuthCookie(NextResponse.json({ status: "ok" }));
}
