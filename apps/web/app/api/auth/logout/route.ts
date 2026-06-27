import { NextResponse } from "next/server";

import { apiUrl, buildApiHeaders, clearAuthCookie, clearChemVaultUserCookie, userCenterUrl } from "@/lib/proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const headers = buildApiHeaders(request);
  await fetch(apiUrl("/auth/logout"), {
    method: "POST",
    headers,
    cache: "no-store",
  }).catch(() => null);
  await fetch(userCenterUrl("/api/auth/logout"), {
    method: "POST",
    headers,
    cache: "no-store",
  }).catch(() => null);
  return clearChemVaultUserCookie(clearAuthCookie(NextResponse.json({ status: "ok" })));
}
