export interface Env {
  BACKEND_API_URL: string;
  ALLOWED_ORIGINS?: string;
}

const SENSITIVE_HEADERS = new Set(["cf-connecting-ip", "x-real-ip"]);

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();

    if (request.method === "OPTIONS") {
      return withCors(new Response(null, { status: 204 }), request, env, requestId);
    }

    if (url.pathname === "/health") {
      return withCors(
        Response.json({ status: "ok", service: "cloudflare-api-gateway" }, { headers: { "x-request-id": requestId } }),
        request,
        env,
        requestId,
      );
    }

    const backendUrl = buildBackendUrl(url, env);
    const headers = new Headers(request.headers);
    headers.set("x-request-id", requestId);
    for (const header of SENSITIVE_HEADERS) headers.delete(header);

    const proxied = new Request(backendUrl, {
      method: request.method,
      headers,
      body: request.body,
      redirect: "manual",
      duplex: "half",
    } as RequestInit);

    const response = await fetch(proxied);
    return withCors(response, request, env, requestId);
  },
};

function buildBackendUrl(incoming: URL, env: Env): string {
  const backend = new URL(env.BACKEND_API_URL);
  let pathname = incoming.pathname;
  if (pathname.startsWith("/api/")) {
    pathname = pathname.slice(4);
  }
  backend.pathname = joinPath(backend.pathname, pathname);
  backend.search = incoming.search;
  return backend.toString();
}

function joinPath(basePath: string, path: string): string {
  const base = basePath.replace(/\/$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}

function withCors(response: Response, request: Request, env: Env, requestId: string): Response {
  const headers = new Headers(response.headers);
  const origin = request.headers.get("origin");
  if (origin && allowedOrigins(env).has(origin)) {
    headers.set("access-control-allow-origin", origin);
    headers.set("access-control-allow-credentials", "true");
    headers.set("vary", appendVary(headers.get("vary"), "Origin"));
  }
  headers.set("access-control-allow-methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS");
  headers.set("access-control-allow-headers", "authorization,content-type,x-chemvault-api-key,x-request-id");
  headers.set("access-control-expose-headers", "x-request-id");
  headers.set("x-request-id", requestId);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

function allowedOrigins(env: Env): Set<string> {
  return new Set(
    (env.ALLOWED_ORIGINS ?? "https://app.chemvault.science")
      .split(",")
      .map((origin) => origin.trim())
      .filter(Boolean),
  );
}

function appendVary(current: string | null, value: string): string {
  if (!current) return value;
  const parts = new Set(current.split(",").map((part) => part.trim()).filter(Boolean));
  parts.add(value);
  return [...parts].join(", ");
}
