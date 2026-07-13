import { NextResponse, type NextRequest } from "next/server";

const successorBaseUrl = process.env.CHEMVAULT_LAB_URL || process.env.NEXT_PUBLIC_CHEMVAULT_LAB_URL || "https://lab.chemvault.science";

function successorRedirect(request: NextRequest) {
  const destination = new URL(`${request.nextUrl.pathname}${request.nextUrl.search}`, successorBaseUrl);
  const response = NextResponse.redirect(destination, 307);
  response.headers.set("Deprecation", "true");
  response.headers.set("Link", `<${successorBaseUrl}>; rel=\"successor-version\"`);
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

function retiredApiResponse(request: NextRequest) {
  const successor = new URL(`/api${request.nextUrl.pathname.slice(4)}${request.nextUrl.search}`, successorBaseUrl);
  const response = NextResponse.json(
    {
      error: {
        code: "extract_api_retired",
        message: "ChemVault Extract API is retired. Use the authenticated ChemVault Lab API.",
        details: { successor: successor.toString() },
      },
    },
    { status: 410 },
  );
  response.headers.set("Deprecation", "true");
  response.headers.set("Link", `<${successor}>; rel="successor-version"`);
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

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
  const productMode = process.env.PRODUCT_MODE || process.env.NEXT_PUBLIC_PRODUCT_MODE || "sunset";
  if (productMode !== "legacy") {
    if (request.nextUrl.pathname.startsWith("/api/")) return retiredApiResponse(request);
    return successorRedirect(request);
  }

  const pathname = request.nextUrl.pathname;
  const protectedPath = protectedPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
  if (!protectedPath) {
    return NextResponse.next();
  }
  const token = request.cookies.get("chemvault_token")?.value;
  const userCenterSession = request.cookies.get("chemvault_session")?.value;
  if (token || userCenterSession) {
    return NextResponse.next();
  }
  const loginUrl = request.nextUrl.clone();
  loginUrl.pathname = "/login";
  loginUrl.searchParams.set("next", pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|assets|favicon.ico|health|robots.txt|sitemap.xml).*)",
  ],
};
