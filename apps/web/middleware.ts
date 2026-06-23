import { NextResponse, type NextRequest } from "next/server";

const protectedPrefixes = [
  "/dashboard",
  "/documents",
  "/workspaces",
  "/projects",
  "/batch",
  "/database",
  "/search",
  "/review",
  "/exports",
  "/developers",
  "/settings",
  "/usage",
  "/account",
];

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const protectedPath = protectedPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
  if (!protectedPath) {
    return NextResponse.next();
  }
  const token = request.cookies.get("chemvault_token")?.value;
  if (token) {
    return NextResponse.next();
  }
  const loginUrl = request.nextUrl.clone();
  loginUrl.pathname = "/login";
  loginUrl.searchParams.set("next", pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/documents/:path*",
    "/workspaces/:path*",
    "/projects/:path*",
    "/batch/:path*",
    "/database/:path*",
    "/search/:path*",
    "/review/:path*",
    "/exports/:path*",
    "/developers/:path*",
    "/settings/:path*",
    "/usage/:path*",
    "/account/:path*",
  ],
};
