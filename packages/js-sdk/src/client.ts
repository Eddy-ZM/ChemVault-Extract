import { ChemVaultError } from "./errors.js";
import { ProjectsResource } from "./resources/projects.js";
import { DocumentsResource } from "./resources/documents.js";
import { ExtractionsResource } from "./resources/extractions.js";
import { RecordsResource } from "./resources/records.js";
import { ExportsResource } from "./resources/exports.js";

export type ChemVaultOptions = {
  apiKey: string;
  baseUrl: string;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
};

export type RequestOptions = {
  query?: Record<string, unknown>;
  body?: Record<string, unknown>;
  formData?: FormData;
};

export class ChemVault {
  apiKey: string;
  baseUrl: string;
  timeoutMs: number;
  fetchImpl: typeof fetch;
  projects: ProjectsResource;
  documents: DocumentsResource;
  extractions: ExtractionsResource;
  records: RecordsResource;
  exports: ExportsResource;

  constructor(options: ChemVaultOptions) {
    if (!options.baseUrl?.trim()) {
      throw new Error(
        "ChemVault Extract API is retired. Provide baseUrl only for an explicitly maintained self-hosted legacy API; use ChemVault Lab for current workflows.",
      );
    }
    this.apiKey = options.apiKey;
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.timeoutMs = options.timeoutMs ?? 30000;
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.projects = new ProjectsResource(this);
    this.documents = new DocumentsResource(this);
    this.extractions = new ExtractionsResource(this);
    this.records = new RecordsResource(this);
    this.exports = new ExportsResource(this);
  }

  async request<T = unknown>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
    const headers = new Headers({ Authorization: `Bearer ${this.apiKey}` });
    let body: BodyInit | undefined;
    if (options.formData) {
      body = options.formData;
    } else if (options.body) {
      headers.set("content-type", "application/json");
      body = JSON.stringify(clean(options.body));
    }
    try {
      const response = await this.fetchImpl(`${this.baseUrl}${path}${queryString(options.query)}`, {
        method,
        headers,
        body,
        signal: controller.signal,
      });
      return await handleResponse<T>(response);
    } finally {
      clearTimeout(timeout);
    }
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  const requestId = response.headers.get("x-request-id");
  if (response.ok) {
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    throw new ChemVaultError(response.statusText || "ChemVault API request failed.", {
      statusCode: response.status,
      requestId,
    });
  }
  if (isErrorPayload(payload)) {
    throw new ChemVaultError(payload.error.message, {
      code: payload.error.code,
      statusCode: response.status,
      details: payload.error.details ?? {},
      requestId,
    });
  }
  throw new ChemVaultError("ChemVault API request failed.", { statusCode: response.status, requestId });
}

function isErrorPayload(value: unknown): value is { error: { code: string; message: string; details?: Record<string, unknown> } } {
  return typeof value === "object" && value !== null && "error" in value;
}

function queryString(query?: Record<string, unknown>): string {
  if (!query) return "";
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null) params.set(key, String(value));
  }
  const rendered = params.toString();
  return rendered ? `?${rendered}` : "";
}

function clean(body: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(body).filter(([, value]) => value !== undefined));
}
