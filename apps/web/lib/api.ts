import type {
  AICostEstimate,
  AIExtractionJobResponse,
  ApiKey,
  ApiRequestLog,
  BatchExtractAIResponse,
  BatchJob,
  BatchJobDetail,
  BatchAIExtractionResponse,
  BatchUploadResponse,
  BillingOverview,
  CheckoutSessionResponse,
  Document,
  DocumentBlock,
  DocumentChunk,
  DocumentExtractions,
  DocumentPage,
  ExtractionJob,
  CurrentMonthUsage,
  DeveloperUsage,
  ExportJob,
  NormalizeResponse,
  NormalizedRecords,
  PortalSessionResponse,
  Project,
  ReviewItem,
  ScientificDatabaseResponse,
  SearchResponse,
  User,
  UserAiSettings,
  WebhookDelivery,
  WebhookEndpoint,
  Workspace,
  WorkspaceDetail,
  WorkspaceMember,
} from "@chemvault-extract/schemas";
import { cookies } from "next/headers";

const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const AUTH_COOKIE_NAME = "chemvault_token";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  const headers = new Headers(init?.headers);
  if (token && !headers.has("authorization")) {
    headers.set("authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `API request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function listDocuments(): Promise<Document[]> {
  return apiFetch<Document[]>("/documents");
}

export function getCurrentUser(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export function listProjects(): Promise<Project[]> {
  return apiFetch<Project[]>("/projects");
}

export function listWorkspaces(): Promise<Workspace[]> {
  return apiFetch<Workspace[]>("/workspaces");
}

export function getWorkspace(id: string): Promise<WorkspaceDetail> {
  return apiFetch<WorkspaceDetail>(`/workspaces/${id}`);
}

export function listWorkspaceMembers(id: string): Promise<WorkspaceMember[]> {
  return apiFetch<WorkspaceMember[]>(`/workspaces/${id}/members`);
}

export function getCurrentMonthUsage(): Promise<CurrentMonthUsage> {
  return apiFetch<CurrentMonthUsage>("/usage/current-month");
}

export function getUserAiSettings(): Promise<UserAiSettings> {
  return apiFetch<UserAiSettings>("/settings/ai");
}

export function listApiKeys(): Promise<ApiKey[]> {
  return apiFetch<ApiKey[]>("/settings/api-keys");
}

export function listWebhookEndpoints(): Promise<WebhookEndpoint[]> {
  return apiFetch<WebhookEndpoint[]>("/settings/webhooks");
}

export function listWebhookDeliveries(endpointId: string): Promise<WebhookDelivery[]> {
  return apiFetch<WebhookDelivery[]>(`/settings/webhooks/${endpointId}/deliveries`);
}

export function listApiRequestLogs(): Promise<ApiRequestLog[]> {
  return apiFetch<ApiRequestLog[]>("/developers/logs");
}

export function getDeveloperUsage(): Promise<DeveloperUsage> {
  return apiFetch<DeveloperUsage>("/developers/usage");
}

export function listExports(): Promise<ExportJob[]> {
  return apiFetch<ExportJob[]>("/exports");
}

export function getBillingOverview(): Promise<BillingOverview> {
  return apiFetch<BillingOverview>("/billing/subscription");
}

export function createCheckoutSession(plan: string, billingInterval: "monthly" | "yearly"): Promise<CheckoutSessionResponse> {
  return apiFetch<CheckoutSessionResponse>("/billing/create-checkout-session", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ plan, billing_interval: billingInterval }),
  });
}

export function createPortalSession(): Promise<PortalSessionResponse> {
  return apiFetch<PortalSessionResponse>("/billing/create-portal-session", { method: "POST" });
}

export function getDocument(id: string): Promise<Document> {
  return apiFetch<Document>(`/documents/${id}`);
}

export function getJob(id: string): Promise<ExtractionJob> {
  return apiFetch<ExtractionJob>(`/jobs/${id}`);
}

export function getDocumentPages(id: string): Promise<DocumentPage[]> {
  return apiFetch<DocumentPage[]>(`/documents/${id}/pages`);
}

export function getDocumentBlocks(id: string): Promise<DocumentBlock[]> {
  return apiFetch<DocumentBlock[]>(`/documents/${id}/blocks`);
}

export function getDocumentTables(id: string): Promise<DocumentBlock[]> {
  return apiFetch<DocumentBlock[]>(`/documents/${id}/tables`);
}

export function getDocumentChunks(id: string): Promise<DocumentChunk[]> {
  return apiFetch<DocumentChunk[]>(`/documents/${id}/chunks`);
}

export function runAiExtraction(id: string): Promise<AIExtractionJobResponse> {
  return apiFetch<AIExtractionJobResponse>(`/documents/${id}/extract-ai`, { method: "POST" });
}

export function runBatchAiExtraction(documentIds: string[]): Promise<BatchAIExtractionResponse> {
  return apiFetch<BatchAIExtractionResponse>("/documents/batch-extract-ai", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ documentIds }),
  });
}

export function listBatchJobs(): Promise<BatchJob[]> {
  return apiFetch<BatchJob[]>("/batch/jobs");
}

export function getBatchJob(id: string): Promise<BatchJobDetail> {
  return apiFetch<BatchJobDetail>(`/batch/jobs/${id}`);
}

export function runProjectBatchAiExtraction(payload: {
  projectId: string;
  documentIds?: string[];
  mode?: string;
}): Promise<BatchExtractAIResponse> {
  return apiFetch<BatchExtractAIResponse>("/batch/extract-ai", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getScientificDatabase(query = ""): Promise<ScientificDatabaseResponse> {
  return apiFetch<ScientificDatabaseResponse>(`/database${query}`);
}

export function searchScientificData(query = ""): Promise<SearchResponse> {
  return apiFetch<SearchResponse>(`/search${query}`);
}

export function estimateAiCost(id: string): Promise<AICostEstimate> {
  return apiFetch<AICostEstimate>(`/documents/${id}/estimate-ai-cost`, { method: "POST" });
}

export function normalizeDocument(id: string, rawData?: Record<string, unknown> | null): Promise<NormalizeResponse> {
  return apiFetch<NormalizeResponse>(`/documents/${id}/normalize`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ rawData: rawData ?? null }),
  });
}

export function getNormalizedRecords(id: string): Promise<NormalizedRecords> {
  return apiFetch<NormalizedRecords>(`/documents/${id}/normalized-records`);
}

export function getDocumentExtractions(id: string): Promise<DocumentExtractions> {
  return apiFetch<DocumentExtractions>(`/documents/${id}/extractions`);
}

export function getReviewItems(id: string): Promise<ReviewItem[]> {
  return apiFetch<ReviewItem[]>(`/documents/${id}/review-items`);
}

export function listReviewItems(): Promise<ReviewItem[]> {
  return apiFetch<ReviewItem[]>("/review-items");
}

export function updateReviewItem(
  id: string,
  payload: { status?: string; extractedData?: Record<string, unknown> },
): Promise<ReviewItem> {
  return apiFetch<ReviewItem>(`/review-items/${id}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function renormalizeRecord(
  recordType: string,
  recordId: string,
  rawData?: Record<string, unknown> | null,
): Promise<NormalizeResponse> {
  return apiFetch<NormalizeResponse>(`/records/${recordType}/${recordId}/renormalize`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ rawData: rawData ?? null }),
  });
}

export { API_BASE_URL };
