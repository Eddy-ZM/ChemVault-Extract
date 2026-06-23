import { NextResponse } from "next/server";

import { API_BASE_URL, AUTH_COOKIE_NAME } from "@/lib/api";

export function buildApiHeaders(request: Request, extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  const incoming = new Headers(request.headers);
  const authorization = incoming.get("authorization");
  const cookieToken = readCookie(incoming.get("cookie"), AUTH_COOKIE_NAME);
  if (authorization && !headers.has("authorization")) {
    headers.set("authorization", authorization);
  } else if (cookieToken && !headers.has("authorization")) {
    headers.set("authorization", `Bearer ${cookieToken}`);
  }
  return headers;
}

export async function proxyApiResponse(response: Response): Promise<Response> {
  const body = await response.text();
  return new Response(body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
  });
}

export function clearAuthCookie(response: NextResponse): NextResponse {
  response.cookies.set(AUTH_COOKIE_NAME, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
  return response;
}

export function setAuthCookie(response: NextResponse, token: string): NextResponse {
  response.cookies.set(AUTH_COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });
  return response;
}

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

function readCookie(header: string | null, name: string): string | null {
  if (!header) return null;
  for (const part of header.split(";")) {
    const [rawKey, ...rest] = part.trim().split("=");
    if (rawKey === name) {
      return decodeURIComponent(rest.join("="));
    }
  }
  return null;
}
