import { NextResponse } from "next/server";

import { API_BASE_URL, AUTH_COOKIE_NAME } from "@/lib/api";

export function buildApiHeaders(request: Request, extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  const incoming = new Headers(request.headers);
  const authorization = incoming.get("authorization");
  const cookie = incoming.get("cookie");
  const cookieToken = readCookie(incoming.get("cookie"), AUTH_COOKIE_NAME);
  const userCenterSession = readCookie(incoming.get("cookie"), process.env.CHEMVAULT_USER_COOKIE_NAME ?? "chemvault_session");
  if (cookie && !headers.has("cookie")) {
    headers.set("cookie", cookie);
  }
  if (authorization && !headers.has("authorization")) {
    headers.set("authorization", authorization);
  } else if (cookieToken && !userCenterSession && !headers.has("authorization")) {
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

export function clearChemVaultUserCookie(response: NextResponse): NextResponse {
  const domain = process.env.CHEMVAULT_USER_COOKIE_DOMAIN || undefined;
  response.cookies.set(process.env.CHEMVAULT_USER_COOKIE_NAME ?? "chemvault_session", "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    domain,
    path: "/",
    maxAge: 0,
  });
  return response;
}

export function userCenterUrl(path: string): string {
  const baseUrl = process.env.CHEMVAULT_USER_BASE_URL ?? process.env.NEXT_PUBLIC_CHEMVAULT_USER_URL ?? "https://user.chemvault.science";
  return `${baseUrl.replace(/\/$/, "")}${path}`;
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
