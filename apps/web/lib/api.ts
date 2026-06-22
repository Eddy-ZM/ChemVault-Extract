import type {
  Document,
  DocumentBlock,
  DocumentChunk,
  DocumentExtractions,
  DocumentPage,
  ExtractionJob,
  ReviewItem,
} from "@chemvault-extract/schemas";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
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

export function runAiExtraction(id: string): Promise<ExtractionJob> {
  return apiFetch<ExtractionJob>(`/documents/${id}/extract-ai`, { method: "POST" });
}

export function getDocumentExtractions(id: string): Promise<DocumentExtractions> {
  return apiFetch<DocumentExtractions>(`/documents/${id}/extractions`);
}

export function getReviewItems(id: string): Promise<ReviewItem[]> {
  return apiFetch<ReviewItem[]>(`/documents/${id}/review-items`);
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

export { API_BASE_URL };
